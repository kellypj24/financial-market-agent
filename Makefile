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
	$(PYTEST) stock_tracker/tests -v

# Run tests with coverage
test-cov:
	$(PYTEST) stock_tracker/tests -v --cov=stock_tracker --cov-report=term-missing

# Run linters
lint:
	$(FLAKE8) stock_tracker
	$(MYPY) stock_tracker

# Format code
format:
	$(BLACK) stock_tracker
	$(ISORT) stock_tracker

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
	$(PYTHON) -m stock_tracker.tests.test_data_fetcher 