.PHONY: help setup venv install migrate makemigrations createsuperuser run test test-bdd test-unit test-integration lint format coverage coverage-domain check-dod seed import-repos generate-md collectstatic clean

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip

help:
	@echo "Repo-Analyst Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup              - Set up development environment (venv + install + migrate)"
	@echo "  venv               - Create virtual environment"
	@echo "  install            - Install dependencies with pip"
	@echo "  migrate            - Run database migrations"
	@echo "  makemigrations     - Create new migrations"
	@echo "  createsuperuser    - Create Django superuser"
	@echo "  run                - Run Django development server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test               - Run all tests"
	@echo "  test-unit          - Run unit tests only"
	@echo "  test-integration   - Run integration tests only"
	@echo "  test-bdd           - Run BDD tests only"
	@echo "  coverage           - Run tests with full coverage report"
	@echo "  coverage-domain    - Check domain coverage (minimum 80%)"
	@echo "  check-dod          - Run Definition of Done checks (all tests + coverage)"
	@echo "  lint               - Run linter (ruff)"
	@echo "  format             - Format code (black + ruff)"
	@echo ""
	@echo "Data Management:"
	@echo "  seed               - Seed initial data (ARTs, Apps, Prompts, Providers)"
	@echo "  import-repos       - Import repositories from CSV"
	@echo "  generate-md        - Generate markdown corpus (usage: make generate-md REPO_ID=1)"
	@echo ""
	@echo "Other:"
	@echo "  collectstatic      - Collect static files"
	@echo "  clean              - Remove generated files"

# Setup and Installation
setup: venv install migrate seed
	@echo "✓ Setup complete! Run 'make run' to start the server"

venv:
	@echo "Creating virtual environment..."
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "✓ Virtual environment created at $(VENV)"

install: venv
	@echo "Installing dependencies..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed"

# Database
migrate:
	@echo "Running migrations..."
	@$(PYTHON_VENV) manage.py migrate

makemigrations:
	@echo "Creating migrations..."
	@$(PYTHON_VENV) manage.py makemigrations

createsuperuser:
	@echo "Creating superuser..."
	@$(PYTHON_VENV) manage.py createsuperuser

# Development Server
run:
	@echo "Starting development server..."
	@$(PYTHON_VENV) manage.py runserver

# Testing
test:
	@echo "Running all tests..."
	@$(VENV_BIN)/pytest -v

test-unit:
	@echo "Running unit tests..."
	@$(VENV_BIN)/pytest src/tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	@$(VENV_BIN)/pytest src/tests/integration/ -v --ds=config.settings

test-bdd:
	@echo "Running BDD tests..."
	@$(VENV_BIN)/pytest src/tests/bdd/ -v --ds=config.settings

coverage:
	@echo "Running tests with coverage..."
	@$(VENV_BIN)/pytest --cov=src --cov-report=html --cov-report=term

coverage-domain:
	@echo "Running tests with domain coverage check (minimum 80%)..."
	@$(VENV_BIN)/pytest --cov=src/domain --cov-report=html --cov-report=term --cov-fail-under=80

# Definition of Done Check
check-dod:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Definition of Done (DoD) Check"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "1. Running linter..."
	@$(VENV_BIN)/ruff check src/ || (echo "✗ Linting failed" && exit 1)
	@echo "✓ Linting passed"
	@echo ""
	@echo "2. Running all unit tests..."
	@$(VENV_BIN)/pytest src/tests/unit/ -v --ds=config.settings || (echo "✗ Unit tests failed" && exit 1)
	@echo "✓ Unit tests passed"
	@echo ""
	@echo "3. Running integration tests..."
	@$(VENV_BIN)/pytest src/tests/integration/ -v --ds=config.settings || (echo "✗ Integration tests failed" && exit 1)
	@echo "✓ Integration tests passed"
	@echo ""
	@echo "4. Running BDD tests..."
	@$(VENV_BIN)/pytest src/tests/bdd/ -v --ds=config.settings || (echo "✗ BDD tests failed" && exit 1)
	@echo "✓ BDD tests passed"
	@echo ""
	@echo "5. Checking domain coverage (minimum 80%)..."
	@$(VENV_BIN)/pytest --cov=src/domain --cov-report=term --cov-fail-under=80 -q || (echo "✗ Domain coverage below 80%" && exit 1)
	@echo "✓ Domain coverage >= 80%"
	@echo ""
	@echo "6. Checking overall coverage..."
	@$(VENV_BIN)/pytest --cov=src --cov-report=html --cov-report=term-missing -q || echo "⚠ Some code not covered"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ✓ DoD Check Complete - All criteria met!"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Coverage report available at: htmlcov/index.html"

# Code Quality
lint:
	@echo "Running linter..."
	@$(VENV_BIN)/ruff check src/

format:
	@echo "Formatting code..."
	@$(VENV_BIN)/ruff check --fix src/
	@$(VENV_BIN)/black src/

# Data Management
seed:
	@echo "Seeding initial data..."
	@$(PYTHON_VENV) manage.py seed_data

import-repos:
	@echo "Importing repositories from CSV..."
	@$(PYTHON_VENV) manage.py import_repositories

generate-md:
ifndef REPO_ID
	@echo "Error: REPO_ID is required. Usage: make generate-md REPO_ID=1"
	@exit 1
endif
	@echo "Generating markdown corpus for repository $(REPO_ID)..."
	@$(PYTHON_VENV) manage.py generate_markdown --repo-id=$(REPO_ID)

# Static Files
collectstatic:
	@echo "Collecting static files..."
	@$(PYTHON_VENV) manage.py collectstatic --noinput

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	@echo "✓ Cleanup complete"

# Quick start for first time users
quickstart: setup
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Repo-Analyst Quick Start Guide"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "1. Create .env file (copy from .env.example and edit)"
	@echo "   cp .env.example .env"
	@echo ""
	@echo "2. Create superuser for admin access"
	@echo "   make createsuperuser"
	@echo ""
	@echo "3. Import test repositories"
	@echo "   make import-repos"
	@echo ""
	@echo "4. Start the development server"
	@echo "   make run"
	@echo ""
	@echo "5. Open browser to http://localhost:8000"
	@echo ""
	@echo "6. Admin interface: http://localhost:8000/admin"
	@echo "   API Explorer: http://localhost:8000/api/v1/"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
