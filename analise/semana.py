"""T-207: uma semana de coorte contra as 4 anteriores — decomposição de Kitagawa (mix × taxa), teste de duas proporções e veredito.

Pergunta do case: "o retorno caiu naquela semana; por quê?". A queda pode vir de MUDANÇA DE PERFIL (chegou mais gente de um
segmento que volta menos: efeito de mix) ou de MUDANÇA DE COMPORTAMENTO dentro dos segmentos (efeito de taxa) ou ser só ruído
(base pequena: ~50 usuários novos por semana). Segmento = dispositivo × família de modelo.

Kitagawa (simétrico, fecha exatamente): Δ = Σ (Δpeso_s × taxa média_s)  [mix]  +  Σ (peso médio_s × Δtaxa_s)  [taxa].
Segmento sem usuários em um dos lados herda a taxa do outro lado (não gera efeito de taxa); segmentos com menos de n_minimo
usuários (base + semana) viram "outros".

Uso:  python -m analise semana [AAAA-MM-DD ...]     (sem argumento: as semanas candidatas abaixo)
"""
from __future__ import annotations

from datetime import date, timedelta
from math import sqrt

import pandas as pd
import psycopg
from scipy.stats import norm

from analise.bruto import n_minimo
from analise.gravar import substituir

# 20/11/2023 é a semana que o case cita; 01/05/2023 e 17/07/2023 saíram do discovery (T-106/T-107: as de menor retorno com n >= 30).
SEMANAS_CANDIDATAS = [date(2023, 11, 20), date(2023, 5, 1), date(2023, 7, 17)]
SEMANAS_BASE = 4
ROTULO_RARO = "outros"

SQL = """
SELECT d.coorte_semana AS semana, f.dispositivo, f.modelo_familia, f.voltou_7d, a.inicio_coleta
FROM mart.fct_primeira_experiencia f JOIN mart.dim_usuario d USING (usuario_id)
JOIN mart.agg_retencao_periodo a ON a.granularidade = 'semana' AND a.periodo = d.coorte_semana
WHERE f.elegivel
"""


# ----------------------------------------------------------------------------------------------- regras puras
def teste_duas_proporcoes(k1: int, n1: int, k2: int, n2: int) -> float:
    """p-valor bilateral do teste z de duas proporções (variância combinada). 1,0 se as taxas combinadas forem 0 ou 1."""
    p = (k1 + k2) / (n1 + n2)
    if p in (0.0, 1.0):
        return 1.0
    z = (k1 / n1 - k2 / n2) / sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return float(2 * norm.sf(abs(z)))


def kitagawa(base: dict[str, tuple[int, int]], semana: dict[str, tuple[int, int]]) -> tuple[list[dict], dict]:
    """Decompõe taxa_semana - taxa_base. Entradas: segmento -> (n, voltaram). Devolve (linhas por segmento, totais em fração)."""
    nb, ns = sum(n for n, _ in base.values()), sum(n for n, _ in semana.values())
    linhas = []
    for seg in sorted(set(base) | set(semana)):
        n_b, k_b = base.get(seg, (0, 0))
        n_s, k_s = semana.get(seg, (0, 0))
        r_b = k_b / n_b if n_b else (k_s / n_s if n_s else 0.0)
        r_s = k_s / n_s if n_s else r_b
        w_b, w_s = n_b / nb, n_s / ns
        linhas.append({
            "segmento": seg, "peso_base": w_b, "peso_semana": w_s, "taxa_base": r_b, "taxa_semana": r_s,
            "efeito_mix": (w_s - w_b) * (r_b + r_s) / 2, "efeito_taxa": (w_b + w_s) / 2 * (r_s - r_b),
        })
    taxa_b = sum(k for _, k in base.values()) / nb
    taxa_s = sum(k for _, k in semana.values()) / ns
    return linhas, {"taxa_base": taxa_b, "taxa_semana": taxa_s, "delta": taxa_s - taxa_b,
                    "mix": sum(l["efeito_mix"] for l in linhas), "taxa": sum(l["efeito_taxa"] for l in linhas)}


