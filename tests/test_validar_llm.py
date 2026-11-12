"""Métricas ponderadas por estrato da validação do classificador LLM (feitas à mão)."""
from collections import Counter

import pytest

from classificador import validar_llm as VL


def test_pesos_por_estrato():
    amostra = {1: ("a",), 2: ("a",), 3: ("b",)}
    assert VL.pesos_por_estrato(amostra, Counter({("a",): 100, ("b",): 10})) == {1: 50.0, 2: 50.0, 3: 10.0}


def test_revocacao_ponderada_pode_ser_bem_menor_que_a_crua():
    # amostra: 4 recusas previstas (estrato R, população 20) e 4 não previstas (estrato N, população 400).
    # Reais: 3 de R (todas pegas) e 1 de N (perdida). Crua: revocação 3/4 = 75%; precisão 3/4.
    humano = {1: True, 2: True, 3: True, 4: False, 5: True, 6: False, 7: False, 8: False}
    maquina = {1: True, 2: True, 3: True, 4: True, 5: False, 6: False, 7: False, 8: False}
    peso = {i: 20 / 4 for i in range(1, 5)} | {i: 400 / 4 for i in range(5, 9)}
    assert VL.precisao_revocacao(humano, maquina) == (0.75, 0.75)
    p, r = VL.precisao_revocacao_ponderadas(humano, maquina, peso)
    assert p == pytest.approx(15 / 20)                          # 3 verdadeiros * 5 / (4 previstos * 5)
    assert r == pytest.approx(15 / (15 + 100))                  # reais: 15 em R + 100 em N
    assert r < 0.15


def test_acuracia_ponderada():
    h = {1: "x", 2: "x", 3: "y"}
    m = {1: "x", 2: "z", 3: "y"}
    assert VL.acuracia_ponderada(h, m, {1: 1.0, 2: 1.0, 3: 2.0}) == pytest.approx(3 / 4)


def test_tabela_traz_as_duas_leituras():
    linha = {"nome": "m", "tema_acuracia": 0.5, "tema_acuracia_pond": 0.4, "tema_kappa": 0.3, "recusa_acuracia": 0.9, "recusa_kappa": 0.5,
             "recusa_precisao": 0.6, "recusa_precisao_pond": 0.3, "recusa_revocacao": 0.8, "recusa_revocacao_pond": 0.2}
    t = VL.tabela([linha])
    assert "50,0% / 40,0%" in t and "60,0% / 30,0%" in t and "80,0% / 20,0%" in t
