# M3 — Backend (API)

## Objetivo
Rotas de API em Next.js/TypeScript que entregam às telas apenas dados de `mart.*` e `resultado.*`, com contrato estável, validação de entrada, cache e registro suficiente para investigar um número errado.

## Requirements
| ID | Requirement | Prioridade | Case |
|----|-------------|-----------|------|
| REQ-301 | A API conecta com o papel `app_ro` e não tem nenhuma consulta a `stg` nem ao bruto | Crítica | C-10, C-12 |
| REQ-302 | Endpoints do contrato em `design.md` implementados com os campos exatos | Crítica | C-29 |
| REQ-303 | Parâmetros validados com zod; erro 400 com mensagem clara; SQL sempre parametrizado | Crítica | C-29 |
| REQ-304 | Toda resposta vem no envelope `{dados, meta}` com `versao_definicao`, `versao_analise`, `atualizado_em`, `lote_id`, `request_id` | Crítica | C-07, C-32 |
| REQ-305 | Cada requisição gera uma linha de log JSON: `request_id, endpoint, params, status, duracao_ms, linhas, lote_id, cache` | Crítica | C-32 |
| REQ-306 | Cache em memória por (endpoint, params, lote_id): expira quando entra lote novo ou em 1 h; cabeçalho `Cache-Control: public, s-maxage=300, stale-while-revalidate=3600` para a CDN | Alta | C-31 |
| REQ-307 | Cabeçalho `Server-Timing` com tempo de banco e total; script que mede p50/p95 de cada endpoint e grava o resultado no README | Alta | C-31 |
| REQ-308 | Parâmetro `pais` aceito em todos os endpoints (hoje só `Brazil`; outro valor → 400 "país ainda não carregado") — desenho pronto para multi-país | Média | C-30 |
| REQ-309 | Testes de contrato: cada endpoint devolve o formato do contrato contra a base sintética; teste que falha se um campo sumir ou mudar de tipo | Crítica | C-34 |
| REQ-310 | `GET /api/saude` responde estado do banco e último lote | Alta | C-32 |

## Gate de saída
Todos os endpoints do contrato respondendo com dados reais; testes de contrato verdes; p95 medido e registrado.
