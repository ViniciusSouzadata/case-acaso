-- REVERSÃO da migração 014. Fica fora de sql/migrations/: o executor NÃO roda este arquivo. Rodar à mão, em transação.
BEGIN;
ALTER TABLE resultado.achado
    DROP COLUMN IF EXISTS vimos_curto,
    DROP COLUMN IF EXISTS limite_curto;
DELETE FROM ops.schema_migrations WHERE versao = '014';
COMMIT;
