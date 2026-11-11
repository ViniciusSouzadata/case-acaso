"""Leitura da população analisada: usuários elegíveis de mart.fct_primeira_experiencia (nunca texto de conversa)."""
from __future__ import annotations

import pandas as pd
import psycopg

COLUNAS_CATEGORICAS = [
    "modelo_familia", "modelo_versao", "era_modelo", "tema", "faixa_chars_pergunta", "faixa_chars_resposta",
    "idioma", "periodo_dia", "dia_semana", "dispositivo", "estado", "regiao",
]
COLUNAS_BOOL = ["recusa", "idioma_divergente", "fim_de_semana", "voltou_7d"]

SQL_ELEGIVEIS = """
SELECT usuario_id, modelo_familia, modelo_versao, era_modelo, tema, faixa_chars_pergunta, faixa_chars_resposta,
       recusa, idioma, idioma_divergente, n_turnos_sessao, n_conversas_sessao, hora_local, periodo_dia,
       dia_semana, fim_de_semana, dispositivo, estado, regiao, voltou_7d
FROM mart.fct_primeira_experiencia
WHERE elegivel
ORDER BY usuario_id
"""


def carregar_elegiveis(conn: psycopg.Connection) -> pd.DataFrame:
    """Um DataFrame tipado com um usuário elegível por linha (maduro, fora do burn-in, sem tráfego anômalo)."""
    cur = conn.execute(SQL_ELEGIVEIS)
    colunas = [d.name for d in cur.description]
    df = pd.DataFrame(cur.fetchall(), columns=colunas)
    for c in COLUNAS_CATEGORICAS:
        df[c] = df[c].astype("category")
    for c in COLUNAS_BOOL:
        df[c] = df[c].astype(bool)
    return df
