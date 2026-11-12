"""T-203: efeito bruto de cada nível de cada fator contra o nível de referência (o mais frequente), com IC de Newcombe.

Bruto = diferença de taxas de retorno sem controlar por mais nada. Fica ao lado do ajustado (T-204): a diferença entre os
dois é a seleção que o case pede para separar. Só agregados.
"""
from __future__ import annotations

import pandas as pd
import psycopg

from analise.dados import carregar_elegiveis
from analise.fatores import FATORES, Fator, agrupar_raros
from analise.gravar import substituir
from analise.intervalos import newcombe

COLUNAS_BRUTO = [
    "fator", "nivel", "referencia", "grupo", "n_nivel", "n_referencia", "taxa_nivel", "taxa_referencia",
    "efeito_bruto_pp", "bruto_ic_inf", "bruto_ic_sup", "metodo", "amostra_suficiente",
]


def calcular_bruto(df: pd.DataFrame, n_minimo: int, fatores: list[Fator] | None = None) -> list[dict]:
    """Uma linha por (fator, nível ≠ referência). `df` precisa de `voltou_7d` e das colunas que os fatores usam."""
    linhas: list[dict] = []
    for f in fatores or FATORES:
        nivel = f.preparar(df)
        valido = nivel.notna()
        nivel = agrupar_raros(nivel[valido], n_minimo)
        voltou = df.loc[valido, "voltou_7d"].astype(int)
        n = nivel.value_counts()
        if len(n) < 2:
            continue  # um só nível: não há comparação (ex.: tema ainda "não classificado")
        ref = min(n.index, key=lambda x: (-n[x], str(x)))  # mais frequente; empate: ordem alfabética (determinístico)
        n_ref, k_ref = int(n[ref]), int(voltou[nivel == ref].sum())
        for nv in sorted(n.index, key=str):
            if nv == ref:
                continue
            n_nv, k_nv = int(n[nv]), int(voltou[nivel == nv].sum())
            d, inf, sup = newcombe(k_nv, n_nv, k_ref, n_ref)
            linhas.append({
                "fator": f.nome, "nivel": str(nv), "referencia": str(ref), "grupo": f.grupo,
                "n_nivel": n_nv, "n_referencia": n_ref,
                "taxa_nivel": round(k_nv / n_nv, 6), "taxa_referencia": round(k_ref / n_ref, 6),
                "efeito_bruto_pp": round(d * 100, 4), "bruto_ic_inf": round(inf * 100, 4), "bruto_ic_sup": round(sup * 100, 4),
                "metodo": "logit_ame", "amostra_suficiente": n_nv >= n_minimo and n_ref >= n_minimo,
            })
    return linhas


def bruto_tema_descritivo(df: pd.DataFrame, n_minimo: int) -> list[dict]:
    """Tema em TODOS os níveis, cada um contra os demais temas, só diferença simples (Newcombe). Descritivo: o tema vem de IA com
    concordância moderada e não entra no modelo ajustado (que agrupa em 3 temas + demais por causa do limite de parâmetros)."""
    t = df["tema"].astype(object)
    if t.isin(["não classificado"]).all():
        return []
    voltou = df["voltou_7d"].astype(int)
    linhas = []
    for nv in sorted(t.dropna().unique(), key=str):
        dentro = t == nv
        n1, k1, n0, k0 = int(dentro.sum()), int(voltou[dentro].sum()), int((~dentro).sum()), int(voltou[~dentro].sum())
        if n1 == 0 or n0 == 0:
            continue
        d, inf, sup = newcombe(k1, n1, k0, n0)
        linhas.append({
            "fator": "tema_descritivo", "nivel": str(nv), "referencia": "demais temas", "grupo": "perfil",
            "n_nivel": n1, "n_referencia": n0, "taxa_nivel": round(k1 / n1, 6), "taxa_referencia": round(k0 / n0, 6),
            "efeito_bruto_pp": round(d * 100, 4), "bruto_ic_inf": round(inf * 100, 4), "bruto_ic_sup": round(sup * 100, 4),
            "metodo": "logit_ame", "amostra_suficiente": n1 >= n_minimo and n0 >= n_minimo,
        })
    return linhas


def n_minimo(conn: psycopg.Connection) -> int:
    return int(conn.execute("SELECT ops.param('n_minimo')").fetchone()[0])


def gravar(conn: psycopg.Connection) -> list[dict]:
    """Calcula e grava só as colunas de bruto em resultado.efeito_fator (a T-204 completa as de ajustado)."""
    df, n_min = carregar_elegiveis(conn), n_minimo(conn)
    linhas = calcular_bruto(df, n_min) + bruto_tema_descritivo(df, n_min)
    substituir(conn, "efeito_fator", COLUNAS_BRUTO, [[l[c] for c in COLUNAS_BRUTO] for l in linhas])
    return linhas
