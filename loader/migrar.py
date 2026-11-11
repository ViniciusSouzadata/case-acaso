"""Executor de migrações (T-103): aplica sql/migrations/NNN_*.sql em ordem, uma transação por arquivo."""
import os
import re
import sys
from pathlib import Path

import psycopg
from psycopg import sql

PASTA_MIGRACOES = Path(os.environ.get("MIGRACOES_DIR", Path(__file__).resolve().parent.parent / "sql" / "migrations"))
PADRAO = re.compile(r"^(\d{3})_.+\.sql$")
LOCK_ID = 727103  # advisory lock: impede dois migradores simultâneos


def dsn() -> str:
    return (
        f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


def aplicar_senha_app_ro(conn: psycopg.Connection) -> None:
    """Define a senha do app_ro a partir de APP_RO_PASSWORD (literal escapado pelo psycopg)."""
    senha = os.environ.get("APP_RO_PASSWORD")
    if not senha:
        raise RuntimeError("APP_RO_PASSWORD não definida: não dá pra configurar o papel app_ro")
    conn.execute(sql.SQL("ALTER ROLE app_ro PASSWORD {}").format(sql.Literal(senha)))


def migrar() -> list[str]:
    """Aplica migrações pendentes; devolve os nomes aplicados nesta execução."""
    arquivos = sorted(p for p in PASTA_MIGRACOES.iterdir() if PADRAO.match(p.name))
    aplicadas: list[str] = []
    with psycopg.connect(dsn(), autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
        try:
            conn.execute("CREATE SCHEMA IF NOT EXISTS ops")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS ops.schema_migrations ("
                "versao text PRIMARY KEY, nome text NOT NULL, "
                "aplicada_em timestamptz NOT NULL DEFAULT now())"
            )
            feitas = {r[0] for r in conn.execute("SELECT versao FROM ops.schema_migrations")}
            for arq in arquivos:
                versao = PADRAO.match(arq.name).group(1)
                if versao in feitas:
                    continue
                with conn.transaction():
                    conn.execute(arq.read_text(encoding="utf-8"))
                    conn.execute(
                        "INSERT INTO ops.schema_migrations (versao, nome) VALUES (%s, %s)",
                        (versao, arq.name),
                    )
                aplicadas.append(arq.name)
            aplicar_senha_app_ro(conn)
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
    return aplicadas


def main() -> None:
    aplicadas = migrar()
    print(f"Migrações aplicadas agora: {aplicadas if aplicadas else 'nenhuma (já em dia)'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # mensagem clara, código de saída != 0
        print(f"ERRO nas migrações: {e}", file=sys.stderr)
        sys.exit(1)
