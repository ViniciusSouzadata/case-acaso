# Case Acaso: retenção de um assistente de IA

Repositório privado. Base analítica (Postgres 16) + carga (Python) + app (Next.js, em milestone futuro).

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

### Testes
```
docker compose run --build --rm loader sh -c "python -m loader.migrar && python -m pytest /app/tests -q -p no:cacheprovider"
```
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

## Estado
M1 (base analítica): carga, marts e reconciliação sobem com um comando. `mart.calc_retencao` foi reescrita em conjuntos (migração 006): a transformação do snapshot real caiu de ~118 s para ~3 s sem mudar nenhum resultado.

## Dados brutos (`data/bruto/`)
- `wildchat_brasil.parquet`: snapshot do extrato Brasil (`country = 'Brazil'`, 11.621 conversas, ~22 MB) do dataset [allenai/WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), versão com toxicidade e PII removidas pelos autores. Snapshot gerado em **10/11/2026**. Integridade em `wildchat_brasil.sha256`.
- **Licença: ODC-BY** (Open Data Commons Attribution). Atribuição: Zhao et al., "WildChat: 1M ChatGPT Interaction Logs in the Wild", ICLR 2024 / Allen Institute for AI.
- `python -m loader.extrair` confere o SHA-256 e falha com mensagem clara se o arquivo foi alterado.
- **`FULL_REFRESH=1`**: baixa o WildChat-1M completo (3,4 GB) do Hugging Face para `data/raw/wildchat/` (reaproveita `data/raw/wildchat/data/*.parquet` se já existir), filtra Brasil com DuckDB e regrava snapshot + checksum. Lento e pesado em memória; o padrão é usar o snapshot.
