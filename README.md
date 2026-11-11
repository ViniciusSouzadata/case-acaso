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
