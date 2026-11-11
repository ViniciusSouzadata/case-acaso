# Tasks — M3 Backend

Pré-requisito: gate do M1. Endpoints de `resultado.*` usam a migração da T-201 (tabelas vazias servem para começar).
```
T-301 ─► T-302 ─► T-303 ─► T-304 ─► T-305 (gate)
```

## [ ] T-301 — Projeto Next.js, conexão e utilitários da API
- **What:** Criar `app/` (Next.js App Router, TypeScript estrito, Tailwind). `lib/db.ts` (pool `pg` com `DATABASE_URL` do papel `app_ro`), `lib/api.ts` (envelope `{dados, meta}`, erro padronizado, `request_id`, log JSON de uma linha, `Server-Timing`), `lib/meta.ts` (lê versão da definição, versão da análise, último lote). `GET /api/saude`. Serviço `app` no compose, dependente do `loader` concluído. Dockerfile de produção (build + start).
- **Where:** `app/`, `docker-compose.yml`
- **Depends on:** T-110
- **Reuses:** design.md M3 — Stack, Envelope, Log
- **Done when:** `docker compose up` sobe o app; `/api/saude` responde com o último lote; log JSON aparece no console
- **Tests:** vitest do envelope e do formato do log
- **Gate:** Esqueleto da API no ar com rastreio por requisição
- **Reqs:** REQ-301, REQ-304, REQ-305, REQ-310

## [x] T-302 — Endpoints de retenção e dicionário
- **What:** `/api/retencao/resumo`, `/api/retencao/coortes` (com `meta.eras`), `/api/retencao/sensibilidade`, `/api/dicionario`. Validação zod (`pais`, `inicio`, `fim`, `granularidade`, `indicador`); `pais` ≠ Brazil → 400 "país ainda não carregado"; SQL parametrizado em `lib/consultas/`.
- **Where:** `app/app/api/retencao/**`, `app/app/api/dicionario/`, `app/lib/consultas/`
- **Depends on:** T-301
- **Reuses:** design.md M3 — tabela de endpoints
- **Done when:** campos idênticos ao contrato; datas inválidas e intervalo invertido devolvem 400
- **Tests:** vitest de contrato por endpoint (esquema zod da saída) contra a base sintética; testes dos erros 400
- **Gate:** Tela 1 tem todos os dados de que precisa
- **Reqs:** REQ-302, REQ-303, REQ-308, REQ-309

## [ ] T-303 — Endpoints de fatores, semana, achados e qualidade
- **What:** `/api/fatores/efeitos`, `/api/fatores/segmentos`, `/api/fatores/balanco`, `/api/semana/decomposicao`, `/api/achados`, `/api/qualidade`.
- **Where:** `app/app/api/**`
- **Depends on:** T-302
- **Reuses:** design.md M2 (contrato de `resultado.*`) e M3 (endpoints)
- **Done when:** campos idênticos ao contrato; tabela vazia devolve `dados: []` com 200 (não erro)
- **Tests:** vitest de contrato por endpoint; caso de tabela vazia
- **Gate:** Telas 2 e 3 têm todos os dados
- **Reqs:** REQ-302, REQ-303, REQ-309

## [ ] T-304 — Cache e medição de tempo
- **What:** Cache em memória por (rota, parâmetros, `lote_id`) com TTL de 1 h; campo `cache: hit|miss` no log; cabeçalho `Cache-Control` do design. `scripts/medir_api.ts`: 50 chamadas por rota, imprime p50/p95 (frio e quente) e grava a tabela em `docs/desempenho.md`.
- **Where:** `app/lib/cache.ts`, `scripts/medir_api.ts`
- **Depends on:** T-303
- **Reuses:** design.md M3 — Desempenho
- **Done when:** segunda chamada igual é `hit`; lote novo invalida; `docs/desempenho.md` com números reais
- **Tests:** vitest do cache (hit, expiração, invalidação por lote)
- **Gate:** Desempenho medido, não suposto
- **Reqs:** REQ-306, REQ-307

## [ ] T-305 — Varredura de privacidade e gate
- **What:** Teste automático que percorre todas as rotas e falha se alguma resposta contiver chaves ou valores com cara de `hashed_ip`, user-agent ou texto de conversa; teste que confirma que nenhuma consulta em `lib/consultas/` referencia `stg.`. Rodar todos os testes dentro do compose via `make test`.
- **Where:** `app/tests/`
- **Depends on:** T-304
- **Reuses:** PROJECT.md — princípios 1 e 6
- **Done when:** `make test` verde (Python + TypeScript)
- **Tests:** os próprios
- **Gate:** **Gate de saída do M3**
- **Reqs:** REQ-301, REQ-309
