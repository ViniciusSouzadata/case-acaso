# M1 — Base analítica

## Objetivo
Com um comando, sair da base bruta (extrato Brasil do WildChat-1M) e chegar a uma base analítica em Postgres que define, de forma única e testada, **usuário, sessão, primeira experiência e retorno em 7 dias**, com as variáveis da primeira experiência e o registro de cada carga. O dashboard e a análise só leem esta base.

## Features
- F01 — Carga idempotente do bruto
- F02 — Identidade, sessão, primeira experiência e retorno
- F03 — Variáveis da primeira experiência
- F04 — Agregados e dicionário de indicadores
- F05 — Privacidade por construção
- F06 — Rastreabilidade e testes de definição

## Requirements

### F01 — Carga idempotente do bruto
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-101 | `docker compose up` sobe Postgres, aplica migrações, carrega o bruto, constrói staging e marts e termina com sucesso, sem credencial externa | Crítica | C-14, C-10 |
| REQ-102 | A fonte padrão é o snapshot versionado do extrato Brasil (parquet + SHA-256 conferido na carga); `FULL_REFRESH=1` baixa o WildChat-1M do Hugging Face e reextrai `country = 'Brazil'` | Crítica | C-08, C-14 |
| REQ-103 | Rodar a carga duas vezes produz exatamente o mesmo resultado (upsert por `conversa_id`, transação por lote) | Crítica | C-34, C-38 |
| REQ-104 | Cada carga grava um lote em `ops.lote_carga` (fonte, checksum, linhas lidas/gravadas/rejeitadas, duração, versão da definição) e os rejeitados com motivo | Crítica | C-32 |

### F02 — Identidade, sessão, primeira experiência e retorno
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-110 | `usuario_id` oficial = hash de `hashed_ip` + família do user-agent (sistema + navegador, sem versão). As chaves alternativas (só IP; IP + UA completo) ficam calculadas para sensibilidade | Crítica | C-09, C-16 |
| REQ-111 | "Uso" = conversa com ≥ 1 mensagem não vazia do usuário e resposta do assistente; o resto é marcado e fica fora das métricas | Crítica | C-13, C-19 |
| REQ-112 | Início da conversa = horário da 1ª resposta do assistente; fim = `timestamp` da conversa | Crítica | C-19 |
| REQ-113 | Sessão = conversas do mesmo usuário com intervalo ≤ 30 min entre o fim de uma e o início da próxima | Crítica | C-16 |
| REQ-114 | Primeira experiência = primeira sessão do usuário. Retorno em 7 dias = existe outra sessão com início ≤ 7 dias (168 h) após o início da primeira | Crítica | C-05, C-16 |
| REQ-115 | Coorte = semana (segunda a domingo) do início da primeira sessão no fuso `America/Sao_Paulo` | Crítica | C-13 |
| REQ-116 | Usuário **maduro** = teve 7 dias completos de observação; **burn-in** = primeira sessão nos 14 primeiros dias da base. Só maduros fora do burn-in entram em taxas e modelos; os demais ficam marcados com o motivo | Crítica | C-16, C-28 |
| REQ-117 | IPs com volume anômalo (≥ 200 conversas ou ≥ 10 user-agents distintos) marcam seus usuários como `trafego_anomalo`; ficam fora do modelo principal e visíveis na qualidade dos dados | Alta | C-19, C-20 |
| REQ-118 | Todos os limiares (30 min, 7 dias, 14 dias, 200, 10, n mínimo 30, fuso) vivem em `ops.parametros` com versão da definição | Crítica | C-34 |

### F03 — Variáveis da primeira experiência
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-120 | Por usuário: modelo (família e versão), era de oferta de modelo, tema, tamanho da pergunta e da resposta, recusa, idioma, idioma da resposta ≠ idioma da pergunta, turnos e conversas da sessão, hora local, período do dia, dia da semana, dispositivo, estado | Crítica | C-17 |
| REQ-121 | Cada variável tem derivação documentada (regra, fonte, limitação) no dicionário | Crítica | C-17 |
| REQ-122 | Tema vem de um seed versionado (`conversa_id`, tema, modelo, versão do prompt); sem seed, a carga funciona e o tema fica "não classificado" | Alta | C-18, C-11 |
| REQ-123 | Hora local usa o fuso do estado quando existir; senão, o do país | Média | C-13, C-30 |

### F04 — Agregados e dicionário
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-130 | `mart.agg_retencao_periodo` (semana e mês): novos, voltaram, taxa, IC 95% (Wilson), média móvel de 4 semanas, `madura`, `amostra_suficiente` (n ≥ 30) | Crítica | C-28, C-31 |
| REQ-131 | `mart.agg_retencao_sensibilidade`: a mesma taxa global sob cada definição alternativa (chave × intervalo de sessão × fuso × cortes) | Crítica | C-13, C-16 |
| REQ-132 | `mart.agg_retencao_segmento`: novos, voltaram, taxa e IC por valor de cada variável | Crítica | C-20, C-27 |
| REQ-133 | `mart.dicionario_indicador`: definição, fórmula, denominador, período, fonte e SQL de cada indicador — única fonte do glossário da tela e do documento | Crítica | C-07, C-28 |

### F05 — Privacidade por construção
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-140 | Nenhum texto de conversa entra no Postgres: as variáveis de texto são calculadas na carga e só o resultado é gravado | Crítica | C-12 |
| REQ-141 | A aplicação conecta com um papel que só lê `mart` e `resultado`; `hashed_ip` e user-agent existem apenas em `stg` | Crítica | C-12, C-10 |

### F06 — Rastreabilidade e testes
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-150 | Teste com base sintética de resposta conhecida cobre: retorno em 6d23h (conta) e 7d+1min (não conta); 2ª conversa em 20 min (mesma sessão); troca de versão do navegador (mesmo usuário); user-agent rotativo no mesmo IP; pergunta vazia; coorte imatura; burn-in | Crítica | C-34 |
| REQ-151 | Teste de invariantes no snapshot real: 11.621 conversas, `conversa_id` único, voltaram ≤ novos, soma das coortes = total de usuários elegíveis | Crítica | C-33, C-34 |
| REQ-152 | Reconciliação bruto × marts gravada em `ops.reconciliacao` a cada carga; diferença fora da tolerância falha a carga | Alta | C-33 |
| REQ-153 | Mudar um parâmetro de definição sem subir a versão faz um teste falhar | Crítica | C-34 |

## Gate de saída
`docker compose up` do zero popula a base; testes REQ-150/151/153 verdes; retorno global coerente com o discovery (~24%, variando conforme a chave); nenhum texto de conversa no banco.

## Fora do escopo do M1
Modelos estatísticos (M2), API e telas (M3/M4), classificação de tema em si (só o contrato do seed), deploy AWS.
