# Fullstack Monolith Transformation Makefile
# Enterprise-grade development, testing, and deployment commands

.PHONY: help install dev build test lint format clean docker k8s

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation commands
install: ## Install all dependencies
	@echo "Installing root dependencies..."
	npm install
	@echo "Installing web app dependencies..."
	cd apps/web && npm install
	@echo "Installing API dependencies..."
	cd apps/api && pip install -r requirements/development.txt
	@echo "Installing shared packages..."
	$(MAKE) install-packages

install-packages: ## Install shared packages in development mode
	@echo "Installing shared packages..."
	cd packages/core && pip install -e .
	cd packages/auth && pip install -e .
	cd packages/cache && pip install -e .
	cd packages/database && pip install -e .
	cd packages/config && pip install -e .
	cd packages/api-client && npm install

# Development commands
dev: ## Start development servers
	npm run dev

dev-api: ## Start Django API development server
	cd apps/api && python manage.py runserver

dev-web: ## Start Next.js development server
	cd apps/web && npm run dev

dev-docker: ## Start development environment with Docker
	docker-compose -f docker-compose.dev.yml up --build

# Build commands
build: ## Build all applications
	npm run build

build-web: ## Build Next.js web application
	cd apps/web && npm run build

build-api: ## Build Django API (collect static files)
	cd apps/api && python manage.py collectstatic --noinput

build-docker: ## Build Docker images
	docker-compose build

# Testing commands
test: ## Run all tests
	@echo "Running web tests..."
	cd apps/web && npm test -- --watchAll=false
	@echo "Running API tests..."
	cd apps/api && python -m pytest
	@echo "Running package tests..."
	$(MAKE) test-packages

test-web: ## Run Next.js tests
	cd apps/web && npm test -- --watchAll=false

test-api: ## Run Django API tests
	cd apps/api && python -m pytest

test-packages: ## Run shared package tests
	cd packages/core && python -m pytest
	cd packages/auth && python -m pytest
	cd packages/cache && python -m pytest
	cd packages/database && python -m pytest
	cd packages/config && python -m pytest

test-e2e: ## Run end-to-end tests
	cd tests/e2e && npx playwright test

test-coverage: ## Run tests with coverage
	cd apps/web && npm test -- --coverage --watchAll=false
	cd apps/api && python -m pytest --cov=. --cov-report=html
	cd packages/core && python -m pytest --cov=. --cov-report=html

# Code quality commands
lint: ## Run linting for all code
	npm run lint

lint-web: ## Run ESLint for Next.js
	cd apps/web && npm run lint

lint-api: ## Run Flake8 for Django API
	cd apps/api && flake8 .

lint-packages: ## Run linting for shared packages
	cd packages/core && flake8 .
	cd packages/auth && flake8 .
	cd packages/cache && flake8 .
	cd packages/database && flake8 .
	cd packages/config && flake8 .

format: ## Format all code
	npm run format

format-web: ## Format Next.js code
	cd apps/web && npm run format

format-api: ## Format Django API code
	cd apps/api && black . && isort .

format-packages: ## Format shared package code
	cd packages/core && black . && isort .
	cd packages/auth && black . && isort .
	cd packages/cache && black . && isort .
	cd packages/database && black . && isort .
	cd packages/config && black . && isort .

# Database commands
db-migrate: ## Run Django migrations
	cd apps/api && python manage.py migrate

db-makemigrations: ## Create Django migrations
	cd apps/api && python manage.py makemigrations

db-reset: ## Reset database (WARNING: destroys data)
	cd apps/api && python manage.py flush --noinput

db-seed: ## Seed database with sample data
	cd apps/api && python manage.py loaddata fixtures/sample_data.json

db-backup: ## Backup database
	cd apps/api && python manage.py dumpdata > backup_$$(date +%Y%m%d_%H%M%S).json

# Cleanup commands
clean: ## Clean all build artifacts
	npm run clean

clean-web: ## Clean Next.js build artifacts
	cd apps/web && rm -rf .next node_modules/.cache

clean-api: ## Clean Django build artifacts
	cd apps/api && find . -name "*.pyc" -delete && find . -name "__pycache__" -delete

clean-docker: ## Clean Docker containers and images
	docker-compose down --volumes --remove-orphans
	docker system prune -f

# Docker commands
docker-build: ## Build Docker images
	docker-compose build

docker-build-prod: ## Build production Docker images
	docker-compose -f docker-compose.prod.yml build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-up-prod: ## Start production Docker containers
	docker-compose -f docker-compose.prod.yml up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-down-prod: ## Stop production Docker containers
	docker-compose -f docker-compose.prod.yml down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-logs-prod: ## View production Docker logs
	docker-compose -f docker-compose.prod.yml logs -f

docker-shell-api: ## Open shell in Django API container
	docker-compose exec django-api bash

docker-shell-web: ## Open shell in Next.js container
	docker-compose exec nextjs-web bash

docker-shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d fullstack_blog

docker-shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

docker-restart: ## Restart all Docker containers
	docker-compose restart

docker-restart-api: ## Restart Django API container
	docker-compose restart django-api

docker-restart-web: ## Restart Next.js container
	docker-compose restart nextjs-web

docker-clean: ## Clean Docker containers and images
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	docker volume prune -f

docker-clean-all: ## Clean everything Docker related
	docker-compose down --volumes --remove-orphans
	docker system prune -af
	docker volume prune -f

