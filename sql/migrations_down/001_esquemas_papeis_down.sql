-- REVERSÃO da migração 001. Remove os esquemas (só se estiverem vazios; usar CASCADE só de propósito) e as permissões. Os papéis loader_rw e app_ro NÃO são apagados (podem ter outros donos).
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
REVOKE ALL ON SCHEMA mart, resultado FROM app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart REVOKE SELECT ON TABLES FROM app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA resultado REVOKE SELECT ON TABLES FROM app_ro;
DROP SCHEMA IF EXISTS resultado;
DROP SCHEMA IF EXISTS mart;
DROP SCHEMA IF EXISTS stg;
-- O esquema ops (e ops.schema_migrations) fica: é do executor de migrações.
DELETE FROM ops.schema_migrations WHERE versao = '001';
COMMIT;
