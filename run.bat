@echo off
REM MarkezardAI Run Script for Windows
REM This script helps you run the application in different modes

setlocal enabledelayedexpansion

REM Function to print status messages
:print_status
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

REM Function to check if .env file exists
:check_env_file
if not exist .env (
    call :print_warning ".env file not found. Creating from .env.example..."
    if exist .env.example (
        copy .env.example .env
        call :print_warning "Please edit .env file with your actual API keys and configuration"
    ) else (
        call :print_error ".env.example file not found. Please create .env file manually."
        exit /b 1
    )
)
goto :eof

REM Function to run development mode
:run_dev
call :print_status "Starting MarkezardAI in development mode..."
call :check_env_file

REM Start backend
call :print_status "Starting backend..."
cd backend
if not exist .venv (
    call :print_status "Creating Python virtual environment..."
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -r requirements.txt
start "Backend" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Start frontend
call :print_status "Starting frontend..."
cd frontend
if not exist node_modules (
    call :print_status "Installing Node.js dependencies..."
    npm install
)
start "Frontend" cmd /k "npm run dev"
cd ..

call :print_success "Development servers started!"
call :print_status "Backend: http://localhost:8000"
call :print_status "Frontend: http://localhost:3000"
call :print_status "API Docs: http://localhost:8000/docs"
call :print_status "Press any key to continue..."
pause >nul
goto :eof

REM Function to run with Docker
:run_docker
call :print_status "Starting MarkezardAI with Docker..."
call :check_env_file

REM Build and start containers
docker-compose up --build
goto :eof

REM Function to run production mode
:run_prod
call :print_status "Starting MarkezardAI in production mode..."
call :check_env_file

REM Build frontend
call :print_status "Building frontend..."
cd frontend
npm install
npm run build
cd ..

REM Start backend
call :print_status "Starting backend..."
cd backend
call .venv\Scripts\activate.bat
pip install -r requirements.txt
start "Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..

REM Start frontend
call :print_status "Starting frontend..."
cd frontend
start "Frontend" cmd /k "npm start"
cd ..

call :print_success "Production servers started!"
call :print_status "Application: http://localhost:3000"
call :print_status "API: http://localhost:8000"
call :print_status "Press any key to continue..."
pause >nul
goto :eof

REM Function to run tests
:run_tests
call :print_status "Running tests..."

REM Backend tests
call :print_status "Running backend tests..."
cd backend
if exist .venv (
    call .venv\Scripts\activate.bat
)
python -m pytest tests/ -v
cd ..

REM Frontend tests
call :print_status "Running frontend tests..."
cd frontend
if exist node_modules (
    npm test -- --watchAll=false
) else (
    call :print_warning "Frontend dependencies not installed. Run 'npm install' first."
)
cd ..

call :print_success "Tests completed!"
goto :eof

REM Function to run linting and security checks
:run_checks
call :print_status "Running code quality checks..."

REM Backend checks
call :print_status "Running backend checks..."
cd backend
if exist .venv (
    call .venv\Scripts\activate.bat
)

call :print_status "Running black formatter..."
black . --check

call :print_status "Running flake8 linter..."
flake8 .

call :print_status "Running bandit security scan..."
bandit -r app/

call :print_status "Running pip-audit..."
pip-audit
cd ..

REM Frontend checks
call :print_status "Running frontend checks..."
cd frontend
if exist node_modules (
    call :print_status "Running ESLint..."
    npm run lint
    
    call :print_status "Running npm audit..."
    npm audit
)
cd ..

call :print_success "Code quality checks completed!"
goto :eof

REM Function to setup the project
:setup_project
call :print_status "Setting up MarkezardAI project..."

REM Check for required tools
python --version >nul 2>&1 || (
    call :print_error "Python is required but not installed."
    exit /b 1
)

node --version >nul 2>&1 || (
    call :print_error "Node.js is required but not installed."
    exit /b 1
)

npm --version >nul 2>&1 || (
    call :print_error "npm is required but not installed."
    exit /b 1
)

REM Setup backend
call :print_status "Setting up backend..."
cd backend
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

REM Setup frontend
call :print_status "Setting up frontend..."
cd frontend
npm install
cd ..

REM Create .env file
call :check_env_file

call :print_success "Project setup completed!"
call :print_status "Next steps:"
call :print_status "1. Edit .env file with your API keys"
call :print_status "2. Run 'run.bat dev' to start development servers"
call :print_status "3. Visit http://localhost:3000 to see the application"
goto :eof

REM Function to show help
:show_help
echo MarkezardAI Run Script for Windows
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   dev      Start development servers (default)
echo   prod     Start production servers
echo   docker   Start with Docker Compose
echo   test     Run all tests
echo   check    Run linting and security checks
echo   setup    Setup the project for first time
echo   help     Show this help message
echo.
echo Examples:
echo   %~nx0 dev     # Start development mode
echo   %~nx0 docker  # Start with Docker
echo   %~nx0 test    # Run tests
goto :eof

REM Main script logic
set "command=%~1"
if "%command%"=="" set "command=dev"

if "%command%"=="dev" (
    call :run_dev
) else if "%command%"=="prod" (
    call :run_prod
) else if "%command%"=="docker" (
    call :run_docker
) else if "%command%"=="test" (
    call :run_tests
) else if "%command%"=="check" (
    call :run_checks
) else if "%command%"=="setup" (
    call :setup_project
) else if "%command%"=="help" (
    call :show_help
) else if "%command%"=="-h" (
    call :show_help
) else if "%command%"=="--help" (
    call :show_help
) else (
    call :print_error "Unknown command: %command%"
    call :show_help
    exit /b 1
)

endlocal
