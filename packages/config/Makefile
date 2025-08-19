# Makefile for enterprise configuration package

.PHONY: help install install-dev test test-coverage lint format clean build publish docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package
	pip install -e .

install-dev:  ## Install package with development dependencies
	pip install -e ".[dev]"

test:  ## Run tests
	pytest tests/ -v

test-coverage:  ## Run tests with coverage
	pytest tests/ --cov=enterprise_config --cov-report=html --cov-report=term-missing

lint:  ## Run linting
	flake8 src/enterprise_config tests/
	mypy src/enterprise_config

format:  ## Format code
	black src/enterprise_config tests/
	isort src/enterprise_config tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	python -m build

publish:  ## Publish to PyPI
	python -m twine upload dist/*

docs:  ## Generate documentation
	cd docs && make html

validate-config:  ## Validate example configurations
	enterprise-config validate --config-path examples/config/

show-config:  ## Show example configuration
	enterprise-config show --config-path examples/config/ --environment development

# Development commands
dev-setup:  ## Set up development environment
	pip install -e ".[dev]"
	pre-commit install

dev-test:  ## Run development tests
	pytest tests/ -v --tb=short

dev-watch:  ## Watch for changes and run tests
	ptw tests/ -- -v --tb=short