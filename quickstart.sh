#!/bin/bash
# ==========================================
# Quick Start Script
# Intelligent Book Management System (IBMS)
# ==========================================
#
# Services started by Docker Compose:
#   api    (book_api)   — FastAPI on port 8000
#   db     (book_db)    — PostgreSQL 15-alpine on port 5432
#   ollama (ollama)     — Ollama LLM on port 11434
#
# For local dev, you need: Python 3.11+, PostgreSQL 13+, Ollama

set -e

echo "=========================================="
echo "  IBMS - Quick Start Setup"
echo "=========================================="
echo ""

# ------------------------------------------
# Detect OS
# ------------------------------------------
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="windows"
fi

# ------------------------------------------
# Pre-flight checks
# ------------------------------------------

# Docker
if command -v docker &> /dev/null; then
    echo "[ok] Docker found"
else
    echo "[--] Docker not found"
fi

# Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "[ok] Docker Compose found"
else
    echo "[--] Docker Compose not found"
fi

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "[ok] Python $PYTHON_VERSION found"
else
    echo "[--] Python 3 not found"
fi

# PostgreSQL client
if command -v psql &> /dev/null; then
    echo "[ok] psql found"
else
    echo "[--] psql not found (needed for local setup)"
fi

# Ollama
if command -v ollama &> /dev/null; then
    echo "[ok] Ollama found"
else
    echo "[--] Ollama not found (needed for local setup)"
fi

echo ""
echo "Select setup method:"
echo "  1) Docker Compose (Recommended)"
echo "  2) Local development"
echo ""
read -p "Enter choice (1 or 2): " choice

