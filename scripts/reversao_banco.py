"""Executa de verdade as migrações inversas (desfazer e refazer) num banco DESCARTÁVEL e confere os números no fim.

Nunca toca o banco da stack: cria `acaso_reversao`, usa e apaga no fim.
  Ciclo A (parcial, sem perder dado): desfaz 021, 020, 014, 013, 012, refaz, e confere que os números não mudaram.
  Ciclo B (total): desfaz 021 → 001, confere que stg/mart/resultado sumiram, refaz tudo, recarrega e confere os números.
Números conferidos: pessoas elegíveis, pessoas que voltaram e taxa oficial (mart.agg_retencao_sensibilidade, definicao = 'oficial').
Imprime só contagens. Rodar no container do loader:
  docker compose run --rm loader python -m scripts.reversao_banco   (ou: python /app/scripts/reversao_banco.py)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from loader import carregar, migrar, transformar  # noqa: E402

DESCARTAVEL = "acaso_reversao"
ESPERADO = (2372, 566, "23,86%")
DOWN = RAIZ / "sql" / "migrations_down"


def _admin() -> str:
    return migrar.dsn()


def _numeros() -> tuple[int, int, str]:
    with psycopg.connect(migrar.dsn()) as c:
        u, v, t = c.execute(
            "SELECT usuarios, voltaram_7d, taxa FROM mart.agg_retencao_sensibilidade WHERE definicao = 'oficial'"
        ).fetchone()
    return int(u), int(v), f"{float(t) * 100:.2f}%".replace(".", ",")


def _desfazer(versoes: list[str]) -> None:
    """Roda os arquivos *_down.sql na ordem dada (de trás para frente), cada um na sua transação."""
    with psycopg.connect(migrar.dsn(), autocommit=True) as c:
        for v in versoes:
            arq = next(DOWN.glob(f"{v}_*_down.sql"))
            c.execute(arq.read_text(encoding="utf-8"))
            print(f"  desfeita {arq.name}", flush=True)


def _apagar_derivadas() -> None:
    with psycopg.connect(migrar.dsn(), autocommit=True) as c:
        tabelas = c.execute(
            "SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('stg','mart','resultado')").fetchall()
        for esq, tab in tabelas:
            c.execute(f'DROP TABLE IF EXISTS "{esq}"."{tab}" CASCADE')
        funcoes = c.execute(
            "SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid) FROM pg_proc p "
            "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname IN ('stg','mart','resultado')").fetchall()
        for esq, f, args in funcoes:
            c.execute(f'DROP FUNCTION IF EXISTS "{esq}"."{f}"({args}) CASCADE')
    print(f'  apagadas {len(tabelas)} tabelas e {len(funcoes)} funções derivadas (produto da transformação)', flush=True)


def _versoes_aplicadas() -> list[str]:
    with psycopg.connect(migrar.dsn()) as c:
        try:
            return [r[0] for r in c.execute("SELECT versao FROM ops.schema_migrations ORDER BY versao")]
        except psycopg.errors.UndefinedTable:
            return []


def _esquemas() -> set[str]:
    with psycopg.connect(migrar.dsn()) as c:
        return {r[0] for r in c.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('stg','mart','resultado','ops')")}


def _confere(rotulo: str, n: tuple[int, int, str]) -> None:
    print(f"  {rotulo}: {n[0]} pessoas, {n[1]} voltaram, {n[2]}", flush=True)
    assert n == ESPERADO, f"{rotulo}: esperado {ESPERADO}, veio {n}"


def main() -> int:
    original = os.environ["POSTGRES_DB"]
    with psycopg.connect(_admin(), autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{DESCARTAVEL}" WITH (FORCE)')
        c.execute(f'CREATE DATABASE "{DESCARTAVEL}"')
    os.environ["POSTGRES_DB"] = DESCARTAVEL
    try:
        print("== preparo: migrar, carregar e transformar num banco descartável")
        migrar.migrar()
        carregar.carregar()
        transformar.transformar()
        todas = _versoes_aplicadas()
        print(f"  migrações aplicadas: {len(todas)} ({todas[0]} a {todas[-1]})")
        _confere("antes", _numeros())

        print("== ciclo A: desfaz 021, 020, 014, 013, 012 e refaz (sem recarregar)")
        _desfazer(["021", "020", "014", "013", "012"])
        assert _versoes_aplicadas() == todas[: todas.index("012")], "o registro não voltou ao estado esperado"
        refeitas = migrar.migrar()
        print(f"  refeitas: {[r[:3] for r in refeitas]}")
        assert _versoes_aplicadas() == todas
        _confere("depois do ciclo A", _numeros())

        print("== ciclo B: desfaz tudo (021 → 001), refaz, recarrega")
        ordem = sorted(todas, reverse=True)
        _desfazer([v for v in ordem if v != '001'])
        # 001 só apaga esquemas VAZIOS (de propósito). As tabelas que sobram em mart/resultado são produto da transformação,
        # não das migrações: o equivalente a um 'down -v' é apagá-las antes e refazê-las com a carga.
        _apagar_derivadas()
        _desfazer(['001'])
        sobrou = _esquemas() & {"stg", "mart", "resultado"}
        assert not sobrou, f"esquemas que sobraram: {sobrou}"
        print(f"  registro de migrações depois de desfazer tudo: {_versoes_aplicadas()}")
        migrar.migrar()
        assert _versoes_aplicadas() == todas
        carregar.carregar()
        transformar.transformar()
        _confere("depois do ciclo B", _numeros())
        print("OK: reversão executada e números idênticos.")
        return 0
    finally:
        os.environ["POSTGRES_DB"] = original
        with psycopg.connect(_admin(), autocommit=True) as c:
            c.execute(f'DROP DATABASE IF EXISTS "{DESCARTAVEL}" WITH (FORCE)')
        print(f"banco descartável {DESCARTAVEL} apagado.")


if __name__ == "__main__":
    raise SystemExit(main())
