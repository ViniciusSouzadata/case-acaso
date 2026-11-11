"""T-206: causa × seleção. Escore de propensão, pesos, balanço e efeito ponderado para recusa, idioma divergente e modelo.

Ideia (para "Como defender"): quem recebe recusa (ou resposta em outro idioma, ou o GPT-4) não é sorteado — pode ser gente de perfil
diferente. A propensão é a chance de receber o "tratamento" dado o que se sabia ANTES da resposta (perfil, tema, tamanho da
pergunta, era). Ponderar pelo inverso dessa chance faz os dois grupos ficarem parecidos; a tabela de balanço mostra isso
(diferença padronizada abaixo de 0,1). Se não ficarem parecidos, o efeito não é comparável e não é mostrado.

- Pesos estabilizados (P(T) / P(T | covariáveis)) truncados em p1 e p99.
- IC por bootstrap de 1.000 reamostragens por IP (o modelo de propensão é reajustado em cada reamostragem), semente fixa.
- E-value (VanderWeele & Ding) a partir da razão de riscos ponderada.
- Modelo comparado só onde havia escolha (abr–jun/2023 e nov/2023). A virada de dez/2023 (GPT-4 vira o padrão) entra como
  antes/depois, evidência de APOIO, não prova.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import psycopg
from scipy.stats import norm

from analise.ajustado import (COLUNAS_EFEITO, ROTULOS, benjamini_hochberg, e_value, e_value_do_intervalo, leitura_efeito, montar_plano)
from analise.bruto import n_minimo
from analise.dados import carregar_elegiveis, carregar_grupos_ip
from analise.fatores import ASSISTENTE, FATORES, PERFIL
from analise.gravar import substituir
from analise.intervalos import newcombe

REPLICACOES = 1000
SEMENTE = 20261111
LIMITE_BALANCO = 0.1
TRUNCAR_PERCENTIS = (1, 99)
ERAS_COM_ESCOLHA = ("2023-04..06 (3.5 + 4 opcional)", "2023-11 (4 volta)")
ERA_GPT4_PADRAO = "2023-12+ (4 padrão)"
CONTROLE_IPW = "comparando pessoas de perfil parecido"


@dataclass(frozen=True)
class Tratamento:
    nome: str                                 # vira `tratamento` em balanco_propensao e `fator` em efeito_fator
    nivel: str
    referencia: str
    selecionar: Callable[[pd.DataFrame], pd.Series]   # população em que a comparação existe
    tratado: Callable[[pd.DataFrame], pd.Series]      # True = recebeu o "nivel"
    incluir_era: bool = True                  # era entra entre as covariáveis (não entra quando a era DEFINE o tratamento)


TRATAMENTOS = [
    Tratamento("recusa", "sim", "não", lambda d: pd.Series(True, index=d.index), lambda d: d["recusa"].astype(bool)),
    Tratamento("idioma_divergente", "sim", "não", lambda d: d["faixa_chars_pergunta"].astype(object) != "até 30",
               lambda d: d["idioma_divergente"].astype(bool)),
    Tratamento("modelo_familia", "gpt-4", "gpt-3.5", lambda d: d["era_modelo"].astype(object).isin(ERAS_COM_ESCOLHA),
               lambda d: d["modelo_familia"].astype(object) == "gpt-4"),
    Tratamento("virada_dez2023", "depois (dez/2023 em diante, GPT-4 padrão)", "antes (abr a nov/2023)",
               lambda d: pd.Series(True, index=d.index), lambda d: d["era_modelo"].astype(object) == ERA_GPT4_PADRAO, incluir_era=False),
]


# ----------------------------------------------------------------------------------------------- peças puras
def logit_ridge(X: np.ndarray, t: np.ndarray, lam: float = 1e-4, iteracoes: int = 50) -> np.ndarray:
    """Regressão logística por Newton com penalidade L2 mínima (fora do intercepto, 1ª coluna): converge mesmo com colunas quase
    constantes em reamostragens. Devolve os coeficientes."""
    n, k = X.shape
    b = np.zeros(k)
    pen = np.full(k, lam)
    pen[0] = 0.0
    for _ in range(iteracoes):
        p = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))
        g = X.T @ (t - p) - pen * b
        H = (X * (p * (1 - p))[:, None]).T @ X + np.diag(pen) + 1e-10 * np.eye(k)
        passo = np.linalg.solve(H, g)
        b = b + passo
        if np.max(np.abs(passo)) < 1e-9:
            break
    return b


def pesos_estabilizados(X: np.ndarray, t: np.ndarray, percentis: tuple[int, int] = TRUNCAR_PERCENTIS) -> np.ndarray:
    """P(T = t_i) / P(T = t_i | X_i), truncados nos percentis dados."""
    b = logit_ridge(X, t)
    p1 = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))
    marginal = t.mean()
    w = np.where(t == 1, marginal / p1, (1 - marginal) / (1 - p1))
    lo, hi = np.percentile(w, percentis)
    return np.clip(w, lo, hi)


def diferenca_padronizada(x: np.ndarray, t: np.ndarray, w: np.ndarray | None = None) -> float:
    """(média tratados - média controles) / sqrt((var tratados + var controles) / 2); com pesos se dados. 0 se não há variação."""
    w = np.ones(len(x)) if w is None else w
    m, v = [], []
    for g in (1, 0):
        sel = t == g
        mg = np.average(x[sel], weights=w[sel])
        m.append(mg)
        v.append(np.average((x[sel] - mg) ** 2, weights=w[sel]))
    sd = np.sqrt((v[0] + v[1]) / 2)
    return 0.0 if sd == 0 else float((m[0] - m[1]) / sd)


def riscos_ponderados(y: np.ndarray, t: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """(risco ponderado dos tratados, dos controles)."""
    return float(np.average(y[t == 1], weights=w[t == 1])), float(np.average(y[t == 0], weights=w[t == 0]))


def _estimar(X: np.ndarray, t: np.ndarray, y: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    """(efeito em fração, risco tratados, risco controles, pesos) numa amostra: reajusta a propensão e pondera."""
    w = pesos_estabilizados(X, t)
    rt, rc = riscos_ponderados(y, t, w)
    return rt - rc, rt, rc, w


def bootstrap_por_grupo(X: np.ndarray, t: np.ndarray, y: np.ndarray, grupos: np.ndarray, replicacoes: int,
                        semente: np.random.SeedSequence | int) -> np.ndarray:
    """Matriz (replicacoes × 3): efeito (fração), risco tratados, risco controles. Reamostra GRUPOS (IPs) inteiros com reposição.
    Reamostragens sem os dois grupos de tratamento são descartadas e refeitas."""
    rng = np.random.default_rng(semente)
    ids, inverso = np.unique(grupos, return_inverse=True)
    posicoes = [np.flatnonzero(inverso == g) for g in range(len(ids))]
    saida = []
    while len(saida) < replicacoes:
        escolhidos = rng.integers(0, len(ids), len(ids))
        idx = np.concatenate([posicoes[g] for g in escolhidos])
        if t[idx].min() == t[idx].max():
            continue
        ef, rt, rc, _ = _estimar(X[idx], t[idx], y[idx])
        saida.append((ef, rt, rc))
    return np.array(saida)


# ----------------------------------------------------------------------------------------------- um tratamento
def analisar(df: pd.DataFrame, grupos: np.ndarray, trat: Tratamento, n_min: int, replicacoes: int = REPLICACOES,
             semente: np.random.SeedSequence | int = SEMENTE) -> tuple[dict, list[dict]]:
    """Linha de efeito_fator (metodo = 'ipw', sem `ordem`) e linhas de balanço do tratamento. `df` precisa ter índice 0..n-1."""
    sel = trat.selecionar(df).to_numpy()
    sub = df.loc[sel].reset_index(drop=True)
    g = grupos[sel]
    t = trat.tratado(sub).to_numpy().astype(float)
    y = sub["voltou_7d"].to_numpy().astype(float)
    perfil = [f for f in FATORES if f.grupo == PERFIL and (trat.incluir_era or f.nome != "era_modelo")]
    plano = montar_plano(sub, n_min, perfil)
    X = plano.X.to_numpy()
    nomes = [c for c in plano.X.columns if c != "const"]
    n1, n0 = int(t.sum()), int((1 - t).sum())
    k1, k0 = int(y[t == 1].sum()), int(y[t == 0].sum())
    d_bruto, inf_b, sup_b = newcombe(k1, n1, k0, n0)

    ef, rt, rc, w = _estimar(X, t, y)
    antes = {c: abs(diferenca_padronizada(X[:, i + 1], t)) for i, c in enumerate(nomes)}
    depois = {c: abs(diferenca_padronizada(X[:, i + 1], t, w)) for i, c in enumerate(nomes)}
    balanco = [{"tratamento": trat.nome, "covariavel": c, "dp_antes": round(antes[c], 4), "dp_depois": round(depois[c], 4)} for c in nomes]
    pior = max(depois.values()) if depois else 0.0
    comparavel = pior < LIMITE_BALANCO

    linha = {
        "fator": trat.nome, "nivel": trat.nivel, "referencia": trat.referencia, "grupo": ASSISTENTE,
        "n_nivel": n1, "n_referencia": n0, "taxa_nivel": round(k1 / n1, 6), "taxa_referencia": round(k0 / n0, 6),
        "efeito_bruto_pp": round(d_bruto * 100, 4), "bruto_ic_inf": round(inf_b * 100, 4), "bruto_ic_sup": round(sup_b * 100, 4),
        "metodo": "ipw", "amostra_suficiente": n1 >= n_min and n0 >= n_min,
        "efeito_ajustado_pp": None, "ajustado_ic_inf": None, "ajustado_ic_sup": None, "p_valor": None, "significativo_fdr": None,
        "e_value": None, "e_value_ic": None, "leitura": None, "ordem": None,
        "_pior_balanco": pior, "_comparavel": comparavel, "_ef": ef,
    }
    if not comparavel:
        rot = ROTULOS.get(trat.nome, trat.nome)
        linha["leitura"] = (f"{rot}: comparando '{trat.nivel}' com '{trat.referencia}', mesmo ajustando, os dois grupos continuam diferentes "
                            f"demais em perfil para uma comparação justa (um deles tem poucos usuários); por isso este resultado não é "
                            f"comparável e não é mostrado. O efeito depois de levar em conta o perfil, pelo outro método, continua na tabela.")
        return linha, balanco

    boot = bootstrap_por_grupo(X, t, y, g, replicacoes, semente)
    efs = boot[:, 0] * 100
    inf, sup = (float(v) for v in np.percentile(efs, [2.5, 97.5]))
    se = float(efs.std(ddof=1))
    est = ef * 100
    rr = rt / rc
    validas = boot[:, 2] > 0  # risco dos controles zero numa reamostragem: razão indefinida, fica de fora
    rrs = boot[validas, 1] / boot[validas, 2]
    rr_inf, rr_sup = (float(v) for v in np.percentile(rrs, [2.5, 97.5])) if len(rrs) >= len(boot) / 2 else (None, None)
    linha.update({
        "efeito_ajustado_pp": round(est, 4), "ajustado_ic_inf": round(inf, 4), "ajustado_ic_sup": round(sup, 4),
        "p_valor": round(float(2 * norm.sf(abs(est / se))) if se > 0 else 1.0, 6),
        "e_value": round(e_value(rr), 4),
        "e_value_ic": None if rr_inf is None else round(e_value_do_intervalo(rr_inf, rr_sup), 4),
    })
    return linha, balanco


# ----------------------------------------------------------------------------------------------- tudo
def calcular(df: pd.DataFrame, grupos: np.ndarray, n_min: int, replicacoes: int = REPLICACOES) -> tuple[list[dict], list[dict]]:
    """Todas as linhas ipw (com BH e leitura) e todas as linhas de balanço. Semente por tratamento derivada de SEMENTE."""
    df = df.reset_index(drop=True)
    sementes = np.random.SeedSequence(SEMENTE).spawn(len(TRATAMENTOS))
    linhas, balancos = [], []
    for trat, sem in zip(TRATAMENTOS, sementes):
        linha, balanco = analisar(df, grupos, trat, n_min, replicacoes, sem)
        linhas.append(linha)
        balancos += balanco
    estimados = [l for l in linhas if l["p_valor"] is not None]
    for l, passa in zip(estimados, benjamini_hochberg([l["p_valor"] for l in estimados])):
        l["significativo_fdr"] = passa
        l["leitura"] = leitura_efeito(l["fator"], l["nivel"], l["referencia"], l["efeito_ajustado_pp"], l["ajustado_ic_inf"],
                                      l["ajustado_ic_sup"], sobrevive_fdr=passa, controle=CONTROLE_IPW)
    return linhas, balancos


def gravar(conn: psycopg.Connection, replicacoes: int = REPLICACOES) -> tuple[list[dict], list[dict]]:
    """Acrescenta as linhas ipw a resultado.efeito_fator (sem tocar nas logit_ame) e regrava resultado.balanco_propensao."""
    df = carregar_elegiveis(conn)
    grupos = carregar_grupos_ip(conn).reindex(df["usuario_id"]).to_numpy()
    linhas, balancos = calcular(df, grupos, n_minimo(conn), replicacoes)
    with conn.transaction():
        conn.execute("DELETE FROM resultado.efeito_fator WHERE metodo = 'ipw'")
        ins = f"INSERT INTO resultado.efeito_fator ({', '.join(COLUNAS_EFEITO)}) VALUES ({', '.join(['%s'] * len(COLUNAS_EFEITO))})"
        with conn.cursor() as cur:
            cur.executemany(ins, [[l[c] for c in COLUNAS_EFEITO] for l in linhas])
    substituir(conn, "balanco_propensao", ["tratamento", "covariavel", "dp_antes", "dp_depois"],
               [[b[c] for c in ("tratamento", "covariavel", "dp_antes", "dp_depois")] for b in balancos])
    return linhas, balancos
