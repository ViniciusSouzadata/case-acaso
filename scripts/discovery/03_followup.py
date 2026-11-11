"""Discovery 03 — checagens que o perfil 02 levantou (só agregados).

Uso: python -I scripts/discovery/03_followup.py <brazil.parquet>
"""
import sys

import duckdb

src = sys.argv[1].replace("\\", "/")
con = duckdb.connect()
con.sql("SET memory_limit='2GB'; SET threads=2; SET TimeZone='UTC'")


def q(title, sql):
    print(f"\n== {title} ==")
    rel = con.sql(sql)
    print(rel.columns)
    for row in rel.fetchall():
        print(row)


con.sql(f"CREATE TEMP TABLE b AS SELECT * FROM read_parquet('{src}')")
con.sql("""CREATE TEMP TABLE u AS
SELECT b.conversation_hash, b.hashed_ip ip, b.timestamp ts_last, b.turn, b.model, b.state,
       unnest(b.conversation) AS t FROM b""")

q("Timestamp nulo por papel", """SELECT t.role, count(*) n, sum((t.timestamp IS NULL)::int) nulos FROM u GROUP BY 1""")
q("hashed_ip/header nulo por papel", """SELECT t.role, sum((t.hashed_ip IS NULL)::int) ip_nulo,
   sum((t.header IS NULL)::int) header_nulo FROM u GROUP BY 1""")

# Início da conversa = timestamp da 1a resposta do assistente (o usuário não tem timestamp).
con.sql("""CREATE TEMP TABLE c AS SELECT conversation_hash, hashed_ip ip, model, state, turn, timestamp ts_last,
  list_filter(conversation, lambda t: t.role='assistant')[1].timestamp AS ts_first_bot,
  struct_extract(header,'user-agent') ua FROM b""")
q("Duração conversa (último - 1a resposta), min", """SELECT quantile_cont(epoch(ts_last-ts_first_bot)/60,[0.5,0.9,0.99]),
   sum((ts_first_bot IS NULL)::int) sem_bot, sum((ts_last < ts_first_bot)::int) inconsistentes FROM c""")

q("IP mais pesado: participação, estado, modelos, dias ativos", """
WITH top AS (SELECT ip FROM c GROUP BY 1 ORDER BY count(*) DESC LIMIT 5)
SELECT row_number() OVER (ORDER BY count(*) DESC) rk, count(*) conv, round(100.0*count(*)/11621,1) pct,
  mode(state) estado, count(DISTINCT ua) uas, count(DISTINCT ts_first_bot::date) dias_ativos,
  round(avg(turn),1) turnos_med
FROM c WHERE ip IN (SELECT ip FROM top) GROUP BY ip ORDER BY conv DESC""")

q("Gap entre conversas do mesmo IP (min) — quantis", """
WITH s AS (SELECT ip, ts_first_bot, lag(ts_last) OVER (PARTITION BY ip ORDER BY ts_first_bot) prev FROM c)
SELECT quantile_cont(epoch(ts_first_bot-prev)/60,[0.1,0.25,0.5,0.75,0.9]) FROM s WHERE prev IS NOT NULL""")
q("Gap: % abaixo de 30 min / 60 min / 24h", """
WITH s AS (SELECT ip, ts_first_bot, lag(ts_last) OVER (PARTITION BY ip ORDER BY ts_first_bot) prev FROM c),
g AS (SELECT epoch(ts_first_bot-prev)/60 m FROM s WHERE prev IS NOT NULL)
SELECT round(100*avg((m<30)::int),1) lt30, round(100*avg((m<60)::int),1) lt60, round(100*avg((m<1440)::int),1) lt24h FROM g""")

# Retenção por chave IP com início correto, sessão = gap de 30 min, retorno = nova sessão em (fim 1a sessão, início+7d].
q("Retenção IP — usuários elegíveis e taxa global (sessão 30 min)", """
WITH s AS (SELECT ip, ts_first_bot st, ts_last en,
   CASE WHEN ts_first_bot - lag(ts_last) OVER (PARTITION BY ip ORDER BY ts_first_bot) <= INTERVAL 30 MINUTE THEN 0 ELSE 1 END new_s
   FROM c WHERE ts_first_bot IS NOT NULL),
s2 AS (SELECT *, sum(new_s) OVER (PARTITION BY ip ORDER BY st) sid FROM s),
sess AS (SELECT ip, sid, min(st) st, max(en) en FROM s2 GROUP BY 1,2),
f AS (SELECT ip, st t0, en t0end FROM sess WHERE sid=1),
r AS (SELECT f.ip, f.t0, EXISTS (SELECT 1 FROM sess x WHERE x.ip=f.ip AND x.sid>1 AND x.st <= f.t0 + INTERVAL 7 DAY) voltou FROM f)
SELECT count(*) usuarios, sum(voltou::int) voltaram, round(100*avg(voltou::int),1) pct,
  sum((t0 < TIMESTAMP '2024-04-29' - INTERVAL 7 DAY)::int) maduros FROM r""")

q("Uso do GPT-4 x período (disponibilidade)", """SELECT strftime(ts_first_bot,'%Y-%m') mes,
  round(100*avg((model LIKE 'gpt-4%')::int),0) pct_gpt4, count(*) n FROM c GROUP BY 1 ORDER BY 1""")
