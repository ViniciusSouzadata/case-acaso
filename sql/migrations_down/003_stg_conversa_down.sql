-- REVERSÃO da migração 003. Apaga stg.conversa: PERDE os dados carregados; recarregar com a carga (`python -m loader.cli`).
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
DROP TABLE IF EXISTS stg.conversa;
DELETE FROM ops.schema_migrations WHERE versao = '003';
COMMIT;
