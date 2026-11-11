# Tasks — M1 Base analítica

Ordem e paralelismo:
```
T-101 ──► T-102 ─┐
   └────► T-103 ─┼─► T-104 ──► T-106 ──► T-107 ──► T-108 ─┐
                 └─► T-105 ───────────────────────► T-109 ─┴─► T-110 (gate)
```
T-102, T-103 e T-105 podem rodar em paralelo depois da T-101. T-109 precisa de T-105 e T-107.

## [x] T-101 — Esqueleto do repositório e compose mínimo
- **What:** Criar a estrutura de pastas do `design.md` (loader/, sql/migrations/, sql/transform/, seeds/, tests/, data/bruto/). `docker-compose.yml` com `db` (postgres:16, healthcheck) e `loader` (python:3.12-slim; por enquanto só conecta e imprime a versão do Postgres). `Makefile` com `up`, `down`, `test`, `reset`. `.env.example`. Ajustar `.gitignore`: ignorar `data/raw/` e `data/interim/`, **versionar** `data/bruto/`. README inicial com os dois jeitos de rodar (Docker Desktop ou WSL).
- **Where:** raiz do repo
- **Depends on:** —
- **Reuses:** design.md M1 — Serviços do compose, Estrutura de pastas
- **Done when:** `docker compose up` (via `wsl -d Ubuntu-22.04` nesta máquina) sobe `db` saudável e o `loader` termina com código 0 imprimindo a versão do Postgres
- **Tests:** `docker compose up --abort-on-container-exit` do zero duas vezes seguidas; `docker compose down -v` limpa tudo
- **Gate:** Um comando sobe o esqueleto; Docker do WSL confirmado funcionando
- **Reqs:** REQ-101

## [x] T-102 — Snapshot do bruto e extração reproduzível
- **What:** Promover `data/interim/brazil.parquet` a `data/bruto/wildchat_brasil.parquet` com `wildchat_brasil.sha256`. Criar `loader/extrair.py` a partir de `scripts/discovery/01_extract_brazil.py`: sem `FULL_REFRESH`, confere o SHA-256 do snapshot; com `FULL_REFRESH=1`, baixa `allenai/WildChat-1M` do Hugging Face, filtra `country = 'Brazil'` e regrava snapshot + checksum. Registrar no README a licença (ODC-BY) e a data do snapshot.
- **Where:** `data/bruto/`, `loader/extrair.py`
- **Depends on:** T-101
- **Reuses:** scripts/discovery/01_extract_brazil.py (sintaxe DuckDB 2.x já corrigida: `lambda t:`; usar `.fetchall()`)
- **Done when:** checksum confere; snapshot tem 11.621 linhas; checksum errado faz a carga falhar com mensagem clara
- **Tests:** teste unitário do verificador de checksum (arquivo íntegro × arquivo alterado)
- **Gate:** Bruto versionado e verificável
- **Reqs:** REQ-102

## [x] T-103 — Migrações: esquemas, papéis, tabelas de operação e staging
- **What:** Executor de migrações (`loader/migrar.py`: aplica `sql/migrations/NNN_*.sql` em ordem, registra em `ops.schema_migrations`). Migrações: esquemas `stg`, `mart`, `resultado`, `ops`; papéis `loader_rw` e `app_ro` (SELECT só em `mart`, `resultado` e `ops.lote_carga`); `ops.parametros` com os valores v1.0.0; `ops.lote_carga`, `ops.rejeitado`, `ops.reconciliacao`; `stg.conversa` exatamente com as colunas do design.
- **Where:** `sql/migrations/`, `loader/migrar.py`
- **Depends on:** T-101
- **Reuses:** design.md M1 — Esquemas e papéis, Tabelas
- **Done when:** rodar migrações duas vezes não dá erro nem duplica; conectado como `app_ro`, `SELECT` em `stg.conversa` é negado e em `mart.*` é permitido
- **Tests:** teste de idempotência das migrações; teste de permissão do papel `app_ro`
- **Gate:** Privacidade por permissão comprovada por teste
- **Reqs:** REQ-118, REQ-141

