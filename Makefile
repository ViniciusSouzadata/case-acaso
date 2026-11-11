# Atalhos opcionais: cada alvo chama exatamente os comandos `docker compose` do README ("Como rodar").
# Rodar onde houver `make` e `docker compose` (no WSL desta máquina não há make: use os comandos do README).

# Sobe do zero: db + loader (migra, verifica o bruto, carrega, transforma, reconcilia). O db continua de pé.
up:
	docker compose up -d --build
	docker compose logs -f loader

down:
	docker compose down -v

# Testes: migrar -> pytest, no container loader contra o db do compose.
test:
	docker compose run --build --rm loader sh -c "python -m loader.migrar && python -m pytest /app/tests -q -p no:cacheprovider --durations=10"
	# TypeScript (vitest + fumaça contra o banco do compose); roda depois do Python porque ele aplica as migrações
	docker compose --profile testes run --build --rm app-testes

reset: down up
