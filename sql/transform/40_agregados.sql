-- T-107: agregados que a tela lê. Limiares (n mínimo) de ops.parametros; taxas das sensibilidades via mart.calc_retencao.
-- Lê as tabelas _novo (ainda não trocadas): a troca acontece ao final da transação, em loader/transformar.py.

-- ---------------------------------------------------------------------------------------------- por período
-- Universo: usuários fora de burn-in e de tráfego anômalo (maduros OU NÃO). Período imaturo aparece com madura = false,
-- novos = todos os usuários do período e voltaram_7d / taxa / IC = NULL (não se mostra taxa parcial).
-- madura = TODOS os usuários do período são maduros. taxa_mm4 = soma(voltaram) / soma(novos) das 4 semanas maduras
-- consecutivas que terminam na semana (só 'semana'; NULL se faltar semana ou ela não for madura).
DROP TABLE IF EXISTS mart.agg_retencao_periodo_novo;
CREATE TABLE mart.agg_retencao_periodo_novo AS
WITH p AS (
    SELECT ops.param('n_minimo')::int AS n_min,
           (SELECT (min(ts_inicio) AT TIME ZONE ops.param('fuso_pais'))::date FROM stg.conversa) AS ini_coleta
),
u AS (
    SELECT d.coorte_semana, d.coorte_mes, d.maduro, f.voltou_7d, (d.coorte_semana < p.ini_coleta + 28) AS sem_inicio
    FROM mart.dim_usuario_novo d
    CROSS JOIN p
    JOIN mart.fct_primeira_experiencia_novo f USING (usuario_id)
    WHERE NOT d.burn_in AND NOT d.trafego_anomalo
),
per AS (
    SELECT 'semana'::text AS granularidade, coorte_semana AS periodo, count(*)::bigint AS novos,
           bool_and(maduro) AS madura, count(*) FILTER (WHERE voltou_7d)::bigint AS vol,
           bool_or(sem_inicio) AS inicio
    FROM u GROUP BY coorte_semana
    UNION ALL
    SELECT 'mes', coorte_mes, count(*)::bigint, bool_and(maduro), count(*) FILTER (WHERE voltou_7d)::bigint, (count(*) FILTER (WHERE sem_inicio) * 2 > count(*))
    FROM u GROUP BY coorte_mes
),
mm AS (
    SELECT a.periodo, sum(b.vol)::numeric / sum(b.novos) AS taxa_mm4
    FROM per a
    JOIN per b ON b.granularidade = 'semana' AND b.madura AND b.periodo BETWEEN a.periodo - 21 AND a.periodo
    WHERE a.granularidade = 'semana' AND a.madura
    GROUP BY a.periodo
    HAVING count(*) = 4
)
SELECT per.granularidade,
       per.periodo,
       per.novos,
       CASE WHEN per.madura THEN per.vol END AS voltaram_7d,
       CASE WHEN per.madura THEN round(per.vol::numeric / per.novos, 6) END AS taxa,
       CASE WHEN per.madura THEN mart.wilson_inf(per.vol, per.novos) END AS ic_inf,
       CASE WHEN per.madura THEN mart.wilson_sup(per.vol, per.novos) END AS ic_sup,
       CASE WHEN per.granularidade = 'semana' THEN round(mm.taxa_mm4, 6) END AS taxa_mm4,
       per.madura,
       (per.novos >= p.n_min) AS amostra_suficiente,
       -- BDR-09: semana de coorte que começa a menos de 28 dias do 1º dado da base pode misturar usuários antigos (início da coleta).
       -- Calculado do mínimo da base, sem data fixa. Mês: true se mais da metade dos novos do mês está em semanas marcadas.
       per.inicio AS inicio_coleta
FROM per
CROSS JOIN p
LEFT JOIN mm ON per.granularidade = 'semana' AND mm.periodo = per.periodo;

ALTER TABLE mart.agg_retencao_periodo_novo ADD PRIMARY KEY (granularidade, periodo);

