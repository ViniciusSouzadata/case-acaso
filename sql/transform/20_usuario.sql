-- T-106: mart.dim_era_modelo e mart.dim_usuario. Limiares lidos de ops.parametros.
DROP TABLE IF EXISTS mart.dim_era_modelo_novo;
CREATE TABLE mart.dim_era_modelo_novo (
    era       text PRIMARY KEY,
    inicio    date NOT NULL,
    fim       date,           -- NULL = em aberto (a era vai até o fim da base)
    descricao text NOT NULL
);
INSERT INTO mart.dim_era_modelo_novo (era, inicio, fim, descricao) VALUES
    ('2023-04..06 (3.5 + 4 opcional)', DATE '2023-04-01', DATE '2023-06-30', 'GPT-3.5 como padrão; GPT-4 disponível como opção'),
    ('2023-07..10 (só 3.5)',           DATE '2023-07-01', DATE '2023-10-31', 'GPT-4 indisponível; só GPT-3.5'),
    ('2023-11 (4 volta)',              DATE '2023-11-01', DATE '2023-11-30', 'GPT-4 volta a ser oferecido'),
    ('2023-12+ (4 padrão)',            DATE '2023-12-01', NULL,              'GPT-4 passa a ser o modelo padrão');

DROP TABLE IF EXISTS mart.dim_usuario_novo;
CREATE TABLE mart.dim_usuario_novo AS
WITH p AS (
    SELECT ops.param('janela_retorno_horas')::int * interval '1 hour' AS janela,
           ops.param('burn_in_dias')::int * interval '1 day'          AS burn_in,
           ops.param('limiar_conversas_ip')::int                      AS lim_conv,
           ops.param('limiar_uas_ip')::int                            AS lim_ua,
           ops.param('fuso_pais')                                     AS fuso
),
base AS (SELECT min(ts_inicio) AS inicio, max(ts_fim) AS fim FROM stg.conversa),
ips AS (  -- tráfego anômalo é por IP, sobre TODAS as conversas carregadas
    SELECT hashed_ip,
           (count(*) >= (SELECT lim_conv FROM p) OR count(DISTINCT user_agent) >= (SELECT lim_ua FROM p)) AS anomalo
    FROM stg.conversa GROUP BY hashed_ip
),
primeira AS (  -- 1ª conversa que conta como uso (abre a sessão 1)
    SELECT DISTINCT ON (usuario_id) usuario_id, hashed_ip, ua_dispositivo AS dispositivo, estado
    FROM stg.conversa
    WHERE conta_como_uso
    ORDER BY usuario_id, ts_inicio, conversa_id
),
conv AS (
    SELECT usuario_id, count(*)::int AS n_conversas FROM stg.conversa WHERE conta_como_uso GROUP BY usuario_id
),
ses AS (
    SELECT usuario_id, count(*)::int AS n_sessoes, min(ts_inicio) FILTER (WHERE seq = 1) AS ts_primeira
    FROM mart.fct_sessao_novo GROUP BY usuario_id
),
u AS (
    SELECT ses.usuario_id, ses.ts_primeira, ses.n_sessoes, conv.n_conversas,
           pr.dispositivo, nullif(trim(pr.estado), '') AS estado,
           coalesce(ips.anomalo, false) AS trafego_anomalo,
           (ses.ts_primeira + p.janela <= base.fim)       AS maduro,
           (ses.ts_primeira < base.inicio + p.burn_in)    AS burn_in,
           p.fuso
    FROM ses
    JOIN conv USING (usuario_id)
    JOIN primeira pr USING (usuario_id)
    LEFT JOIN ips ON ips.hashed_ip = pr.hashed_ip
    CROSS JOIN p CROSS JOIN base
)
SELECT usuario_id,
       ts_primeira,
       date_trunc('week',  ts_primeira AT TIME ZONE fuso)::date AS coorte_semana,
       date_trunc('month', ts_primeira AT TIME ZONE fuso)::date AS coorte_mes,
       n_sessoes, n_conversas, dispositivo, estado,
       trafego_anomalo, maduro, burn_in,
       (maduro AND NOT burn_in AND NOT trafego_anomalo) AS elegivel,
       CASE WHEN trafego_anomalo THEN 'trafego_anomalo'
            WHEN burn_in         THEN 'burn_in'
            WHEN NOT maduro      THEN 'imaturo' END      AS motivo_inelegivel
FROM u;

ALTER TABLE mart.dim_usuario_novo ADD PRIMARY KEY (usuario_id);
