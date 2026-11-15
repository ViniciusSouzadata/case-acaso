# M3 — Design do backend

## Stack
Next.js (App Router) + TypeScript estrito; rotas em `app/api/**/route.ts`; `pg` (pool) com `DATABASE_URL` do papel `app_ro`; `zod` para parâmetros; `vitest` para testes. Sem ORM: consultas SQL nomeadas em `lib/consultas/*.ts`, uma por indicador, as mesmas citadas em `mart.dicionario_indicador`.

## Envelope
```json
{ "dados": [...],
  "meta": { "versao_definicao": "1.0.0", "versao_analise": "1.0.0", "atualizado_em": "2026-11-14T12:00:00Z",
            "lote_id": 3, "request_id": "req_ab12cd", "fonte": "mart.agg_retencao_semanal" } }
```
Erro: `{ "erro": { "codigo": "PARAMETRO_INVALIDO", "mensagem": "...", "request_id": "..." } }`.

## Endpoints (contrato congelado)
| Método e rota | Entrada (query) | Saída (`dados`) | Fonte |
|---|---|---|---|
| GET `/api/retencao/resumo` | `pais` | `{usuarios, voltaram_7d, taxa, ic_inf, ic_sup, periodo_inicio, periodo_fim, efeito_minimo_detectavel_pp}` | resultado.meta |
| GET `/api/retencao/coortes` | `pais`, `inicio`, `fim` (datas ISO), `granularidade` = `semana`\|`mes` | `[{periodo, novos, voltaram_7d, taxa, ic_inf, ic_sup, taxa_mm4, madura, amostra_suficiente}]` + `meta.eras` | mart.agg_retencao_periodo, mart.dim_era_modelo |
| GET `/api/retencao/sensibilidade` | `pais` | `[{definicao, descricao, usuarios, voltaram_7d, taxa, ic_inf, ic_sup, delta_vs_oficial}]` | mart.agg_retencao_sensibilidade |
| GET `/api/fatores/efeitos` | `pais`, `grupo?` = `assistente`\|`perfil`\|`engajamento` | linhas de `resultado.efeito_fator` | resultado.efeito_fator |
| GET `/api/fatores/segmentos` | `pais`, `variavel` | `[{valor, novos, voltaram_7d, taxa, ic_inf, ic_sup, amostra_suficiente}]` | mart.agg_retencao_segmento |
| GET `/api/fatores/balanco` | `pais`, `tratamento` | `[{covariavel, dp_antes, dp_depois}]` | resultado.balanco_propensao |
| GET `/api/semana/decomposicao` | `pais`, `semana` | `{resumo: {...}, segmentos: [...]}` | resultado.decomposicao_* |
| GET `/api/achados` | `pais` | `[{ordem, titulo, evidencia, decisao, limite}]` | resultado.achado |
| GET `/api/qualidade` | `pais` | `{lote: {...}, reconciliacao: [...], problemas: [...], validacao: [...]}` | ops.*, resultado.problema_qualidade, resultado.validacao_classificador |
| GET `/api/dicionario` | `indicador?` | `[{indicador, nome_exibicao, definicao, formula, denominador, periodo_referencia, fonte, sql_referencia, limitacoes}]` | mart.dicionario_indicador |
| GET `/api/saude` | — | `{ok, banco, ultimo_lote, versao_definicao}` | ops.lote_carga |

Regras: `inicio`/`fim` opcionais (padrão = período todo); `fim` exclusivo; intervalo invertido → 400. Valores abaixo do n mínimo saem com `amostra_suficiente: false` e taxa preservada — quem decide ocultar é a tela (uma regra só, no front).

## Desempenho
- Tudo que a tela mostra é pré-calculado na carga; as rotas fazem `SELECT` simples com filtro por período.
- Cache em memória (Map com TTL de 1 h, chave inclui `lote_id`) + cabeçalhos para CDN (CloudFront na implantação).
- Medição: `Server-Timing` por resposta; `scripts/medir_api.ts` faz 50 chamadas por rota e imprime p50/p95; em produção, métricas no CloudWatch a partir do log JSON.

## Log
`console.log(JSON.stringify({...}))` em uma linha por requisição (campos do REQ-305) — pronto para CloudWatch Logs Insights.

## Multi-país (desenho)
`pais` já é parâmetro e entra na chave de cache; os marts ganham coluna `pais`; fuso por país em `ops.parametros`; a comparação entre países usa taxa padronizada pela composição (mesmo mix) — descrito no documento, não implementado.


## Atualização final (painel aprovado em 15/11/2026)
- `GET /api/achados` devolve também, quando existem: `numero_destaque`, `rotulo_destaque`, `acao_curta`, `vimos_curto`, `limite_curto` e `tecnico` (colunas opcionais de `resultado.achado`, migrações 012 a 014). O texto longo (`evidencia`, `decisao`, `limite`) não mudou.
- `GET /api/qualidade`: `validacao[].detalhe_json.ponderadas` traz precisão e cobertura da recusa e acurácia do assunto ponderadas pelo estrato da amostra conferida à mão.
- Telas: "Quantos voltam" (`/`), "O que faz voltar" (`/fatores`) e "Dá para confiar?" (`/dados`); detalhes numa caixa central (`CaixaDetalhe`).
