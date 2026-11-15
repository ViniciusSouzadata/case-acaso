-- REVERSÃO da migração 012. Fica fora de sql/migrations/: o executor NÃO roda este arquivo. Rodar à mão, em transação.
BEGIN;
ALTER TABLE resultado.achado
    DROP COLUMN IF EXISTS numero_destaque,
    DROP COLUMN IF EXISTS rotulo_destaque,
    DROP COLUMN IF EXISTS acao_curta;
DELETE FROM ops.schema_migrations WHERE versao = '012';
COMMIT;
