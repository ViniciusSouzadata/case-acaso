# Case Acaso: retenção de um assistente de IA

Repositório privado. Base analítica (Postgres 16) + carga e análise (Python) + painel e API (Next.js) que respondem: de cada 100 pessoas que experimentam o assistente, quantas voltam em até 7 dias, e o que muda essa chance.

**Pré-requisitos:** Docker Engine com o plugin Compose (Docker Desktop, ou Engine dentro do WSL2). Nada mais: sem credencial AWS e sem internet depois do primeiro `build`. Portas livres no host: `5433` (Postgres) e `3000` (painel); mude com `POSTGRES_HOST_PORT` e `APP_HOST_PORT` no `.env`.

## Como rodar

Não precisa de credencial AWS nem de internet depois do `build`. Copie `.env.example` para `.env` (opcional: há valores padrão).
O Docker é só o Docker Engine com o plugin Compose (Docker Desktop **ou** Engine dentro do WSL2). `make` é atalho opcional.

### Subir do zero (um comando)
```
docker compose up -d --build
docker compose logs -f loader
```
`up -d` sobe o `db` (Postgres 16) e o `loader`, que migra, verifica o bruto, carrega, transforma e reconcilia, e então **termina**.
O `db` continua de pé (o app do M3 vai depender dele). `logs -f loader` acompanha e **volta sozinho** quando o loader acaba;
para saber que deu certo: a última linha é `loader-1 exited with code 0` (ou `docker compose ps -a` mostra `loader  exited (0)`).
Também funciona só `docker compose up --build` em primeiro plano (ele não devolve o prompt porque o `db` segue rodando:
espere a linha `exited with code 0` e use Ctrl+C, que também para o `db`; para o dia a dia prefira o `up -d`).

No WSL2 desta máquina, prefixe com `wsl -d Ubuntu-22.04 -- bash -lc "cd '/mnt/c/Users/VINICIUS/Desktop/Meus agentes/case_acaso' && <comando>"`.
Se o daemon não responder: `sudo service docker start`.

### Tempos esperados (máquina de dev, WSL2)
| Situação | Tempo |
|---|---|
| Subida fria em pasta limpa (imagem do loader recriada, imagens base já locais; o `build` leva ~35 s e o loader ~85 s em disco montado frio) | ~2 min |
| Subida com cache (`up -d --build` até o loader terminar) | ~30 s (loader ~15 s) |

Dependência de rede só no 1º `build` (imagens `postgres:16` e `python:3.12-slim` e pacotes pip): some o tempo de download.

### O que aparece no fim
Uma linha `[ok] <etapa>  <duração>` por etapa (migrar, verificar bruto, carregar, transformar, reconciliar) e este resumo (valores reais do snapshot):
```
RESUMO DA SUBIDA
  conversas na base ........ 11.621
  usuários (definição v1) .. 2.498
  elegíveis ................ 2.372
  voltaram em 7 dias ....... 566
  taxa oficial ............. 23,86%  (IC 95%: 22,19% a 25,62%; n = 2372)
  linhas rejeitadas ........ 0
  reconciliação ............ OK (9/9 métricas com diferença dentro da tolerância)
```
Qualquer falha encerra com código 1 e `ERRO: etapa '<nome>' falhou: ...`.

### Painel e API (endereços)
Depois que o loader termina, o serviço `app` sobe sozinho:

| Endereço | O que é |
|---|---|
| <http://localhost:3000/> | Tela 1, Retenção: a taxa de retorno em 7 dias por semana ou mês, com faixa de incerteza |
| <http://localhost:3000/fatores> | Tela 2, O que faz voltar: comparações entre grupos parecidos, com intervalo e n |
| <http://localhost:3000/dados> | Tela 3, Confiança nos dados: última carga, conferências e limites |
| <http://localhost:3000/api/saude> | Verificação de saúde (última carga, versão da definição) |

A API (`/api/retencao/*`, `/api/fatores/*`, `/api/semana/decomposicao`, `/api/achados`, `/api/dicionario`, `/api/qualidade`) devolve `{dados, meta}` e lê só `mart.*` e `resultado.*` com o papel `app_ro`. Nenhum texto de conversa, IP ou user-agent sai pela API nem pela tela. Tempos medidos: `docs/desempenho.md`.

Os textos de "achados" e as tabelas de efeitos vêm de `resultado.*`, preenchido pela análise (`python -m analise ...`, ver `analise/__main__.py`). Sem essa etapa, as telas mostram avisos de "ainda não há" em vez de números inventados.

### Testes
Tudo de uma vez (Python no `loader` e TypeScript no `app-testes`, ambos contra o banco do compose):
```
docker compose run --build --rm loader sh -c "python -m loader.migrar && python -m pytest /app/tests -q -p no:cacheprovider"
docker compose --profile testes run --build --rm app-testes
```
(`make test` chama os dois.) Sem Docker, só o app: `cd app && npm ci && npx tsc --noEmit && npx vitest run`; com `DATABASE_URL=postgres://app_ro:<senha>@localhost:5433/acaso` entram também os testes de fumaça contra o banco real.

