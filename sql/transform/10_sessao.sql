-- T-106: mart.fct_sessao. Só conversas que contam como uso. Limiares lidos de ops.parametros.
-- Constrói mart.fct_sessao_novo; loader/transformar.py troca o nome na mesma transação.
DROP TABLE IF EXISTS mart.fct_sessao_novo;

CREATE TABLE mart.fct_sessao_novo AS
WITH p AS (
    SELECT ops.param('gap_sessao_min')::int * interval '1 minute' AS gap
),
marc AS (
    SELECT usuario_id, conversa_id, ts_inicio, ts_fim, n_turnos,
           CASE WHEN lag(ts_fim) OVER w IS NULL OR ts_inicio - lag(ts_fim) OVER w > (SELECT gap FROM p)
                THEN 1 ELSE 0 END AS nova
    FROM stg.conversa
    WHERE conta_como_uso
    WINDOW w AS (PARTITION BY usuario_id ORDER BY ts_inicio, conversa_id)
),
seqs AS (
    SELECT *, sum(nova) OVER (PARTITION BY usuario_id ORDER BY ts_inicio, conversa_id)::int AS seq FROM marc
)
SELECT usuario_id,
       seq,
       min(ts_inicio)       AS ts_inicio,
       max(ts_fim)          AS ts_fim,
       count(*)::int        AS n_conversas,
       sum(n_turnos)::int   AS n_turnos
FROM seqs
GROUP BY usuario_id, seq;

ALTER TABLE mart.fct_sessao_novo ADD PRIMARY KEY (usuario_id, seq);
