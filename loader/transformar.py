"""Transformações (T-106/T-107): executa sql/transform/NN_*.sql em ordem, em UMA transação.

Hoje: 10_sessao, 20_usuario, 30_primeira_experiencia, 40_agregados, 50_dicionario (a ordem do prefixo importa:
os agregados leem as tabelas `_novo` das etapas anteriores).
Cada arquivo constrói tabelas `mart.<nome>_novo`. Ao final, na mesma transação, cada `_novo` substitui a tabela
atual (DROP + RENAME): quem lê nunca vê tabela vazia ou pela metade. Tudo ou nada.

Uso:  python -m loader.transformar
Variável opcional: TRANSFORM_DIR (padrão: sql/transform).
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import psycopg

from loader.migrar import dsn

PASTA = Path(os.environ.get("TRANSFORM_DIR", Path(__file__).resolve().parent.parent / "sql" / "transform"))
PADRAO = re.compile(r"^\d{2}_.+\.sql$")
LOCK_ID = 727106  # impede duas transformações simultâneas


def arquivos(pasta: Path = PASTA) -> list[Path]:
    return sorted(p for p in Path(pasta).iterdir() if PADRAO.match(p.name))


def _trocar_novas(conn: psycopg.Connection) -> list[str]:
    """Troca mart.X_novo por mart.X (e renomeia a chave primária). Devolve os nomes trocados."""
    novas = [r[0] for r in conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'mart' AND tablename LIKE %s ORDER BY 1", (r"%\_novo",))]
    trocadas = []
    for nova in novas:
        final = nova[: -len("_novo")]
        conn.execute(f"DROP TABLE IF EXISTS mart.{final}")
        conn.execute(f"ALTER TABLE mart.{nova} RENAME TO {final}")
        conn.execute(f"ALTER INDEX IF EXISTS mart.{nova}_pkey RENAME TO {final}_pkey")
        trocadas.append(final)
    return trocadas


def transformar(pasta: Path | None = None) -> list[str]:
    """Roda os arquivos em ordem e troca as tabelas. Em qualquer erro, rollback total."""
    with psycopg.connect(dsn()) as conn:  # transação única
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
        for arq in arquivos(pasta or PASTA):
            conn.execute(arq.read_text(encoding="utf-8"))
        return _trocar_novas(conn)


def main() -> int:
    t0 = time.time()
    try:
        feitas = transformar()
    except Exception as e:
        print(f"ERRO na transformação: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"Marts reconstruídos: {', '.join(feitas)} em {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
