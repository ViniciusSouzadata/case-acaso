"""T-207: decomposição mix × taxa com exemplos feitos à mão; fechamento no banco real."""
from datetime import date

import pandas as pd
import psycopg
import pytest

from analise import semana
from loader.migrar import dsn


def _soma(linhas, chave):
    return sum(l[chave] for l in linhas)


def test_so_mudanca_de_perfil_vira_tudo_mix():
    # base: A 50% (taxa 0,2), B 50% (taxa 0,4) -> 0,30. Semana: A 25%, B 75% com as MESMAS taxas -> 0,35.
    # mix = (-0,25 * 0,2) + (+0,25 * 0,4) = +0,05; taxa = 0
    base = {"A": (50, 10), "B": (50, 20)}
    sem = {"A": (25, 5), "B": (75, 30)}
    linhas, tot = semana.kitagawa(base, sem)
    assert tot["delta"] == pytest.approx(0.05) and tot["mix"] == pytest.approx(0.05) and tot["taxa"] == pytest.approx(0.0)


def test_so_mudanca_de_taxa_vira_tudo_taxa():
    # pesos iguais (50/50); A sobe de 0,2 para 0,3, B fica em 0,4. Delta = 0,5 * 0,1 = +0,05, todo de taxa
    base = {"A": (100, 20), "B": (100, 40)}
    sem = {"A": (100, 30), "B": (100, 40)}
    _, tot = semana.kitagawa(base, sem)
    assert tot["mix"] == pytest.approx(0.0) and tot["taxa"] == pytest.approx(0.05) and tot["delta"] == pytest.approx(0.05)


def test_mix_mais_taxa_fecha_exatamente_com_os_dois_efeitos_juntos():
    base = {"A": (60, 12), "B": (30, 15), "C": (10, 2)}
    sem = {"A": (20, 6), "B": (45, 18), "C": (15, 3)}
    linhas, tot = semana.kitagawa(base, sem)
    assert tot["mix"] + tot["taxa"] == pytest.approx(tot["delta"], abs=1e-12)
    assert _soma(linhas, "peso_base") == pytest.approx(1.0) and _soma(linhas, "peso_semana") == pytest.approx(1.0)
    assert tot["delta"] == pytest.approx(27 / 80 - 29 / 100)  # 0,3375 - 0,29


def test_segmento_ausente_de_um_lado_nao_gera_efeito_de_taxa_e_ainda_fecha():
    base = {"A": (80, 16), "B": (20, 10)}
    sem = {"A": (50, 10), "B": (30, 15), "C": (20, 4)}  # C só aparece na semana
    linhas, tot = semana.kitagawa(base, sem)
    c = next(l for l in linhas if l["segmento"] == "C")
    assert c["efeito_taxa"] == 0.0 and c["peso_base"] == 0.0
    assert tot["mix"] + tot["taxa"] == pytest.approx(tot["delta"], abs=1e-12)


def test_agrupa_segmentos_raros_nos_dois_lados():
    base = {"A": (90, 20), "R1": (3, 1), "R2": (2, 0)}
    sem = {"A": (40, 8), "R1": (1, 0), "R2": (4, 1)}
    b, s = semana.agrupar_segmentos_raros(base, sem, 30)
    assert b == {"A": (90, 20), "outros": (5, 1)} and s == {"A": (40, 8), "outros": (5, 1)}


def test_duas_proporcoes_feito_a_mao():
    # 30/100 contra 20/100: p combinado 0,25; z = 0,10 / sqrt(0,25*0,75*0,02) = 0,10/0,061237 = 1,63299; p bilateral = 0,1025
    assert semana.teste_duas_proporcoes(30, 100, 20, 100) == pytest.approx(0.1025, abs=2e-4)
    assert semana.teste_duas_proporcoes(0, 50, 0, 50) == 1.0
    assert semana.teste_duas_proporcoes(25, 100, 25, 100) == pytest.approx(1.0)


JARGAO = ["mix", "p =", "p<", "p <", "IC ", "IC:", "teste", "marginal", "p.p.", "Kitagawa", "proporç", "z ="]


def _sem_jargao(texto):
    achados = [j for j in JARGAO if j in texto]
    assert not achados, f"jargão no texto para o cliente: {achados}"


