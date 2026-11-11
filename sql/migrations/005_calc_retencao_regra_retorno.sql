-- T-107: calc_retencao ganha regra_retorno ('sessao' | 'outro_dia') e entram as funções do IC de Wilson.
-- Troca de assinatura: DROP da antiga + CREATE da nova. Chamadas com até 6 argumentos continuam valendo (novo é o último, com padrão).
DROP FUNCTION IF EXISTS mart.calc_retencao(text, int, text, bool, bool, bool);

-- IC 95% de Wilson para k sucessos em n tentativas (z = 1,96). NULL se n <= 0.
--   centro = (p + z²/2n) / (1 + z²/n);  meia-largura = z·sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n)
CREATE FUNCTION mart.wilson_inf(k bigint, n bigint) RETURNS numeric
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN n IS NULL OR k IS NULL OR n <= 0 THEN NULL ELSE
        round(greatest(0::numeric,
            ((k::numeric / n + 1.96^2 / (2 * n::numeric))
             - 1.96 * sqrt((k::numeric / n) * (1 - k::numeric / n) / n + 1.96^2 / (4 * n::numeric ^ 2)))
            / (1 + 1.96^2 / n::numeric)), 6) END
$$;

CREATE FUNCTION mart.wilson_sup(k bigint, n bigint) RETURNS numeric
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN n IS NULL OR k IS NULL OR n <= 0 THEN NULL ELSE
        round(least(1::numeric,
            ((k::numeric / n + 1.96^2 / (2 * n::numeric))
             + 1.96 * sqrt((k::numeric / n) * (1 - k::numeric / n) / n + 1.96^2 / (4 * n::numeric ^ 2)))
            / (1 + 1.96^2 / n::numeric)), 6) END
$$;

-- mart.calc_retencao: refaz sessões a partir de stg.conversa para a chave de usuário pedida e devolve UMA linha
-- (usuarios, voltaram_7d, taxa) entre os usuários elegíveis. É a fonte única das taxas oficial e de sensibilidade.
--   chave            'oficial' -> usuario_id | 'ip' -> usuario_id_ip | 'ip_ua' -> usuario_id_ip_ua
--   gap_min          NULL -> ops.parametros.gap_sessao_min (mesma sessão se intervalo <= gap, inclusivo)
--   fuso             NULL -> ops.parametros.fuso_pais. Só afeta a regra 'outro_dia' (qual é o dia local de cada
--                    conversa). Na regra 'sessao' NÃO afeta o cálculo global: o fuso só define a semana/mês da COORTE.
--   usar_burn_in     NULL -> true  (exclui quem começou antes do burn-in)
--   incluir_anomalo  NULL -> false (exclui usuários de IP com tráfego anômalo)
--   incluir_vazias   NULL -> false (false = só conversas que contam como uso; true = todas as carregadas)
--   regra_retorno    'sessao' (padrão) -> existe outra sessão com início <= 168 h após o início da 1ª
--                    'outro_dia'      -> existe conversa com uso (ou todas, se incluir_vazias) em dia LOCAL (fuso da função)
--                                        diferente do dia da 1ª conversa, com início <= 168 h após o início da 1ª
-- Elegível = maduro AND (NOT burn_in OR NOT usar_burn_in) AND (NOT anomalo OR incluir_anomalo).
-- Executa com os privilégios de quem chama: lê stg.conversa, portanto não é para o papel app_ro.
CREATE FUNCTION mart.calc_retencao(
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
               CASE WHEN v_regra = 'sessao'
                    THEN EXISTS (SELECT 1 FROM sessao s2 WHERE s2.u = s1.u AND s2.seq > 1
                                 AND s2.ts_ini <= s1.ts_ini + (SELECT janela FROM p))
                    ELSE EXISTS (SELECT 1 FROM c c2 WHERE c2.u = s1.u
                                 AND c2.ts_inicio <= s1.ts_ini + (SELECT janela FROM p)
                                 AND (c2.ts_inicio AT TIME ZONE v_fuso)::date <> (s1.ts_ini AT TIME ZONE v_fuso)::date)
               END AS voltou
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
