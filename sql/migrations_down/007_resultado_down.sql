-- REVERSÃO da migração 007. Apaga as 9 tabelas de resultado.* (são saída da análise: `python -m analise tudo` as recria).
-- Fica em sql/migrations_down/ (fora de sql/migrations/): o executor só aplica arquivos de sql/migrations/ e NÃO roda estes.
-- Rodar à mão, como loader_rw, em transação, de trás para frente (020 → 001), e depois apagar a linha da migração em ops.schema_migrations.
BEGIN;
DROP TABLE IF EXISTS resultado.achado;
DROP TABLE IF EXISTS resultado.problema_qualidade;
DROP TABLE IF EXISTS resultado.validacao_classificador;
DROP TABLE IF EXISTS resultado.sensibilidade_efeito;
DROP TABLE IF EXISTS resultado.decomposicao_resumo;
DROP TABLE IF EXISTS resultado.decomposicao_semana;
DROP TABLE IF EXISTS resultado.balanco_propensao;
DROP TABLE IF EXISTS resultado.efeito_fator;
DROP TABLE IF EXISTS resultado.meta;
DELETE FROM ops.schema_migrations WHERE versao = '007';
COMMIT;
