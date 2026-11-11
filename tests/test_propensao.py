"""T-206: simulação com confusão conhecida (bruto enviesado, ponderado recupera o efeito), balanço, E-value e banco real."""
import numpy as np
import pandas as pd
import psycopg
import pytest

from analise import ajustado, propensao
from analise.dados import carregar_elegiveis, carregar_grupos_ip
from analise.fatores import ASSISTENTE, PERFIL, Fator
from loader.migrar import dsn


def _sig(x):
    return 1 / (1 + np.exp(-x))


# ----------------------------------------------------------------------------------------------- peças puras
def test_e_value_valores_de_referencia():
    # VanderWeele & Ding (2017): RR = 3,9 -> E-value 7,26; RR < 1 é invertido (0,5 e 2 dão o mesmo valor); RR = 1 dá 1
    assert ajustado.e_value(3.9) == pytest.approx(3.9 + (3.9 * 2.9) ** 0.5) and round(ajustado.e_value(3.9), 2) == 7.26
    assert ajustado.e_value(0.5) == pytest.approx(ajustado.e_value(2.0)) and ajustado.e_value(2.0) == pytest.approx(2 + 2 ** 0.5)
    assert ajustado.e_value(1.0) == 1.0


def test_e_value_do_intervalo():
    assert ajustado.e_value_do_intervalo(0.8, 1.5) == 1.0                       # IC contém 1: nada a explicar
    assert ajustado.e_value_do_intervalo(1.2, 2.0) == pytest.approx(ajustado.e_value(1.2))   # limite mais perto de 1
    assert ajustado.e_value_do_intervalo(0.4, 0.8) == pytest.approx(ajustado.e_value(0.8))   # efeito negativo: usa o limite superior


def test_e_values_do_efeito_a_partir_de_pontos_percentuais():
    # risco de referência 0,20 e efeito +10 p.p. -> RR = 1,5
    est, lim = ajustado.e_values_do_efeito(0.20, 10.0, 2.0, 18.0)
    assert est == pytest.approx(ajustado.e_value(1.5)) and lim == pytest.approx(ajustado.e_value(1.1))


def test_diferenca_padronizada_feita_a_mao():
    # tratados x = [1,0,1,1] (média 0,75; var 0,1875); controles x = [0,0,1,0] (média 0,25; var 0,1875); sd = 0,4330; dp = 0,5/0,4330
    x = np.array([1, 0, 1, 1, 0, 0, 1, 0], float)
    t = np.array([1, 1, 1, 1, 0, 0, 0, 0], float)
    assert propensao.diferenca_padronizada(x, t) == pytest.approx(0.5 / 0.4330127, abs=1e-6)
    assert propensao.diferenca_padronizada(np.ones(8), t) == 0.0
    # pesos que igualam as médias zeram a diferença: nos tratados o 0 pesa 3x
    w = np.array([1, 3, 1, 1, 1, 1, 1, 1], float)
    assert abs(propensao.diferenca_padronizada(x, t, w) - propensao.diferenca_padronizada(x, t)) > 0.1


def test_logit_ridge_bate_com_statsmodels():
    import statsmodels.api as sm
    rng = np.random.default_rng(3)
    n = 3000
    X = np.column_stack([np.ones(n), rng.normal(size=n), rng.integers(0, 2, n)])
    t = (rng.random(n) < _sig(0.3 + 0.8 * X[:, 1] - 0.5 * X[:, 2])).astype(float)
    ref = sm.Logit(t, X).fit(disp=0).params
    assert np.allclose(propensao.logit_ridge(X, t, lam=1e-8), ref, atol=1e-3)


def test_pesos_truncados_nos_percentis():
    rng = np.random.default_rng(5)
    n = 2000
    X = np.column_stack([np.ones(n), rng.normal(size=n)])
    t = (rng.random(n) < _sig(1.5 * X[:, 1])).astype(float)
    w = propensao.pesos_estabilizados(X, t)
    bruto = propensao.pesos_estabilizados(X, t, percentis=(0, 100))
    assert w.max() < bruto.max() and w.min() > bruto.min()


# ----------------------------------------------------------------------------------------------- simulação com confusão
def _simular(n=5000, semente=11, forca=1.6):
    """Z (perfil) empurra o tratamento T e o retorno; T tem efeito verdadeiro conhecido. Cada usuário em seu próprio IP."""
    rng = np.random.default_rng(semente)
    z = rng.random(n) < 0.5
    t = rng.random(n) < _sig(-0.2 + forca * (z - 0.5) * 2)
    y = rng.random(n) < _sig(-1.5 + 0.5 * t + 1.0 * z)
    df = pd.DataFrame({"z": np.where(z, "b", "a"), "t": t, "voltou_7d": y})
    verdade = 100 * np.mean(_sig(-1.5 + 0.5 + 1.0 * z) - _sig(-1.5 + 1.0 * z))
    return df, verdade


def _trat():
    return propensao.Tratamento("t", "sim", "não", lambda d: pd.Series(True, index=d.index), lambda d: d["t"].astype(bool))


def _com_fatores(monkeypatch):
    monkeypatch.setattr(propensao, "FATORES", [Fator("z", PERFIL, lambda d: d["z"])])


