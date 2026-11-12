-- REVERSÃO da migração 002. Apaga as tabelas de operação (parâmetros, lotes, rejeitados, reconciliação). Ao apagar, perde o histórico de lotes.
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
DROP TABLE IF EXISTS ops.reconciliacao;
DROP TABLE IF EXISTS ops.rejeitado;
DROP TABLE IF EXISTS ops.lote_carga;
DROP TABLE IF EXISTS ops.parametros;
-- A tabela ops.schema_migrations é do executor e fica; esta linha só a limpa se ela ainda existir.
DELETE FROM ops.schema_migrations WHERE versao = '002';
COMMIT;
