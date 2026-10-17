.PHONY: up down logs build test lint typecheck

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

test:
	docker compose run --rm backend pytest
	docker compose run --rm frontend vitest run

lint:
	docker compose run --rm backend ruff check .
	docker compose run --rm backend ruff format --check .

typecheck:
	docker compose run --rm backend mypy backend
	docker compose run --rm frontend tsc --noEmit
