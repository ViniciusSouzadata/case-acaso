-- REVERSÃO da migração 008. Remove a coluna e_value_ic (a análise a recalcula com `python -m analise tudo`).
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
ALTER TABLE resultado.efeito_fator DROP COLUMN IF EXISTS e_value_ic;
DELETE FROM ops.schema_migrations WHERE versao = '008';
COMMIT;
