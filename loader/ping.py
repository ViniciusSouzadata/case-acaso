"""Esqueleto (T-101): conecta no Postgres e imprime a versão. Substituído pelo cli.py na T-110."""
import os

import psycopg


def main() -> None:
    dsn = (
        f"host={os.environ['PGHOST']} port={os.environ.get('PGPORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )
    with psycopg.connect(dsn) as conn:
        versao = conn.execute("SELECT version()").fetchone()[0]
    print(f"Conectado ao Postgres: {versao}")


if __name__ == "__main__":
    main()
