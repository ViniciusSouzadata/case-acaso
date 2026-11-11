"""T-204: efeito ajustado recupera um efeito conhecido numa simulação com confusão; BH; limite de parâmetros; banco real."""
import numpy as np
import pandas as pd
import psycopg
import pytest

from analise import ajustado
from analise.bruto import calcular_bruto
from analise.dados import carregar_elegiveis, carregar_grupos_ip
from analise.fatores import ASSISTENTE, ENGAJAMENTO, PERFIL, Fator
from loader.migrar import dsn


def _sig(t):
    return 1 / (1 + np.exp(-t))


def _simular(n=30000, semente=7):
    """x (fator do assistente) e z (perfil) afetam o retorno; z também empurra a exposição x -> confusão."""
    rng = np.random.default_rng(semente)
    z = rng.random(n) < 0.5
    x = rng.random(n) < np.where(z, 0.45, 0.15)
    y = rng.random(n) < _sig(-1.6 + 0.5 * x + 1.0 * z)
    df = pd.DataFrame({"x": np.where(x, "sim", "não"), "z": np.where(z, "b", "a"), "voltou_7d": y})
    verdadeiro = 100 * np.mean([_sig(-1.6 + 0.5 + 1.0 * zz) - _sig(-1.6 + 1.0 * zz) for zz in z])
    fatores = [Fator("x", ASSISTENTE, lambda d: d["x"]), Fator("z", PERFIL, lambda d: d["z"])]
    return df, fatores, verdadeiro


def test_ajustado_recupera_efeito_conhecido_e_bruto_fica_enviesado():
    df, fatores, verdadeiro = _simular()
    aj, diag = ajustado.ajustar(df, pd.Series(np.arange(len(df))), 30, fatores)
    x = next(l for l in aj if l["fator"] == "x")
    assert x["ajustado_ic_inf"] <= verdadeiro <= x["ajustado_ic_sup"]
    assert abs(x["efeito_ajustado_pp"] - verdadeiro) < 1.5
    bruto = next(b for b in calcular_bruto(df, 30, fatores) if b["fator"] == "x")
    assert bruto["bruto_ic_inf"] > verdadeiro + 2  # a confusão infla o bruto muito além do verdadeiro
    assert diag["convergiu"] and diag["n_parametros"] == 2 and diag["eventos"] == int(df["voltou_7d"].sum())


def test_erro_agrupado_por_ip_alarga_o_intervalo_quando_ha_correlacao_dentro_do_grupo():
    df, fatores, _ = _simular(n=6000)
    # grupos de 50 usuários com o MESMO desfecho e exposição copiados: forte dependência interna
    base = df.iloc[::50].reset_index(drop=True)
    df2 = base.loc[base.index.repeat(50)].reset_index(drop=True)
    indep, _ = ajustado.ajustar(df2, pd.Series(np.arange(len(df2))), 30, fatores)
    agrup, _ = ajustado.ajustar(df2, pd.Series(np.repeat(np.arange(len(base)), 50)), 30, fatores)
    larg = lambda r: next(l for l in r if l["fator"] == "x")["ajustado_ic_sup"] - next(l for l in r if l["fator"] == "x")["ajustado_ic_inf"]  # noqa: E731
    assert larg(agrup) > 3 * larg(indep)


def test_benjamini_hochberg_feito_a_mao():
    # m=4, q=5%: limites k/4*0,05 = 0,0125 / 0,025 / 0,0375 / 0,05. p ordenados 0,01 0,03 0,04 0,20 -> só o 1º passa
    assert ajustado.benjamini_hochberg([0.01, 0.04, 0.03, 0.20]) == [True, False, False, False]
    # 0,001 0,01 0,02 0,04: o maior k com p_k <= limite é 4 (0,04 <= 0,05) -> todos passam, em qualquer ordem
    assert ajustado.benjamini_hochberg([0.04, 0.001, 0.02, 0.01]) == [True] * 4
    assert ajustado.benjamini_hochberg([]) == []
    assert ajustado.benjamini_hochberg([0.2, 0.3]) == [False, False]


JARGAO = ["p.p.", "IC ", "IC:", "p =", "p-valor", "marginal", "logit", "FDR", "Benjamini", "significativ", "bruto"]


def _sem_jargao(texto):
    achados = [j for j in JARGAO if j in texto]
    assert not achados, f"jargão no texto para o cliente: {achados}"


