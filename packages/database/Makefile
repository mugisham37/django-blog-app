# Makefile for enterprise database package

.PHONY: help install install-dev test test-verbose lint format clean build upload docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  upload       - Upload package to PyPI"
	@echo "  docs         - Generate documentation"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev,monitoring,testing]

# Testing targets
test:
	python run_tests.py

test-verbose:
	python run_tests.py --verbosity=2

test-coverage:
	python -m pytest tests/ --cov=enterprise_database --cov-report=html --cov-report=term-missing

# Code quality targets
lint:
	flake8 src/enterprise_database tests/
	black --check src/enterprise_database tests/
	isort --check-only src/enterprise_database tests/

format:
	black src/enterprise_database tests/
	isort src/enterprise_database tests/

# Build targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

build: clean
	python setup.py sdist bdist_wheel

upload: build
	twine upload dist/*

# Documentation targets
docs:
	@echo "Generating documentation..."
	@echo "# Enterprise Database Package Documentation" > docs.md
	@echo "" >> docs.md
	@echo "## Installation" >> docs.md
	@echo "" >> docs.md
	@echo "\`\`\`bash" >> docs.md
	@echo "pip install enterprise-database" >> docs.md
	@echo "\`\`\`" >> docs.md
	@echo "" >> docs.md
	@echo "## Usage" >> docs.md
	@echo "" >> docs.md
	@echo "See README.md for detailed usage instructions." >> docs.md

# Development targets
dev-setup: install-dev
	pre-commit install

check: lint test

# Database management targets
migrate:
	python -m enterprise_database.cli migrate

seed:
	python -m enterprise_database.cli seed

backup:
	python -m enterprise_database.cli backup

monitor:
	python -m enterprise_database.cli monitor --stats

# Docker targets
docker-build:
	docker build -t enterprise-database .

docker-test:
	docker run --rm enterprise-database python run_tests.py

# CI/CD targets
ci: lint test-coverage

# Release targets
release-patch:
	bump2version patch
	git push origin main --tags

release-minor:
	bump2version minor
	git push origin main --tags

release-major:
	bump2version major
	git push origin main --tags