-- ---------------------------------------------------------------------------------------------- sensibilidade
-- Todas as linhas saem de mart.calc_retencao (mesma função da oficial). O 60 (min) e o 'UTC' abaixo são os
-- valores ALTERNATIVOS testados na sensibilidade, não limiares da definição oficial.
DROP TABLE IF EXISTS mart.agg_retencao_sensibilidade_novo;
CREATE TABLE mart.agg_retencao_sensibilidade_novo AS
WITH mudam_semana AS (  -- usuários elegíveis cuja semana de coorte muda se a semana for contada em UTC
    SELECT count(*)::bigint AS n
    FROM mart.dim_usuario_novo
    WHERE elegivel AND date_trunc('week', ts_primeira AT TIME ZONE 'UTC')::date <> coorte_semana
),
r AS (
    SELECT 'oficial' AS definicao,
           'Definição oficial: usuário = IP + família de navegador; sessão de até ' || ops.param('gap_sessao_min')
           || ' min; retorno = nova sessão em até ' || (ops.param('janela_retorno_horas')::int / 24)
           || ' dias; sem os primeiros ' || ops.param('burn_in_dias') || ' dias da base e sem tráfego anômalo.' AS descricao,
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial') c
    UNION ALL
    SELECT 'so_ip', 'Usuário = só o IP (junta pessoas que dividem o mesmo IP).', c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('ip') c
    UNION ALL
    SELECT 'ip_ua_completo', 'Usuário = IP + user-agent completo (separa a mesma pessoa a cada atualização de navegador).',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('ip_ua') c
    UNION ALL
    SELECT 'sessao_60min', 'Sessão encerra após 60 min sem uso (em vez de ' || ops.param('gap_sessao_min') || ' min).',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', 60) c
    UNION ALL
    SELECT 'outro_dia', 'Voltou = usou em um dia (hora local) diferente do dia da 1ª conversa, dentro de '
           || (ops.param('janela_retorno_horas')::int / 24) || ' dias.', c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, NULL, 'outro_dia') c
    UNION ALL
    SELECT 'sem_burn_in', 'Inclui quem chegou nos primeiros ' || ops.param('burn_in_dias') || ' dias da base.',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, NULL, false) c
    UNION ALL
    SELECT 'burn_in_28d', 'Descarta os primeiros 28 dias da base (em vez de ' || ops.param('burn_in_dias') || '): trata o início da coleta com mais folga (BDR-09).',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, NULL, 'sessao', 28) c
    UNION ALL
    SELECT 'com_trafego_anomalo', 'Inclui os usuários de IPs com volume anômalo (provável automação).',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, NULL, NULL, true) c
    UNION ALL
    SELECT 'com_perguntas_vazias', 'Conta também as conversas com pergunta vazia como uso.',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, NULL, NULL, NULL, true) c
    UNION ALL
    SELECT 'fuso_utc',
           'Semana contada em UTC em vez do horário de Brasília: a taxa global não muda; '
           || (SELECT n FROM mudam_semana) || ' usuários elegíveis trocariam de semana de coorte.',
           c.usuarios, c.voltaram_7d, c.taxa
    FROM mart.calc_retencao('oficial', NULL, 'UTC') c
)
SELECT r.definicao, r.descricao, r.usuarios, r.voltaram_7d, r.taxa,
       mart.wilson_inf(r.voltaram_7d, r.usuarios) AS ic_inf,
       mart.wilson_sup(r.voltaram_7d, r.usuarios) AS ic_sup,
       round((r.taxa - o.taxa) * 100, 2) AS delta_vs_oficial   -- pontos percentuais
FROM r CROSS JOIN (SELECT taxa FROM r WHERE definicao = 'oficial') o;

ALTER TABLE mart.agg_retencao_sensibilidade_novo ADD PRIMARY KEY (definicao);

-- ---------------------------------------------------------------------------------------------- por segmento
-- Só elegíveis. Uma linha por valor de cada variável da primeira experiência.
DROP TABLE IF EXISTS mart.agg_retencao_segmento_novo;
CREATE TABLE mart.agg_retencao_segmento_novo AS
WITH p AS (SELECT ops.param('n_minimo')::int AS n_min),
e AS (SELECT * FROM mart.fct_primeira_experiencia_novo WHERE elegivel),
top_idioma AS (SELECT idioma FROM e GROUP BY idioma ORDER BY count(*) DESC, idioma LIMIT 3),
l AS (
    SELECT v.variavel, coalesce(v.valor, 'não informado') AS valor, e.voltou_7d
    FROM e CROSS JOIN LATERAL (VALUES
        ('modelo_familia',       e.modelo_familia::text),
        ('modelo_versao',        e.modelo_versao::text),
        ('era_modelo',           e.era_modelo::text),
        ('tema',                 e.tema::text),
        ('faixa_chars_pergunta', e.faixa_chars_pergunta::text),
        ('faixa_chars_resposta', e.faixa_chars_resposta::text),
        ('recusa',               CASE WHEN e.recusa THEN 'sim' ELSE 'não' END),
        ('idioma',               CASE WHEN e.idioma IN (SELECT idioma FROM top_idioma) THEN e.idioma ELSE 'outros' END),
        ('idioma_divergente',    CASE WHEN e.idioma_divergente THEN 'sim' ELSE 'não' END),
        ('n_turnos_sessao',      CASE WHEN e.n_turnos_sessao <= 1 THEN '1' WHEN e.n_turnos_sessao <= 3 THEN '2–3' ELSE '4+' END),
        ('n_conversas_sessao',   CASE WHEN e.n_conversas_sessao <= 1 THEN '1' ELSE '2+' END),
        ('periodo_dia',          e.periodo_dia::text),
        ('dia_semana',           e.dia_semana::text),
        ('fim_de_semana',        CASE WHEN e.fim_de_semana THEN 'sim' ELSE 'não' END),
        ('dispositivo',          e.dispositivo::text),
        ('regiao',               e.regiao::text)
    ) AS v(variavel, valor)
)
SELECT l.variavel, l.valor,
       count(*)::bigint AS novos,
       count(*) FILTER (WHERE l.voltou_7d)::bigint AS voltaram_7d,
       round(count(*) FILTER (WHERE l.voltou_7d)::numeric / count(*), 6) AS taxa,
       mart.wilson_inf(count(*) FILTER (WHERE l.voltou_7d), count(*)) AS ic_inf,
       mart.wilson_sup(count(*) FILTER (WHERE l.voltou_7d), count(*)) AS ic_sup,
       (count(*) >= (SELECT n_min FROM p)) AS amostra_suficiente
FROM l GROUP BY l.variavel, l.valor;

ALTER TABLE mart.agg_retencao_segmento_novo ADD PRIMARY KEY (variavel, valor);
