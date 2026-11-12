"""T-205b: validação do classificador de tema e da regra de recusa contra uma amostra rotulada à mão (REQ-250).

Fluxo (o texto das conversas nunca sai da máquina nem entra em git/banco):
  1. `python -m analise.validacao planilha`      gera seeds/validacao_manual_em_branco.csv (200 conversas estratificadas; só a
                                                 1ª pergunta e a 1ª resposta, truncadas; SEM os rótulos da máquina). Ignorado pelo git.
  2. O Vinícius preenche `tema_vinicius` e `recusa_vinicius` e salva como seeds/validacao_manual_preenchida.csv (ignorado pelo git).
  3. `python -m analise.validacao anonimizar`    cria seeds/validacao_manual.csv só com conversa_id + rótulos (esse vai para o git).
  4. `python -m analise validacao`               (no compose) compara com o seed de tema e a regra de recusa e grava
                                                 resultado.validacao_classificador: acurácia, kappa de Cohen e matriz de confusão.

Passos 1 e 3 rodam fora do compose (a pasta seeds é montada só leitura lá).
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SNAPSHOT = RAIZ / "data" / "bruto" / "wildchat_brasil.parquet"
SEED_TEMA = RAIZ / "seeds" / "tema_conversa.csv"
REGRAS_RECUSA = RAIZ / "seeds" / "regras_recusa.yaml"
EM_BRANCO = RAIZ / "seeds" / "validacao_manual_em_branco.csv"
PREENCHIDA = RAIZ / "seeds" / "validacao_manual_preenchida.csv"
ROTULOS = RAIZ / "seeds" / "validacao_manual.csv"
PREVISOES = RAIZ / "seeds" / "validacao_previsoes.csv"   # classificador/previsoes_200.py

N_AMOSTRA = 200
N_RECUSA_PREVISTA = 50   # parte da amostra sorteada entre as respostas que a regra marcou como recusa (o resto, entre as que não marcou)
SEMENTE = 20261111
TRUNCAR_TEXTO = 600      # caracteres de pergunta/resposta mostrados na planilha
CABECALHO_PLANILHA = ["id_amostra", "conversa_id", "pergunta", "resposta", "tema_vinicius", "recusa_vinicius"]
CABECALHO_ROTULOS = ["conversa_id", "tema_vinicius", "recusa_vinicius"]
DELIMITADOR = ";"        # Excel em português abre CSV com ponto e vírgula


# ----------------------------------------------------------------------------------------------- métricas (puras)
def matriz_confusao(humano: list[str], maquina: list[str]) -> dict[str, dict[str, int]]:
    """{rótulo humano: {rótulo da máquina: contagem}}."""
    m: dict[str, Counter] = defaultdict(Counter)
    for h, q in zip(humano, maquina):
        m[h][q] += 1
    return {h: dict(c) for h, c in sorted(m.items())}


def acuracia(humano: list[str], maquina: list[str]) -> float:
    return sum(h == q for h, q in zip(humano, maquina)) / len(humano)


def kappa_cohen(humano: list[str], maquina: list[str]) -> float:
    """Concordância além do acaso: (po - pe) / (1 - pe). 1,0 se os dois só usam um mesmo rótulo."""
    n = len(humano)
    po = sum(h == q for h, q in zip(humano, maquina)) / n
    ch, cq = Counter(humano), Counter(maquina)
    pe = sum(ch[r] * cq[r] for r in set(ch) | set(cq)) / n**2
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def por_classe(humano: list[str], maquina: list[str]) -> dict[str, dict]:
    """Por rótulo: n (humano), precisão, revocação — para decidir quais classes fundir."""
    out = {}
    for r in sorted(set(humano) | set(maquina)):
        tp = sum(1 for h, q in zip(humano, maquina) if h == r and q == r)
        n_h, n_q = sum(1 for h in humano if h == r), sum(1 for q in maquina if q == r)
        out[r] = {"n_humano": n_h, "n_maquina": n_q,
                  "precisao": round(tp / n_q, 4) if n_q else None, "revocacao": round(tp / n_h, 4) if n_h else None}
    return out


def resumo_metricas(humano: list[str], maquina: list[str]) -> dict:
    return {"n": len(humano), "acuracia": round(acuracia(humano, maquina), 6), "kappa": round(kappa_cohen(humano, maquina), 6),
            "matriz_confusao": matriz_confusao(humano, maquina), "por_classe": por_classe(humano, maquina)}


# ----------------------------------------------------------------------------------------------- amostra
def sortear_estratificada(candidatos: list[tuple[int, str, bool]], n_total: int, n_recusa: int, semente: int = SEMENTE) -> list[int]:
    """candidatos = (conversa_id, tema previsto, recusa prevista). Devolve conversa_id sorteados: `n_recusa` entre os de recusa
    prevista e o resto entre os demais, ambos espalhados por igual entre os temas previstos (revezamento entre os estratos).
    Se um estrato esvazia, os outros cobrem; se faltar candidato, devolve menos que n_total."""
    rng = random.Random(semente)
    escolhidos: list[int] = []
    for com_recusa, quantos in ((True, n_recusa), (False, n_total - n_recusa)):
        estratos: dict[str, list[int]] = defaultdict(list)
        for cid, t, r in sorted(candidatos):
            if r == com_recusa:
                estratos[t].append(cid)
        for lista in estratos.values():
            rng.shuffle(lista)
        nomes = sorted(estratos)
        pegos = 0
        while pegos < quantos and any(estratos[n] for n in nomes):
            for nome in nomes:
                if pegos < quantos and estratos[nome]:
                    escolhidos.append(estratos[nome].pop())
                    pegos += 1
    return escolhidos


# ----------------------------------------------------------------------------------------------- leitura do bruto (local)
def _padroes_recusa(caminho: Path = REGRAS_RECUSA) -> tuple[str, list[str]]:
    """Mesma leitura de loader.carregar.carregar_regras_recusa (repetida aqui para não puxar psycopg nos passos locais)."""
    import yaml

    dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    return str(dados["versao"]), [p.lower() for grupo in dados["padroes"].values() for p in grupo]


def _ler_seed(caminho: Path = SEED_TEMA) -> dict[int, tuple[str, str]]:
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return {int(l["conversa_id"]): (l["tema"], l["tema_origem"]) for l in csv.DictReader(f)}


_CONSULTA = """
SELECT conversation[1].turn_identifier AS conversa_id,
       list_transform(list_filter(conversation, lambda t: t.role = 'user'), lambda t: t.content) AS mensagens,
       list_filter(conversation, lambda t: t.role = 'assistant')[1].content AS resposta_1
