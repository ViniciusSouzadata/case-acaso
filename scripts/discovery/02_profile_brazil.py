"""Discovery 02 — perfil do subconjunto Brasil (só agregados, nunca conteúdo nem IDs).

Uso: python -I scripts/discovery/02_profile_brazil.py <brazil.parquet>
Objetivo: levantar os fatos que a spec precisa (tamanho, período, identidade,
qualidade, concentração, sinais do incidente) antes de qualquer decisão em .specs/.
"""
import sys

import duckdb

src = sys.argv[1].replace("\\", "/")
con = duckdb.connect()
con.sql("SET memory_limit='2GB'; SET threads=2")
con.sql(f"""
CREATE TEMP TABLE c AS
SELECT
  conversation_hash, model, timestamp AS ts_last, turn, language, toxic, redacted,
  state, hashed_ip AS ip,
  struct_extract(header, 'user-agent') AS ua,
  struct_extract(header, 'accept-language') AS accept_lang,
  conversation[1].turn_identifier AS conv_id,
  conversation[1].timestamp AS ts_first_turn,
  conversation[1].content AS first_user_msg,
  conversation[2].content AS first_bot_msg,
  conversation[2].timestamp AS ts_first_bot,
  len(conversation) AS n_utt,
  len(list_filter(conversation, lambda t: t.role = 'user' AND t.hashed_ip IS NOT NULL AND t.hashed_ip <> hashed_ip)) AS n_turn_ip_diff,
  len(list_filter(conversation, lambda t: t.role = 'user' AND trim(coalesce(t.content,'')) = '')) AS n_empty_user,
  len(list_filter(conversation, lambda t: t.timestamp IS NULL)) AS n_null_ts
FROM read_parquet('{src}')
""")
con.sql("""
CREATE TEMP TABLE c2 AS SELECT *,
  coalesce(ts_first_turn, ts_last) AS ts_start,
  CASE WHEN ua ILIKE '%android%' THEN 'android' WHEN ua ILIKE '%iphone%' OR ua ILIKE '%ipad%' THEN 'ios'
       WHEN ua ILIKE '%windows%' THEN 'windows' WHEN ua ILIKE '%mac os%' THEN 'mac'
       WHEN ua ILIKE '%linux%' THEN 'linux' ELSE 'other' END AS os,
  CASE WHEN ua LIKE '%Edg/%' THEN 'edge' WHEN ua LIKE '%OPR/%' THEN 'opera'
       WHEN ua LIKE '%Chrome/%' THEN 'chrome' WHEN ua LIKE '%Firefox/%' THEN 'firefox'
       WHEN ua LIKE '%Safari/%' THEN 'safari' ELSE 'other' END AS browser
FROM c
""")


def q(title, sql):
    print(f"\n== {title} ==")
    rel = con.sql(sql)
    print(rel.columns)
    for row in rel.fetchall():
        print(row)


q("Tamanho e período", """SELECT count(*) conversas, min(ts_start), max(ts_start),
   count(DISTINCT conversation_hash) hashes_distintos, count(DISTINCT conv_id) conv_ids_distintos,
   count(DISTINCT ip) ips, count(DISTINCT ip||'|'||coalesce(ua,'')) ip_ua,
   count(DISTINCT ip||'|'||os||'|'||browser) ip_familia_ua FROM c2""")
q("Modelos (versão exata)", "SELECT model, count(*) n FROM c2 GROUP BY 1 ORDER BY 2 DESC")
q("Modelo por mês", """SELECT strftime(ts_start,'%Y-%m') mes, model, count(*) FROM c2 GROUP BY ALL ORDER BY 1,2""")
q("Idiomas (top 10)", "SELECT language, count(*) n FROM c2 GROUP BY 1 ORDER BY 2 DESC LIMIT 10")
q("Turnos (quantis) e % 1 turno", """SELECT quantile_cont(turn,[0.25,0.5,0.75,0.9,0.99]) q, max(turn),
   round(100.0*avg((turn=1)::int),1) pct_1turno FROM c2""")
q("Flags", """SELECT round(100*avg(toxic::int),3) pct_toxic, round(100*avg(redacted::int),2) pct_redacted,
   sum((n_empty_user>0)::int) conv_com_input_vazio, sum((n_turn_ip_diff>0)::int) conv_ip_muda_no_meio,
   sum((n_null_ts>0)::int) conv_com_ts_nulo, sum((ua IS NULL)::int) ua_nulo, sum((state IS NULL)::int) state_nulo FROM c2""")
