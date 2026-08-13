#!/usr/bin/env bash

# ==============================================================================
# DocMind — Control & Setup Script
#
# Usage:
#   ./run.sh setup        First-time setup
#   ./run.sh dev          PostgreSQL in Docker + backend/frontend locally
#   ./run.sh ingest       Ingest PDFs into pgvector
#   ./run.sh all          Backend + frontend locally
#   ./run.sh backend      FastAPI backend only
#   ./run.sh frontend     Next.js frontend only
#   ./run.sh docker       Full stack with Docker Compose
#   ./run.sh test         Backend tests
#   ./run.sh help         Show help
# ==============================================================================

set -e

# ------------------------------------------------------------------------------
# Colors
# ------------------------------------------------------------------------------

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# Always run from project root
# ------------------------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

get_python() {
    if command_exists python3; then
        echo "python3"
    elif command_exists python; then
        echo "python"
    else
        echo -e "${RED}❌ Python is not installed.${NC}" >&2
        exit 1
    fi
}

activate_venv() {
    local venv_path="$1"

    # Linux / macOS / WSL
    if [ -f "$venv_path/bin/activate" ]; then
        # shellcheck disable=SC1090
        source "$venv_path/bin/activate"
        return 0
    fi

    # Windows Git Bash
    if [ -f "$venv_path/Scripts/activate" ]; then
        # shellcheck disable=SC1090
        source "$venv_path/Scripts/activate"
        return 0
    fi

    return 1
}

docker_compose() {
    # Modern Docker Compose v2
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
        return
    fi

    # Legacy Docker Compose v1
    if command_exists docker-compose; then
        docker-compose "$@"
        return
    fi

    echo -e "${RED}❌ Docker Compose was not found.${NC}"
    echo ""
    echo "Expected one of:"
    echo "  docker compose"
    echo "  docker-compose"
    echo ""
    echo "On Fedora with Docker Engine, install:"
    echo "  sudo dnf install docker-compose-plugin"
    exit 1
}

check_docker() {
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is not installed.${NC}"
        exit 1
    fi

    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is installed but not running or inaccessible.${NC}"
        echo ""
        echo "On Fedora try:"
        echo "  sudo systemctl start docker"
        echo ""
        echo "Check status:"
        echo "  systemctl status docker"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# Help
# ------------------------------------------------------------------------------

show_help() {
    echo -e "${CYAN}DocMind Control & Setup Script${NC}"
    echo ""
    echo "Usage:"
    echo "  ./run.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup, -i            First-time setup"
    echo "  dev, -s              PostgreSQL Docker + local backend/frontend"
    echo "  ingest, -g           Ingest PDFs from data/documents/"
    echo "  all, -a              Local backend + frontend"
    echo "  backend, -b          FastAPI backend only (port 8000)"
    echo "  frontend, -f         Next.js frontend only (port 3000)"
    echo "  docker, -d           Full stack with Docker Compose"
    echo "  test, -t             Run backend pytest suite"
    echo "  help, -h             Show this menu"
    echo ""
}

# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------

run_setup() {
    echo -e "${GREEN}🛠️ Running First-Time Setup for DocMind...${NC}"

    local PYTHON
    PYTHON="$(get_python)"

    # --------------------------------------------------------------------------
    # Environment
    # --------------------------------------------------------------------------

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo -e "${CYAN}Creating .env from .env.example...${NC}"
            cp .env.example .env
        else
            echo -e "${YELLOW}⚠️ .env.example not found. Skipping .env creation.${NC}"
        fi
    else
        echo -e "${YELLOW}.env already exists. Skipping copy.${NC}"
    fi

    # --------------------------------------------------------------------------
    # Backend
    # --------------------------------------------------------------------------

    echo -e "${CYAN}Setting up Python virtual environment...${NC}"

    cd "$ROOT_DIR/backend"

    if [ ! -d ".venv" ]; then
        "$PYTHON" -m venv .venv
    else
        echo -e "${YELLOW}.venv already exists.${NC}"
    fi

    if ! activate_venv ".venv"; then
        echo -e "${RED}❌ Could not activate Python virtual environment.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Upgrading pip...${NC}"
    python -m pip install --upgrade pip

    echo -e "${CYAN}Installing backend requirements...${NC}"
    pip install -e ".[dev]"

    # --------------------------------------------------------------------------
    # Frontend
    # --------------------------------------------------------------------------

    cd "$ROOT_DIR/frontend"

    if ! command_exists npm; then
        echo -e "${RED}❌ npm is not installed.${NC}"
        exit 1
    fi

    echo -e "${CYAN}Installing frontend dependencies...${NC}"
    npm install

    cd "$ROOT_DIR"

    # --------------------------------------------------------------------------
    # Model
    # --------------------------------------------------------------------------

    echo ""
    echo -e "${YELLOW}Download local Llama 3.1 8B GGUF model (~4.9 GB)? [y/N]${NC}"
    read -r response

    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}Downloading local GGUF model...${NC}"

        "$PYTHON" backend/models/download_model.py
    else
        echo -e "${YELLOW}Skipping GGUF model download.${NC}"
        echo "You can download it later using:"
        echo "  POST /api/models/download"
        echo "or:"
        echo "  python backend/models/download_model.py"
    fi

    # --------------------------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------------------------

    check_docker

    echo -e "${GREEN}🐘 Starting PostgreSQL + pgvector...${NC}"
    docker_compose up -d postgres

    echo ""
    echo -e "${GREEN}✅ Setup complete.${NC}"
    echo ""
    echo "Start development with:"
    echo "  ./run.sh dev"
}