161 testes; ~70 s na primeira vez (monta o banco real em segundo plano), e menos com o banco de testes em cache (o volume do `db` sobrevive; `down -v` ou `TESTES_SEM_CACHE=1` forçam a reconstrução).

### Zerar tudo
```
docker compose down -v
```
Remove containers, rede e o volume do banco. A porta do Postgres no host é `POSTGRES_HOST_PORT` (padrão 5433).

### FULL_REFRESH
`FULL_REFRESH=1` troca "verificar o snapshot" por "baixar o WildChat-1M (3,4 GB) do Hugging Face para `data/raw/`, reextrair o Brasil com DuckDB e regravar snapshot + checksum", e o `python -m loader.cli` passa a chamar a etapa `extrair`. Exige rede e `data/bruto` gravável, e o compose monta `data/bruto` como somente leitura; por isso rode **fora do compose**, com o `.venv` local e o `db` de pé: `FULL_REFRESH=1 python -m loader.cli` (ou só `FULL_REFRESH=1 python -m loader.extrair`). Lento e pesado em memória; o padrão é o snapshot versionado. Não testado nesta task (baixa 3,4 GB).

### Números do snapshot (definição v1.0.0)
11.621 conversas · 2.385 IPs · 2.498 usuários com uso · **2.372 elegíveis** · 566 voltaram em 7 dias · **taxa oficial 23,86%** (IC 95% 22,19%–25,62%) · 0 rejeitadas · reconciliação bruto × marts: diferença 0 nas 9 métricas.

### Atalhos (Makefile, opcional)
`make up`, `make down`, `make test`, `make reset` chamam os mesmos comandos acima.

## Estrutura de pastas
| Pasta | Conteúdo |
|---|---|
| `data/bruto/` | Snapshot versionado do WildChat (Brasil) e checksum |
| `loader/` | Carga: migra, verifica o bruto, carrega, transforma, reconcilia |
| `sql/migrations/`, `sql/transform/` | Esquema (`stg`, `mart`, `resultado`, `ops`) e transformações |
| `analise/` | Análise estatística que grava em `resultado.*` |
| `classificador/` | Classificação de tema (regras em `seeds/`) |
| `seeds/` | Regras de tema e recusa, planilha de validação manual |
| `app/` | API e telas (Next.js, TypeScript estrito), testes em `app/tests/` |
| `scripts/` | Medição da API (`medir_api.ts`), página de rotulagem (`rotulagem/rotular.html`) |
| `docs/` | Desempenho, arquitetura e custo AWS (`docs/arquitetura/`), figuras |
| `tests/` | Testes Python |
| `.specs/` | Especificações, decisões e registro de execução |

## Solução de problemas
- **Porta ocupada** (`bind: address already in use`): defina `POSTGRES_HOST_PORT` ou `APP_HOST_PORT` no `.env` e suba de novo.
- **Docker no WSL não responde:** `sudo service docker start`; rode os comandos dentro do WSL (ver "Subir do zero").
- **Painel mostra "Não foi possível carregar":** confira `docker compose ps -a` (o loader deve estar `exited (0)`) e `docker compose logs app`; a mensagem de erro na tela traz um código `request_id` que aparece também nos logs.
- **Pouca memória:** suba um serviço por vez (`docker compose up -d db`, depois `loader`, depois `app`) e evite builds em paralelo.
- **Recomeçar do zero:** `docker compose down -v` apaga o volume do banco.

## Estado
M1 (base analítica): carga, marts e reconciliação sobem com um comando. M3/M4: API e três telas conferidas com dados reais; a prova de `docker compose up` do zero com o app e `make test` completo ainda será feita numa rodada única (ver `docs/gate_m4.md`).

## Dados brutos (`data/bruto/`)
- `wildchat_brasil.parquet`: snapshot do extrato Brasil (`country = 'Brazil'`, 11.621 conversas, ~22 MB) do dataset [allenai/WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), versão com toxicidade e PII removidas pelos autores. Snapshot gerado em **10/11/2026**. Integridade em `wildchat_brasil.sha256`.
- **Licença: ODC-BY** (Open Data Commons Attribution). Atribuição: Zhao et al., "WildChat: 1M ChatGPT Interaction Logs in the Wild", ICLR 2024 / Allen Institute for AI.
- `python -m loader.extrair` confere o SHA-256 e falha com mensagem clara se o arquivo foi alterado.
- **`FULL_REFRESH=1`**: baixa o WildChat-1M completo (3,4 GB) do Hugging Face para `data/raw/wildchat/` (reaproveita `data/raw/wildchat/data/*.parquet` se já existir), filtra Brasil com DuckDB e regrava snapshot + checksum. Lento e pesado em memória; o padrão é usar o snapshot.