# ==========================================
# OPTION 1: Docker Compose
# ==========================================
if [ "$choice" == "1" ]; then

    # Verify Docker is available
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        echo ""
        echo "Error: Docker and Docker Compose are required for this option."
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    echo ""
    echo "Setting up with Docker Compose..."
    echo ""

    # Create .env from template if missing
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "[ok] .env created from .env.example"
        else
            echo "[!!] .env.example not found. Create .env manually."
            exit 1
        fi
    else
        echo "[ok] .env already exists"
    fi

    # Build the multi-stage Dockerfile (python:3.11-slim)
    echo ""
    echo "Building Docker images..."
    docker-compose build
    echo "[ok] Images built"

    # Start all three services (db starts first via healthcheck dependency)
    echo ""
    echo "Starting services (api, db, ollama)..."
    docker-compose up -d
    echo "[ok] Services started"

    # Wait for API — the compose healthcheck has start_period: 40s
    echo ""
    echo "Waiting for API to become healthy (this may take up to 45s)..."
    RETRIES=15
    HEALTHY=false
    for i in $(seq 1 $RETRIES); do
        sleep 3
        API_HEALTH=$(curl -sf http://localhost:8000/health 2>/dev/null || true)
        if [[ "$API_HEALTH" == *"OK"* ]]; then
            HEALTHY=true
            break
        fi
        echo "  ... attempt $i/$RETRIES"
    done

    if [ "$HEALTHY" = true ]; then
        echo "[ok] API is healthy"
    else
        echo "[!!] API not responding yet. Check logs: docker-compose logs -f api"
    fi

    # Check Ollama and pull model
    echo ""
    echo "Checking Ollama..."
    OLLAMA_OK=$(curl -sf http://localhost:11434/api/tags 2>/dev/null || true)
    if [[ -n "$OLLAMA_OK" ]]; then
        echo "[ok] Ollama is running"
        echo ""
        echo "Pulling llama3 model (this may take several minutes)..."
        docker-compose exec -T ollama ollama pull llama3
        echo "[ok] llama3 model ready"
    else
        echo "[!!] Ollama not responding yet. Try later:"
        echo "     docker-compose exec ollama ollama pull llama3"
    fi

    echo ""
    echo "=========================================="
    echo "  Docker Setup Complete"
    echo "=========================================="
    echo ""
    echo "  API:           http://localhost:8000"
    echo "  Swagger docs:  http://localhost:8000/docs"
    echo "  ReDoc:         http://localhost:8000/redoc"
    echo "  PostgreSQL:    localhost:5432  (user: postgres, db: bookdb)"
    echo "  Ollama:        http://localhost:11434"
    echo ""
    echo "Useful commands:"
    echo "  docker-compose logs -f api          View API logs"
    echo "  docker-compose exec api pytest      Run tests"
    echo "  docker-compose restart api          Restart API"
    echo "  docker-compose down                 Stop all services"
    echo "  docker-compose down -v              Stop + remove volumes"
    echo ""

# ==========================================
# OPTION 2: Local Development
# ==========================================
elif [ "$choice" == "2" ]; then

    echo ""
    echo "Setting up for local development..."
    echo ""

    # Verify Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3.11+ is required."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo "[ok] Using Python $PYTHON_VERSION"

    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "[ok] Virtual environment created"
    else
        echo "[ok] Virtual environment already exists"
    fi

    # Activate venv
    if [ "$OS" == "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    echo "[ok] Virtual environment activated"

    # Install dependencies from requirements.txt
    echo ""
    echo "Installing dependencies..."
    pip install --upgrade pip setuptools wheel -q
    pip install -r requirements.txt
    echo "[ok] Dependencies installed"

    # Create .env with local-dev defaults
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            # Override OLLAMA_BASE_URL to localhost (default in .env.example
            # and config.py points to http://ollama:11434 which is the Docker
            # service name — won't work for local dev)
            if grep -q "OLLAMA_BASE_URL" .env; then
                sed -i.bak 's|OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://localhost:11434|' .env
                rm -f .env.bak
            fi
            # Also fix DATABASE_URL if it points to the Docker 'db' host
            if grep -q "@db:" .env; then
                sed -i.bak 's|@db:|@localhost:|' .env
                rm -f .env.bak
            fi
            echo "[ok] .env created (OLLAMA_BASE_URL and DATABASE_URL set to localhost)"
        else
            echo "[!!] .env.example not found. Create .env manually with:"
            echo "     DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb"
            echo "     OLLAMA_BASE_URL=http://localhost:11434"
            echo "     OLLAMA_MODEL=llama3"
            echo "     SECRET_KEY=your-secret-key-change-in-production"
            echo "     APP_ENV=development"
        fi
    else
        echo "[ok] .env already exists"
    fi

    # Check PostgreSQL and create database
    echo ""
    if command -v psql &> /dev/null; then
        echo "Checking PostgreSQL..."
        if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw bookdb; then
            echo "[ok] Database 'bookdb' already exists"
        else
            echo "Creating database 'bookdb'..."
            createdb -U postgres bookdb 2>/dev/null && echo "[ok] Database created" \
                || echo "[!!] Could not create database. Create it manually:"
            echo "     createdb -U postgres bookdb"
            echo "     psql -U postgres -d bookdb -f app/db/init-db.sql"
        fi
    else
        echo "[!!] psql not found. Make sure PostgreSQL is running and create the database:"
        echo "     createdb -U postgres bookdb"
        echo "     psql -U postgres -d bookdb -f app/db/init-db.sql"
    fi

    # Check Ollama
    echo ""
    if command -v ollama &> /dev/null; then
        echo "Checking Ollama..."
        OLLAMA_RUNNING=$(curl -sf http://localhost:11434/api/tags 2>/dev/null || true)
        if [[ -n "$OLLAMA_RUNNING" ]]; then
            echo "[ok] Ollama is running"
            # Check if llama3 is already pulled
            if echo "$OLLAMA_RUNNING" | grep -q "llama3"; then
                echo "[ok] llama3 model already available"
            else
                echo "Pulling llama3 model (this may take several minutes)..."
                ollama pull llama3
                echo "[ok] llama3 model ready"
            fi
        else
            echo "[!!] Ollama is installed but not running. Start it with:"
            echo "     ollama serve"
            echo "     ollama pull llama3"
        fi
    else
        echo "[!!] Ollama not found. Install from: https://ollama.ai"
        echo "     Then run: ollama serve && ollama pull llama3"
    fi

    echo ""
    echo "=========================================="
    echo "  Local Development Setup Complete"
    echo "=========================================="
    echo ""
    echo "To start the application:"
    echo ""
    if [ "$OS" == "windows" ]; then
        echo "  venv\\Scripts\\activate"
    else
        echo "  source venv/bin/activate"
    fi
    echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "On startup the app will:"
    echo "  - Create all database tables (via SQLAlchemy Base.metadata.create_all)"
    echo "  - Start 1 background worker for async summarization"
    echo ""
    echo "  API:           http://localhost:8000"
    echo "  Swagger docs:  http://localhost:8000/docs"
    echo "  ReDoc:         http://localhost:8000/redoc"
    echo ""
    echo "Run tests (uses in-memory SQLite, no external services needed):"
    echo "  pytest"
    echo "  pytest --cov=app --cov-report=html"
    echo ""

else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo "For more information, see:"
echo "  - README.md"
echo "  - DEPLOYMENT_GUIDE.md"
echo ""