def agrupar_segmentos_raros(base: dict, semana: dict, n_min: int) -> tuple[dict, dict]:
    """Segmentos com (n base + n semana) < n_min viram 'outros' nos dois lados."""
    raros = {s for s in set(base) | set(semana) if base.get(s, (0, 0))[0] + semana.get(s, (0, 0))[0] < n_min}
    if len(raros) < 2:
        return base, semana

    def junta(d: dict) -> dict:
        out: dict[str, tuple[int, int]] = {}
        for s, (n, k) in d.items():
            c = ROTULO_RARO if s in raros else s
            a = out.get(c, (0, 0))
            out[c] = (a[0] + n, a[1] + k)
        return out
    return junta(base), junta(semana)


def veredito(taxa_base: float, taxa_semana: float, n_base: int, n_semana: int, mix_pp: float, taxa_pp: float, p: float,
             n_semanas: int, n_sig: int, base_rotulo: str = "nas semanas anteriores") -> str:
    """Texto para o cliente (sem jargão estatístico): quanto voltou, de onde veio a diferença e se dá para distinguir de ruído.

    Os números técnicos (mix, taxa, p-valor, IC) ficam nas colunas numéricas da tabela; aqui só linguagem simples.
    """
    por_100 = lambda x: f"{round(x * 100):d}"  # noqa: E731
    queda = taxa_semana < taxa_base
    s1 = (f"Nesta semana, {por_100(taxa_semana)} de cada 100 novos usuários ({n_semana} no total) voltaram, contra "
          f"{por_100(taxa_base)} de cada 100 {base_rotulo} ({n_base} usuários).")
    total = abs(mix_pp) + abs(taxa_pp)
    parte_comportamento = abs(taxa_pp) / total if total else 0.0
    movimento = "queda" if queda else "subida"
    if parte_comportamento >= 0.8:
        s2 = (f"Quase toda a {movimento} veio de as pessoas {'voltarem menos' if queda else 'voltarem mais'}, "
              f"não de ter chegado um público diferente.")
    elif parte_comportamento <= 0.2:
        s2 = (f"Quase toda a {movimento} veio de ter chegado um público diferente (outra mistura de celular, computador e modelo), "
              f"não de as pessoas terem mudado de comportamento.")
    else:
        s2 = f"Parte da {movimento} veio de um público diferente e parte de as pessoas terem mudado de comportamento."
    if p < 0.05:
        esperado = max(1, round(0.05 * n_semanas))
        s3 = (f"A {movimento} é maior do que a variação normal entre semanas, mas, olhando todas as {n_semanas} semanas com amostra "
              f"suficiente, {n_sig} tiveram uma diferença assim e só pelo acaso se esperam cerca de {esperado}: não dá para descartar coincidência.")
    else:
        s3 = ("A diferença está dentro da variação normal entre semanas: com tão poucos usuários por semana, "
              "não dá para afirmar que houve uma mudança real.")
    return f"{s1} {s2} {s3}"


# ----------------------------------------------------------------------------------------------- dados
def _contagens(df: pd.DataFrame) -> dict[str, tuple[int, int]]:
    seg = df["dispositivo"].astype(str) + " × " + df["modelo_familia"].astype(str)
    g = df.assign(seg=seg).groupby("seg")["voltou_7d"].agg(["size", "sum"])
    return {s: (int(r["size"]), int(r["sum"])) for s, r in g.iterrows()}


def _limpas(df: pd.DataFrame) -> pd.DataFrame:
    """BDR-09: semanas que começam a menos de 28 dias do 1º dado (inicio_coleta) nunca servem de base: podem ter usuários antigos como novos."""
    return df[~df["inicio_coleta"].astype(bool)] if "inicio_coleta" in df.columns else df


def _base_da_semana(df: pd.DataFrame, semana: date) -> pd.DataFrame:
    ini = semana - timedelta(weeks=SEMANAS_BASE)
    return _limpas(df[(df["semana"] >= ini) & (df["semana"] < semana)])


def _base_seguintes(df: pd.DataFrame, semana: date) -> pd.DataFrame:
    fim = semana + timedelta(weeks=SEMANAS_BASE + 1)
    return _limpas(df[(df["semana"] > semana) & (df["semana"] < fim)])


def contar_semanas_significativas(df: pd.DataFrame, n_min: int) -> tuple[int, int]:
    """Aplica o mesmo teste a TODA semana com n >= n_min e base >= n_min: devolve (semanas testadas, quantas com p < 0,05)."""
    testadas = sig = 0
    for s in sorted(df["semana"].unique()):
        a, b = df[df["semana"] == s], _base_da_semana(df, s)
        if len(a) < n_min or len(b) < n_min:
            continue
        testadas += 1
        if teste_duas_proporcoes(int(a["voltou_7d"].sum()), len(a), int(b["voltou_7d"].sum()), len(b)) < 0.05:
            sig += 1
    return testadas, sig


