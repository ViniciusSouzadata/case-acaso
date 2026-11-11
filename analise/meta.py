"""resultado.meta: população, taxa global com IC e efeito mínimo detectável."""
from __future__ import annotations

from datetime import datetime, timezone

import psycopg

from analise import VERSAO_ANALISE
from analise.dados import carregar_elegiveis
from analise.gravar import substituir
from analise.intervalos import efeito_minimo_detectavel, wilson

COLUNAS = [
    "versao_analise", "versao_definicao", "executado_em", "n_elegiveis", "n_retornos", "taxa_global",
    "ic_inf", "ic_sup", "efeito_minimo_detectavel_pp", "efeito_minimo_detectavel_15_85_pp",
]


def calcular(conn: psycopg.Connection) -> dict:
    df = carregar_elegiveis(conn)
    n, k = len(df), int(df["voltou_7d"].sum())
    p = k / n
    inf, sup = wilson(k, n)
    versao_def = conn.execute("SELECT valor FROM ops.parametros WHERE chave = 'versao_definicao'").fetchone()[0]
    return {
        "versao_analise": VERSAO_ANALISE, "versao_definicao": versao_def, "executado_em": datetime.now(timezone.utc),
        "n_elegiveis": n, "n_retornos": k, "taxa_global": round(p, 6), "ic_inf": inf, "ic_sup": sup,
        "efeito_minimo_detectavel_pp": efeito_minimo_detectavel(n, p, 0.5),
        "efeito_minimo_detectavel_15_85_pp": efeito_minimo_detectavel(n, p, 0.15),
    }


def gravar(conn: psycopg.Connection) -> dict:
    m = calcular(conn)
    substituir(conn, "meta", COLUNAS, [[m[c] for c in COLUNAS]])
    return m