## [ ] T-104 — Carga: derivar variáveis de texto e gravar staging
- **What:** `loader/derivar.py` (funções puras): `conversa_id`, início/fim, família de user-agent (SO, navegador, dispositivo), `usuario_id` e chaves alternativas, família/versão de modelo, idiomas da 1ª pergunta e 1ª resposta e `idioma_divergente`, fuso por estado, tamanhos, `recusa_1` (regras em `seeds/regras_recusa.yaml`), `pergunta_vazia`, `conta_como_uso`, `ip_mudou`, `hash_repetido`. `loader/carregar.py`: lê o parquet com DuckDB, aplica as derivações, **descarta o texto**, grava em `stg.conversa` com upsert por `conversa_id` em uma transação, cria o lote em `ops.lote_carga` e grava rejeitados com motivo. Junta o seed de tema se existir.
- **Where:** `loader/derivar.py`, `loader/carregar.py`, `seeds/regras_recusa.yaml`
- **Depends on:** T-102, T-103
- **Reuses:** design.md M1 — stg.conversa, Regras de carga; scripts/discovery/02 e 03 (regras de SO/navegador e de início da conversa)
- **Done when:** `stg.conversa` com 11.621 linhas menos rejeitados; segunda carga não muda nenhuma contagem; nenhuma coluna contém texto de conversa; lote registrado com linhas lidas/gravadas/rejeitadas
- **Tests:** unitários de cada função de `derivar.py` (casos de borda: UA desconhecido, pergunta vazia, idioma `Nolang`, estado nulo); teste de idempotência da carga
- **Gate:** Carga idempotente e sem texto no banco
- **Reqs:** REQ-103, REQ-104, REQ-110, REQ-111, REQ-112, REQ-120, REQ-121, REQ-122, REQ-123, REQ-140

## [x] T-105 — Base sintética de resposta conhecida
- **What:** `tests/fabrica_bruto.py` gera um parquet no mesmo formato do bruto com usuários desenhados à mão e a resposta esperada escrita ao lado: retorno em 6d23h (conta); retorno em 7d+1min (não conta); 2ª conversa 20 min depois (mesma sessão, não é retorno); mesma pessoa com versão nova do navegador (mesmo usuário); um IP com 12 user-agents diferentes (tráfego anômalo); pergunta vazia (não conta como uso); usuário nos últimos 7 dias (imaturo); usuário nos primeiros 14 dias (burn-in); conversa sem resposta do assistente (rejeitada).
- **Where:** `tests/fabrica_bruto.py`, `tests/esperado.py`
- **Depends on:** T-101
- **Reuses:** design.md M1 — regras de sessão, usuário, maduro, burn-in, tráfego anômalo
- **Done when:** o parquet sintético é lido pela mesma carga da T-104 sem código especial; `esperado.py` lista, por caso, usuário/sessões/voltou esperados
- **Tests:** teste que valida o próprio formato do parquet sintético contra o esquema do bruto real
- **Gate:** Existe uma verdade conhecida para testar as definições
- **Reqs:** REQ-150

## [ ] T-106 — Transformações: sessão, usuário, primeira experiência
- **What:** `sql/transform/10_sessao.sql`, `20_usuario.sql`, `30_primeira_experiencia.sql` e a função única `mart.calc_retencao(...)` do design. `mart.dim_era_modelo`. `loader/transformar.py` executa em ordem, com `CREATE TABLE ..._novo` + troca de nome na mesma transação. Todos os limiares lidos de `ops.parametros`, nunca escritos no SQL.
- **Where:** `sql/transform/`, `loader/transformar.py`
- **Depends on:** T-104
- **Reuses:** design.md M1 — mart.fct_sessao, mart.dim_usuario, mart.fct_primeira_experiencia, Função de cálculo única
- **Done when:** marts populados; uma linha por usuário em `dim_usuario` e em `fct_primeira_experiencia`; retorno global coerente com o discovery (ordem de 24%; registrar o número exato da chave oficial no STATE.md)
- **Tests:** contagens (usuários = sessões com seq 1); nenhum usuário elegível imaturo ou em burn-in
- **Gate:** Definições oficiais materializadas
- **Reqs:** REQ-113, REQ-114, REQ-115, REQ-116, REQ-117, REQ-120

