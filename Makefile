APP_SERVICE := client-deribit
DB_SERVICE := postgres
DB_VOLUME := $(DB_SERVICE)_data

-include .env

.PHONY: up down clean migrate-up migrate-down migration psql

# BASE

up:
	docker compose up -d --wait $(DB_SERVICE)

down:
	docker compose down

clean:
	docker compose down -v

# DATABASE

migrate-up:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

migration: # make migration m="name"
	uv run alembic revision --autogenerate -m "$(m)"

psql:
	docker compose exec $(DB_SERVICE) psql -U $(DB_USER) -d $(DB_NAME)