"""T-201: Wilson, Newcombe e efeito mínimo detectável contra valores de referência (feitos à mão ou publicados)."""
import pytest

from analise.intervalos import efeito_minimo_detectavel, newcombe, wilson


def test_wilson_zero_sucessos_feito_a_mao():
    # k=0, n=10: limite inferior 0; superior = z²/(n+z²) = 3,8416/13,8416 = 0,277540
    inf, sup = wilson(0, 10)
    assert inf == 0.0
    assert sup == pytest.approx(3.8416 / 13.8416, abs=1e-6)


def test_wilson_todos_sucessos_e_simetrico():
    inf, sup = wilson(10, 10)
    assert sup == 1.0
    assert inf == pytest.approx(1 - 3.8416 / 13.8416, abs=1e-6)


def test_wilson_meio_a_meio_feito_a_mao():
    # k=5, n=10: centro = 0,5 + 1,9208/10 = 0,69208; meia = 1,96*sqrt(0,025 + 0,096040) = 0,681913;
    # denominador 1,38416 -> (0,00912.., 0,99...) ; conferido com a fórmula escrita por extenso abaixo
    from math import sqrt
    z = 1.96
    meia = z * sqrt(0.25 / 10 + z**2 / 400)
    inf, sup = wilson(5, 10)
    assert inf == pytest.approx((0.5 + z**2 / 20 - meia) / (1 + z**2 / 10), abs=1e-6)
    assert sup == pytest.approx((0.5 + z**2 / 20 + meia) / (1 + z**2 / 10), abs=1e-6)
    assert round(inf, 3) == 0.237 and round(sup, 3) == 0.763


def test_wilson_valida_entrada():
    with pytest.raises(ValueError):
        wilson(1, 0)
    with pytest.raises(ValueError):
        wilson(11, 10)


def test_newcombe_exemplo_publicado():
    # Newcombe (1998, Statistics in Medicine), exemplo 56/70 contra 48/80: diferença 0,2000, IC 95% 0,0524 a 0,3339
    d, inf, sup = newcombe(56, 70, 48, 80)
    assert d == pytest.approx(0.2, abs=1e-6)
    assert inf == pytest.approx(0.0524, abs=5e-5)
    assert sup == pytest.approx(0.3339, abs=5e-5)


def test_newcombe_proporcoes_iguais_ic_contem_zero_e_e_simetrico():
    d, inf, sup = newcombe(30, 100, 30, 100)
    assert d == 0.0
    assert inf == pytest.approx(-sup, abs=1e-6)
    assert inf < 0 < sup


def test_newcombe_antissimetrico_na_troca_dos_grupos():
    d1, i1, s1 = newcombe(56, 70, 48, 80)
    d2, i2, s2 = newcombe(48, 80, 56, 70)
    assert d2 == pytest.approx(-d1, abs=1e-6)
    assert i2 == pytest.approx(-s1, abs=1e-6)
    assert s2 == pytest.approx(-i1, abs=1e-6)


def test_efeito_minimo_detectavel_ordem_de_grandeza():
    # n = 2.372, taxa 23,86%: ~4,9 p.p. com divisão 50/50 e ~6,9 p.p. com 15/85 (o grupo pequeno custa poder)
    p = 566 / 2372
    assert efeito_minimo_detectavel(2372, p, 0.5) == 4.9
    assert efeito_minimo_detectavel(2372, p, 0.15) == 6.87
    assert efeito_minimo_detectavel(2372, p, 0.15) > efeito_minimo_detectavel(2372, p, 0.5)