def test_veredito_dentro_do_ruido_em_linguagem_de_cliente():
    t = semana.veredito(0.264, 0.215, 197, 65, -0.4, -4.4, 0.434, 35, 2)
    assert t.startswith("Nesta semana, 22 de cada 100 novos usuários (65 no total) voltaram, contra 26 de cada 100")
    assert "Quase toda a queda veio de as pessoas voltarem menos, não de ter chegado um público diferente." in t
    assert "dentro da variação normal entre semanas" in t and "não dá para afirmar que houve uma mudança real" in t
    _sem_jargao(t)


def test_veredito_distinguivel_mas_com_cautela_de_comparacoes_multiplas():
    t = semana.veredito(0.338, 0.167, 74, 84, 0.7, -17.8, 0.013, 35, 2)
    assert "17 de cada 100" in t and "34 de cada 100" in t
    assert "maior do que a variação normal entre semanas, mas" in t and "todas as 35 semanas" in t
    assert "2 tiveram uma diferença assim" in t and "cerca de 2" in t and "não dá para descartar coincidência" in t
    _sem_jargao(t)


def test_veredito_separa_mudanca_de_publico_de_mudanca_de_comportamento():
    publico = semana.veredito(0.30, 0.25, 100, 100, -4.8, -0.2, 0.5, 30, 1)   # quase tudo mix
    assert "veio de ter chegado um público diferente" in publico and "outra mistura de celular" in publico
    misto = semana.veredito(0.30, 0.25, 100, 100, -2.5, -2.5, 0.5, 30, 1)
    assert "Parte da queda veio de um público diferente e parte" in misto
    subida = semana.veredito(0.20, 0.28, 100, 100, 0.1, 7.9, 0.5, 30, 1)
    assert "Quase toda a subida veio de as pessoas voltarem mais" in subida
    for t in (publico, misto, subida):
        _sem_jargao(t)


def test_decompor_sintetico_ponta_a_ponta():
    s0, s1 = date(2023, 11, 13), date(2023, 11, 20)
    linhas = []
    for sem, grupos in ((s0, {("celular", "gpt-4"): (40, 10), ("computador", "gpt-4"): (60, 18)}),
                        (s1, {("celular", "gpt-4"): (70, 14), ("computador", "gpt-4"): (30, 9)})):
        for (disp, mod), (n, k) in grupos.items():
            linhas += [{"semana": sem, "dispositivo": disp, "modelo_familia": mod, "voltou_7d": i < k} for i in range(n)]
    r, segs = semana.decompor(pd.DataFrame(linhas), s1, 30)
    assert r["n_base"] == 100 and r["n_semana"] == 100
    assert r["taxa_base"] == 0.28 and r["taxa_semana"] == 0.23
    assert r["delta_pp"] == pytest.approx(-5.0) and r["mix_pp"] + r["taxa_pp"] == pytest.approx(r["delta_pp"], abs=1e-3)
    assert len(segs) == 2


@pytest.mark.usefixtures("usar_real")
def test_semanas_reais_gravadas_e_fecham():
    with psycopg.connect(dsn(), autocommit=True) as c:
        resumos = semana.gravar(c)
        res = c.execute("SELECT semana, n_base, n_semana, delta_pp, mix_pp, taxa_pp, p_valor, conclusao FROM resultado.decomposicao_resumo").fetchall()
        segs = c.execute("SELECT semana, sum(efeito_mix_pp + efeito_taxa_pp), sum(peso_base), sum(peso_semana) FROM resultado.decomposicao_semana GROUP BY 1").fetchall()
    assert {r[0] for r in res} == {date(2023, 11, 20), date(2023, 5, 1), date(2023, 7, 17)}
    assert len(resumos) == 3
    for _, n_b, n_s, delta, mix, taxa, p, conclusao in res:
        assert n_b > 0 and n_s > 0 and 0 <= float(p) <= 1
        assert float(mix) + float(taxa) == pytest.approx(float(delta), abs=2e-3)
        assert "de cada 100" in conclusao and "variação normal entre semanas" in conclusao
        _sem_jargao(conclusao)
    for _, total, pb, ps in segs:
        assert float(pb) == pytest.approx(1.0, abs=1e-4) and float(ps) == pytest.approx(1.0, abs=1e-4)
    assert {s[0]: float(s[1]) for s in segs}.keys() == {r[0] for r in res}
