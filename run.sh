#!/usr/bin/env bash

# ==============================================================================
# DocMind — Control & Setup Script
# Usage:
#   ./run.sh setup        # First-timer setup: install packages & setup environment
#   ./run.sh dev          # (Recommended) Starts pgvector in Docker + Backend & Frontend locally
#   ./run.sh all          # Starts both Backend and Frontend locally
#   ./run.sh backend      # Starts FastAPI backend only
#   ./run.sh frontend     # Starts Next.js frontend only
#   ./run.sh docker       # Runs full stack in Docker containers
#   ./run.sh test         # Runs backend pytest suite
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_help() {
    echo -e "${CYAN}DocMind Control & Setup Script${NC}"
    echo ""
    echo "Usage: ./run.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup, -i            First-timer setup: installs Python/Node dependencies, copies .env & prepares GGUF model"
    echo "  dev, -s              Starts pgvector in Docker + launches Backend and Frontend locally"
    echo "  all, -a, (default)   Starts FastAPI backend and Next.js frontend locally"
    echo "  backend, -b          Starts FastAPI backend only (Port 8000)"
    echo "  frontend, -f         Starts Next.js frontend only (Port 3000)"
    echo "  docker, -d           Starts full stack in Docker containers"
    echo "  test, -t             Runs backend pytest suite"
    echo "  help, -h             Show this help menu"
    echo ""
}

run_setup() {
    echo -e "${GREEN}🛠️ Running First-Timer Setup for DocMind...${NC}"

    # 1. Environment file setup
    if [ ! -f ".env" ]; then
        echo -e "${CYAN}Creating .env file from .env.example...${NC}"
        cp .env.example .env
    else
        echo -e "${YELLOW}.env file already exists. Skipping copy.${NC}"
    fi

    # 2. Python backend environment & dependencies
    echo -e "${CYAN}Setting up Python virtual environment (.venv) and backend dependencies...${NC}"
    cd backend
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv 2>/dev/null || python -m venv .venv 2>/dev/null || true
    fi
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..

    # 3. Frontend dependencies
    echo -e "${CYAN}Installing Frontend Node.js dependencies...${NC}"
    cd frontend
    npm install
    cd ..

    # 4. Optional GGUF Model Download prompt
    echo -e "${YELLOW}Do you want to download the local Llama 3.1 8B GGUF model weights (~4.9GB)? [y/N]${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}Downloading local GGUF model...${NC}"
        python3 backend/models/download_model.py 2>/dev/null || python backend/models/download_model.py
    else
        echo -e "${YELLOW}Skipping GGUF download. You can download later via API 'POST /api/models/download' or script.${NC}"
    fi

    # 5. Start pgvector container in Docker
    echo -e "${GREEN}Starting PostgreSQL + pgvector Docker container...${NC}"
    docker-compose up -d postgres

    echo -e "${GREEN}✅ Setup complete! Run './run.sh dev' to start local development.${NC}"
}

start_postgres_docker() {
    echo -e "${GREEN}🐘 Starting PostgreSQL + pgvector container in Docker...${NC}"
    if [ ! -f ".env" ]; then
        cp .env.example .env
    fi
    docker-compose up -d postgres
}

start_backend() {
    echo -e "${GREEN}🚀 Starting DocMind FastAPI Backend on http://localhost:8000...${NC}"
    cd backend
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
    fi
    uvicorn main:app --reload --port 8000
}

start_frontend() {
    echo -e "${CYAN}🎨 Starting DocMind Next.js 15 Frontend on http://localhost:3000...${NC}"
    cd frontend
    npm run dev
}

start_dev_hybrid() {
    echo -e "${GREEN}⚡ Starting Hybrid Mode (pgvector in Docker + Local Backend & Frontend)...${NC}"
    
    start_postgres_docker

    trap 'echo -e "${YELLOW}Stopping local development processes...${NC}"; kill 0' INT TERM EXIT

    (start_backend) &
    sleep 3
    (start_frontend) &

    wait
}

start_all() {
    echo -e "${GREEN}⚡ Starting Local Backend + Frontend...${NC}"
    trap 'echo -e "${YELLOW}Stopping local processes...${NC}"; kill 0' INT TERM EXIT

    (start_backend) &
    sleep 2
    (start_frontend) &

    wait
}

start_docker() {
    echo -e "${GREEN}🐳 Starting Full Stack with Docker Compose...${NC}"
    if [ ! -f ".env" ]; then
        cp .env.example .env
    fi
    docker-compose up --build
}

run_tests() {
    echo -e "${GREEN}🧪 Running Backend Pytest Suite...${NC}"
    cd backend
    if [ -d ".venv" ]; then
        source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
    fi
    pytest tests/
}

MODE="${1:-dev}"

case "$MODE" in
    setup|init|-i)
        run_setup
        ;;
    dev|hybrid|-s)
        start_dev_hybrid
        ;;
    all|-a)
        start_all
        ;;
    backend|-b)
        start_backend
        ;;
    frontend|-f)
        start_frontend
        ;;
    docker|-d)
        start_docker
        ;;
    test|-t)
        run_tests
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}Invalid option: $MODE${NC}"
        show_help
        exit 1
        ;;
esac
