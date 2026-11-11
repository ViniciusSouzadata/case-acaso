# Rodar a partir do WSL (ou onde houver docker compose).
up:
	docker compose up --build --abort-on-container-exit

down:
	docker compose down -v

# Os testes entram nas tasks T-103 em diante (pytest sera adicionado ao loader).
test:
	docker compose run --build loader python -m pytest /app/tests

reset: down up
