-- REVERSÃO da migração 021. Fica fora de sql/migrations/: o executor NÃO roda este arquivo. Rodar à mão, em transação.
BEGIN;
DELETE FROM ops.parametros WHERE chave IN ('alerta_desvios', 'alerta_janela_semanas', 'alerta_min_historico', 'alerta_semanas_avaliadas');
DELETE FROM ops.schema_migrations WHERE versao = '021';
COMMIT;
