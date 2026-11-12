"""Rodada grande do classificador LLM: tema + recusa das 1ªs conversas que entram em algum número (união das 4 definições, T-208).

Roda local contra o db do compose (porta do host) e o snapshot. Grava o seed `seeds/tema_conversa.csv` com colunas extras
`recusa` e `recusa_origem`; as demais conversas ficam com tema das regras e recusa em branco (= regra de palavras-chave).
Nenhum texto de conversa é impresso ou gravado; só agregados.

Uso:  python -m classificador.rodada_llm <id do modelo na OpenRouter> [--simular-custo]
Teto: LLM_TETO_USD (padrão US$ 3,00). Conversa já classificada (cache) nunca é reenviada.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEED = RAIZ / "seeds" / "tema_conversa.csv"
CABECALHO = ["conversa_id", "tema", "tema_origem", "versao_prompt", "recusa", "recusa_origem"]


def montar_seed(linhas_antigas: list[dict], resultados: dict[int, object], origem: str, versao_prompt: str) -> list[list]:
    """Linhas do novo seed. `resultados`: conversa_id -> objeto com .tema, .recusa, .origem (openrouter:<modelo> ou regras-fallback).
    Só as respostas do LLM substituem a linha; falha (regras-fallback) mantém a linha antiga, de regras."""
    saida = []
    for l in linhas_antigas:
        cid = int(l["conversa_id"])
        r = resultados.get(cid)
        if r is not None and r.origem == origem:
            saida.append([cid, r.tema, origem, versao_prompt, "true" if r.recusa else "false", origem])
        else:
            saida.append([cid, l["tema"], l.get("tema_origem", ""), l.get("versao_prompt", ""), "", ""])
    return saida


def ler_seed(caminho: Path = SEED) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def gravar_seed(linhas: list[list], caminho: Path = SEED) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECALHO)
        w.writerows(linhas)


def main(argv: list[str]) -> int:
    if not argv:
        print("uso: python -m classificador.rodada_llm <modelo> [--simular-custo]", file=sys.stderr)
        return 2
    sys.path.insert(0, str(RAIZ))
    import psycopg

    from analise import uniao_definicoes as U
    from analise import validacao as V
    from classificador import openrouter as O
    from classificador.tema import primeira_pergunta
    from loader.derivar import detectar_recusa
    from loader.migrar import dsn

    modelo, simular = argv[0], "--simular-custo" in argv
    if "--ids" in argv:  # lista de conversa_id (um por linha) gerada por `--listar-ids` dentro do compose
        ids = {int(l) for l in Path(argv[argv.index("--ids") + 1]).read_text().split() if l.strip()}
    else:
        with psycopg.connect(dsn(), autocommit=True) as conn:
            por_def = U.calcular(conn)
        ids = U.uniao(por_def)
        print("conversas por definição:", U.contagens(por_def), file=sys.stderr)
        if "--listar-ids" in argv:
            print(*sorted(ids), sep="\n")
            return 0

    textos = {}
    for cid, mensagens, resposta in V._conversas_do_bruto(V.SNAPSHOT):
        if cid in ids:
            textos[cid] = (primeira_pergunta(mensagens) or "", resposta or "")
    faltam = ids - set(textos)
    if faltam:
        raise ValueError(f"{len(faltam)} conversas da união não estão no snapshot")

    pr = next((m for m in O.listar_modelos() if m["id"] == modelo), None)
    if pr is None:
        print(f"modelo {modelo!r} não está em GET /api/v1/models", file=sys.stderr)
        return 1
    _, padroes = V._padroes_recusa()
    paralelo = int(argv[argv.index("--paralelo") + 1]) if "--paralelo" in argv else 1
    timeout = int(argv[argv.index("--timeout") + 1]) if "--timeout" in argv else 120
    cl = O.criar(modelo, pr["preco_entrada_por_milhao"], pr["preco_saida_por_milhao"], timeout=timeout,
                 recusa_por_regra=lambda r: detectar_recusa(r, padroes))
    ja_no_cache = sum(1 for c in ids if c in cl.cache)
    print(f"{len(ids)} conversas a classificar; {ja_no_cache} já no cache; teto US$ {cl.teto_usd:.2f}; gasto acumulado US$ {cl.gasto_usd:.4f}")
    if simular:
        return 0
    itens = [(cid, *textos[cid]) for cid in sorted(ids)]
    res = {}
    try:
        res = cl.classificar_lote(itens, paralelismo=paralelo)
    except O.TetoAtingido as e:
        print(f"PAROU no teto: {e}", file=sys.stderr)
        res = {c: O.Resultado(*cl.cache[c], cl.origem) for c in cl.cache if c in ids}
    n_llm = sum(1 for r in res.values() if r.origem == cl.origem)
    print(f"classificadas pelo LLM: {n_llm}/{len(ids)}; fallback: {len(ids) - n_llm}; gasto total US$ {cl.gasto_usd:.4f}")
    erros = {}
    with (O.PASTA_CACHE / "chamadas.csv").open(encoding="utf-8", newline="") as f:
        for l in csv.DictReader(f):
            if l["modelo"] == cl.origem and l["status"].startswith("erro:"):
                erros[l["status"]] = erros.get(l["status"], 0) + 1
    print("erros por tipo (log inteiro do modelo):", erros or "nenhum")
    gravar_seed(montar_seed(ler_seed(), res, cl.origem, O.PROMPT_VERSAO))
    print(f"seed gravado em {SEED}")
    return 0 if n_llm == len(ids) else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
