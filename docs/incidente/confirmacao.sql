-- Incidente §4.2: consulta de confirmação (versão Postgres). Mesma lógica de scripts/incidente_confirmacao.py (DuckDB no snapshot).
-- Roda como o dono da carga (a tabela stg é restrita). Só agregados; não seleciona IP, user-agent nem texto.
-- Hipótese que confirma: a chave `hashed_ip|user-agent` infla "usuários novos" (carga), sem mudar quem voltou.
WITH chave_ip_ua AS (
  SELECT hashed_ip AS ip, user_agent AS ua, min(ts_inicio) AS t0
  FROM stg.conversa
  WHERE hashed_ip IS NOT NULL
  GROUP BY 1, 2
), chave_ip AS (
  SELECT ip, min(t0) AS t0 FROM chave_ip_ua GROUP BY 1
), k AS (
  SELECT c.ip, c.t0, i.t0 AS t0_ip,
         date_trunc('week', c.t0 AT TIME ZONE 'America/Sao_Paulo')::date AS semana
  FROM chave_ip_ua c JOIN chave_ip i USING (ip)
), novos_ip AS (
  SELECT date_trunc('week', t0 AT TIME ZONE 'America/Sao_Paulo')::date AS semana, count(*) AS novos_ip FROM chave_ip GROUP BY 1
), novos_ip_ua AS (
  SELECT semana, count(*) AS novos_ip_ua, count(*) FILTER (WHERE t0_ip < t0) AS novos_em_ip_ja_visto FROM k GROUP BY 1
), max_ua AS (
  SELECT semana, max(n) AS max_uas_novos_por_ip FROM (SELECT semana, ip, count(*) AS n FROM k GROUP BY 1, 2) x GROUP BY 1
)
SELECT semana, coalesce(novos_ip, 0) AS novos_ip, novos_ip_ua, novos_em_ip_ja_visto, max_uas_novos_por_ip
FROM novos_ip_ua LEFT JOIN novos_ip USING (semana) JOIN max_ua USING (semana)
ORDER BY semana;
