.PHONY: help build up down restart logs shell dbshell migrate makemigrations \
       superuser seed flush test test-frontend lint format clean

COMPOSE = docker compose
BACKEND = $(COMPOSE) exec backend
FRONTEND = $(COMPOSE) exec frontend

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

build: ## Build all Docker images
	$(COMPOSE) build

up: ## Start all services in detached mode
	$(COMPOSE) up -d

down: ## Stop and remove all containers
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

logs: ## Follow logs from all services
	$(COMPOSE) logs -f

logs-backend: ## Follow backend logs
	$(COMPOSE) logs -f backend

logs-celery: ## Follow Celery worker logs
	$(COMPOSE) logs -f celery_worker

logs-frontend: ## Follow frontend logs
	$(COMPOSE) logs -f frontend

ps: ## List running containers
	$(COMPOSE) ps

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

shell: ## Open Django shell_plus
	$(BACKEND) python manage.py shell_plus

dbshell: ## Open database shell
	$(BACKEND) python manage.py dbshell

migrate: ## Run database migrations
	$(BACKEND) python manage.py migrate

makemigrations: ## Create new migration files
	$(BACKEND) python manage.py makemigrations

superuser: ## Create a Django superuser
	$(BACKEND) python manage.py createsuperuser

seed: ## Load sample fixture data
	$(BACKEND) python manage.py loaddata fixtures/*.json

flush: ## Reset database (destroy all data)
	$(BACKEND) python manage.py flush --no-input

collectstatic: ## Collect static files
	$(BACKEND) python manage.py collectstatic --noinput

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run backend tests with pytest
	$(BACKEND) pytest -v --tb=short

test-coverage: ## Run backend tests with coverage report
	$(BACKEND) pytest --cov=apps --cov-report=term-missing --cov-report=html

test-frontend: ## Run frontend tests
	$(FRONTEND) npm test -- --watchAll=false

test-all: test test-frontend ## Run all tests

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run all linters
	$(BACKEND) flake8 .
	$(BACKEND) mypy apps/
	$(FRONTEND) npx eslint src/

format: ## Auto-format code
	$(BACKEND) black .
	$(BACKEND) isort .
	$(FRONTEND) npx prettier --write "src/**/*.{js,jsx,css}"

check: ## Run format check without modifying files
	$(BACKEND) black --check .
	$(BACKEND) isort --check-only .

# ---------------------------------------------------------------------------
# Elasticsearch
# ---------------------------------------------------------------------------

reindex: ## Rebuild Elasticsearch indices
	$(BACKEND) python manage.py search_index --rebuild -f

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------

celery-worker: ## Start Celery worker (foreground)
	$(BACKEND) celery -A config worker -l info

celery-beat: ## Start Celery beat scheduler (foreground)
	$(BACKEND) celery -A config beat -l info

celery-flower: ## Start Celery Flower monitoring
	$(COMPOSE) exec celery_worker celery -A config flower --port=5555

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove Python cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage

clean-docker: ## Remove all Docker volumes and orphan containers
	$(COMPOSE) down -v --remove-orphans

clean-all: clean clean-docker ## Full cleanup
