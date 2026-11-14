"""Fixtures compartilhadas (T-109): carrega + transforma o snapshot real UMA vez e o sintético UMA vez por sessão.

Cada conjunto vive em seu próprio banco (`acaso_t_sint`, `acaso_t_real`), criado no início da sessão (o sintético é removido no fim; o real fica em cache, ver abaixo); os testes escolhem o conjunto com `@pytest.mark.usefixtures("usar_sint")` ou `("usar_real")`, que só apontam
POSTGRES_DB para ele durante o teste (o código sob teste lê o banco de `migrar.dsn()` a cada chamada). Os bancos
padrão (`POSTGRES_DB`) ficam para test_migracoes e test_carregar, que mexem em stg/ops à vontade.

O banco real leva ~100 s para transformar (9 chamadas de mart.calc_retencao sobre 11,6 mil conversas): por isso é
montado em um SUBPROCESSO iniciado já na coleta (só se algum teste coletado usar `usar_real`), em paralelo com o resto.
Testes que alteram um desses bancos (parâmetro, mart) devem restaurar antes de terminar.

Cache do banco real entre execuções (o volume do db sobrevive a `make test`): ele só é reconstruído quando muda
algo que o afeta (impressão digital = SQL, código do loader, seeds e checksum do snapshot, gravada como comentário
do banco). `docker compose down -v` ou TESTES_SEM_CACHE=1 forçam a reconstrução.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

import fabrica_bruto
from loader import carregar, migrar, transformar

DB_SINT = "acaso_t_sint"
DB_REAL = "acaso_t_real"
DB_GERAL = "acaso_t_geral"  # test_carregar e test_migracoes: nunca no banco padrão (o da stack no ar)
SNAPSHOT = Path(carregar.SNAPSHOT)
RAIZ = Path(carregar.RAIZ)

_estado: dict = {"proc_real": None, "log_real": None, "impressao": None}


def _impressao_real() -> str:
    """Hash do que determina o conteúdo do banco real: SQL, loader, seeds e checksum do snapshot."""
    h = hashlib.sha256()
    arquivos = [*sorted((RAIZ / "sql").rglob("*.sql")), *sorted((RAIZ / "loader").glob("*.py")),
                *sorted((RAIZ / "seeds").glob("*")), SNAPSHOT.with_suffix(".sha256")]
    for a in arquivos:
        if a.is_file():
            h.update(a.relative_to(RAIZ).as_posix().encode() + b" " + a.read_bytes() + b" ")
    return h.hexdigest()


def _comentario_banco(nome: str) -> str | None:
    with psycopg.connect(_dsn_admin(), autocommit=True) as c:
        r = c.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = %s", (nome,)).fetchone()
    return r[0] if r else None


def _dsn_admin() -> str:
    return migrar.dsn()  # banco padrão do compose


def _recriar_banco(nome: str) -> None:
    with psycopg.connect(_dsn_admin(), autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)')
        c.execute(f'CREATE DATABASE "{nome}"')


class _em_banco:
    """Context manager: aponta POSTGRES_DB para `nome` e restaura ao sair."""

    def __init__(self, nome: str):
        self.nome, self.antes = nome, None

    def __enter__(self):
        self.antes = os.environ["POSTGRES_DB"]
        os.environ["POSTGRES_DB"] = self.nome

    def __exit__(self, *exc):
        os.environ["POSTGRES_DB"] = self.antes


def _usa_real(item) -> bool:
    return "usar_real" in getattr(item, "fixturenames", ())


def pytest_collection_modifyitems(items):
    """Testes do banco real por último: a montagem em segundo plano termina enquanto o resto roda."""
    items.sort(key=_usa_real)  # sort estável: só empurra os `usar_real` para o fim


def pytest_collection_finish(session):
    """Começa a montar o banco real em segundo plano se algum teste coletado precisa dele (e o cache não vale)."""
    if not SNAPSHOT.is_file() or not any(_usa_real(i) for i in session.items):
        return
    _estado["impressao"] = _impressao_real()
    if not os.environ.get("TESTES_SEM_CACHE") and _comentario_banco(DB_REAL) == _estado["impressao"]:
        return  # banco real já montado para este código + snapshot
    _recriar_banco(DB_REAL)
    log = Path("/tmp/montagem_real.log").open("w")
    env = {**os.environ, "POSTGRES_DB": DB_REAL}
    _estado["log_real"] = log
    _estado["proc_real"] = subprocess.Popen(
        [sys.executable, "-c",
         "from loader import migrar, carregar, transformar; migrar.migrar(); carregar.carregar(); transformar.transformar()"],
        cwd=RAIZ, env=env, stdout=log, stderr=subprocess.STDOUT)


def pytest_sessionfinish(session, exitstatus):
    proc = _estado["proc_real"]
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait()
    if _estado["log_real"]:
        _estado["log_real"].close()
    with psycopg.connect(_dsn_admin(), autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{DB_SINT}" WITH (FORCE)')
        if _estado["impressao"] and _comentario_banco(DB_REAL) != _estado["impressao"]:  # montagem interrompida ou sem validade: não deixa lixo
            c.execute(f'DROP DATABASE IF EXISTS "{DB_REAL}" WITH (FORCE)')


@pytest.fixture(scope="session")
def sint_parquet(tmp_path_factory) -> Path:
    return fabrica_bruto.gerar(tmp_path_factory.mktemp("sint") / "sintetico.parquet")


@pytest.fixture(scope="session")
def banco_sint(sint_parquet) -> str:
    """Banco sintético migrado, carregado e transformado uma única vez na sessão."""
    _recriar_banco(DB_SINT)
    with _em_banco(DB_SINT):
        migrar.migrar()
        carregar.carregar(sint_parquet)
        transformar.transformar()
    return DB_SINT


@pytest.fixture(scope="session")
def banco_real() -> str:
    """Espera o subprocesso que monta o banco real (iniciado na coleta)."""
    if not SNAPSHOT.is_file():
        pytest.skip("snapshot real ausente")
    proc = _estado["proc_real"]
    if proc is not None:  # None = cache válido (banco já montado)
        if proc.wait() != 0:
            pytest.fail("montagem do banco real falhou: " + Path("/tmp/montagem_real.log").read_text()[-2000:])
        _estado["proc_real"] = None
        with psycopg.connect(_dsn_admin(), autocommit=True) as c:
            c.execute(sql.SQL("COMMENT ON DATABASE {} IS {}").format(sql.Identifier(DB_REAL), sql.Literal(_estado["impressao"])))
    return DB_REAL


@pytest.fixture(scope="module")
def banco_geral():
    """Banco descartável migrado para os testes que gravam em stg/ops (carga, migrações): o banco padrão é o da stack no ar."""
    _recriar_banco(DB_GERAL)
    with _em_banco(DB_GERAL):
        migrar.migrar()
        yield DB_GERAL
    with psycopg.connect(_dsn_admin(), autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{DB_GERAL}" WITH (FORCE)')


@pytest.fixture
def usar_sint(banco_sint):
    with _em_banco(banco_sint):
        yield


@pytest.fixture
def usar_real(banco_real):
    with _em_banco(banco_real):
        yield


def restaurar_sint(sint_parquet: Path) -> None:
    """Recarrega + retransforma o sintético (depois de um teste que sabotou stg/mart). Deve rodar dentro de usar_sint."""
    carregar.carregar(sint_parquet)
    transformar.transformar()
