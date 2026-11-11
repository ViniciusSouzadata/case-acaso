"""Discovery 01 — extrai o subconjunto Brasil do WildChat-1M para um parquet local.

Uso: python -I scripts/discovery/01_extract_brazil.py <raw_dir> <out_dir>
Fase: Context Absorption (Waldemar). Não é código de produção; o pipeline oficial
vai ser especificado em .specs/ depois deste perfil.
"""
import sys
from pathlib import Path

import duckdb

raw_dir = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
src = (raw_dir / "data" / "*.parquet").as_posix()
con = duckdb.connect()
con.sql("SET memory_limit='2GB'; SET threads=2; SET preserve_insertion_order=false")

# Contexto global: quantas conversas por país (top 15) e quanto o Brasil pesa.
print("== Conversas por país (top 15) ==")
print(con.sql(f"""
    SELECT country, count(*) AS n, round(100.0*count(*)/sum(count(*)) OVER (),2) AS pct
    FROM read_parquet('{src}') GROUP BY 1 ORDER BY 2 DESC LIMIT 15
""").fetchall())

# Conversas cujo país "da conversa" não é Brasil, mas algum turno de usuário veio do Brasil
# (o campo top-level é o país do IP mais comum na conversa).
print("== Conversas com algum turno BR mas country top-level != Brazil ==")
print(con.sql(f"""
    SELECT count(*) FROM read_parquet('{src}')
    WHERE coalesce(country,'') <> 'Brazil'
      AND len(list_filter(conversation, lambda t: t.country = 'Brazil')) > 0
""").fetchall())

out = (out_dir / "brazil.parquet").as_posix()
con.sql(f"""
    COPY (SELECT * FROM read_parquet('{src}') WHERE country = 'Brazil')
    TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
print("== Linhas Brasil ==", con.sql(f"SELECT count(*) FROM read_parquet('{out}')").fetchall())
