-- REVERSÃO da migração 005. Volta mart.calc_retencao à versão da 004 (sem regra_retorno) e remove as funções de Wilson.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
DROP FUNCTION IF EXISTS mart.calc_retencao(text, int, text, bool, bool, bool, text);
DROP FUNCTION IF EXISTS mart.wilson_inf(bigint, bigint);
DROP FUNCTION IF EXISTS mart.wilson_sup(bigint, bigint);

CREATE FUNCTION mart.calc_retencao(
    chave           text,
    gap_min         int  DEFAULT NULL,
    fuso            text DEFAULT NULL,
    usar_burn_in    bool DEFAULT NULL,
    incluir_anomalo bool DEFAULT NULL,
    incluir_vazias  bool DEFAULT NULL
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
BEGIN
    IF v_chave NOT IN ('oficial', 'ip', 'ip_ua') THEN
        RAISE EXCEPTION 'chave inválida: % (use oficial, ip ou ip_ua)', v_chave;
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
    ips AS (
        SELECT hashed_ip,
               (count(*) >= (SELECT lim_conv FROM p) OR count(DISTINCT user_agent) >= (SELECT lim_ua FROM p)) AS anomalo
        FROM stg.conversa GROUP BY hashed_ip
    ),
    c AS (
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
    sessao AS (
        SELECT u, seq, min(ts_inicio) AS ts_ini, min(hashed_ip) AS hashed_ip FROM seqs GROUP BY u, seq
    ),
    usr AS (
        SELECT s1.u, s1.ts_ini AS ts_primeira, s1.hashed_ip,
               EXISTS (SELECT 1 FROM sessao s2 WHERE s2.u = s1.u AND s2.seq > 1
                       AND s2.ts_ini <= s1.ts_ini + (SELECT janela FROM p)) AS voltou
        FROM sessao s1 WHERE s1.seq = 1
    ),
    elegivel AS (
        SELECT usr.* FROM usr, base, p
        WHERE usr.ts_primeira + p.janela <= base.fim
          AND (NOT v_burn OR NOT usr.ts_primeira < base.inicio + p.burn_in)
          AND (v_anomalo OR NOT coalesce((SELECT i.anomalo FROM ips i WHERE i.hashed_ip = usr.hashed_ip), false))
    )
    SELECT count(*)::bigint,
           count(*) FILTER (WHERE voltou)::bigint,
           round(count(*) FILTER (WHERE voltou)::numeric / nullif(count(*), 0), 6)
    FROM elegivel;
END
$$;
DELETE FROM ops.schema_migrations WHERE versao = '005';
COMMIT;
