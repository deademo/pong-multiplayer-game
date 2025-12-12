.PHONY: help build up down restart logs clean migrate test test-unit test-integration test-cov shell db-shell check-docker start stop status packages

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Pong Game - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

check-docker: ## Check if Docker is running
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)ERROR: Docker is not running!$(NC)"; \
		echo "$(YELLOW)Please start Docker Desktop and try again.$(NC)"; \
		exit 1; \
	fi

build: check-docker ## Build all Docker containers
	@echo "$(BLUE)Building Docker containers...$(NC)"
	docker compose build

up: check-docker ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose up -d
	@echo "$(YELLOW)Waiting for database to be ready...$(NC)"
	@sleep 8
	@echo "$(GREEN)Services started!$(NC)"
	@make migrate
	@echo ""
	@echo "$(GREEN)✓ Game is ready!$(NC)"
	@echo "$(BLUE)Access at: http://localhost:8000$(NC)"

start: up ## Alias for up

down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)Services stopped!$(NC)"

stop: down ## Alias for down

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	@make down
	@make up

clean: ## Remove all containers, volumes, and orphans
	@echo "$(RED)Removing all containers, volumes, and data...$(NC)"
	docker compose down -v --remove-orphans
	@echo "$(GREEN)Cleanup complete!$(NC)"

migrate: check-docker ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker compose run --rm backend python manage.py migrate
	@echo "$(GREEN)Migrations complete!$(NC)"

makemigrations: check-docker ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(NC)"
	docker compose run --rm backend python manage.py makemigrations
	@echo "$(GREEN)Migrations created!$(NC)"

packages: check-docker ## Show installed package versions
	@echo "$(BLUE)Installed Package Versions:$(NC)"
	@docker compose run --rm backend pip list | grep -E "Django|channels|daphne|psycopg2|redis|pytest|websockets"

test: check-docker build ## Run all tests with coverage
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)Starting Pong Game Test Suite$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@echo ""
	docker compose up -d db redis
	@echo "$(YELLOW)Waiting for database...$(NC)"
	@sleep 8
	@make migrate
	@echo ""
	@make packages
	@echo ""
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)Running Unit Tests$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@docker compose run --rm backend pytest tests/unit/ -v --tb=short || true
	@echo ""
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)Running Integration Tests$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@docker compose run --rm backend pytest tests/integration/ -v --tb=short || true
	@echo ""
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)Running All Tests with Coverage$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@docker compose run --rm backend pytest tests/ -v --cov=pong --cov-report=term-missing --tb=short
	@echo ""
	@echo "$(GREEN)===================================$(NC)"
	@echo "$(GREEN)All Tests Complete!$(NC)"
	@echo "$(GREEN)===================================$(NC)"
	@make down

test-unit: check-docker ## Run only unit tests
	@echo "$(BLUE)Running Unit Tests...$(NC)"
	docker compose run --rm backend pytest tests/unit/ -v

test-integration: check-docker ## Run only integration tests (with Redis)
	@echo "$(BLUE)Running Integration Tests with Redis...$(NC)"
	@echo "$(YELLOW)Starting test environment...$(NC)"
	docker compose -f docker-compose.integration.yml up --abort-on-container-exit --exit-code-from backend-test
	@echo "$(YELLOW)Cleaning up test environment...$(NC)"
	docker compose -f docker-compose.integration.yml down -v
	@echo "$(GREEN)Integration tests complete!$(NC)"

test-integration-dev: check-docker ## Run integration tests in development mode (keeps containers)
	@echo "$(BLUE)Running Integration Tests (Dev Mode)...$(NC)"
	docker compose -f docker-compose.integration.yml up --build

test-frontend: check-docker ## Run frontend JavaScript unit tests with Vitest
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)Running Frontend Unit Tests$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(YELLOW)Using Vitest (fastest JS testing framework)$(NC)"
	@echo ""
	cd frontend-tests && docker-compose -f docker-compose.frontend-tests.yml up --abort-on-container-exit --exit-code-from frontend-tests
	@echo ""
	@echo "$(GREEN)Frontend tests complete!$(NC)"

test-frontend-watch: check-docker ## Run frontend tests in watch mode
	@echo "$(BLUE)Starting frontend tests in watch mode...$(NC)"
	cd frontend-tests && docker-compose -f docker-compose.frontend-tests.yml run --rm frontend-tests npm run test:watch

test-frontend-coverage: check-docker ## Run frontend tests with coverage report
	@echo "$(BLUE)Running frontend tests with coverage...$(NC)"
	cd frontend-tests && docker-compose -f docker-compose.frontend-tests.yml run --rm frontend-tests npm run test:coverage
	@echo "$(GREEN)Coverage report generated in frontend-tests/coverage/$(NC)"

test-integration-real: check-docker ## Run integration tests against REAL Daphne server with Redis
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(BLUE)Running REAL Integration Tests$(NC)"
	@echo "$(BLUE)======================================$(NC)"
	@echo "$(YELLOW)This uses:$(NC)"
	@echo "  - Real Daphne ASGI server"
	@echo "  - Real Redis channel layer"
	@echo "  - Real WebSocket connections"
	@echo "$(BLUE)======================================$(NC)"
	@echo ""
	docker compose -f docker-compose.integration-server.yml up --abort-on-container-exit --exit-code-from test-client
	@echo ""
	@echo "$(YELLOW)Cleaning up test environment...$(NC)"
	docker compose -f docker-compose.integration-server.yml down -v
	@echo "$(GREEN)Real integration tests complete!$(NC)"

test-cov: check-docker ## Run tests with coverage report
	@echo "$(BLUE)Running Tests with Coverage...$(NC)"
	docker compose run --rm backend pytest tests/ -v --cov=pong --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

logs: ## Show logs from all services
	docker compose logs -f

logs-backend: ## Show backend logs only
	docker compose logs -f backend

logs-db: ## Show database logs only
	docker compose logs -f db

logs-redis: ## Show redis logs only
	docker compose logs -f redis

shell: check-docker ## Open Python shell in backend container
	docker compose run --rm backend python manage.py shell

bash: check-docker ## Open bash shell in backend container
	docker compose run --rm backend bash

db-shell: check-docker ## Open PostgreSQL shell
	docker compose exec db psql -U pong -d pong

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker compose ps

createsuperuser: check-docker ## Create Django superuser
	docker compose run --rm backend python manage.py createsuperuser

install: ## Full installation (build, start, migrate)
	@echo "$(BLUE)===================================$(NC)"
	@echo "$(BLUE)Installing Pong Game$(NC)"
	@echo "$(BLUE)===================================$(NC)"
	@make build
	@make up
	@echo ""
	@echo "$(GREEN)===================================$(NC)"
	@echo "$(GREEN)Installation Complete!$(NC)"
	@echo "$(GREEN)===================================$(NC)"
	@echo ""
	@echo "$(BLUE)Game is running at: http://localhost:8000$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  - Run tests: $(GREEN)make test$(NC)"
	@echo "  - View logs: $(GREEN)make logs$(NC)"
	@echo "  - Create admin: $(GREEN)make createsuperuser$(NC)"
	@echo "  - Stop services: $(GREEN)make stop$(NC)"

dev: ## Start development environment with logs
	@make up
	@make logs

reset: ## Reset everything (clean and install)
	@echo "$(YELLOW)This will delete all data. Continue? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@make clean
	@make install

# Default target
.DEFAULT_GOAL := help
