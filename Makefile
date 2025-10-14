# MarkezardAI Makefile
# Cross-platform development commands

.PHONY: help setup dev prod test lint security clean docker-build docker-run

# Default target
help:
	@echo "MarkezardAI Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          Setup project for first time"
	@echo "  install        Install dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev            Start development servers"
	@echo "  prod           Start production servers"
	@echo "  frontend       Start frontend only"
	@echo "  backend        Start backend only"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run all tests"
	@echo "  test-backend   Run backend tests only"
	@echo "  test-frontend  Run frontend tests only"
	@echo "  coverage       Run tests with coverage"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint           Run all linting"
	@echo "  format         Format all code"
	@echo "  security       Run security scans"
	@echo "  audit          Run dependency audits"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-run     Run with Docker Compose"
	@echo "  docker-clean   Clean Docker resources"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean          Clean build artifacts"
	@echo "  logs           Show application logs"

# Setup commands
setup:
	@echo "Setting up MarkezardAI..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please edit with your API keys"; fi
	@$(MAKE) install
	@echo "Setup complete! Run 'make dev' to start development servers"

install:
	@echo "Installing dependencies..."
	@cd backend && python -m venv .venv
	@cd backend && .venv/bin/pip install -r requirements.txt || .venv\\Scripts\\pip install -r requirements.txt
	@cd frontend && npm install
	@echo "Dependencies installed"

# Development commands
dev:
	@echo "Starting development servers..."
	@cd backend && (.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &) || (.venv\\Scripts\\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &)
	@cd frontend && npm run dev &
	@echo "Servers started - Backend: http://localhost:8000, Frontend: http://localhost:3000"

prod:
	@echo "Starting production servers..."
	@cd frontend && npm run build
	@cd backend && (.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &) || (.venv\\Scripts\\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &)
	@cd frontend && npm start &
	@echo "Production servers started"

frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

backend:
	@echo "Starting backend development server..."
	@cd backend && .venv/bin/python -m uvicorn app.main:app --reload || .venv\\Scripts\\python -m uvicorn app.main:app --reload

# Testing commands
test:
	@echo "Running all tests..."
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend:
	@echo "Running backend tests..."
	@cd backend && (.venv/bin/python -m pytest tests/ -v) || (.venv\\Scripts\\python -m pytest tests/ -v)

test-frontend:
	@echo "Running frontend tests..."
	@cd frontend && npm test -- --watchAll=false

coverage:
	@echo "Running tests with coverage..."
	@cd backend && (.venv/bin/python -m pytest tests/ --cov=app --cov-report=html) || (.venv\\Scripts\\python -m pytest tests/ --cov=app --cov-report=html)

# Code quality commands
lint:
	@echo "Running linting..."
	@cd backend && (.venv/bin/python -m flake8 .) || (.venv\\Scripts\\python -m flake8 .)
	@cd frontend && npm run lint

format:
	@echo "Formatting code..."
	@cd backend && (.venv/bin/python -m black .) || (.venv\\Scripts\\python -m black .)
	@cd frontend && npm run lint -- --fix

security:
	@echo "Running security scans..."
	@cd backend && (.venv/bin/python -m bandit -r app/) || (.venv\\Scripts\\python -m bandit -r app/)

audit:
	@echo "Running dependency audits..."
	@cd backend && (.venv/bin/pip-audit) || (.venv\\Scripts\\pip-audit) || echo "pip-audit not available"
	@cd frontend && npm audit

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@docker build -f Dockerfile.backend -t markezardai-backend .
	@docker build -f Dockerfile.frontend -t markezardai-frontend .

docker-run:
	@echo "Starting with Docker Compose..."
	@docker-compose up --build

docker-clean:
	@echo "Cleaning Docker resources..."
	@docker-compose down
	@docker system prune -f

# Utility commands
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf backend/.pytest_cache backend/__pycache__ backend/htmlcov
	@rm -rf frontend/.next frontend/out frontend/build
	@rm -rf frontend/node_modules/.cache
	@echo "Clean complete"

logs:
	@echo "Showing application logs..."
	@docker-compose logs -f

# Health check
health:
	@echo "Checking application health..."
	@curl -f http://localhost:8000/health || echo "Backend not responding"
	@curl -f http://localhost:3000 || echo "Frontend not responding"

# Database commands (if needed in future)
db-migrate:
	@echo "Running database migrations..."
	@echo "No migrations configured yet"

db-seed:
	@echo "Seeding database..."
	@echo "No seed data configured yet"

# Deployment commands
deploy-staging:
	@echo "Deploying to staging..."
	@echo "Configure your staging deployment here"

deploy-prod:
	@echo "Deploying to production..."
	@echo "Configure your production deployment here"
