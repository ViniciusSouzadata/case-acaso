# Tasks — M2 Análise

Pré-requisito: gate do M1 (T-110) — `mart.*` congelado.
```
T-201 ─► T-202 ─► T-203 ─► T-204 ─┬─► T-206 ─► T-208 ─► T-209 (gate)
T-205 (tema) ─ T-205b (rotulagem, Vinícius) ─┘         ▲
T-207 (semana) ────────────────────────────────────────┘
```
T-201, T-205 e T-207 podem começar em paralelo.

## [x] T-201 — Pacote de análise, população e migração de `resultado.*`
- **What:** Pacote `analise/` com `dados.py` (lê `mart.fct_primeira_experiencia` elegível via SQL, devolve DataFrame tipado), `intervalos.py` (Wilson, Newcombe) e `gravar.py` (grava tabelas `resultado.*` com `versao_analise`). Migração criando todas as tabelas `resultado.*` do contrato. `resultado.meta` preenchida (n elegíveis, retornos, taxa global com IC, efeito mínimo detectável para divisão 50/50 e 15/85).
- **Where:** `analise/`, `sql/migrations/`
- **Depends on:** T-110
- **Reuses:** design.md M2 — Contrato das tabelas de resultado
- **Done when:** `python -m analise meta` grava `resultado.meta`; taxa global = linha "oficial" de `mart.agg_retencao_sensibilidade`
- **Tests:** unitários de Wilson e Newcombe contra valores de referência calculados à mão; teste de igualdade com o mart
- **Gate:** Análise e base concordam no número principal
- **Reqs:** REQ-214, REQ-270

## [x] T-202 — EDA e problemas de qualidade
- **What:** `analise/eda.py`: gera no máximo 6 figuras (PNG em `docs/figuras/`) — volume semanal com eras de modelo; concentração de conversas por IP; retorno semanal com IC e média móvel; distribuição de turnos; retorno por tema; uso por idioma — cada uma com uma frase de conclusão em `docs/figuras/conclusoes.md`. Grava `resultado.problema_qualidade` (pergunta vazia, hash repetido, IP que muda no meio, idioma mal detectado, semanas de volume anômalo, IP dominante, conversas tóxicas/PII removidas pelos autores) com contagem, % e tratamento.
- **Where:** `analise/eda.py`, `docs/figuras/`
- **Depends on:** T-201
- **Reuses:** docs/discovery/00-resumo-discovery.md (números de conferência)
- **Done when:** figuras geradas por um comando; contagens batem com o discovery; nenhuma figura sem conclusão
- **Tests:** teste que falha se existir figura sem linha em `conclusoes.md`
- **Gate:** EDA só com gráfico que leva a conclusão
- **Reqs:** REQ-201, REQ-202, REQ-203

## [ ] T-203 — Efeito bruto por fator
- **What:** `analise/bruto.py`: para cada fator e nível (lista e grupo — assistente/perfil/engajamento — definidos em `analise/fatores.py`, níveis raros agrupados em "outros"), n, taxa, diferença em p.p. contra a referência (nível mais frequente) e IC de Newcombe. Grava as colunas de bruto de `resultado.efeito_fator`.
- **Where:** `analise/bruto.py`, `analise/fatores.py`
- **Depends on:** T-202
- **Reuses:** `analise/intervalos.py`
- **Done when:** todos os fatores do REQ-212 presentes; `amostra_suficiente` correto
- **Tests:** caso sintético pequeno com resposta feita à mão
- **Gate:** Bruto pronto para comparar com ajustado
- **Reqs:** REQ-210, REQ-212

## [ ] T-204 — Efeito ajustado (logística + efeito marginal)
- **What:** `analise/ajustado.py`: Logit (statsmodels) de `voltou_7d` em fatores de assistente + perfil + era de modelo; erro agrupado por `hashed_ip` (lido de `stg` pelo job de análise, nunca gravado em `resultado`); efeito marginal médio por nível em p.p. com IC (delta); p-valor; Benjamini-Hochberg; `ordem` por |efeito|; `leitura` em frase simples gerada por regra. Limite de ~25 parâmetros; registrar em `resultado.meta` quantos entraram.
- **Where:** `analise/ajustado.py`
- **Depends on:** T-203
- **Reuses:** design.md M2 — passo 3 e 6
- **Done when:** `resultado.efeito_fator` completo para assistente e perfil; engajamento com ajustado nulo; modelo converge; diagnóstico de separação/colinearidade impresso
- **Tests:** dados simulados com efeito conhecido (ex.: +10 p.p.) → estimativa dentro do IC; teste da correção de comparações múltiplas
- **Gate:** Cada efeito com IC, n e leitura
- **Reqs:** REQ-211, REQ-212, REQ-213, REQ-214