FROM read_parquet(?)
"""


def _conversas_do_bruto(snapshot: Path):
    import duckdb

    con = duckdb.connect()
    con.execute("SET memory_limit='1GB'")
    try:
        return con.execute(_CONSULTA, [snapshot.as_posix()]).fetchall()
    finally:
        con.close()


def gerar_planilha(saida: Path = EM_BRANCO, snapshot: Path = SNAPSHOT, seed: Path = SEED_TEMA) -> dict:
    """Escreve a planilha em branco. Devolve só agregados (quantas por tema previsto e por recusa prevista)."""
    sys.path.insert(0, str(RAIZ))
    from classificador.tema import primeira_pergunta
    from loader.derivar import detectar_recusa

    _, padroes = _padroes_recusa()
    temas = _ler_seed(seed)
    textos: dict[int, tuple[str, str]] = {}
    candidatos: list[tuple[int, str, bool]] = []
    for cid, mensagens, resposta in _conversas_do_bruto(snapshot):
        if cid not in temas:
            continue
        pergunta = primeira_pergunta(mensagens)
        textos[cid] = ((pergunta or "")[:TRUNCAR_TEXTO], (resposta or "")[:TRUNCAR_TEXTO])
        candidatos.append((cid, temas[cid][0], detectar_recusa(resposta, padroes)))
    escolhidos = sortear_estratificada(candidatos, N_AMOSTRA, N_RECUSA_PREVISTA)
    random.Random(SEMENTE + 1).shuffle(escolhidos)  # a ordem não revela o estrato
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=DELIMITADOR, quoting=csv.QUOTE_ALL)
        w.writerow(CABECALHO_PLANILHA)
        for i, cid in enumerate(escolhidos, start=1):
            w.writerow([i, cid, textos[cid][0], textos[cid][1], "", ""])
    previsto = {c: (t, r) for c, t, r in candidatos}
    return {"n": len(escolhidos), "por_tema_previsto": dict(Counter(previsto[c][0] for c in escolhidos)),
            "recusa_prevista": sum(1 for c in escolhidos if previsto[c][1])}


# ----------------------------------------------------------------------------------------------- rótulos
def normalizar_recusa(valor: str) -> str:
    v = (valor or "").strip().lower()
    if v in ("sim", "s", "1", "true", "recusa", "y", "yes"):
        return "sim"
    if v in ("não", "nao", "n", "0", "false", "nao recusa", "no"):
        return "não"
    raise ValueError(f"recusa_vinicius inválida: {valor!r} (use sim ou não)")


def anonimizar(preenchida: Path = PREENCHIDA, saida: Path = ROTULOS) -> int:
    """Copia só conversa_id + rótulos da planilha preenchida para o arquivo que vai para o git. Falha se faltar rótulo."""
    from classificador.tema import TAXONOMIA

    linhas = []
    with Path(preenchida).open(encoding="utf-8-sig", newline="") as f:
        for l in csv.DictReader(f, delimiter=DELIMITADOR):
            tema = (l["tema_vinicius"] or "").strip()
            if tema not in TAXONOMIA:
                raise ValueError(f"tema_vinicius inválido na amostra {l['id_amostra']}: {tema!r} (use um dos {len(TAXONOMIA)} temas, escrito igual)")
            linhas.append([l["conversa_id"], tema, normalizar_recusa(l["recusa_vinicius"])])
    with Path(saida).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECALHO_ROTULOS)
        w.writerows(linhas)
    return len(linhas)


def ler_rotulos(caminho: Path = ROTULOS) -> dict[int, tuple[str, str]]:
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return {int(l["conversa_id"]): (l["tema_vinicius"], l["recusa_vinicius"]) for l in csv.DictReader(f)}


# ----------------------------------------------------------------------------------------------- gravação no banco
def ler_previsoes(caminho: Path = PREVISOES) -> dict[str, dict[int, tuple[str, str]]]:
    """classificador -> {conversa_id: (tema, 'sim'|'não' de recusa)} nas 200; versão por classificador em `versoes`."""
    saida: dict[str, dict[int, tuple[str, str]]] = {}
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        for l in csv.DictReader(f):
            saida.setdefault(l["classificador"], {})[int(l["conversa_id"])] = (l["tema"], "sim" if l["recusa"] == "true" else "não")
    return saida


def _versoes(caminho: Path = PREVISOES) -> dict[str, str]:
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return {l["classificador"]: l["versao"] for l in csv.DictReader(f)}


def validar(conn, rotulos: Path = ROTULOS, previsoes: Path = PREVISOES) -> list[dict]:
    """Compara os rótulos do Vinícius com CADA classificador nas 200 completas e grava em resultado.validacao_classificador.

    Uma linha por (tipo, classificador): `classificador` = 'tema' ou 'recusa'; `modelo` = 'regras' ou 'openrouter:<modelo>'.
    As previsões vêm de `seeds/validacao_previsoes.csv` (regras aplicadas na hora às 200; LLM do cache), não do seed de tema.
    """
    from analise.gravar import substituir

    humanos = ler_rotulos(rotulos)
    ids = sorted(humanos)
    prev = ler_previsoes(previsoes)
    versoes = _versoes(previsoes)
    resultados = []
    for origem in sorted(prev, key=lambda o: (o != "regras", o)):
        if set(prev[origem]) != set(ids):
            raise ValueError(f"{origem}: previsões não cobrem as {len(ids)} conversas rotuladas")
        v_tema, _, v_rec = versoes[origem].partition("|")
        for nome, pos, versao in (("tema", 0, v_tema), ("recusa", 1, v_rec or v_tema)):
            m = resumo_metricas([humanos[i][pos] for i in ids], [prev[origem][i][pos] for i in ids])
            resultados.append({"classificador": nome, "n": m["n"], "acuracia": m["acuracia"], "kappa": m["kappa"],
                               "detalhe_json": json.dumps({"matriz_confusao": m["matriz_confusao"], "por_classe": m["por_classe"]}, ensure_ascii=False),
                               "versao_prompt": versao, "modelo": origem if origem != "regras" else f"regras:{v_tema}" if nome == "tema" else "regras"})
    cols = ["classificador", "n", "acuracia", "kappa", "detalhe_json", "versao_prompt", "modelo"]
    substituir(conn, "validacao_classificador", cols, [[r[c] for c in cols] for r in resultados])
    return resultados


def main(argv: list[str]) -> int:
    if argv[:1] == ["planilha"]:
        r = gerar_planilha()
        print(f"planilha em branco gravada em {EM_BRANCO} ({r['n']} conversas; {r['recusa_prevista']} com recusa prevista pela regra)")
        for t, n in sorted(r["por_tema_previsto"].items()):
            print(f"  {t:<32} {n:>4}")
        return 0
    if argv[:1] == ["anonimizar"]:
        sys.path.insert(0, str(RAIZ))
        print(f"{anonimizar()} rótulos gravados em {ROTULOS}")
        return 0
    print("uso: python -m analise.validacao planilha | anonimizar", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
