.PHONY: help install dev test lint format clean docker-up docker-down migrate

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies
	pip install -e .[dev]
	cd apps/admin && npm install
	pre-commit install

dev:  ## Start all services in development mode
	docker compose up --build

test:  ## Run all tests
	pytest --cov --cov-report=html

lint:  ## Run linters
	ruff check apps/ libs/
	black --check apps/ libs/
	mypy apps/ libs/

format:  ## Format code
	ruff check --fix apps/ libs/
	black apps/ libs/

clean:  ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov

docker-up:  ## Start Docker services
	docker compose up -d

docker-down:  ## Stop Docker services
	docker compose down

docker-logs:  ## View Docker logs
	docker compose logs -f

migrate:  ## Run database migrations
	alembic -c libs/database/alembic.ini upgrade head

migrate-create:  ## Create new migration (use: make migrate-create MSG="description")
	alembic -c libs/database/alembic.ini revision --autogenerate -m "$(MSG)"