## [ ] T-205 — Classificador de tema e seed
- **What:** `classificador/tema.py` com interface única `classificar(pergunta) -> tema` e provedores trocáveis por configuração (`TEMA_PROVEDOR`): `bedrock` (Claude Haiku; reserva Amazon Nova), `regras` (palavras-chave, sem LLM) e o provedor alternativo declarado no ADR-09. Taxonomia v1 do design. Lê a 1ª pergunta do snapshot (truncada), grava `seeds/tema_conversa.csv` (`conversa_id, tema, tema_origem, versao_prompt`). **Qual provedor gera o seed da entrega é decisão registrada no STATE.md (depende da conta AWS e da resposta da Acaso).**
- **Where:** `classificador/`, `seeds/tema_conversa.csv`
- **Depends on:** T-110
- **Reuses:** design.md M2 — Tema
- **Done when:** seed cobre todas as conversas que contam como uso; a carga junta o seed; sem seed, tema = "não classificado"
- **Tests:** unitário do provedor `regras`; teste de contrato do seed; provedor LLM testado com resposta simulada (sem chamar rede no CI)
- **Gate:** Tema disponível sem credencial no compose
- **Reqs:** REQ-251, REQ-122

## [ ] T-205b — Rotulagem manual (Vinícius) e validação
- **What:** Script gera `seeds/validacao_manual_em_branco.csv` com 200 conversas estratificadas (por tema previsto e por recusa prevista), mostrando só a 1ª pergunta e a 1ª resposta, **sem** os rótulos da máquina. Vinícius preenche tema e recusa. `analise/validacao.py` calcula acurácia, kappa de Cohen e matriz de confusão para tema e recusa e grava `resultado.validacao_classificador`. Classes com concordância baixa são fundidas e o seed regenerado.
- **Where:** `analise/validacao.py`, `seeds/validacao_manual.csv`
- **Depends on:** T-205
- **Reuses:** —
- **Done when:** validação gravada; decisão de fundir classes registrada no ADR-09
- **Tests:** unitário do kappa contra valor de referência
- **Gate:** "Como conferiu a IA" tem número
- **Reqs:** REQ-250

## [ ] T-206 — Propensão, balanço e E-value
- **What:** `analise/propensao.py` para recusa, idioma divergente e modelo (só eras com escolha): escore de propensão (Logit em covariáveis pré-resposta), pesos estabilizados truncados p1/p99, diferença padronizada antes/depois em `resultado.balanco_propensao`, efeito ponderado com IC por bootstrap agrupado por IP (1.000, semente fixa). E-value dos efeitos de assistente. Antes/depois da virada de dez/2023 como evidência de apoio. Se o balanço não fechar (< 0,1), marcar o efeito como "não comparável".
- **Where:** `analise/propensao.py`
- **Depends on:** T-204, T-205b
- **Reuses:** design.md M2 — passos 4 e 5
- **Done when:** linhas `metodo = 'ipw'` em `resultado.efeito_fator`; balanço gravado; E-values gravados
- **Tests:** simulação com confusão conhecida: bruto enviesado, ponderado recupera o efeito verdadeiro
- **Gate:** Causa × seleção tratada e demonstrável
- **Reqs:** REQ-220, REQ-221, REQ-222

## [ ] T-207 — Semana de 20/11/2023: mix × taxa
- **What:** `analise/semana.py`: compara a coorte de 20/11/2023 com as 4 semanas anteriores; decomposição de Kitagawa por segmento (dispositivo × família de modelo); teste de duas proporções; `conclusao` em texto ("x p.p. por mudança de perfil, y p.p. por mudança de taxa; diferença [não] distinguível de ruído, p = ..."). Grava `resultado.decomposicao_semana` e `_resumo`.
- **Where:** `analise/semana.py`
- **Depends on:** T-201
- **Reuses:** design.md M2 — passo 7
- **Done when:** mix + taxa = delta (até arredondamento)
- **Tests:** exemplo numérico feito à mão
- **Gate:** Movimento explicado com veredito honesto
- **Reqs:** REQ-230

## [ ] T-208 — Sensibilidade dos efeitos
- **What:** `analise/sensibilidade.py`: refaz o modelo ajustado com as chaves alternativas (só IP; IP + UA completo) e sessão de 60 min; grava `resultado.sensibilidade_efeito` com `mesmo_sinal`.
- **Where:** `analise/sensibilidade.py`
- **Depends on:** T-206
- **Reuses:** `mart.calc_retencao` e as chaves alternativas de `stg.conversa`
- **Done when:** tabela gravada para os fatores de assistente e os 5 maiores de perfil
- **Tests:** teste de fumaça
- **Gate:** Sabemos quais conclusões resistem à mudança de definição
- **Reqs:** REQ-240

## [ ] T-209 — Achados, sugestões e encadeamento (gate do M2)
- **What:** `python -m analise tudo` roda tudo em ordem e é chamado pelo `loader` depois dos marts. **Os 3 achados, as decisões e as sugestões são escritos pelo planejador com o Vinícius a partir dos números** (não pelo executor) e gravados em `resultado.achado` a partir de `seeds/achados.yaml`.
- **Where:** `analise/__main__.py`, `seeds/achados.yaml`, `loader/cli.py`
- **Depends on:** T-207, T-208
- **Reuses:** —
- **Done when:** `docker compose up` do zero popula `resultado.*`; segunda execução dá números idênticos
- **Tests:** teste de reprodutibilidade (duas execuções, mesmo resultado)
- **Gate:** **Gate de saída do M2**
- **Reqs:** REQ-260, REQ-261, REQ-270
