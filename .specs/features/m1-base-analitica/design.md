# M1 — Design da base analítica

## Fluxo
```
 data/bruto/wildchat_brasil.parquet (snapshot + sha256)      [FULL_REFRESH=1: Hugging Face → extrair_brasil.py]
        │  loader (Python + DuckDB): lê, deriva variáveis de TEXTO, descarta o texto
        ▼
 stg.conversa            1 linha por conversa, sem conteúdo            (upsert por conversa_id)
        │  SQL versionado (sql/transform/*.sql), reconstrução completa em transação
        ▼
 mart.fct_sessao → mart.dim_usuario → mart.fct_primeira_experiencia
        │
        ▼
 mart.agg_retencao_semanal | _sensibilidade | _segmento | mart.dicionario_indicador
        │                                             (M2 grava em resultado.*)
        ▼
 app (Next.js) lê só mart.* e resultado.* com o papel app_ro
```
Volume: 11.621 conversas → reconstrução completa a cada carga leva segundos; carga incremental não se paga (ADR).

## Serviços do compose
| Serviço | Imagem | Papel |
|---------|--------|-------|
| `db` | postgres:16 | Base analítica; healthcheck `pg_isready` |
| `loader` | python:3.12-slim + duckdb, psycopg, pyarrow | migra → carrega → transforma → (M2) analisa → reconcilia → sai com 0 |
| `app` | node:22 (Next.js) | `depends_on: loader: service_completed_successfully` |

## Esquemas e papéis
- `stg` (restrito), `mart`, `resultado`, `ops`.
- Papel `loader_rw`: dono. Papel `app_ro`: `USAGE`/`SELECT` só em `mart` e `resultado` (+ `ops.lote_carga` para mostrar "dados atualizados em").

## Tabelas

### ops.parametros (definição versionada)
| chave | valor v1.0.0 |
|---|---|
| versao_definicao | 1.0.0 |
| gap_sessao_min | 30 |
| janela_retorno_horas | 168 |
| burn_in_dias | 14 |
| n_minimo | 30 |
| limiar_conversas_ip | 200 |
| limiar_uas_ip | 10 |
| fuso_pais | America/Sao_Paulo |

### ops.lote_carga
`lote_id, iniciado_em, terminado_em, fonte, sha256, linhas_lidas, linhas_gravadas, linhas_rejeitadas, versao_definicao, status, erro`
### ops.rejeitado
`lote_id, conversa_id, motivo`
### ops.reconciliacao
`lote_id, metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok`
Métricas: total de conversas; IPs distintos; usuários por chave oficial; novos e voltaram por semana recalculados direto do parquet com SQL independente (DuckDB).

### stg.conversa (PK conversa_id)
| coluna | derivação |
|---|---|
| conversa_id | `conversation[1].turn_identifier` (o hash de conteúdo não é único) |
| conversation_hash, hash_repetido | hash e flag de conteúdo idêntico em outra conversa |
| hashed_ip, user_agent, accept_language | top-level / `header` |
| ua_so, ua_navegador, ua_dispositivo | regras sobre o user-agent (android/ios/windows/mac/linux/outro; chrome/edge/firefox/safari/opera/outro; celular × computador) |
| usuario_id | `sha256(hashed_ip‖ua_so‖ua_navegador)` — **oficial** |
| usuario_id_ip, usuario_id_ip_ua | alternativas para sensibilidade |
| modelo_versao, modelo_familia | `model`; `gpt-4%` → gpt-4, senão gpt-3.5 |
| ts_inicio | timestamp da 1ª resposta do assistente (UTC) |
| ts_fim | `timestamp` da conversa (UTC) |
| n_turnos | `turn` |
| idioma_conversa, idioma_pergunta_1, idioma_resposta_1, idioma_divergente | campos `language`; divergente = 1ª resposta em idioma diferente da 1ª pergunta (ignora `Nolang`) |
| estado, fuso | `state`; fuso por estado (AC → America/Rio_Branco; AM, RR, RO, MT, MS → America/Manaus; demais → America/Sao_Paulo) |
| chars_pergunta_1, chars_resposta_1 | tamanho da 1ª pergunta e da 1ª resposta |
| recusa_1 | regra pt/en sobre a 1ª resposta (lista versionada; validada por amostra manual no M2) |
| pergunta_vazia, conta_como_uso | REQ-111 |
| ip_mudou | algum turno com `hashed_ip` diferente do da conversa |
| redacted | flag de PII anonimizada (`toxic` não é carregada: é constante nesta versão do dataset) |
| tema, tema_origem | junção com o seed; nulo → "não classificado" |
| lote_id | rastreio |

### mart.fct_sessao (PK usuario_id, seq)
Só conversas com `conta_como_uso`. Ordena por `ts_inicio`; nova sessão quando `ts_inicio − ts_fim anterior > gap_sessao_min`.
`usuario_id, seq, ts_inicio, ts_fim, n_conversas, n_turnos`

### mart.dim_usuario (PK usuario_id)
`usuario_id, ts_primeira (início da sessão 1), coorte_semana, coorte_mes, n_sessoes, n_conversas, dispositivo, estado, trafego_anomalo, maduro, burn_in, elegivel, motivo_inelegivel`
- `coorte_semana = date_trunc('week', ts_primeira AT TIME ZONE fuso_pais)::date`
- `maduro = ts_primeira + janela ≤ max(ts_fim) da base`
- `burn_in = ts_primeira < min(ts_inicio) da base + burn_in_dias`
- `trafego_anomalo`: o IP do usuário passa de um dos limiares
- `elegivel = maduro AND NOT burn_in AND NOT trafego_anomalo`