## [ ] T-107 — Agregados e dicionário de indicadores
- **What:** `40_agregados.sql`: `mart.agg_retencao_periodo` (semana e mês, IC de Wilson, média móvel de 4 semanas, `madura`, `amostra_suficiente`), `mart.agg_retencao_sensibilidade` (todas as linhas do design, via `calc_retencao`), `mart.agg_retencao_segmento`. `50_dicionario.sql`: `mart.dicionario_indicador` com definição, fórmula, denominador, período, fonte, SQL e limitações de cada indicador exibido.
- **Where:** `sql/transform/40_agregados.sql`, `50_dicionario.sql`
- **Depends on:** T-106
- **Reuses:** design.md M1 — tabelas agg_*, dicionário
- **Done when:** soma de `novos` das coortes semanais = usuários elegíveis; linha "oficial" da sensibilidade = taxa global; todo indicador usado nos agregados tem linha no dicionário
- **Tests:** teste do IC de Wilson contra valores calculados à mão (ex.: 12/50); teste de fechamento das somas
- **Gate:** Tudo que a tela vai mostrar está pré-calculado
- **Reqs:** REQ-130, REQ-131, REQ-132, REQ-133

## [ ] T-108 — Reconciliação bruto × marts
- **What:** `loader/reconciliar.py`: recalcula direto do parquet, com SQL independente em DuckDB, total de conversas, IPs distintos, usuários pela chave oficial e novos/voltaram por semana; compara com os marts; grava `ops.reconciliacao`; diferença acima da tolerância encerra a carga com erro e marca o lote como falho.
- **Where:** `loader/reconciliar.py`
- **Depends on:** T-107
- **Reuses:** design.md M1 — ops.reconciliacao; scripts/discovery/03_followup.py (cálculo de sessão em DuckDB)
- **Done when:** reconciliação passa no snapshot real; ao sabotar uma linha do mart, a carga falha
- **Tests:** teste com divergência injetada
- **Gate:** Divergência é pega pela carga, não pelo cliente
- **Reqs:** REQ-152

## [ ] T-109 — Testes que travam as definições
- **What:** `tests/test_definicoes_sintetico.py` (roda a carga + transformações na base sintética e compara com `esperado.py`, caso a caso); `tests/test_invariantes_snapshot.py` (11.621 conversas, `conversa_id` único, voltaram ≤ novos, somas fecham); `tests/test_versao_definicao.py` (os valores de `ops.parametros` para a versão corrente batem com um arquivo de referência; mudar parâmetro sem subir a versão falha). `make test` roda tudo dentro do compose.
- **Where:** `tests/`
- **Depends on:** T-105, T-107
- **Reuses:** T-105 (fábrica e esperado)
- **Done when:** `make test` verde; alterar `gap_sessao_min` para 60 sem mudar a versão faz o teste de versão falhar; alterar a regra de retorno no SQL faz o teste sintético falhar
- **Tests:** os próprios; demonstrar as duas falhas provocadas e registrar no STATE.md
- **Gate:** Definição de indicador não muda sem um teste quebrar
- **Reqs:** REQ-150, REQ-151, REQ-153

## [ ] T-110 — Subida do zero, ponta a ponta (gate do M1)
- **What:** `loader/cli.py` encadeia migrar → verificar bruto → carregar → transformar → reconciliar. `docker compose down -v && docker compose up` em pasta limpa (clone novo). Registrar tempo total e números finais (conversas, usuários, taxa global oficial, linhas rejeitadas) no STATE.md e no README.
- **Where:** `loader/cli.py`, README, STATE.md
- **Depends on:** T-108, T-109
- **Reuses:** —
- **Done when:** clone novo + um comando = base populada, reconciliação ok, `make test` verde, sem credencial externa
- **Tests:** execução real em pasta limpa, duas vezes
- **Gate:** **Gate de saída do M1** — contratos de `mart.*` congelados para M2/M3/M4
- **Reqs:** REQ-101, REQ-103, REQ-104
