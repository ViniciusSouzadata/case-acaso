-- REVERSÃO da migração 004. Remove mart.calc_retencao e ops.param.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
DROP FUNCTION IF EXISTS mart.calc_retencao(text, int, text, bool, bool, bool);
DROP FUNCTION IF EXISTS ops.param(text);
DELETE FROM ops.schema_migrations WHERE versao = '004';
COMMIT;
