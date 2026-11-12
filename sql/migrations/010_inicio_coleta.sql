-- BDR-09: marca de "início da coleta" em mart.agg_retencao_periodo.
-- A coluna é recalculada em sql/transform/40_agregados.sql a cada carga (a tabela é recriada); esta migração só garante a coluna
-- na tabela que já existe antes da 1ª carga nova, para a leitura do app_ro não quebrar.
ALTER TABLE IF EXISTS mart.agg_retencao_periodo ADD COLUMN IF NOT EXISTS inicio_coleta boolean NOT NULL DEFAULT false;
