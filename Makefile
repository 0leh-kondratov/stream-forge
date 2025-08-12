.PHONY: dev test lint install-pre-commit

dev:
	@echo "Starting development environment..."
	# Placeholder for starting local services, e.g.:
	# docker compose up -d

test:
	@echo "Running tests..."
	pytest

lint:
	@echo "Running linters and formatters..."
	pre-commit run --all-files

install-pre-commit:
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
