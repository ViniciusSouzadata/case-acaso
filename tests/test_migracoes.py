import os

import psycopg
import pytest

from loader import migrar


def _dsn(usuario: str, senha: str) -> str:
    return (
        f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} user={usuario} password={senha}"
    )


@pytest.fixture(scope="module", autouse=True)
def banco_migrado():
    migrar.migrar()


def test_idempotencia():
    with psycopg.connect(migrar.dsn()) as c:
        antes = c.execute("SELECT versao, nome FROM ops.schema_migrations ORDER BY versao").fetchall()
        n_param = c.execute("SELECT count(*) FROM ops.parametros").fetchone()[0]
    assert antes, "nenhuma migração registrada"
    assert migrar.migrar() == []  # segunda execução não reaplica nada
    with psycopg.connect(migrar.dsn()) as c:
        depois = c.execute("SELECT versao, nome FROM ops.schema_migrations ORDER BY versao").fetchall()
        assert c.execute("SELECT count(*) FROM ops.parametros").fetchone()[0] == n_param
    assert antes == depois


def test_parametros_v1():
    with psycopg.connect(migrar.dsn()) as c:
        p = dict(c.execute("SELECT chave, valor FROM ops.parametros").fetchall())
    assert p == {
        "versao_definicao": "1.0.0",
        "gap_sessao_min": "30",
        "janela_retorno_horas": "168",
        "burn_in_dias": "14",
        "n_minimo": "30",
        "limiar_conversas_ip": "200",
        "limiar_uas_ip": "10",
        "fuso_pais": "America/Sao_Paulo",
    }


def test_app_ro_sem_acesso_a_stg():
    with psycopg.connect(_dsn("app_ro", os.environ["APP_RO_PASSWORD"])) as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("SELECT * FROM stg.conversa")


def test_app_ro_le_mart_e_resultado_futuros_e_lote():
    with psycopg.connect(migrar.dsn(), autocommit=True) as dono:
        dono.execute("CREATE TABLE mart.t_teste_permissao (x int)")
        dono.execute("CREATE TABLE resultado.t_teste_permissao (x int)")
        try:
            with psycopg.connect(_dsn("app_ro", os.environ["APP_RO_PASSWORD"])) as c:
                assert c.execute("SELECT * FROM mart.t_teste_permissao").fetchall() == []
                assert c.execute("SELECT * FROM resultado.t_teste_permissao").fetchall() == []
                assert isinstance(c.execute("SELECT * FROM ops.lote_carga").fetchall(), list)  # T-104: pode haver lotes
                # 020 (T-303): ops.reconciliacao passou a ser legível (tela de Qualidade); parametros e rejeitado seguem fechados
                assert isinstance(c.execute("SELECT * FROM ops.reconciliacao").fetchall(), list)
                for tabela in ("ops.parametros", "ops.rejeitado"):
                    with pytest.raises(psycopg.errors.InsufficientPrivilege):
                        c.execute(f"SELECT * FROM {tabela}")
                    c.rollback()
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    c.execute("INSERT INTO mart.t_teste_permissao VALUES (1)")
        finally:
            dono.execute("DROP TABLE mart.t_teste_permissao")
            dono.execute("DROP TABLE resultado.t_teste_permissao")
