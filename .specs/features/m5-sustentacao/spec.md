# M5 — Sustentação e investigação de falhas

## Objetivo
Responder ao §4 do case com coisa que roda (reconciliação, testes de definição, logs) e com texto curto para o que é só desenho (ambientes, deploy), mais a investigação completa do incidente §4.2.

## Requirements
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-501 | Tabela "o que registramos em cada camada": carga (`ops.lote_carga`, rejeitados, checksum), base analítica (versão da definição, reconciliação), backend (log JSON por requisição com `request_id` e `lote_id`), tela (`request_id` visível no erro, rodapé com data e versão) — com o caminho de investigação de um número errado: tela → request_id → consulta → mart → lote → bruto | Crítica | C-32 |
| REQ-502 | Reconciliação automática rodando a cada carga (REQ-152) + regra de alerta descrita: divergência acima da tolerância, salto de "novos" > 3 desvios da média de 8 semanas, salto de user-agents por IP | Crítica | C-33 |
| REQ-503 | Testes que travam a definição: base sintética de resposta conhecida (REQ-150), versão da definição (REQ-153), contrato da API (REQ-309) — todos em um comando (`make test`) | Crítica | C-34 |
| REQ-504 | Descrição do caminho até produção: ambientes (local → homologação → produção), migrações numeradas e reversíveis, deploy por imagem versionada, verificação pós-deploy (saúde + reconciliação) e reversão | Crítica | C-34 |
| REQ-505 | Workflow de CI (GitHub Actions) rodando lint + testes | Could | C-34 |
| REQ-510 | Incidente §4.2 — resposta às 5 perguntas, na ordem do case | Crítica | C-35..C-39 |
| REQ-511 | Pergunta 1: começar reconciliando as duas fontes na mesma granularidade; mostrar que só "novos" diverge → problema de contagem de usuários | Crítica | C-35 |
| REQ-512 | Pergunta 2: camada = carga (definição de `usuario_id`), com as evidências numéricas e a **consulta de confirmação** escrita; demonstração do mecanismo com dado real (IP + UA gera +21% de "usuários" no Brasil) | Crítica | C-36 |
| REQ-513 | Pergunta 3: trecho exato (`chave = f"{hashed_ip}|{user-agent}"`) + correção escrita em código (identidade única vinda de uma dimensão de usuário; upsert; transação) e os demais defeitos do endpoint (último turno como "primeira vez", coorte imatura, semana em UTC) | Crítica | C-37 |
| REQ-514 | Pergunta 4: reprocessar histórico, versionar a mudança de definição, alinhar a definição com o relatório do time de dados, reconciliação + alerta, teste de regressão com user-agent rotativo, registro pós-incidente | Crítica | C-38 |
| REQ-515 | Pergunta 5: mensagem pronta para a gerente de produto — durante e depois — em linguagem simples | Crítica | C-39 |
| REQ-516 | O teste de regressão do incidente existe de verdade na suíte (caso sintético de UA rotativo e de troca de versão de navegador) | Alta | C-38 |

## Fonte
`docs/discovery/incidente-4.2-raciocinio.md` (rascunho validado) + números do discovery.

## Gate de saída
Seção §4 do documento escrita; `make test` verde; a consulta de confirmação roda no bruto (DuckDB) sem erro.
