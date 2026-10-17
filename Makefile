APP_SERVICE := client-deribit
DB_SERVICE := postgres
QUEUE_SERVICE := redis

-include .env

.PHONY: up-all up down clean migrate-up migrate-down migration psql api worker beat test test-db lint fmt

# BASE

up-all:
	docker compose up -d --build

up:
	docker compose up -d --wait $(DB_SERVICE) $(QUEUE_SERVICE)

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

# SCHEDULE

api:
	uv run uvicorn deribit_client.api.app:create_app --factory --reload

worker:
	uv run celery -A deribit_client.worker.app worker --loglevel=info --concurrency=2

beat:
	uv run celery -A deribit_client.worker.app beat --loglevel=info

# TESTS

test:
	uv run pytest

test-db:
	-docker compose exec $(DB_SERVICE) createdb -U $(DB_USER) $(DB_NAME)_test
	DB_NAME=$(DB_NAME)_test uv run alembic upgrade head

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests

fmt:
	uv run ruff check --fix --exit-zero .
	uv run ruff format .