q("Estados (top 12)", "SELECT state, count(*) n FROM c2 GROUP BY 1 ORDER BY 2 DESC LIMIT 12")
q("OS x browser", "SELECT os, browser, count(*) n FROM c2 GROUP BY ALL ORDER BY 3 DESC LIMIT 12")
q("Latência 1a resposta (s)", """SELECT quantile_cont(epoch(ts_first_bot - ts_first_turn),[0.1,0.5,0.9,0.99]) FROM c2
   WHERE ts_first_bot IS NOT NULL AND ts_first_turn IS NOT NULL""")
q("Duplicatas de hash (mesmo conteúdo)", """SELECT count(*) hashes_repetidos, sum(n) conversas_envolvidas FROM
   (SELECT conversation_hash, count(*) n FROM c2 GROUP BY 1 HAVING count(*)>1)""")
q("Concentração por IP", """WITH t AS (SELECT ip, count(*) n FROM c2 GROUP BY 1),
   r AS (SELECT n, row_number() OVER (ORDER BY n DESC) rk, count(*) OVER () tot, sum(n) OVER () s FROM t)
   SELECT max(tot) ips, quantile_cont(n,[0.5,0.9,0.99]) conv_por_ip, max(n) max_conv_1_ip,
   round(100.0*sum(n) FILTER (WHERE rk<=greatest(1,tot*0.01))/max(s),1) pct_conv_top1pct_ips,
   round(100.0*sum(n) FILTER (WHERE rk<=10)/max(s),1) pct_conv_top10_ips FROM r""")
q("UAs distintos por IP", """WITH t AS (SELECT ip, count(DISTINCT ua) k FROM c2 GROUP BY 1)
   SELECT quantile_cont(k,[0.5,0.9,0.99]), max(k), sum((k>=5)::int) ips_5mais_uas, sum((k>=20)::int) ips_20mais FROM t""")
q("Recusa (heurística 1a resposta)", """SELECT round(100*avg((regexp_matches(lower(first_bot_msg),
   'i''m sorry|i cannot|i can''t|as an ai|desculpe, mas|não posso|nao posso|como uma ia|como um modelo de linguagem'))::int),1) pct FROM c2""")
q("Volume semanal (UTC)", "SELECT date_trunc('week', ts_start)::date sem, count(*) FROM c2 GROUP BY 1 ORDER BY 1")

# Retenção ingênua por duas chaves de identidade, por coorte semanal (UTC).
for nome, chave in [("IP", "ip"), ("IP+UA", "ip||'|'||coalesce(ua,'')"), ("IP+familia", "ip||'|'||os||'|'||browser")]:
    q(f"Retenção 7d ingênua — chave {nome}", f"""
    WITH u AS (SELECT {chave} k, ts_start FROM c2),
    f AS (SELECT k, min(ts_start) t0 FROM u GROUP BY 1)
    SELECT date_trunc('week', f.t0)::date coorte, count(*) novos,
      count(*) FILTER (WHERE EXISTS (SELECT 1 FROM u WHERE u.k=f.k AND u.ts_start > f.t0 + INTERVAL 1 HOUR
                                    AND u.ts_start <= f.t0 + INTERVAL 7 DAY)) voltaram,
      round(100.0*voltaram/novos,1) pct
    FROM f GROUP BY 1 ORDER BY 1""")

# Incidente §4.2: semanas 06/11, 13/11, 20/11/2023 — novos por IP+UA que caem em IPs já vistos.
q("Incidente: novos IP+UA cujo IP já existia antes", """
WITH f AS (SELECT ip, ua, min(ts_start) t0 FROM c2 GROUP BY 1,2),
fi AS (SELECT ip, min(ts_start) t0ip FROM c2 GROUP BY 1)
SELECT date_trunc('week', f.t0)::date sem, count(*) novos_ip_ua,
  sum((f.t0 > fi.t0ip + INTERVAL 1 HOUR)::int) ip_ja_visto_antes
FROM f JOIN fi USING (ip)
WHERE f.t0 >= '2023-10-30' AND f.t0 < '2023-12-04' GROUP BY 1 ORDER BY 1""")
q("Incidente: IPs com mais UAs novos por semana (contagem, sem IDs)", """
WITH f AS (SELECT ip, ua, min(ts_start) t0 FROM c2 GROUP BY 1,2)
SELECT sem, max(k) max_uas_novos_1ip, sum((k>=10)::int) ips_com_10mais FROM
 (SELECT date_trunc('week', t0)::date sem, ip, count(*) k FROM f
  WHERE t0 >= '2023-10-30' AND t0 < '2023-12-04' GROUP BY 1,2) GROUP BY 1 ORDER BY 1""")
