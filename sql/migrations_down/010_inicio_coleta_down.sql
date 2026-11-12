-- REVERSÃO da migração 010. Remove mart.agg_retencao_periodo.inicio_coleta.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor NÃO roda estes. Rodar à mão, em transação.
BEGIN;
ALTER TABLE IF EXISTS mart.agg_retencao_periodo DROP COLUMN IF EXISTS inicio_coleta;
DELETE FROM ops.schema_migrations WHERE versao = '010';
COMMIT;
