"""Etapa 1 do provedor openrouter: valida modelos candidatos SÓ nas 200 conversas rotuladas pelo Vinícius, lado a lado com `regras`.

Roda local (DuckDB no snapshot, sem banco). Imprime e grava `docs/validacao_llm.md` com agregados: nenhum texto de conversa.

Uso:  python -m classificador.validar_llm <especificação>[,<especificação>...]
  openrouter:  <id da OpenRouter>                          ex.: anthropic/claude-haiku-5.5      (OPENROUTER_API_KEY)
  bedrock:     bedrock:<id do Bedrock>@<id OpenRouter>     o id depois do @ só empresta o PREÇO (o Bedrock não lista preço pela API de modelos)
               (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION no ambiente ou .env; as chaves nunca são impressas)
Preços por milhão de tokens vêm de GET /api/v1/models na hora (nada de preço de memória).

Duas leituras de cada métrica:
  crua        sobre as 200 como estão;
  ponderada   a amostra foi estratificada pela previsão das regras (recusa prevista × tema previsto); cada conversa pesa
              N_estrato / n_estrato (população de conversas que contam como uso / amostra), o que estima a métrica na população.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from analise import validacao as V
from classificador import openrouter as O
from classificador.tema import INDEFINIDO, TAXONOMIA, primeira_pergunta

RAIZ = V.RAIZ
SAIDA = RAIZ / "docs" / "validacao_llm.md"


# ----------------------------------------------------------------------------------------------- métricas ponderadas (puras)
def pesos_por_estrato(estrato_amostra: dict[int, tuple], populacao: Counter) -> dict[int, float]:
    """Peso de cada conversa da amostra = N_estrato / n_estrato."""
    n = Counter(estrato_amostra.values())
    return {cid: populacao[e] / n[e] for cid, e in estrato_amostra.items()}


def acuracia_ponderada(humano: dict[int, str], maquina: dict[int, str], peso: dict[int, float]) -> float:
    return sum(peso[i] for i in humano if humano[i] == maquina[i]) / sum(peso[i] for i in humano)


def precisao_revocacao_ponderadas(humano: dict[int, bool], maquina: dict[int, bool], peso: dict[int, float]) -> tuple[float | None, float | None]:
    """Precisão e revocação da classe positiva (recusa = True) com peso por estrato."""
    tp = sum(peso[i] for i in humano if humano[i] and maquina[i])
    pred = sum(peso[i] for i in humano if maquina[i])
    real = sum(peso[i] for i in humano if humano[i])
    return (tp / pred if pred else None), (tp / real if real else None)


def precisao_revocacao(humano: dict[int, bool], maquina: dict[int, bool]) -> tuple[float | None, float | None]:
    return precisao_revocacao_ponderadas(humano, maquina, {i: 1.0 for i in humano})


# ----------------------------------------------------------------------------------------------- dados locais
def carregar_amostra(snapshot: Path = V.SNAPSHOT):
    """(humanos, textos, regras, populacao): rótulos do Vinícius; (pergunta, resposta) truncados; previsão das regras
    (tema, recusa) das 200 e contagem da população por estrato (recusa prevista, tema previsto)."""
    from loader.derivar import detectar_recusa

    humanos = V.ler_rotulos()
    _, padroes = V._padroes_recusa()
    temas = V._ler_seed()
    textos, regras, populacao = {}, {}, Counter()
    for cid, mensagens, resposta in V._conversas_do_bruto(snapshot):
        if cid not in temas:
            continue
        est = (detectar_recusa(resposta, padroes), temas[cid][0])
        populacao[est] += 1
        if cid in humanos:
            textos[cid] = ((primeira_pergunta(mensagens) or ""), (resposta or ""))
            regras[cid] = est[::-1]  # (tema, recusa)
    faltam = set(humanos) - set(textos)
    if faltam:
        raise ValueError(f"{len(faltam)} conversas rotuladas não estão no snapshot")
    return humanos, textos, regras, populacao


def avaliar(nome: str, humanos, previsto: dict[int, tuple[str, bool]], peso: dict[int, float], extra: dict | None = None) -> dict:
    ids = sorted(humanos)
    h_tema = [humanos[i][0] for i in ids]
    m_tema = [previsto[i][0] for i in ids]
    h_rec = {i: humanos[i][1] == "sim" for i in ids}
    m_rec = {i: previsto[i][1] for i in ids}
    p, r = precisao_revocacao(h_rec, m_rec)
    pp, rp = precisao_revocacao_ponderadas(h_rec, m_rec, peso)
    h_rec_txt = ["sim" if h_rec[i] else "não" for i in ids]
    m_rec_txt = ["sim" if m_rec[i] else "não" for i in ids]
    return {
        "nome": nome,
        "tema_acuracia": V.acuracia(h_tema, m_tema), "tema_kappa": V.kappa_cohen(h_tema, m_tema),
        "tema_acuracia_pond": acuracia_ponderada({i: humanos[i][0] for i in ids}, {i: previsto[i][0] for i in ids}, peso),
        "recusa_acuracia": V.acuracia(h_rec_txt, m_rec_txt), "recusa_kappa": V.kappa_cohen(h_rec_txt, m_rec_txt),
        "recusa_precisao": p, "recusa_revocacao": r, "recusa_precisao_pond": pp, "recusa_revocacao_pond": rp,
        **(extra or {}),
    }


def _fmt(x, pct=True) -> str:
    if x is None:
        return "n/d"
    return f"{100 * x:.1f}%".replace(".", ",") if pct else f"{x:.2f}".replace(".", ",")


def tabela(linhas: list[dict]) -> str:
    cab = ("| Classificador | Tema acurácia (crua / pond.) | Tema kappa | Recusa acurácia | Recusa kappa | Recusa precisão (crua / pond.) | "
           "Recusa revocação (crua / pond.) | Falhas | Custo (200) |\n|---|---|---|---|---|---|---|---|---|")
    out = [cab]
    for l in linhas:
        out.append(f"| {l['nome']} | {_fmt(l['tema_acuracia'])} / {_fmt(l['tema_acuracia_pond'])} | {_fmt(l['tema_kappa'], False)} | "
                   f"{_fmt(l['recusa_acuracia'])} | {_fmt(l['recusa_kappa'], False)} | {_fmt(l['recusa_precisao'])} / {_fmt(l['recusa_precisao_pond'])} | "
                   f"{_fmt(l['recusa_revocacao'])} / {_fmt(l['recusa_revocacao_pond'])} | {l.get('falhas', '—')} | {l.get('custo', '—')} |")
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------- execução
def rodar_modelo(modelo: str, preco_in: float, preco_out: float, textos, pasta: Path | None = None,
                 provedor: str = "openrouter") -> tuple[dict[int, O.Resultado], O.ClassificadorOpenRouter]:
    from loader.derivar import detectar_recusa

    _, padroes = V._padroes_recusa()
    fabrica = O.criar_bedrock if provedor == "bedrock" else O.criar
    cl = fabrica(modelo, preco_in, preco_out, recusa_por_regra=lambda r: detectar_recusa(r, padroes), **({"pasta": pasta} if pasta else {}))
    itens = [(cid, p, r) for cid, (p, r) in sorted(textos.items())]
    return cl.classificar_lote(itens), cl


def main(argv: list[str]) -> int:
    if not argv:
        print("uso: python -m classificador.validar_llm <modelo>[,<modelo>...]", file=sys.stderr)
        return 2
    especs = argv[0].split(",")
    if any(not e.startswith("bedrock:") for e in especs) and not O.chave_existe():
        print("OPENROUTER_API_KEY não encontrada (ambiente ou .env)", file=sys.stderr)
        return 1
    if any(e.startswith("bedrock:") for e in especs) and not O.credenciais_aws_existem():
        print("credenciais AWS não encontradas (AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY no ambiente ou .env)", file=sys.stderr)
        return 1
    humanos, textos, regras, populacao = carregar_amostra()
    peso = pesos_por_estrato({i: regras[i][::-1] for i in humanos}, populacao)  # estrato = (recusa prevista, tema previsto)
    # a chave do estrato na população é (recusa, tema); na amostra, regras[i] = (tema, recusa) -> inverter
    linhas = [avaliar("regras (linha de base)", humanos, regras, peso)]
    precos = {m["id"]: m for m in O.listar_modelos()}
    for espec in especs:
        provedor, modelo, preco_id = "openrouter", espec, espec
        if espec.startswith("bedrock:"):
            provedor, resto = "bedrock", espec[len("bedrock:"):]
            modelo, _, preco_id = resto.partition("@")
        if preco_id not in precos:
            print(f"id {preco_id!r} (para o preço) não está em GET /api/v1/models", file=sys.stderr)
            return 1
        pr = precos[preco_id]
        res, cl = rodar_modelo(modelo, pr["preco_entrada_por_milhao"], pr["preco_saida_por_milhao"], textos, provedor=provedor)
        previsto = {i: (res[i].tema, res[i].recusa) for i in humanos}
        n_fallback = sum(1 for r in res.values() if r.origem == "regras-fallback")
        linhas.append(avaliar(f"{provedor}:{modelo}", humanos, previsto, peso, {
            "falhas": f"{n_fallback}/{len(res)} em fallback", "custo": f"US$ {cl.gasto_usd:.4f}".replace(".", ",")}))
        print(f"{modelo}: preço por milhão (entrada/saída) US$ {pr['preco_entrada_por_milhao']:.3f} / {pr['preco_saida_por_milhao']:.3f}; "
              f"gasto US$ {cl.gasto_usd:.4f}; fallback {n_fallback}/{len(res)}")
    texto = ("# Validação do classificador LLM (200 conversas rotuladas)\n\nGerado por `python -m classificador.validar_llm`; só agregados.\n"
             f"Truncamento {O.TRUNCAR_EM} caracteres, lote de {O.TAMANHO_LOTE}, prompt {O.PROMPT_VERSAO}, temperatura 0.\n\n" + tabela(linhas) + "\n")
    SAIDA.write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(RAIZ))
    sys.exit(main(sys.argv[1:]))
