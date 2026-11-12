# ADR-10 — Método estatístico
**Atende:** C-05, C-06, C-23, C-24, C-25

## Contexto
O cliente quer o efeito de cada fator no retorno, com incerteza, separando assistente de perfil, e saber o que é causa e o que é seleção.

## Opções consideradas e escolha
| Pergunta | Método |
|---|---|
| Taxa e diferença bruta | Intervalo de Wilson para a taxa; Newcombe para a diferença |
| Efeito de cada fator, controlando os outros | Regressão logística com efeito marginal médio (em pontos percentuais) e erro robusto agrupado por IP |
| Muitos fatores testados | Correção de Benjamini-Hochberg (5%) |
| Grupos parecidos (modelo, recusa, idioma divergente, virada de dez/2023) | Ponderação por propensão, com balanço medido (diferença padronizada < 0,1) e bootstrap por IP (1.000 repetições, semente fixa) |
| Quão forte teria de ser uma confusão não medida | E-value |
| Semana que caiu | Decomposição de Kitagawa (mix × taxa) e teste de duas proporções |

## Resultados que sustentam a escolha
- Nenhum dos 25 efeitos ajustados passa a correção de comparações múltiplas. Modelo gpt-4: −3,3 pontos (−8,4 a +1,8) no logit e −5,4 (−12,0 a +0,9) por propensão: os dois métodos concordam em "não se distingue de zero".
- A leitura se repete nas 4 definições de usuário e sessão (mesmo sinal em 24 de 25, 20 de 23 e 24 de 25 níveis).
- E-values entre 1,26 e 1,90, com o limite do intervalo em 1,0.

## O limite que eu declaro
Para **recusa** (153 usuários) e **idioma divergente** (158), não deu para montar um grupo de comparação equilibrado: com cerca de 150 usuários em cada grupo, o ruído de amostra já faz alguma covariável passar de 0,1 de diferença padronizada (pior balanço: 0,189 e 0,276). O resultado fica no modelo ajustado, e lá não se distingue de zero. É limite do dado, não do método.

## Como defender
- **Por quê:** são métodos que eu explico passo a passo e que o dado aguenta.
- **O que descartei:** balanceamento por entropia (forçaria o balanço, mas é mais difícil de defender e de explicar ao cliente), modelos de árvore (não dão intervalo simples).
- **O que não prova:** nenhum desses métodos prova causa; só um teste controlado prova. O documento diz isso.
- **O que mudaria minha decisão:** um experimento A/B no produto.
