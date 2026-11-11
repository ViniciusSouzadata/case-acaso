-- T-106: mart.fct_primeira_experiencia. Uma linha por usuário; variáveis da 1ª conversa da sessão 1.
-- Limiares (janela, fuso do país) lidos de ops.parametros. As FAIXAS de tamanho, os períodos do dia e o mapa
-- estado -> região são categorização descritiva (não são limiares de definição de indicador).
DROP TABLE IF EXISTS mart.fct_primeira_experiencia_novo;

CREATE TABLE mart.fct_primeira_experiencia_novo AS
WITH p AS (
    SELECT ops.param('janela_retorno_horas')::int * interval '1 hour' AS janela,
           ops.param('fuso_pais')                                     AS fuso_pais
),
regiao(estado, regiao) AS (
    VALUES
    ('Acre','Norte'),('Amapá','Norte'),('Amazonas','Norte'),('Pará','Norte'),('Rondônia','Norte'),
    ('Roraima','Norte'),('Tocantins','Norte'),
    ('Alagoas','Nordeste'),('Bahia','Nordeste'),('Ceará','Nordeste'),('Maranhão','Nordeste'),
    ('Paraíba','Nordeste'),('Pernambuco','Nordeste'),('Piauí','Nordeste'),('Rio Grande do Norte','Nordeste'),
    ('Sergipe','Nordeste'),
    ('Goiás','Centro-Oeste'),('Mato Grosso','Centro-Oeste'),('Mato Grosso do Sul','Centro-Oeste'),
    ('Federal District','Centro-Oeste'),('Distrito Federal','Centro-Oeste'),
    ('Espírito Santo','Sudeste'),('Minas Gerais','Sudeste'),('Rio de Janeiro','Sudeste'),('São Paulo','Sudeste'),
    ('Paraná','Sul'),('Rio Grande do Sul','Sul'),('Santa Catarina','Sul')
),
primeira AS (  -- 1ª conversa que conta como uso de cada usuário (= abre a sessão 1)
    SELECT DISTINCT ON (usuario_id)
           usuario_id, modelo_familia, modelo_versao, tema, chars_pergunta_1, chars_resposta_1, recusa_1,
           coalesce(idioma_pergunta_1, 'Nolang') AS idioma, idioma_divergente,
           ts_inicio, fuso, ua_dispositivo, nullif(trim(estado), '') AS estado
    FROM stg.conversa
    WHERE conta_como_uso
    ORDER BY usuario_id, ts_inicio, conversa_id
),
retorno AS (  -- início da 2ª sessão, se existir
    SELECT usuario_id, ts_inicio AS ts_retorno FROM mart.fct_sessao_novo WHERE seq = 2
),
base AS (
    SELECT d.usuario_id, d.ts_primeira, d.elegivel, d.coorte_semana,
           pr.modelo_familia, pr.modelo_versao, pr.tema, pr.chars_pergunta_1, pr.chars_resposta_1,
           pr.recusa_1, pr.idioma, pr.idioma_divergente, pr.ua_dispositivo, pr.estado,
           extract(hour FROM pr.ts_inicio AT TIME ZONE pr.fuso)::int AS hora_local,
           extract(isodow FROM pr.ts_inicio AT TIME ZONE pr.fuso)::int AS isodow,
           s1.n_turnos AS n_turnos_sessao, s1.n_conversas AS n_conversas_sessao,
           (r.ts_retorno IS NOT NULL AND r.ts_retorno <= d.ts_primeira + p.janela) AS voltou_7d,
           r.ts_retorno, p.janela, p.fuso_pais
    FROM mart.dim_usuario_novo d
    JOIN primeira pr USING (usuario_id)
    JOIN mart.fct_sessao_novo s1 ON s1.usuario_id = d.usuario_id AND s1.seq = 1
    LEFT JOIN retorno r ON r.usuario_id = d.usuario_id
    CROSS JOIN p
)
SELECT b.usuario_id,
       b.modelo_familia,
       b.modelo_versao,
       e.era AS era_modelo,
       coalesce(b.tema, 'não classificado') AS tema,
       CASE WHEN b.chars_pergunta_1 <= 30   THEN 'até 30'
            WHEN b.chars_pergunta_1 <= 100  THEN '31–100'
            WHEN b.chars_pergunta_1 <= 400  THEN '101–400'
            ELSE 'mais de 400' END AS faixa_chars_pergunta,
       CASE WHEN b.chars_resposta_1 <= 300  THEN 'até 300'
            WHEN b.chars_resposta_1 <= 1000 THEN '301–1.000'
            WHEN b.chars_resposta_1 <= 2500 THEN '1.001–2.500'
            ELSE 'mais de 2.500' END AS faixa_chars_resposta,
       b.recusa_1 AS recusa,
       b.idioma,
       b.idioma_divergente,
       b.n_turnos_sessao,
       b.n_conversas_sessao,
       b.hora_local,
       CASE WHEN b.hora_local BETWEEN 0 AND 5  THEN 'madrugada'
            WHEN b.hora_local BETWEEN 6 AND 11 THEN 'manhã'
            WHEN b.hora_local BETWEEN 12 AND 17 THEN 'tarde'
            ELSE 'noite' END AS periodo_dia,
       (ARRAY['segunda','terça','quarta','quinta','sexta','sábado','domingo'])[b.isodow] AS dia_semana,
       (b.isodow IN (6, 7)) AS fim_de_semana,
       b.ua_dispositivo AS dispositivo,
       b.estado,
       coalesce(rg.regiao, 'não informado') AS regiao,
       b.voltou_7d,
       CASE WHEN b.voltou_7d THEN round((extract(epoch FROM b.ts_retorno - b.ts_primeira) / 3600)::numeric, 2) END AS horas_ate_retorno,
       b.elegivel
FROM base b
LEFT JOIN mart.dim_era_modelo_novo e
       ON (b.ts_primeira AT TIME ZONE b.fuso_pais)::date BETWEEN e.inicio AND coalesce(e.fim, DATE 'infinity')
LEFT JOIN regiao rg ON rg.estado = b.estado;

ALTER TABLE mart.fct_primeira_experiencia_novo ADD PRIMARY KEY (usuario_id);
