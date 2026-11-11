"""T-201: a análise e a base concordam no número principal; reexecutar regrava sem duplicar; app_ro lê resultado.meta."""
import os

import psycopg
import pytest

from analise import meta
from analise.dados import carregar_elegiveis
from loader.migrar import dsn


@pytest.mark.usefixtures("usar_real")
def test_taxa_global_igual_a_linha_oficial_do_mart():
    with psycopg.connect(dsn(), autocommit=True) as c:
        m = meta.gravar(c)
        usuarios, voltaram, taxa, inf, sup = c.execute(
            "SELECT usuarios, voltaram_7d, taxa, ic_inf, ic_sup FROM mart.agg_retencao_sensibilidade "
            "WHERE definicao = 'oficial'").fetchone()
        linhas = c.execute("SELECT count(*) FROM resultado.meta").fetchone()[0]
    assert (m["n_elegiveis"], m["n_retornos"]) == (usuarios, voltaram)
    assert float(m["taxa_global"]) == pytest.approx(float(taxa), abs=1e-6)
    assert float(m["ic_inf"]) == pytest.approx(float(inf), abs=1e-6)
    assert float(m["ic_sup"]) == pytest.approx(float(sup), abs=1e-6)
    assert linhas == 1


@pytest.mark.usefixtures("usar_real")
def test_gravar_duas_vezes_nao_duplica_e_mantem_os_numeros():
    with psycopg.connect(dsn(), autocommit=True) as c:
        a = meta.gravar(c)
        b = meta.gravar(c)
        n = c.execute("SELECT count(*) FROM resultado.meta").fetchone()[0]
    assert n == 1
    for k in ("n_elegiveis", "n_retornos", "taxa_global", "ic_inf", "ic_sup",
              "efeito_minimo_detectavel_pp", "efeito_minimo_detectavel_15_85_pp"):
        assert a[k] == b[k]


@pytest.mark.usefixtures("usar_real")
def test_efeito_minimo_detectavel_gravado_e_plausivel():
    with psycopg.connect(dsn(), autocommit=True) as c:
        meta.gravar(c)
        mde50, mde15 = c.execute(
            "SELECT efeito_minimo_detectavel_pp, efeito_minimo_detectavel_15_85_pp FROM resultado.meta").fetchone()
    assert 4 < float(mde50) < 6 and 6 < float(mde15) < 8


@pytest.mark.usefixtures("usar_real")
def test_populacao_so_elegiveis_e_sem_identificadores():
    with psycopg.connect(dsn(), autocommit=True) as c:
        df = carregar_elegiveis(c)
        esperado = c.execute("SELECT count(*) FROM mart.fct_primeira_experiencia WHERE elegivel").fetchone()[0]
    assert len(df) == esperado
    assert not {"hashed_ip", "user_agent", "pergunta", "resposta"} & set(df.columns)


@pytest.mark.usefixtures("usar_real")
def test_app_ro_le_resultado_meta():
    dsn_ro = (f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} dbname={os.environ['POSTGRES_DB']} "
              f"user=app_ro password={os.environ['APP_RO_PASSWORD']}")
    with psycopg.connect(dsn(), autocommit=True) as c:
        meta.gravar(c)
    with psycopg.connect(dsn_ro, autocommit=True) as ro:
        assert ro.execute("SELECT count(*) FROM resultado.meta").fetchone()[0] == 1
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            ro.execute("SELECT 1 FROM stg.conversa LIMIT 1")
