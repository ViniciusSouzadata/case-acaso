# M2 — Análise (EDA + efeitos + semana + achados)

## Objetivo
Responder à pergunta do cliente com estatística defensável: o efeito de cada fator da primeira experiência no retorno em 7 dias, **bruto e ajustado, com intervalo de confiança**, separando o que o assistente causa do que é perfil de quem chega; explicar a semana de 20/11/2023; e fechar em três achados com decisão. Tudo gravado em tabelas `resultado.*` — o dashboard lê, não calcula.

## Features
- F01 — EDA e qualidade dos dados
- F02 — Efeito de cada fator (bruto × ajustado)
- F03 — Causa × seleção nos fatores principais
- F04 — Semana que mudou (mix × taxa)
- F05 — Sensibilidade às definições
- F06 — Validação das classificações (tema e recusa)
- F07 — Achados e sugestões

## Requirements
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-201 | EDA com no máximo ~6 gráficos, cada um ligado a uma conclusão escrita: volume no tempo com eras de modelo; concentração por IP; retorno semanal com IC; tamanho de conversa; tema; idioma | Crítica | C-20 |
| REQ-202 | Lista de problemas de qualidade com contagem e tratamento (pergunta vazia, hash repetido, IP que muda, idioma mal detectado, tóxicas/PII removidas pelos autores, semanas com queda de volume, IP dominante) | Crítica | C-19 |
| REQ-203 | Seção "o que dá para medir / o que não dá / que dado falta" (sem ID de login, sem avaliação do usuário, sem horário da pergunta → sem latência, conversas removidas) | Crítica | C-21 |
| REQ-210 | Para cada nível de cada fator: n, taxa, diferença bruta em p.p. contra a referência, com IC 95% | Crítica | C-23 |
| REQ-211 | Efeito ajustado: regressão logística com todos os fatores de perfil e de assistente + era de modelo; erro-padrão agrupado por `hashed_ip`; resultado como efeito marginal médio em p.p. com IC 95% | Crítica | C-06, C-23, C-24 |
| REQ-212 | Fatores em três grupos, rotulados na saída: **assistente** (recusa, resposta em outro idioma, tamanho da resposta, modelo), **perfil** (tema, idioma, dispositivo, hora, dia, tamanho da pergunta, região), **engajamento** (turnos e conversas na sessão — descritivo, fora do ajuste, por ser consequência e não causa) | Crítica | C-05, C-24 |
| REQ-213 | Tabela final ordenada pelo tamanho do efeito ajustado; marca o que sobrevive à correção de comparações múltiplas (Benjamini-Hochberg) | Crítica | C-23 |
| REQ-214 | No máximo ~25 parâmetros no modelo (≈ 577 retornos); níveis raros agrupados em "outros"; declarar o efeito mínimo detectável | Crítica | C-06 |
| REQ-220 | Para recusa, resposta em outro idioma e modelo: escore de propensão com covariáveis anteriores à resposta, ponderação (pesos estabilizados e truncados), tabela de balanço (diferença padronizada antes/depois) e IC por bootstrap agrupado por IP | Crítica | C-24 |
| REQ-221 | Modelo comparado só onde havia escolha (abr–jun/2023 e nov/2023); virada de dez/2023 (GPT-4 vira padrão) analisada como antes/depois, declarada como evidência de apoio | Crítica | C-24 |
| REQ-222 | E-value para cada efeito ajustado dos fatores de assistente + parágrafo "o que isto prova / o que não prova" | Crítica | C-24 |
| REQ-230 | Semana de 20/11/2023 contra as 4 semanas anteriores: decomposição da diferença em efeito de mix e efeito de taxa por segmento (dispositivo × família de modelo), teste de duas proporções e conclusão explícita sobre ruído | Crítica | C-25 |
| REQ-240 | Modelo principal refeito com as chaves alternativas de usuário e com sessão de 60 min; reportar se sinal e ordem dos principais efeitos se mantêm | Crítica | C-13, C-16 |
| REQ-250 | Amostra estratificada de 200 conversas rotulada à mão pelo Vinícius (tema e recusa); acurácia, kappa de Cohen e matriz de confusão gravados; classes com concordância baixa são fundidas | Crítica | C-18 |
| REQ-251 | Tema classificado por LLM no Bedrock (taxonomia fixa de ~8 classes, prompt versionado, só a 1ª pergunta truncada); saída = seed versionado | Alta | C-11, C-17, C-18 |
| REQ-260 | Três achados, cada um com evidência (número + IC), decisão que sustenta e limite | Crítica | C-26 |
| REQ-261 | Sugestões para o assistente e para o dashboard derivadas dos dados | Crítica | C-22 |
| REQ-270 | Um comando reexecuta toda a análise e regrava `resultado.*` com `versao_analise`; semente fixa no bootstrap | Crítica | C-14 |

## Gate de saída
`resultado.*` populado e reproduzível; todo efeito com IC e n; validação manual registrada; três achados escritos sem vender ruído como efeito.

## Tarefa que só o Vinícius pode fazer
Rotular à mão as 200 conversas da amostra de validação (~1 h, planilha simples). É a resposta a "como conferiu o resultado da IA".
