-- REVERSÃO da migração 013. Fica fora de sql/migrations/: o executor NÃO roda este arquivo. Rodar à mão, em transação.
BEGIN;
ALTER TABLE resultado.achado
    DROP COLUMN IF EXISTS tecnico;
DELETE FROM ops.schema_migrations WHERE versao = '013';
COMMIT;
