-- T-110: mart.calc_retencao reescrita em conjuntos, SEM mudar nenhum resultado (mesma assinatura, mesma semântica).
-- Causa da lentidão (EXPLAIN ANALYZE): a CTE `ips` era usada em uma subconsulta correlacionada por usuário
-- (`SELECT i.anomalo FROM ips i WHERE i.hashed_ip = usr.hashed_ip`), que o planejador inlinava como um
-- Seq Scan + GroupAggregate de stg.conversa a cada usuário (2.498 x 11,6 mil linhas = 2,4 milhões de buffers, ~11 s).
-- Os EXISTS de retorno também eram subplans por usuário. Agora: `ips` calculada uma vez e ligada por JOIN;
-- o retorno vira um LEFT JOIN + bool_or sobre os eventos de retorno (sessões com seq > 1, ou conversas, conforme a regra).
-- Mesma assinatura: CREATE OR REPLACE basta (as migrações 001-005 não são editadas).
CREATE OR REPLACE FUNCTION mart.calc_retencao(
    chave           text,
    gap_min         int  DEFAULT NULL,
    fuso            text DEFAULT NULL,
    usar_burn_in    bool DEFAULT NULL,
    incluir_anomalo bool DEFAULT NULL,
    incluir_vazias  bool DEFAULT NULL,
    regra_retorno   text DEFAULT 'sessao'
) RETURNS TABLE (usuarios bigint, voltaram_7d bigint, taxa numeric)
LANGUAGE plpgsql STABLE AS $$
#variable_conflict use_column
DECLARE
    v_chave    text := chave;
    v_gap      int  := coalesce(gap_min, ops.param('gap_sessao_min')::int);
    v_fuso     text := coalesce(fuso, ops.param('fuso_pais'));  -- só coorte; sem efeito no total
    v_burn     bool := coalesce(usar_burn_in, true);
    v_anomalo  bool := coalesce(incluir_anomalo, false);
    v_vazias   bool := coalesce(incluir_vazias, false);
    v_regra    text := coalesce(regra_retorno, 'sessao');
BEGIN
    IF v_chave NOT IN ('oficial', 'ip', 'ip_ua') THEN
        RAISE EXCEPTION 'chave inválida: % (use oficial, ip ou ip_ua)', v_chave;
    END IF;
    IF v_regra NOT IN ('sessao', 'outro_dia') THEN
        RAISE EXCEPTION 'regra_retorno inválida: % (use sessao ou outro_dia)', v_regra;
    END IF;
    RETURN QUERY
    WITH p AS (
        SELECT v_gap * interval '1 minute'                                AS gap,
               ops.param('janela_retorno_horas')::int * interval '1 hour' AS janela,
               ops.param('burn_in_dias')::int * interval '1 day'          AS burn_in,
               ops.param('limiar_conversas_ip')::int                      AS lim_conv,
               ops.param('limiar_uas_ip')::int                            AS lim_ua
    ),
    base AS (SELECT min(ts_inicio) AS inicio, max(ts_fim) AS fim FROM stg.conversa),
    ips AS MATERIALIZED (
        SELECT hashed_ip,
               (count(*) >= (SELECT lim_conv FROM p) OR count(DISTINCT user_agent) >= (SELECT lim_ua FROM p)) AS anomalo
        FROM stg.conversa GROUP BY hashed_ip
    ),
    c AS MATERIALIZED (
        SELECT CASE v_chave WHEN 'oficial' THEN usuario_id WHEN 'ip' THEN usuario_id_ip ELSE usuario_id_ip_ua END AS u,
               hashed_ip, conversa_id, ts_inicio, ts_fim
        FROM stg.conversa
        WHERE v_vazias OR conta_como_uso
    ),
    marc AS (
        SELECT u, hashed_ip, conversa_id, ts_inicio,
               CASE WHEN lag(ts_fim) OVER w IS NULL OR ts_inicio - lag(ts_fim) OVER w > (SELECT gap FROM p)
                    THEN 1 ELSE 0 END AS nova
        FROM c WINDOW w AS (PARTITION BY u ORDER BY ts_inicio, conversa_id)
    ),
    seqs AS (
        SELECT u, hashed_ip, ts_inicio,
               sum(nova) OVER (PARTITION BY u ORDER BY ts_inicio, conversa_id) AS seq
        FROM marc
    ),
    sessao AS MATERIALIZED (
        SELECT u, seq, min(ts_inicio) AS ts_ini, min(hashed_ip) AS hashed_ip FROM seqs GROUP BY u, seq
    ),
    -- eventos que podem contar como retorno: outras sessões (regra 'sessao') ou conversas com seu dia local ('outro_dia')
    ret AS (
        SELECT s2.u, s2.ts_ini AS ts, NULL::date AS dia
        FROM sessao s2 WHERE v_regra = 'sessao' AND s2.seq > 1
        UNION ALL
        SELECT c2.u, c2.ts_inicio, (c2.ts_inicio AT TIME ZONE v_fuso)::date
        FROM c c2 WHERE v_regra <> 'sessao'
    ),
    usr AS (
        SELECT s1.u, s1.ts_ini AS ts_primeira, s1.hashed_ip,
               coalesce(bool_or(r.u IS NOT NULL), false) AS voltou
        FROM sessao s1
        LEFT JOIN ret r
               ON r.u = s1.u
              AND r.ts <= s1.ts_ini + (SELECT janela FROM p)
              AND (v_regra = 'sessao' OR r.dia <> (s1.ts_ini AT TIME ZONE v_fuso)::date)
        WHERE s1.seq = 1
        GROUP BY s1.u, s1.ts_ini, s1.hashed_ip
    ),
    elegivel AS (
        SELECT usr.* FROM usr
        CROSS JOIN base CROSS JOIN p
        LEFT JOIN ips i ON i.hashed_ip = usr.hashed_ip
        WHERE usr.ts_primeira + p.janela <= base.fim
          AND (NOT v_burn OR NOT usr.ts_primeira < base.inicio + p.burn_in)
          AND (v_anomalo OR NOT coalesce(i.anomalo, false))
    )
    SELECT count(*)::bigint,
           count(*) FILTER (WHERE voltou)::bigint,
           round(count(*) FILTER (WHERE voltou)::numeric / nullif(count(*), 0), 6)
    FROM elegivel;
END
$$;
