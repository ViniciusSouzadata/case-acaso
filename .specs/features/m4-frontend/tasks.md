# Tasks — M4 Frontend

Pré-requisito: T-302 (retenção) para a Tela 1; T-303 para as Telas 2 e 3. Enquanto `resultado.*` estiver vazio, usar os arquivos de exemplo em `app/exemplos/*.json` no formato exato do contrato.
```
T-401 ─► T-402 ─┬─► T-403 ─┐
                └─► T-404 ─┼─► T-406 (gate)
                    T-405 ─┘
```

## [x] T-401 — Base visual: layout, componentes de confiança e mensagens
- **What:** Layout com navegação (Retenção · O que faz voltar · Confiança nos dados) e rodapé fixo ("dados atualizados em", versão da definição, fonte). Componentes: `Numero` (valor + IC + n + ícone "i"), `Glossario` (painel que abre com definição, fórmula, denominador, período, fonte e SQL de `/api/dicionario`), `AvisoAmostra` (regra única de amostra pequena), `Estado` (carregando, vazio, erro com `request_id`). Textos em `mensagens/pt.json`. Paleta segura para daltonismo.
- **Where:** `app/app/`, `app/components/`, `app/mensagens/`
- **Depends on:** T-302
- **Reuses:** spec M4 — REQ-402..410; shadcn/ui
- **Done when:** página de demonstração mostra `Numero` nos três estados (normal, amostra pequena, erro) e o glossário abrindo com dados reais
- **Tests:** testes de componente (vitest + testing-library) para `Numero` e `AvisoAmostra`
- **Gate:** As regras de confiança existem em um só lugar
- **Reqs:** REQ-401, REQ-402, REQ-403, REQ-404, REQ-407, REQ-409, REQ-410, REQ-411

## [x] T-402 — Tela 1: Retenção
- **What:** Título-pergunta e frase-resposta no topo. Cartão com taxa global, IC e n. Gráfico semanal (Recharts): linha da taxa, faixa de IC, média móvel de 4 semanas, faixas de fundo das eras de modelo, pontos cinza vazados para amostra pequena, semanas imaturas hachuradas com rótulo. Barras de novos usuários alinhadas abaixo. Alternar semana/mês. Tabela acessível com os mesmos dados.
- **Where:** `app/app/page.tsx`, `app/components/graficos/`
- **Depends on:** T-401
- **Reuses:** `/api/retencao/resumo`, `/api/retencao/coortes`
- **Done when:** dados reais na tela; checklist "se explica sozinha" cumprido
- **Tests:** teste de componente: semana com `amostra_suficiente=false` exibe o aviso; semana imatura exibe o rótulo
- **Gate:** Tela 1 entendível sem ajuda
- **Reqs:** REQ-403, REQ-404, REQ-405, REQ-409

## [x] T-403 — Tela 1: sensibilidade e semana de 20/11/2023
- **What:** Bloco "E se a definição de usuário ou de sessão mudar?" (pontos com barra de IC, linha da definição oficial). Bloco da semana: cascata base → mix → taxa → semana, com a frase de conclusão vinda da API.
- **Where:** `app/app/page.tsx`
- **Depends on:** T-402
- **Reuses:** `/api/retencao/sensibilidade`, `/api/semana/decomposicao`
- **Done when:** os dois blocos com dados reais (ou exemplo, se o M2 não tiver terminado) e legenda do que é cada barra
- **Tests:** teste de componente da cascata (soma fecha)
- **Gate:** Premissas e movimento visíveis para o cliente
- **Reqs:** REQ-403, REQ-409

## [x] T-404 — Tela 2: O que faz voltar
- **What:** Gráfico de floresta por grupo (abas Assistente / Perfil / Engajamento): ponto vazado = bruto, ponto cheio = ajustado, barra de IC, linha do zero, ordenado pelo efeito; frase `leitura` em cada linha; rótulos "não dá para distinguir de zero" e "amostra pequena". Texto curto explicando a diferença entre bruto e ajustado em linguagem simples. Cartões dos 3 achados com decisão e limite. Detalhe recolhível "Como comparamos grupos parecidos" (balanço antes/depois).
- **Where:** `app/app/fatores/page.tsx`
- **Depends on:** T-401, T-303
- **Reuses:** `/api/fatores/efeitos`, `/api/fatores/balanco`, `/api/achados`
- **Done when:** dados reais; nenhum termo técnico no texto principal
- **Tests:** teste de componente: efeito com IC cruzando zero recebe o rótulo; engajamento não mostra ajustado
- **Gate:** Tela 2 entendível sem ajuda
- **Reqs:** REQ-403, REQ-404, REQ-406, REQ-409

## [ ] T-405 — Tela 3: Confiança nos dados (Should)
- **What:** Última carga (quando, linhas, rejeitados), reconciliação (ok/falha por métrica), problemas de qualidade com contagem e tratamento, validação da classificação de tema, e o quadro "O que este painel mostra / nunca mostra".
- **Where:** `app/app/dados/page.tsx`
- **Depends on:** T-401, T-303
- **Reuses:** `/api/qualidade`
- **Done when:** dados reais na tela
- **Tests:** teste de fumaça
- **Gate:** Cliente consegue responder "posso confiar?"
- **Reqs:** REQ-408

## [ ] T-406 — Fumaça ponta a ponta e gate
- **What:** Teste de fumaça que sobe o app contra a base e verifica que as telas Must renderizam, que o "i" abre o glossário e que não há texto de conversa, IP ou user-agent no HTML. Conferir 1280 px e largura de celular. Revisar todos os textos de `pt.json` contra o REQ-409.
- **Where:** `app/tests/`
- **Depends on:** T-403, T-404, T-405
- **Reuses:** —
- **Done when:** `docker compose up` do zero → 2 telas Must com dados reais; fumaça verde
- **Tests:** os próprios
- **Gate:** **Gate de saída do M4**
- **Reqs:** REQ-408, REQ-413