# ------------------------------------------------------------------------------
# Ingestion
# ------------------------------------------------------------------------------

run_ingest() {
    echo -e "${GREEN}📄 Ingesting PDFs from data/documents/...${NC}"

    local PYTHON
    PYTHON="$(get_python)"

    if [ -d "$ROOT_DIR/backend/.venv" ]; then
        activate_venv "$ROOT_DIR/backend/.venv" || true
        PYTHON="python"
    fi

    cd "$ROOT_DIR"

    "$PYTHON" backend/scripts/ingest_documents.py
}

# ------------------------------------------------------------------------------
# PostgreSQL
# ------------------------------------------------------------------------------

start_postgres_docker() {
    echo -e "${GREEN}🐘 Starting PostgreSQL + pgvector container...${NC}"

    check_docker

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo -e "${CYAN}Creating .env from .env.example...${NC}"
            cp .env.example .env
        else
            echo -e "${RED}❌ .env and .env.example are missing.${NC}"
            exit 1
        fi
    fi

    docker_compose up -d postgres
}

# ------------------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------------------

start_backend() {
    echo -e "${GREEN}🚀 Starting FastAPI backend...${NC}"
    echo "   http://localhost:8000"
    echo ""

    cd "$ROOT_DIR/backend"

    if [ -d ".venv" ]; then
        if ! activate_venv ".venv"; then
            echo -e "${YELLOW}⚠️ Could not activate .venv.${NC}"
        fi
    else
        echo -e "${RED}❌ backend/.venv does not exist.${NC}"
        echo "Run:"
        echo "  ./run.sh setup"
        exit 1
    fi

    if ! command_exists uvicorn; then
        echo -e "${RED}❌ uvicorn is not installed in the virtual environment.${NC}"
        echo "Run:"
        echo "  ./run.sh setup"
        exit 1
    fi

    uvicorn main:app --reload --port 8000
}

# ------------------------------------------------------------------------------
# Frontend
# ------------------------------------------------------------------------------

start_frontend() {
    echo -e "${CYAN}🎨 Starting Next.js frontend...${NC}"
    echo "   http://localhost:3000"
    echo ""

    cd "$ROOT_DIR/frontend"

    if ! command_exists npm; then
        echo -e "${RED}❌ npm is not installed.${NC}"
        exit 1
    fi

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️ node_modules not found.${NC}"
        echo "Installing frontend dependencies..."
        npm install
    fi

    npm run dev
}

