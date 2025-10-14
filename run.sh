#!/bin/bash

# MarkezardAI Run Script
# This script helps you run the application in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your actual API keys and configuration"
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
}

# Function to run development mode
run_dev() {
    print_status "Starting MarkezardAI in development mode..."
    check_env_file
    
    # Start backend
    print_status "Starting backend..."
    cd backend
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        python -m venv .venv
    fi
    
    source .venv/bin/activate || .venv\Scripts\activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    print_status "Starting frontend..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Development servers started!"
    print_status "Backend: http://localhost:8000"
    print_status "Frontend: http://localhost:3000"
    print_status "API Docs: http://localhost:8000/docs"
    
    # Wait for user to stop
    print_status "Press Ctrl+C to stop all servers..."
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
}

# Function to run with Docker
run_docker() {
    print_status "Starting MarkezardAI with Docker..."
    check_env_file
    
    # Build and start containers
    docker-compose up --build
}

# Function to run production mode
run_prod() {
    print_status "Starting MarkezardAI in production mode..."
    check_env_file
    
    # Build frontend
    print_status "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Start backend
    print_status "Starting backend..."
    cd backend
    source .venv/bin/activate || .venv\Scripts\activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    print_status "Starting frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    print_success "Production servers started!"
    print_status "Application: http://localhost:3000"
    print_status "API: http://localhost:8000"
    
    # Wait for user to stop
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Backend tests
    print_status "Running backend tests..."
    cd backend
    if [ -d ".venv" ]; then
        source .venv/bin/activate || .venv\Scripts\activate
    fi
    python -m pytest tests/ -v
    cd ..
    
    # Frontend tests
    print_status "Running frontend tests..."
    cd frontend
    if [ -d "node_modules" ]; then
        npm test -- --watchAll=false
    else
        print_warning "Frontend dependencies not installed. Run 'npm install' first."
    fi
    cd ..
    
    print_success "Tests completed!"
}

# Function to run linting and security checks
run_checks() {
    print_status "Running code quality checks..."
    
    # Backend checks
    print_status "Running backend checks..."
    cd backend
    if [ -d ".venv" ]; then
        source .venv/bin/activate || .venv\Scripts\activate
    fi
    
    print_status "Running black formatter..."
    black . --check || true
    
    print_status "Running flake8 linter..."
    flake8 . || true
    
    print_status "Running bandit security scan..."
    bandit -r app/ || true
    
    print_status "Running pip-audit..."
    pip-audit || true
    cd ..
    
    # Frontend checks
    print_status "Running frontend checks..."
    cd frontend
    if [ -d "node_modules" ]; then
        print_status "Running ESLint..."
        npm run lint || true
        
        print_status "Running npm audit..."
        npm audit || true
    fi
    cd ..
    
    print_success "Code quality checks completed!"
}

# Function to setup the project
setup_project() {
    print_status "Setting up MarkezardAI project..."
    
    # Check for required tools
    command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed."; exit 1; }
    command -v node >/dev/null 2>&1 || { print_error "Node.js is required but not installed."; exit 1; }
    command -v npm >/dev/null 2>&1 || { print_error "npm is required but not installed."; exit 1; }
    
    # Setup backend
    print_status "Setting up backend..."
    cd backend
    python -m venv .venv
    source .venv/bin/activate || .venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
    
    # Setup frontend
    print_status "Setting up frontend..."
    cd frontend
    npm install
    cd ..
    
    # Create .env file
    check_env_file
    
    print_success "Project setup completed!"
    print_status "Next steps:"
    print_status "1. Edit .env file with your API keys"
    print_status "2. Run './run.sh dev' to start development servers"
    print_status "3. Visit http://localhost:3000 to see the application"
}

# Function to show help
show_help() {
    echo "MarkezardAI Run Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev      Start development servers (default)"
    echo "  prod     Start production servers"
    echo "  docker   Start with Docker Compose"
    echo "  test     Run all tests"
    echo "  check    Run linting and security checks"
    echo "  setup    Setup the project for first time"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev     # Start development mode"
    echo "  $0 docker  # Start with Docker"
    echo "  $0 test    # Run tests"
}

# Main script logic
case "${1:-dev}" in
    "dev")
        run_dev
        ;;
    "prod")
        run_prod
        ;;
    "docker")
        run_docker
        ;;
    "test")
        run_tests
        ;;
    "check")
        run_checks
        ;;
    "setup")
        setup_project
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
