"""T-203: efeito bruto com respostas feitas à mão (sintético) e fechamento no banco real."""
import pandas as pd
import psycopg
import pytest

from analise import bruto
from analise.dados import carregar_elegiveis
from analise.fatores import ENGAJAMENTO, FATORES, Fator
from loader.migrar import dsn


def _df(grupos: dict[str, tuple[int, int]]) -> pd.DataFrame:
    """grupos: nível -> (n, voltaram). Uma coluna `g` com o nível e `voltou_7d`."""
    linhas = []
    for g, (n, k) in grupos.items():
        linhas += [{"g": g, "voltou_7d": i < k} for i in range(n)]
    return pd.DataFrame(linhas)


F = Fator("x", "perfil", lambda d: d["g"])


def test_efeito_bruto_exemplo_publicado_de_newcombe():
    # A: 56 de 70 voltaram; B (referência, mais frequente): 48 de 80. Diferença +20,0 p.p.; IC 5,24 a 33,39 p.p. (Newcombe 1998)
    (l,) = bruto.calcular_bruto(_df({"A": (70, 56), "B": (80, 48)}), 30, [F])
    assert (l["nivel"], l["referencia"], l["n_nivel"], l["n_referencia"]) == ("A", "B", 70, 80)
    assert l["taxa_nivel"] == 0.8 and l["taxa_referencia"] == 0.6
    assert l["efeito_bruto_pp"] == pytest.approx(20.0, abs=1e-3)
    assert l["bruto_ic_inf"] == pytest.approx(5.24, abs=0.01)
    assert l["bruto_ic_sup"] == pytest.approx(33.39, abs=0.01)
    assert l["amostra_suficiente"] is True


def test_nivel_pequeno_marca_amostra_insuficiente_e_sinal_negativo():
    # B: 2 de 20 (10%) contra a referência A: 20 de 80 (25%): -15 p.p.; n do nível (20) < 30
    (l,) = bruto.calcular_bruto(_df({"A": (80, 20), "B": (20, 2)}), 30, [F])
    assert l["efeito_bruto_pp"] == pytest.approx(-15.0, abs=1e-3)
    assert l["amostra_suficiente"] is False
    assert l["bruto_ic_inf"] < l["efeito_bruto_pp"] < l["bruto_ic_sup"]


def test_niveis_raros_viram_outros():
    # C (10) e D (5) estão abaixo de 30: viram "outros" com 15 linhas (6 voltaram); A é a referência
    linhas = bruto.calcular_bruto(_df({"A": (100, 30), "C": (10, 4), "D": (5, 2)}), 30, [F])
    assert [l["nivel"] for l in linhas] == ["outros"]
    assert linhas[0]["n_nivel"] == 15 and linhas[0]["taxa_nivel"] == 0.4 and linhas[0]["amostra_suficiente"] is False


def test_fator_com_um_so_nivel_nao_gera_linha():
    assert bruto.calcular_bruto(_df({"A": (50, 10)}), 30, [F]) == []


def _fator(nome):
    return next(f for f in FATORES if f.nome == nome)


def test_idioma_divergente_so_vale_para_pergunta_com_mais_de_30_caracteres():
    df = pd.DataFrame({
        "idioma_divergente": [True, True, False, False, True, False],
        "faixa_chars_pergunta": ["até 30", "até 30", "até 30", "31–100", "31–100", "mais de 400"],
    })
    niveis = _fator("idioma_divergente").preparar(df)
    assert niveis.isna().tolist() == [True, True, True, False, False, False]
    assert niveis.dropna().tolist() == ["não", "sim", "não"]


def test_faixas_de_engajamento():
    df = pd.DataFrame({"n_turnos_sessao": [1, 2, 3, 4, 9], "n_conversas_sessao": [1, 2, 3, 4, 1]})
    assert _fator("n_turnos_sessao").preparar(df).tolist() == ["1", "2 a 3", "2 a 3", "4 ou mais", "4 ou mais"]
    assert _fator("n_conversas_sessao").preparar(df).tolist() == ["1", "2", "3 ou mais", "3 ou mais", "1"]


@pytest.mark.usefixtures("usar_real")
def test_bruto_real_cobre_os_fatores_e_fecha_com_a_taxa_global():
    with psycopg.connect(dsn(), autocommit=True) as c:
        linhas = bruto.gravar(c)
        df = carregar_elegiveis(c)
        gravadas = c.execute("SELECT count(*) FROM resultado.efeito_fator").fetchone()[0]
        n_min = bruto.n_minimo(c)
    assert gravadas == len(linhas) > 20
    fatores = {l["fator"] for l in linhas}
    esperados = {f.nome for f in FATORES} - {"tema"}  # tema só tem um nível até o seed da T-205
    assert esperados <= fatores
    assert {l["grupo"] for l in linhas} == {"assistente", "perfil", ENGAJAMENTO}
    for l in linhas:
        assert l["amostra_suficiente"] == (l["n_nivel"] >= n_min and l["n_referencia"] >= n_min)
        assert l["bruto_ic_inf"] <= l["efeito_bruto_pp"] <= l["bruto_ic_sup"]
    # fechamento: níveis + referência de um fator sem restrição somam a população elegível
    rec = [l for l in linhas if l["fator"] == "recusa"]
    assert rec[0]["n_nivel"] + rec[0]["n_referencia"] == len(df)
    # idioma_divergente cobre só perguntas com mais de 30 caracteres
    div = [l for l in linhas if l["fator"] == "idioma_divergente"][0]
    assert div["n_nivel"] + div["n_referencia"] == int((df["faixa_chars_pergunta"].astype(object) != "até 30").sum())
