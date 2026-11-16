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
- Dos 25 efeitos ajustados, só a recusa passa a correção de comparações múltiplas: −16,4 pontos (−21,4 a −11,5). Os outros 24 não passam, inclusive conversa pessoal (−8,2; −14,3 a −2,1). Modelo gpt-4: −2,9 pontos (−8,0 a +2,2) no logit e −6,1 (−12,7 a +0,4) por propensão: os dois métodos concordam em "não se distingue de zero".
- A recusa se repete nas 4 definições de usuário e sessão: fica entre −14,4 e −16,4. Nas outras 3 definições (só IP, IP com navegador completo, sessão de 60 min) o sinal dos efeitos se repete em 10 de 11, 8 de 10 e 10 de 11 níveis comparados; os que mudam de sinal são efeitos perto de zero (resposta com mais de 2.500 caracteres e idioma divergente).
- E-value da recusa: 5,32, com 3,11 no limite do intervalo. Nos efeitos que não se distinguem de zero, entre 1,08 e 1,69, com o limite do intervalo em 1,00.

## O limite que eu declaro
Para **recusa** (132 usuários) e **idioma divergente** (158), a ponderação não fecha: com cerca de 150 usuários em cada grupo, o ruído de amostra já faz covariáveis passarem de 0,1 de diferença padronizada (pior balanço: 0,352 na recusa, com 8 de 19 covariáveis acima de 0,1, e 0,232 no idioma divergente, com 7 de 18). Para modelo e virada de dez/2023 o balanço fecha (0,066 e 0,028). O resultado da recusa fica no modelo ajustado, e lá ele se sustenta (−16,4; −21,4 a −11,5); o do idioma divergente não se distingue de zero (+0,1; −7,7 a +7,9). É limite do dado, não do método.

## Como defender
- **Por quê:** são métodos que eu explico passo a passo e que o dado aguenta.
- **O que descartei:** balanceamento por entropia (forçaria o balanço, mas é mais difícil de defender e de explicar ao cliente), modelos de árvore (não dão intervalo simples).
- **O que não prova:** nenhum desses métodos prova causa; só um teste controlado prova. O documento diz isso.
- **O que mudaria minha decisão:** um experimento A/B no produto.

## Histórico
- Escrito em 11/11/2026, quando a recusa era classificada por palavras-chave (153 usuários marcados, efeito de −3,3 pontos, não distinguível de zero).
- Atualizado em 16/11/2026, depois que a classificação por LLM, validada nas 200 conversas rotuladas à mão (ADR-09), mudou o resultado: 132 usuários com recusa e efeito de −16,4 pontos, que passa a correção. Os valores vêm de `resultado.*` (análise 1.1.0).
