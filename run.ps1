# DocMind — PowerShell Control Script for Windows
param (
    [string]$Mode = "dev"
)

function Show-Help {
    Write-Host "DocMind PowerShell Control Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\run.ps1 [Option]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  setup, -i            First-timer setup: upgrades pip, installs Python/Node dependencies & copies .env"
    Write-Host "  dev, -s (default)    Starts pgvector in Docker + launches Backend and Frontend locally"
    Write-Host "  all, -a              Starts FastAPI backend and Next.js frontend locally"
    Write-Host "  backend, -b          Starts FastAPI backend only (Port 8000)"
    Write-Host "  frontend, -f         Starts Next.js frontend only (Port 3000)"
    Write-Host "  docker, -d           Starts full stack in Docker containers"
    Write-Host "  test, -t             Runs backend pytest suite"
    Write-Host ""
}

switch ($Mode.ToLower()) {
    { $_ -in "setup", "init", "-i" } {
        Write-Host "🛠️ Running First-Timer Setup for DocMind..." -ForegroundColor Green
        if (-not (Test-Path ".env")) {
            Copy-Item .env.example .env
            Write-Host "Created .env file." -ForegroundColor Cyan
        }
        
        Write-Host "Setting up Python virtual environment (.venv)..." -ForegroundColor Cyan
        Set-Location backend
        if (-not (Test-Path ".venv")) { python -m venv .venv }
        .\.venv\Scripts\activate.ps1
        
        Write-Host "Upgrading pip to latest version..." -ForegroundColor Green
        python -m pip install --upgrade pip
        
        Write-Host "Installing Backend Python dependencies..." -ForegroundColor Cyan
        pip install -r requirements.txt
        Set-Location ..

        Write-Host "Installing Frontend Node.js dependencies..." -ForegroundColor Cyan
        Set-Location frontend
        npm install
        Set-Location ..

        Write-Host "Starting PostgreSQL pgvector container in Docker..." -ForegroundColor Green
        docker-compose up -d postgres
        Write-Host "✅ Setup complete! Run '.\run.ps1 dev' to start development." -ForegroundColor Green
    }
    { $_ -in "dev", "hybrid", "-s" } {
        Write-Host "🐘 Starting PostgreSQL pgvector in Docker..." -ForegroundColor Green
        if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
        docker-compose up -d postgres

        Write-Host "⚡ Starting Local Backend & Frontend..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\activate; uvicorn main:app --reload --port 8000"
        Start-Sleep -Seconds 3
        Set-Location frontend
        npm run dev
    }
    { $_ -in "all", "-a" } {
        Write-Host "⚡ Starting Local Backend + Frontend..." -ForegroundColor Green
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\activate; uvicorn main:app --reload --port 8000"
        Start-Sleep -Seconds 2
        Set-Location frontend
        npm run dev
    }
    { $_ -in "backend", "-b" } {
        Write-Host "🚀 Starting DocMind FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
        Set-Location backend
        if (Test-Path ".\.venv\Scripts\activate.ps1") { .\.venv\Scripts\activate.ps1 }
        uvicorn main:app --reload --port 8000
    }
    { $_ -in "frontend", "-f" } {
        Write-Host "🎨 Starting DocMind Next.js Frontend on http://localhost:3000..." -ForegroundColor Cyan
        Set-Location frontend
        npm run dev
    }
    { $_ -in "docker", "-d" } {
        Write-Host "🐳 Starting DocMind in Docker..." -ForegroundColor Green
        if (-not (Test-Path ".env")) { Copy-Item .env.example .env }
        docker-compose up --build
    }
    { $_ -in "test", "-t" } {
        Write-Host "🧪 Running Backend Pytest Suite..." -ForegroundColor Green
        Set-Location backend
        pytest tests/
    }
    Default {
        Show-Help
    }
}
