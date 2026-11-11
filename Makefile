# Rodar a partir do WSL (ou onde houver docker compose).
up:
	docker compose up --build --abort-on-container-exit

down:
	docker compose down -v

# Testes: migrar -> pytest, no container loader contra o db do compose.
test:
	docker compose run --build --rm loader sh -c "python -m loader.migrar && python -m pytest /app/tests -v -p no:cacheprovider --durations=10"

reset: down up