### mart.fct_primeira_experiencia (PK usuario_id)
Uma linha por usuário, com as variáveis da sessão 1 (as de conversa vêm da 1ª conversa da sessão):
`modelo_familia, modelo_versao, era_modelo, tema, faixa_chars_pergunta, faixa_chars_resposta, recusa, idioma, idioma_divergente, n_turnos_sessao, n_conversas_sessao, hora_local, periodo_dia, dia_semana, fim_de_semana, dispositivo, estado, regiao, voltou_7d, horas_ate_retorno, elegivel`
- `era_modelo`: `2023-04..06 (3.5 + 4 opcional)`, `2023-07..10 (só 3.5)`, `2023-11 (4 volta)`, `2023-12+ (4 padrão)`.
- `voltou_7d = EXISTS sessão seq > 1 com ts_inicio ≤ ts_primeira + janela`.

### mart.agg_retencao_periodo (auditoria S.5: substitui `agg_retencao_semanal`; o endpoint aceita semana e mês)
`granularidade ('semana'|'mes'), periodo (date), novos, voltaram_7d, taxa, ic_inf, ic_sup, taxa_mm4 (só semana), madura, amostra_suficiente`
IC de Wilson em SQL. `madura` = todo o período tem janela completa. `amostra_suficiente = novos ≥ n_minimo`.

### mart.dim_era_modelo
`era, inicio, fim, descricao` — as 4 eras de oferta de modelo; alimenta as faixas de fundo do gráfico (vai no `meta.eras` de `/api/retencao/coortes`).

### Função de cálculo única (auditoria S.5)
`mart.calc_retencao(chave text, gap_min int, fuso text, usar_burn_in bool, incluir_anomalo bool, incluir_vazias bool)` devolve usuários, voltaram e taxa refazendo sessões para a chave pedida. A linha "oficial" e todas as linhas de sensibilidade saem da **mesma** função — impossível as definições divergirem por cópia de SQL.

### mart.agg_retencao_sensibilidade
`definicao, descricao, usuarios, voltaram_7d, taxa, ic_inf, ic_sup, delta_vs_oficial`
Linhas: oficial; só IP; IP + UA completo; gap 60 min; "voltou em outro dia"; UTC; sem burn-in; com tráfego anômalo; contando perguntas vazias.

### mart.agg_retencao_segmento
`variavel, valor, novos, voltaram_7d, taxa, ic_inf, ic_sup, amostra_suficiente`

### mart.dicionario_indicador
`indicador, nome_exibicao, definicao, formula, denominador, periodo_referencia, fonte, sql_referencia, limitacoes, versao_definicao`

## Regras de carga
- Lote único por execução, em transação: `INSERT ... ON CONFLICT (conversa_id) DO UPDATE` (conversa que cresce atualiza turnos e fim).
- Rejeita (com motivo): sem resposta do assistente; `conversa_id` nulo; `ts_inicio > ts_fim`.
- Marts reconstruídos com `CREATE TABLE ..._novo` + troca de nome na mesma transação (leitor nunca vê tabela vazia).
- Migrações: `sql/migrations/NNN_*.sql` aplicadas em ordem, registradas em `ops.schema_migrations`.

## Estrutura de pastas
```
loader/            pacote Python: extrair, derivar (texto), carregar, transformar, reconciliar, cli
sql/migrations/    DDL numerado
sql/transform/     10_sessao.sql 20_usuario.sql 30_primeira_experiencia.sql 40_agregados.sql 50_dicionario.sql
seeds/             tema_conversa.csv, regras_recusa.yaml
data/bruto/        wildchat_brasil.parquet + .sha256
tests/             test_definicoes_sintetico.py, test_invariantes_snapshot.py, test_versao_definicao.py
docker-compose.yml
```

## Decisões que viram ADR/BDR (cada uma com "Como defender")
| # | Decisão | Alternativas |
|---|---------|-------------|
| BDR-01 | Usuário = IP + família de UA | só IP (junta gente atrás do mesmo IP); IP + UA completo (parte a pessoa a cada atualização de navegador) |
| BDR-02 | Sessão de 30 min; retorno = nova sessão em até 7 dias | 60 min; "outro dia"; regra de 1 h da referência |
| BDR-03 | O que conta como uso | contar tudo |
| BDR-04 | Burn-in de 14 dias e exclusão de coortes imaturas | sem cortes |
| BDR-05 | Tráfego anômalo marcado e fora do modelo | manter; remover da base |
| BDR-06 | Semana no fuso de Brasília; hora local por estado | UTC |
| ADR-01 | Postgres como base analítica; reconstrução completa por carga | incremental; DuckDB/Athena |
| ADR-02 | Texto não entra na base analítica | guardar conteúdo com controle de acesso |
| ADR-03 | SQL versionado + pytest para definições | dbt (evolução quando houver time e mais modelos) |
| ADR-04 | Snapshot do extrato como bruto padrão + FULL_REFRESH | baixar 3,4 GB sempre |
| ADR-05 | Parâmetros de definição versionados em tabela | constantes no código |

## Riscos do M1
- Regra de user-agent classificar mal navegadores raros → cai em "outro" (impacto baixo; medido na qualidade).
- Seed de tema ausente → coluna "não classificado"; M2 roda sem tema e avisa.
