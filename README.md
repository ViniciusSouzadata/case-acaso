# Case Acaso: retenção de um assistente de IA

Repositório privado. Base analítica (Postgres 16) + carga (Python) + app (Next.js, em milestone futuro).

## Como rodar

Não precisa de credencial AWS. Copie `.env.example` para `.env` (opcional: há valores padrão).

### Opção 1: Docker Desktop
```
docker compose up --build --abort-on-container-exit
docker compose down -v
```

### Opção 2: Docker Engine dentro do WSL2 (Windows sem Docker Desktop)
```
wsl -d Ubuntu-22.04 -- bash -lc "cd '/mnt/c/Users/VINICIUS/Desktop/Meus agentes/case_acaso' && docker compose up --build --abort-on-container-exit"
wsl -d Ubuntu-22.04 -- bash -lc "cd '/mnt/c/Users/VINICIUS/Desktop/Meus agentes/case_acaso' && docker compose down -v"
```
Se o daemon não responder: `sudo service docker start`.

Atalhos (Makefile): `make up`, `make down`, `make test`, `make reset`.

A porta do Postgres no host é `POSTGRES_HOST_PORT` (padrão 5433).

## Estado
T-101: esqueleto. O `loader` só conecta no `db` e imprime a versão do Postgres.

## Dados brutos (`data/bruto/`)
- `wildchat_brasil.parquet`: snapshot do extrato Brasil (`country = 'Brazil'`, 11.621 conversas, ~22 MB) do dataset [allenai/WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), versão com toxicidade e PII removidas pelos autores. Snapshot gerado em **10/11/2026**. Integridade em `wildchat_brasil.sha256`.
- **Licença: ODC-BY** (Open Data Commons Attribution). Atribuição: Zhao et al., "WildChat: 1M ChatGPT Interaction Logs in the Wild", ICLR 2024 / Allen Institute for AI.
- `python -m loader.extrair` confere o SHA-256 e falha com mensagem clara se o arquivo foi alterado.
- **`FULL_REFRESH=1`**: baixa o WildChat-1M completo (3,4 GB) do Hugging Face para `data/raw/wildchat/` (reaproveita `data/raw/wildchat/data/*.parquet` se já existir), filtra Brasil com DuckDB e regrava snapshot + checksum. Lento e pesado em memória; o padrão é usar o snapshot.
