# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

COMPOSE ?= docker compose

.PHONY: up down build migrate seed test lint logs

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down --remove-orphans

build:
	$(COMPOSE) build

migrate:
	$(COMPOSE) exec backend alembic upgrade head

seed:
	curl -s -X POST http://localhost/api/v1/demo/seed \
		-H 'Content-Type: application/json' \
		-d '{"intensity": 6}'

test:
	$(COMPOSE) run --rm backend pytest --cov=src --cov-report=term-missing

lint:
	$(COMPOSE) run --rm backend sh -c "ruff check . && ruff format --check . && mypy src && bandit -q -r src"
	$(COMPOSE) run --rm frontend npm run build

logs:
	$(COMPOSE) logs -f