.PHONY: test lint format clean install

# Python environment
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Development tools
BLACK = $(VENV)/bin/black
ISORT = $(VENV)/bin/isort
FLAKE8 = $(VENV)/bin/flake8
MYPY = $(VENV)/bin/mypy
PYTEST = $(VENV)/bin/pytest

# Default target
all: install

# Create virtual environment and install dependencies
install:
	python -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install poetry
	poetry install

# Run tests
test:
	poetry run pytest stock_tracker/tests -v

# Run tests with coverage
test-cov:
	poetry run pytest stock_tracker/tests -v --cov=stock_tracker --cov-report=term-missing

# Run linters
lint:
	poetry run flake8 stock_tracker
	poetry run mypy stock_tracker

# Format code
format:
	poetry run black stock_tracker
	poetry run isort stock_tracker

# Clean up
clean:
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run demo
demo:
	poetry run python -m stock_tracker.tests.test_data_fetcher 