"""Conjunto de conversas cujo tema/recusa entram em algum número de resultado.* ou tela: a UNIÃO das primeiras conversas dos usuários
elegíveis nas 4 definições da sensibilidade (T-208). Assim a sensibilidade não mistura rótulo de regra com rótulo de LLM.

Só devolve ids de conversa e contagens (nenhum texto). Usado para escolher o que o classificador LLM rotula na rodada grande;
o resto do seed continua `regras`, com origem explícita.
"""
from __future__ import annotations

import pandas as pd

from analise import sensibilidade as S


def ids_por_definicao(conv: pd.DataFrame, par: dict, eras: pd.DataFrame) -> dict[str, set[int]]:
    saida: dict[str, set[int]] = {}
    for nome, chave, gap in S.DEFINICOES:
        cov, _ = S.reconstruir(conv, chave, gap or par["gap_sessao_min"], par, eras)
        saida[nome] = {int(i) for i in cov["conversa_id"]}
    return saida


def uniao(por_definicao: dict[str, set[int]]) -> set[int]:
    return set().union(*por_definicao.values())


def contagens(por_definicao: dict[str, set[int]]) -> dict[str, int]:
    """{definição: n, ..., 'uniao': n, 'so_na_uniao': quantas a união acrescenta à oficial}."""
    u = uniao(por_definicao)
    return {**{k: len(v) for k, v in por_definicao.items()}, "uniao": len(u), "so_na_uniao": len(u - por_definicao["oficial"])}


def calcular(conn) -> dict[str, set[int]]:
    conv, par, eras = S.carregar(conn)
    return ids_por_definicao(conv, par, eras)