def decompor(df: pd.DataFrame, semana: date, n_min: int, contra_seguintes: bool = False) -> tuple[dict, list[dict]]:
    """Resumo + linhas por segmento da `semana` contra as 4 semanas de coorte anteriores sem início de coleta (ou, com
    `contra_seguintes`, as 4 seguintes: usado quando a semana é do início da coleta e não há base anterior limpa)."""
    sem = df[df["semana"] == semana]
    base = _base_seguintes(df, semana) if contra_seguintes else _base_da_semana(df, semana)
    if sem.empty or base.empty:
        raise ValueError(f"semana {semana} sem usuários elegíveis ou sem base de comparação")
    b_cont, s_cont = agrupar_segmentos_raros(_contagens(base), _contagens(sem), n_min)
    linhas, tot = kitagawa(b_cont, s_cont)
    n_b, n_s = len(base), len(sem)
    k_b, k_s = int(base["voltou_7d"].sum()), int(sem["voltou_7d"].sum())
    p = teste_duas_proporcoes(k_s, n_s, k_b, n_b)
    testadas, sig = contar_semanas_significativas(df, n_min)
    delta, mix, taxa = (round(tot[k] * 100, 4) for k in ("delta", "mix", "taxa"))
    semanas_base = sorted(base["semana"].unique())
    qual = "seguintes (a semana é do início da coleta; não há base anterior limpa)" if contra_seguintes else "anteriores"
    resumo = {
        "semana": semana,
        "base_descricao": f"{len(semanas_base)} semanas de coorte {qual} ({semanas_base[0]:%d/%m/%Y} a {semanas_base[-1]:%d/%m/%Y}), só elegíveis, sem início de coleta",
        "n_base": n_b, "n_semana": n_s, "taxa_base": round(tot["taxa_base"], 6), "taxa_semana": round(tot["taxa_semana"], 6),
        "delta_pp": delta, "mix_pp": mix, "taxa_pp": taxa, "p_valor": round(p, 6),
        "conclusao": veredito(tot["taxa_base"], tot["taxa_semana"], n_b, n_s, mix, taxa, p, testadas, sig,
                              "nas semanas seguintes" if contra_seguintes else "nas semanas anteriores"),
    }
    segs = [{"semana": semana, "segmento": l["segmento"], "peso_base": round(l["peso_base"], 6), "peso_semana": round(l["peso_semana"], 6),
             "taxa_base": round(l["taxa_base"], 6), "taxa_semana": round(l["taxa_semana"], 6),
             "efeito_mix_pp": round(l["efeito_mix"] * 100, 4), "efeito_taxa_pp": round(l["efeito_taxa"] * 100, 4)} for l in linhas]
    return resumo, segs


COLUNAS_RESUMO = ["semana", "base_descricao", "n_base", "n_semana", "taxa_base", "taxa_semana", "delta_pp", "mix_pp", "taxa_pp", "p_valor", "conclusao"]
COLUNAS_SEG = ["semana", "segmento", "peso_base", "peso_semana", "taxa_base", "taxa_semana", "efeito_mix_pp", "efeito_taxa_pp"]


def gravar(conn: psycopg.Connection, semanas: list[date] | None = None) -> list[dict]:
    cur = conn.execute(SQL)
    df = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
    df["voltou_7d"] = df["voltou_7d"].astype(bool)
    n_min = n_minimo(conn)
    resumos, segs = [], []
    for s in semanas or SEMANAS_CANDIDATAS:
        try:
            r, l = decompor(df, s, n_min)
        except ValueError:  # sem base anterior limpa (semana de início da coleta): compara com as seguintes
            r, l = decompor(df, s, n_min, contra_seguintes=True)
        resumos.append(r)
        segs += l
    substituir(conn, "decomposicao_resumo", COLUNAS_RESUMO, [[r[c] for c in COLUNAS_RESUMO] for r in resumos])
    substituir(conn, "decomposicao_semana", COLUNAS_SEG, [[l[c] for c in COLUNAS_SEG] for l in segs])
    return resumos