docker-health: ## Check Docker container health
	docker-compose ps
	@echo "\nContainer health status:"
	@docker-compose exec django-api curl -f http://localhost:8000/health/ || echo "Django API unhealthy"
	@docker-compose exec nextjs-web curl -f http://localhost:3000/api/health || echo "Next.js unhealthy"

docker-migrate: ## Run Django migrations in Docker
	docker-compose exec django-api python manage.py migrate

docker-collectstatic: ## Collect static files in Docker
	docker-compose exec django-api python manage.py collectstatic --noinput

docker-createsuperuser: ## Create Django superuser in Docker
	docker-compose exec django-api python manage.py createsuperuser

docker-backup-db: ## Backup database from Docker
	docker-compose exec postgres pg_dump -U postgres fullstack_blog > backup_$(shell date +%Y%m%d_%H%M%S).sql

docker-restore-db: ## Restore database to Docker (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE=filename.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U postgres fullstack_blog < $(BACKUP_FILE)

# Kubernetes commands
k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f infrastructure/k8s/

k8s-delete: ## Delete Kubernetes resources
	kubectl delete -f infrastructure/k8s/

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods,services,deployments

k8s-logs-api: ## View Django API logs in Kubernetes
	kubectl logs -l app=django-api -f

k8s-logs-web: ## View Next.js logs in Kubernetes
	kubectl logs -l app=nextjs-web -f

# Security commands
security-scan: ## Run security scans
	cd apps/web && npm audit
	cd apps/api && safety check
	cd apps/api && bandit -r .

security-update: ## Update dependencies for security
	cd apps/web && npm audit fix
	cd apps/api && pip-audit --fix

# Cache commands
cache-setup: ## Setup Redis cluster for distributed caching
	@echo "Setting up Redis cluster..."
	cd infrastructure/redis && ./setup-cluster.sh

cache-setup-windows: ## Setup Redis cluster for distributed caching (Windows)
	@echo "Setting up Redis cluster..."
	cd infrastructure/redis && powershell -ExecutionPolicy Bypass -File setup-cluster.ps1

cache-start: ## Start Redis cluster
	docker-compose --profile cluster up -d

cache-stop: ## Stop Redis cluster
	docker-compose --profile cluster down

cache-status: ## Check Redis cluster status
	docker exec redis-cluster-node-1 redis-cli -p 7000 cluster info

cache-benchmark: ## Run cache performance benchmarks
	python tools/cache/cache-benchmark.py --config tools/cache/cache-benchmark-config.json --format text

cache-monitor: ## Start cache monitoring
	python tools/cache/cache-monitor.py --config tools/cache/cache-monitor-config.json --daemon

cache-report: ## Generate cache performance report
	python tools/cache/cache-monitor.py --config tools/cache/cache-monitor-config.json --report

cache-metrics: ## Export cache metrics in Prometheus format
	python tools/cache/cache-monitor.py --config tools/cache/cache-monitor-config.json --prometheus

cache-test: ## Run cache performance tests
	cd packages/cache && python -m pytest tests/test_performance.py -v

cache-warm: ## Warm cache with frequently accessed data
	cd apps/api && python manage.py warm_cache

cache-clear: ## Clear all cache data
	docker-compose exec redis redis-cli FLUSHALL
	@echo "Cache cleared successfully"

cache-info: ## Show cache information and statistics
	docker-compose exec redis redis-cli INFO memory
	docker-compose exec redis redis-cli INFO stats

# Monitoring commands
monitor-logs: ## View application logs
	tail -f apps/api/logs/django.log apps/web/logs/nextjs.log

monitor-metrics: ## View application metrics (requires Prometheus)
	@echo "Metrics available at: http://localhost:9090"

monitor-cache: ## Monitor cache performance in real-time
	python tools/cache/cache-monitor.py --config tools/cache/cache-monitor-config.json

# Production commands
prod-deploy: ## Deploy to production
	@echo "Deploying to production..."
	$(MAKE) test
	$(MAKE) build-docker
	$(MAKE) k8s-deploy

prod-rollback: ## Rollback production deployment
	kubectl rollout undo deployment/django-api
	kubectl rollout undo deployment/nextjs-web

prod-status: ## Check production status
	kubectl get pods -l environment=production

# Utility commands
generate-types: ## Generate TypeScript types from Django models
	cd apps/api && python manage.py generate_typescript_types

generate-api-client: ## Generate API client from OpenAPI spec
	cd packages/api-client && openapi-generator-cli generate -i ../../apps/api/openapi.json -g typescript-axios -o src/generated

setup-dev: ## Setup development environment
	$(MAKE) install
	$(MAKE) db-migrate
	$(MAKE) db-seed
	@echo "Development environment setup complete!"

setup-prod: ## Setup production environment
	$(MAKE) install
	$(MAKE) build
	$(MAKE) db-migrate
	@echo "Production environment setup complete!"

# Health checks
health-check: ## Check application health
	@echo "Checking Django API health..."
	curl -f http://localhost:8000/health/ || echo "Django API not responding"
	@echo "Checking Next.js health..."
	curl -f http://localhost:3000/api/health || echo "Next.js not responding"

# Documentation
docs-build: ## Build documentation
	cd docs && mkdocs build

docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

docs-deploy: ## Deploy documentation
	cd docs && mkdocs gh-deploy