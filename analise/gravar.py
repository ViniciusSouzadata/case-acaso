"""Gravação em resultado.*: cada tabela é substituída por inteiro, numa transação (reexecutar dá o mesmo estado)."""
from __future__ import annotations

from typing import Sequence

import psycopg
from psycopg import sql

TABELAS = {
    "meta", "efeito_fator", "balanco_propensao", "decomposicao_semana", "decomposicao_resumo",
    "sensibilidade_efeito", "validacao_classificador", "achado", "problema_qualidade",
}


def substituir(conn: psycopg.Connection, tabela: str, colunas: Sequence[str], linhas: Sequence[Sequence]) -> int:
    """Esvazia resultado.<tabela> e grava `linhas` (tuplas na ordem de `colunas`). Devolve quantas gravou."""
    if tabela not in TABELAS:
        raise ValueError(f"tabela desconhecida em resultado: {tabela}")
    ins = sql.SQL("INSERT INTO resultado.{} ({}) VALUES ({})").format(
        sql.Identifier(tabela),
        sql.SQL(", ").join(map(sql.Identifier, colunas)),
        sql.SQL(", ").join(sql.Placeholder() for _ in colunas),
    )
    with conn.transaction():
        conn.execute(sql.SQL("DELETE FROM resultado.{}").format(sql.Identifier(tabela)))
        with conn.cursor() as cur:
            cur.executemany(ins, [tuple(l) for l in linhas])
    return len(linhas)