# ------------------------------------------------------------------------------
# Wait for backend
# ------------------------------------------------------------------------------

wait_for_backend() {
    echo -e "${YELLOW}⏳ Waiting for FastAPI backend...${NC}"

    local retries=60
    local count=0

    while [ "$count" -lt "$retries" ]; do
        if curl -s \
            http://127.0.0.1:8000/health \
            >/dev/null 2>&1; then

            echo -e "${GREEN}✅ FastAPI backend is ready.${NC}"
            return 0
        fi

        sleep 1
        count=$((count + 1))
    done

    echo -e "${YELLOW}⚠️ Backend readiness timeout reached.${NC}"
    echo -e "${YELLOW}Starting frontend anyway...${NC}"
}

# ------------------------------------------------------------------------------
# Development Hybrid Mode
# ------------------------------------------------------------------------------

start_dev_hybrid() {
    echo -e "${GREEN}⚡ Starting Hybrid Development Mode${NC}"
    echo ""
    echo "PostgreSQL → Docker"
    echo "Backend    → Local"
    echo "Frontend   → Local"
    echo ""

    start_postgres_docker

    cleanup() {
        echo ""
        echo -e "${YELLOW}Stopping local development processes...${NC}"

        jobs -p | xargs -r kill 2>/dev/null || true
    }

    trap cleanup INT TERM EXIT

    (
        start_backend
    ) &

    BACKEND_PID=$!

    wait_for_backend

    (
        start_frontend
    ) &

    FRONTEND_PID=$!

    echo ""
    echo -e "${GREEN}✅ DocMind development environment started.${NC}"
    echo ""
    echo "Backend PID:  $BACKEND_PID"
    echo "Frontend PID: $FRONTEND_PID"
    echo ""
    echo "Backend:  http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop local processes."

    wait
}

# ------------------------------------------------------------------------------
# Local Backend + Frontend
# ------------------------------------------------------------------------------

start_all() {
    echo -e "${GREEN}⚡ Starting Local Backend + Frontend...${NC}"

    cleanup() {
        echo ""
        echo -e "${YELLOW}Stopping local processes...${NC}"

        jobs -p | xargs -r kill 2>/dev/null || true
    }

    trap cleanup INT TERM EXIT

    (
        start_backend
    ) &

    BACKEND_PID=$!

    wait_for_backend

    (
        start_frontend
    ) &

    FRONTEND_PID=$!

    echo ""
    echo -e "${GREEN}✅ Local development environment started.${NC}"
    echo ""
    echo "Backend PID:  $BACKEND_PID"
    echo "Frontend PID: $FRONTEND_PID"
    echo ""
    echo "Backend:  http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop."

    wait
}

# ------------------------------------------------------------------------------
# Full Docker
# ------------------------------------------------------------------------------

start_docker() {
    echo -e "${GREEN}🐳 Starting Full Stack with Docker Compose...${NC}"

    check_docker

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            echo -e "${CYAN}Creating .env from .env.example...${NC}"
            cp .env.example .env
        else
            echo -e "${RED}❌ .env and .env.example are missing.${NC}"
            exit 1
        fi
    fi

    docker_compose up --build
}

# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

run_tests() {
    echo -e "${GREEN}🧪 Running Backend Test Suite...${NC}"

    cd "$ROOT_DIR/backend"

    if [ -d ".venv" ]; then
        activate_venv ".venv" || true
    else
        echo -e "${RED}❌ backend/.venv does not exist.${NC}"
        echo "Run:"
        echo "  ./run.sh setup"
        exit 1
    fi

    if ! command_exists pytest; then
        echo -e "${RED}❌ pytest is not installed.${NC}"
        exit 1
    fi

    pytest tests/
}

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

MODE="${1:-dev}"

case "$MODE" in

    setup|init|-i)
        run_setup
        ;;

    dev|hybrid|-s)
        start_dev_hybrid
        ;;

    ingest|-g)
        run_ingest
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
        echo -e "${RED}❌ Invalid option: $MODE${NC}"
        echo ""
        show_help
        exit 1
        ;;

esac