def test_ponderado_recupera_o_efeito_e_o_bruto_fica_enviesado(monkeypatch):
    _com_fatores(monkeypatch)
    df, verdade = _simular()
    linha, balanco = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=200)
    assert linha["_comparavel"] and linha["ajustado_ic_inf"] <= verdade <= linha["ajustado_ic_sup"]
    assert abs(linha["efeito_ajustado_pp"] - verdade) < 2.5
    assert linha["bruto_ic_inf"] > verdade + 3  # a confusão infla muito o bruto
    assert linha["metodo"] == "ipw" and linha["e_value"] > 1


def test_balanco_antes_grande_e_depois_pequeno(monkeypatch):
    _com_fatores(monkeypatch)
    df, _ = _simular()
    _, balanco = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=20)
    assert balanco[0]["tratamento"] == "t" and balanco[0]["dp_antes"] > 0.5 and balanco[0]["dp_depois"] < propensao.LIMITE_BALANCO


def test_sem_balanco_o_efeito_vira_nao_comparavel(monkeypatch):
    _com_fatores(monkeypatch)
    df, _ = _simular()
    monkeypatch.setattr(propensao, "LIMITE_BALANCO", 0.0)  # limite impossível (diferença padronizada é >= 0): reprova sempre
    linha, _ = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=20)
    assert not linha["_comparavel"] and linha["efeito_ajustado_pp"] is None and linha["e_value"] is None
    assert "não é comparável" in linha["leitura"] and "0." not in linha["leitura"]


def test_bootstrap_com_semente_fixa_e_reproduzivel(monkeypatch):
    _com_fatores(monkeypatch)
    df, _ = _simular(n=1500)
    a, _ = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=50, semente=7)
    b, _ = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=50, semente=7)
    c, _ = propensao.analisar(df, np.arange(len(df)), _trat(), 30, replicacoes=50, semente=8)
    assert (a["ajustado_ic_inf"], a["ajustado_ic_sup"]) == (b["ajustado_ic_inf"], b["ajustado_ic_sup"])
    assert (a["ajustado_ic_inf"], a["ajustado_ic_sup"]) != (c["ajustado_ic_inf"], c["ajustado_ic_sup"])


def test_bootstrap_por_ip_alarga_o_intervalo_com_dependencia_dentro_do_ip(monkeypatch):
    _com_fatores(monkeypatch)
    df, _ = _simular(n=1500)
    base = df.iloc[::30].reset_index(drop=True)                      # 50 usuários copiados 30 vezes: dependência total dentro do IP
    dup = base.loc[base.index.repeat(30)].reset_index(drop=True)
    indep, _ = propensao.analisar(dup, np.arange(len(dup)), _trat(), 30, replicacoes=100, semente=1)
    agrup, _ = propensao.analisar(dup, np.repeat(np.arange(len(base)), 30), _trat(), 30, replicacoes=100, semente=1)
    larg = lambda r: r["ajustado_ic_sup"] - r["ajustado_ic_inf"]  # noqa: E731
    assert larg(agrup) > 2 * larg(indep)


# ----------------------------------------------------------------------------------------------- banco real
JARGAO = ["p.p.", "IC ", "p =", "p-valor", "marginal", "propens", "E-value", "bootstrap", "ipw", "balanço", "padronizada"]


@pytest.mark.usefixtures("usar_real")
def test_propensao_real_grava_ipw_balanco_e_nao_apaga_o_ajustado():
    with psycopg.connect(dsn(), autocommit=True) as c:
        from analise import meta
        meta.gravar(c)
        ajustado.gravar(c)
        antes = c.execute("SELECT count(*) FROM resultado.efeito_fator WHERE metodo = 'logit_ame'").fetchone()[0]
        linhas, balancos = propensao.gravar(c, replicacoes=100)
        logit = c.execute("SELECT count(*) FROM resultado.efeito_fator WHERE metodo = 'logit_ame'").fetchone()[0]
        ipw = c.execute("SELECT fator, efeito_ajustado_pp, ajustado_ic_inf, ajustado_ic_sup, e_value, e_value_ic, leitura "
                        "FROM resultado.efeito_fator WHERE metodo = 'ipw' ORDER BY fator").fetchall()
        bal = c.execute("SELECT tratamento, count(*), max(dp_depois), max(dp_antes) FROM resultado.balanco_propensao GROUP BY 1").fetchall()
        ev = c.execute("SELECT count(*) FILTER (WHERE grupo = 'assistente' AND e_value IS NOT NULL), "
                       "count(*) FILTER (WHERE grupo = 'perfil' AND e_value IS NOT NULL) FROM resultado.efeito_fator WHERE metodo = 'logit_ame'").fetchone()
    assert logit == antes > 20
    assert [r[0] for r in ipw] == ["idioma_divergente", "modelo_familia", "recusa", "virada_dez2023"]
    for fator, ef, inf, sup, e, ei, leitura in ipw:
        assert leitura
        if ef is not None:
            assert inf < ef < sup and e >= 1 and ei >= 1
            assert not [j for j in JARGAO if j in leitura], leitura
    assert {b[0] for b in bal} == {"recusa", "idioma_divergente", "modelo_familia", "virada_dez2023"}
    for _, n, depois, antes_ in bal:
        assert n >= 8 and float(depois) <= float(antes_) + 1e-9
    assert ev[0] >= 6 and ev[1] == 0   # E-value só nos fatores do assistente
