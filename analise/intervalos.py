"""Intervalos de confiança de proporções (funções puras).

Wilson usa z = 1,96 fixo e arredonda em 6 casas, igual a mart.wilson_inf / mart.wilson_sup (migração 005):
é assim que a taxa da análise e a do mart saem idênticas.
"""
from __future__ import annotations

from math import sqrt

Z = 1.96


def _wilson_bruto(k: int, n: int) -> tuple[float, float, float]:
    p = k / n
    centro = p + Z**2 / (2 * n)
    meia = Z * sqrt(p * (1 - p) / n + Z**2 / (4 * n**2))
    denom = 1 + Z**2 / n
    return p, max(0.0, (centro - meia) / denom), min(1.0, (centro + meia) / denom)


def wilson(k: int, n: int) -> tuple[float, float]:
    """IC de Wilson (95%) para k sucessos em n tentativas. Levanta ValueError se n <= 0 ou k fora de [0, n]."""
    if n <= 0:
        raise ValueError("n deve ser positivo")
    if not 0 <= k <= n:
        raise ValueError("k deve estar entre 0 e n")
    _, inf, sup = _wilson_bruto(k, n)
    return round(inf, 6), round(sup, 6)


def newcombe(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float, float]:
    """Diferença p1 - p2 com IC híbrido de Newcombe (método 10, escore de Wilson). Devolve (diferença, inf, sup).

    Usa os limites de Wilson sem arredondar; só o resultado final sai em 6 casas.
    """
    if n1 <= 0 or n2 <= 0:
        raise ValueError("n deve ser positivo")
    p1, l1, u1 = _wilson_bruto(k1, n1)
    p2, l2, u2 = _wilson_bruto(k2, n2)
    d = p1 - p2
    inf = d - sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    sup = d + sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return round(d, 6), round(inf, 6), round(sup, 6)


def efeito_minimo_detectavel(n: int, p: float, parcela_grupo: float, z_alfa: float = 1.96, z_poder: float = 0.8416212) -> float:
    """Menor diferença de proporções (em pontos percentuais) detectável com 80% de poder e 5% de erro tipo I.

    Aproximação normal com variância na taxa-base p: MDE = (z_alfa + z_poder) * sqrt(p(1-p) * (1/n1 + 1/n2)),
    com n1 = parcela_grupo * n e n2 = n - n1. Não inclui o efeito do agrupamento por IP (é um piso otimista).
    """
    if not 0 < parcela_grupo < 1:
        raise ValueError("parcela_grupo deve estar entre 0 e 1")
    n1 = parcela_grupo * n
    n2 = n - n1
    return round(100 * (z_alfa + z_poder) * sqrt(p * (1 - p) * (1 / n1 + 1 / n2)), 2)
