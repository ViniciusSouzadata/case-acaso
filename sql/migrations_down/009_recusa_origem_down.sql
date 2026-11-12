-- REVERSÃO da migração 009. Remove stg.conversa.recusa_origem.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor NÃO roda estes. Rodar à mão, em transação.
BEGIN;
ALTER TABLE stg.conversa DROP COLUMN IF EXISTS recusa_origem;
DELETE FROM ops.schema_migrations WHERE versao = '009';
COMMIT;
