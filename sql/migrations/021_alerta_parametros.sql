-- Alerta de divergência (docs/entrega.md, seção 7): limiares em ops.parametros, nunca no código.
-- alerta_desvios: quantos desvios-padrão acima/abaixo da média das semanas anteriores contam como salto.
-- alerta_janela_semanas: quantas semanas anteriores formam a média; alerta_min_historico: mínimo de semanas para avaliar.
INSERT INTO ops.parametros (chave, valor, descricao) VALUES
    ('alerta_desvios',         '3', 'Alerta: salto de uma série semanal acima deste número de desvios-padrão da média anterior'),
    ('alerta_janela_semanas',  '8', 'Alerta: semanas anteriores usadas para a média e o desvio'),
    ('alerta_min_historico',   '4', 'Alerta: mínimo de semanas anteriores para avaliar um salto'),
    ('alerta_semanas_avaliadas', '1', 'Alerta: quantas semanas finais da série são avaliadas a cada carga')
ON CONFLICT (chave) DO NOTHING;
