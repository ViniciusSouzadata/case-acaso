-- REVERSÃO da migração 020. Desfaz o GRANT de leitura da reconciliação para app_ro.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
REVOKE SELECT ON ops.reconciliacao FROM app_ro;
DELETE FROM ops.schema_migrations WHERE versao = '020';
COMMIT;