def test_leitura_nunca_vende_ruido_como_efeito():
    t = ajustado.leitura_efeito("recusa", "sim", "não", -1.8, -7.9, 5.7)
    assert "não dá para afirmar diferença" in t and "pode ser só acaso" in t and "entre −7,9 e +5,7 a cada 100" in t
    _sem_jargao(t)
    t = ajustado.leitura_efeito("recusa", "sim", "não", -6.0, -11.0, -1.0, sobrevive_fdr=True)
    assert "cerca de 6,0 a cada 100 a menos" in t and "não dá para afirmar" not in t and "por acaso" not in t
    _sem_jargao(t)
    t = ajustado.leitura_efeito("faixa_chars_resposta", "301–1.000", "até 300", 6.2, 0.4, 12.1, sobrevive_fdr=False)
    assert "a mais" in t and "muitos fatores ao mesmo tempo" in t
    _sem_jargao(t)


def test_leitura_do_engajamento_diz_que_e_so_descricao():
    t = ajustado.leitura_efeito("n_turnos_sessao", "4 ou mais", "1", 15.6, 11.3, 19.9, ajustado=False)
    assert "voltou 16 a cada 100 a mais" in t and "só descrição" in t
    t = ajustado.leitura_efeito("n_turnos_sessao", "2 a 3", "1", 1.0, -3.0, 5.0, ajustado=False)
    assert "não dá para afirmar diferença" in t


def test_plano_junta_nivel_raro_a_referencia_e_registra():
    df = pd.DataFrame({"voltou_7d": [True, False] * 60,
                       "g": ["a"] * 70 + ["b"] * 40 + ["c"] * 10})  # c (n=10) < 30
    plano = ajustado.montar_plano(df, 30, [Fator("g", PERFIL, lambda d: d["g"])])
    assert list(plano.colunas_nivel) == [("g", "b")]
    assert plano.n_parametros == 1 and any("'c'" in n and "juntado" in n for n in plano.notas)


def test_limite_de_parametros():
    rng = np.random.default_rng(1)
    n = 3000
    df = pd.DataFrame({f"v{i}": rng.integers(0, 2, n).astype(str) for i in range(ajustado.MAX_PARAMETROS + 1)})
    df["voltou_7d"] = rng.random(n) < 0.3
    fatores = [Fator(f"v{i}", PERFIL, lambda d, i=i: d[f"v{i}"]) for i in range(ajustado.MAX_PARAMETROS + 1)]
    with pytest.raises(ValueError, match="limite"):
        ajustado.ajustar(df, pd.Series(np.arange(n)), 30, fatores)


@pytest.mark.usefixtures("usar_real")
def test_ajustado_real_completo_com_ic_e_sem_ip_no_resultado():
    with psycopg.connect(dsn(), autocommit=True) as c:
        from analise import meta
        meta.gravar(c)
        linhas = ajustado.gravar(c)
        df = carregar_elegiveis(c)
        grupos = carregar_grupos_ip(c)
        tabela = c.execute("SELECT * FROM resultado.efeito_fator").fetchall()
        colunas = [d.name for d in c.execute("SELECT * FROM resultado.efeito_fator LIMIT 0").description]
        n_param = c.execute("SELECT parametros_modelo FROM resultado.meta").fetchone()[0]
    assert len(tabela) == len(linhas) > 20
    assert grupos.reindex(df["usuario_id"]).notna().all()
    assert not {"hashed_ip", "user_agent", "grupo_ip"} & set(colunas)
    assert 1 <= n_param <= ajustado.MAX_PARAMETROS
    por_grupo = {}
    for l in linhas:
        por_grupo.setdefault(l["grupo"], []).append(l)
    for l in por_grupo[ENGAJAMENTO]:
        assert l["efeito_ajustado_pp"] is None and l["p_valor"] is None
    for l in por_grupo["assistente"] + por_grupo["perfil"]:
        if l["efeito_ajustado_pp"] is not None:
            assert l["ajustado_ic_inf"] < l["efeito_ajustado_pp"] < l["ajustado_ic_sup"]
            assert l["significativo_fdr"] in (True, False)
    assert sorted(l["ordem"] for l in linhas) == list(range(1, len(linhas) + 1))
    assert all(l["leitura"] for l in linhas)
    for l in linhas:
        _sem_jargao(l["leitura"])
    com_aj = [l for l in linhas if l["efeito_ajustado_pp"] is not None]
    assert [l["ordem"] for l in sorted(com_aj, key=lambda l: l["ordem"])] == list(range(1, len(com_aj) + 1))
    efs = [abs(l["efeito_ajustado_pp"]) for l in sorted(com_aj, key=lambda l: l["ordem"])]
    assert efs == sorted(efs, reverse=True)
