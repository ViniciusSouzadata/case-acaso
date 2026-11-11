# M4 — Frontend (dashboard)

## Objetivo
Telas que uma pessoa de negócio entende sem ajuda: cada número com definição e fonte, cada efeito com incerteza, e avisos claros quando o número não merece confiança.

## Stack
Next.js (App Router) + TypeScript, Tailwind + shadcn/ui, Recharts. Interface em português; textos em arquivo de mensagens (`mensagens/pt.json`) para permitir outros idiomas.

## Telas
| Tela | Pergunta que responde | Gráficos e por quê | Prioridade |
|------|----------------------|--------------------|-----------|
| **1. Retenção** (`/`) | "De cada 100 pessoas que experimentam, quantas voltam em 7 dias — e isso está mudando?" | Cartão com taxa global, IC e n. **Linha semanal com faixa de incerteza + média móvel de 4 semanas** (tendência com ruído visível); barras de novos usuários abaixo (o tamanho da amostra explica a largura da faixa); faixas de fundo com as eras de modelo. **Cascata** da semana de 20/11/2023 (base → mix → taxa → semana). **Pontos com barra** para "e se a definição mudar?" | Must |
| **2. O que faz voltar** (`/fatores`) | "Quais fatores da primeira experiência mais pesam, e quanto disso é efeito do assistente?" | **Gráfico de floresta** (ponto + barra de IC, linha do zero), ordenado pelo efeito; ponto vazado = bruto, ponto cheio = ajustado (a distância entre os dois é a seleção); abas Assistente / Perfil / Engajamento; frase de leitura em cada linha. Cartões dos 3 achados com a decisão. Detalhe recolhível: balanço antes/depois | Must |
| **3. Confiança nos dados** (`/dados`) | "Posso confiar nestes números?" | Última carga, reconciliação (ok/falha), problemas de qualidade com contagem, validação da IA de tema, **o que este painel mostra e o que nunca mostra** | Should |

## Requirements
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-401 | As telas consomem só a API do M3 (nenhum acesso direto ao banco no cliente) | Crítica | C-10 |
| REQ-402 | Todo número tem um ícone "i" que abre definição, fórmula, denominador, período, fonte e SQL vindos de `/api/dicionario` | Crítica | C-07, C-28 |
| REQ-403 | Todo efeito e toda taxa aparecem com IC 95% (faixa ou barra) e n | Crítica | C-07 |
| REQ-404 | Regra única de amostra pequena: com `amostra_suficiente = false`, o valor em destaque vira "amostra pequena (n = X)", o ponto do gráfico fica cinza vazado e a dica explica | Crítica | C-28 |
| REQ-405 | Coortes imaturas aparecem hachuradas e com o rótulo "ainda dentro dos 7 dias" — nunca como queda | Crítica | C-28 |
| REQ-406 | Efeito cujo IC cruza o zero recebe o rótulo "não dá para distinguir de zero" | Crítica | C-07 |
| REQ-407 | Rodapé fixo: "dados atualizados em", versão da definição, fonte (WildChat-1M, Brasil) | Crítica | C-07 |
| REQ-408 | Nenhuma tela mostra texto de conversa, IP, user-agent ou grupo com menos de n mínimo | Crítica | C-12 |
| REQ-409 | Linguagem simples: sem "regressão", "propensão" ou "p-valor" no texto principal; termos técnicos só no detalhe recolhível | Crítica | C-07 |
| REQ-410 | Estados de carregando, vazio e erro (com `request_id`) em todas as telas | Alta | C-32 |
| REQ-411 | Cores seguras para daltonismo; funciona em 1280 px e em celular | Média | — |
| REQ-412 | Alternar pt/es | Could | C-30 |
| REQ-413 | Teste de fumaça (Playwright ou teste de componente): as 2 telas Must renderizam com a base sintética e exibem o aviso de amostra pequena | Alta | C-14 |

## Checklist "se explica sozinha" (gate)
Para cada tela: título em forma de pergunta; uma frase-resposta no topo; cada gráfico com título que diz a conclusão; eixos com unidade; legenda do que é faixa/barra; "i" em todo número; aviso visível quando a amostra é pequena.

## Gate de saída
2 telas Must com dados reais via `docker compose up`; checklist cumprido; REQ-404/405/406 demonstráveis.
