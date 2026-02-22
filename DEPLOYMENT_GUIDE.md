# Deployment Guide - IBMS

Comprehensive guide for deploying the Intelligent Book Management System (FastAPI + PostgreSQL 15 + Ollama/Llama3).

---

## Table of Contents

1. [Docker Deployment](#1-docker-deployment)
2. [Docker Production Hardening](#2-docker-production-hardening)
3. [Local Development](#3-local-development)
4. [AWS Deployment](#4-aws-deployment)
5. [CI/CD Pipeline](#5-cicd-pipeline)
6. [Monitoring & Logging](#6-monitoring--logging)
7. [Backup & Recovery](#7-backup--recovery)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Docker Deployment

The project ships with a multi-stage `dockerfile` and a `docker-compose.yaml` that orchestrates three services: **api** (FastAPI), **db** (PostgreSQL 15-alpine), and **ollama** (Ollama LLM).

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   api        │────▶│   db         │     │   ollama     │
│  (FastAPI)   │     │ (postgres:15 │     │ (llama3)     │
│  port 8000   │     │  -alpine)    │     │  port 11434  │
│              │────▶│  port 5432   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       All connected via bridge network: app-network
```

### 1.1 Quick Start

```bash
# Clone and navigate
git clone <repository-url>
cd IBMS

# Create .env from template (edit values as needed)
cp .env.example .env

# Build & start all services
docker-compose build
docker-compose up -d
```

### 1.2 What Docker Compose Starts

| Service | Image / Build | Container | Ports | Volumes |
|---------|--------------|-----------|-------|---------|
| **api** | Built from `./dockerfile` (multi-stage, python:3.11-slim) | `book_api` | `8000:8000` | `./app:/app/app` (live-reload in dev) |
| **db** | `postgres:15-alpine` | `book_db` | `5432:5432` | `book_db_data` (persistent), `./db/init-db.sql` (init script) |
| **ollama** | `ollama/ollama:latest` | `ollama` | `11434:11434` | `ollama_data` (model cache) |

**Startup order:** `db` starts first (api `depends_on` db healthcheck via `pg_isready`), then `ollama` (start condition), then `api`.

### 1.3 Environment Variables (from docker-compose.yaml)

The `api` service receives these at runtime:

| Variable | Default (Docker) | Description |
|----------|-----------------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/bookdb` | Async SQLAlchemy connection string |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3` | LLM model name |
| `APP_ENV` | `development` | Environment (`development` / `production`) |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token TTL |
| `OLLAMA_TIMEOUT` | `300.0` | HTTP timeout for Ollama calls (seconds) |
| `OLLAMA_MAX_CONCURRENCY` | `2` | Max parallel Ollama requests |
| `OLLAMA_CHUNK_SIZE` | `1000` | Words per text chunk for summarization |
| `OLLAMA_CHUNK_OVERLAP` | `100` | Overlap words between chunks |

The `db` service uses:

| Variable | Value | Description |
|----------|-------|-------------|
| `POSTGRES_DB` | `bookdb` | Database name created on first start |
| `POSTGRES_USER` | `postgres` | Superuser name |
| `POSTGRES_PASSWORD` | `postgres` | Superuser password |

### 1.4 Initialize the Ollama Model

Ollama starts empty. Pull the model after containers are running:

```bash
# Pull llama3 into the ollama container
docker-compose exec ollama ollama pull llama3

# Verify model is loaded
curl http://localhost:11434/api/tags
```

### 1.5 Database Initialization

On first startup, two things happen automatically:
1. PostgreSQL runs `./db/init-db.sql` (mounted to `/docker-entrypoint-initdb.d/init.sql`) which creates the `uuid-ossp` extension and indexes.
2. The FastAPI lifespan event in `app/main.py` calls `Base.metadata.create_all` to create all SQLAlchemy tables (`users`, `books`, `reviews`, `recommendations`, `user_book_interactions`, `ai_model_usages`).

### 1.6 Verify the Deployment

```bash
# Check all services are running
docker-compose ps

# API health check
curl http://localhost:8000/health
# Expected: {"status":"OK","service":"Intelligent Book Management System","version":"1.0.0","environment":"development"}

# Swagger docs
open http://localhost:8000/docs

# Ollama status
curl http://localhost:11434/api/tags
```

### 1.7 Common Docker Commands

```bash
# View live logs
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f ollama

# Run tests inside the container
docker-compose exec api pytest --cov=app

# Restart a single service
docker-compose restart api

# Stop all services
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v
```

### 1.8 Dockerfile Internals

The `dockerfile` uses a two-stage build:

| Stage | Base | Purpose |
|-------|------|---------|
| **builder** | `python:3.11-slim` | Installs `gcc`, runs `pip install -r requirements.txt` |
| **final** | `python:3.11-slim` | Copies installed packages from builder, installs `postgresql-client`, creates non-root `appuser` (uid 1000), exposes port 8000 |

**Entrypoint:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`

The container runs as `appuser` (non-root) for security. A `HEALTHCHECK` is configured to poll `http://localhost:8000/health` every 30s.

---

## 2. Docker Production Hardening

### 2.1 Pre-Deployment Checklist

- [ ] Generate a strong `SECRET_KEY` — `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Set `APP_ENV=production` (triggers SECRET_KEY validation in `config.py`)
- [ ] Change `POSTGRES_PASSWORD` to a strong value
- [ ] Remove `./app:/app/app` volume mount (dev live-reload)
- [ ] Configure CORS origins instead of `allow_origins=["*"]`
- [ ] Set `OLLAMA_NUM_GPU=1` if NVIDIA GPU is available
- [ ] Set up SSL/TLS termination (Nginx or load balancer)
- [ ] Configure database backups
- [ ] Set container resource limits
- [ ] Configure log rotation

### 2.2 Production Environment File

Create `.env.production`:

```env
# Application
APP_ENV=production
LOG_LEVEL=WARNING

# Security — CHANGE THIS
SECRET_KEY=<generated-strong-random-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+asyncpg://prod_user:strong_password@db:5432/bookdb
POSTGRES_DB=bookdb
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=strong_password

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300
OLLAMA_MAX_CONCURRENCY=5
OLLAMA_CHUNK_SIZE=1000
OLLAMA_CHUNK_OVERLAP=100
```

Start with the production env file:

```bash
docker-compose --env-file .env.production up -d
```

### 2.3 Nginx Reverse Proxy

```nginx
upstream ibms_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://ibms_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;  # Allow time for Ollama summarization
    }
}
```

### 2.4 Systemd Service (Linux)

Create `/etc/systemd/system/ibms.service`:

```ini
[Unit]
Description=Intelligent Book Management System
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/IBMS
ExecStart=/usr/bin/docker-compose --env-file .env.production up
ExecStop=/usr/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ibms
sudo systemctl start ibms
```

---

## 3. Local Development

Run the application directly on your machine without Docker.

### 3.1 Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 13+ | Database |
| Ollama | Latest | AI model serving |

### 3.2 Setup Steps

**1. Clone & create virtual environment**

```bash
git clone <repository-url>
cd IBMS

# Create and activate venv
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Key packages installed: `fastapi==0.104.1`, `uvicorn==0.24.0`, `sqlalchemy[asyncio]==2.0.23`, `asyncpg==0.29.0`, `httpx==0.25.1`, `python-jose[cryptography]==3.3.0`, `passlib[bcrypt]==1.7.4`, `PyJWT==2.11.0`, `pydantic==2.5.0`.

**3. Create and configure PostgreSQL database**

```bash
# Create the database
createdb bookdb

# Or via psql
psql -U postgres -c "CREATE DATABASE bookdb;"
```

The init SQL script at `app/db/init-db.sql` creates the `uuid-ossp` extension and indexes. You can run it manually:

```bash
psql -U postgres -d bookdb -f app/db/init-db.sql
```

> Tables are auto-created by SQLAlchemy on application startup via `Base.metadata.create_all` in the lifespan handler (`app/main.py`).

**4. Configure environment variables**

Create a `.env` file in the project root:

```env
# Database — point to your local PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-dev-secret-key

# Ollama — point to local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300.0
OLLAMA_MAX_CONCURRENCY=2
OLLAMA_CHUNK_SIZE=1000
OLLAMA_CHUNK_OVERLAP=100
```

> **Important:** For local development, set `OLLAMA_BASE_URL=http://localhost:11434` (not `http://ollama:11434` which is the Docker service name).

**5. Start Ollama**

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull the model
ollama pull llama3

# Verify
curl http://localhost:11434/api/tags
```

**6. Run the application**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup the app will:
- Create all database tables via SQLAlchemy
- Initialize the database (via `init_db_model`)
- Start 1 background worker for async summarization tasks

**API:** `http://localhost:8000` | **Docs:** `http://localhost:8000/docs` | **ReDoc:** `http://localhost:8000/redoc`

### 3.3 Running Tests

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) via the fixtures in `tests/conftest.py`, so no external database is needed.

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_book_service.py

# Verbose output
pytest -v
```

The `pytest.ini` configures `pythonpath = .` and `asyncio_mode = strict`.

### 3.4 Quick Start Script

An automated setup script is provided:

```bash
chmod +x quickstart.sh
./quickstart.sh
```

This detects your OS, checks for Docker/Docker Compose, and offers two setup paths:
1. **Docker Compose** — builds images, starts services, pulls llama3 model
2. **Local development** — creates virtualenv, installs dependencies, generates `.env`

---

## 4. AWS Deployment

### 4.1 Option A: EC2 with Docker Compose (Simplest)

Deploy the same Docker Compose setup on an EC2 instance.

**1. Launch EC2 instance**
- AMI: Ubuntu 22.04 LTS
- Instance type: `t3.medium` minimum (Ollama needs memory)
- Storage: 30 GB+ (model weights)
- Security group: Allow ports 80, 443, 22

**2. Install Docker on the instance**

```bash
#!/bin/bash
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**3. Deploy the application**

```bash
cd /opt
sudo git clone <repository-url> IBMS
cd IBMS

# Create production env
sudo cp .env.example .env
# Edit .env with production values (strong SECRET_KEY, APP_ENV=production, etc.)

# Build and start
sudo docker-compose up -d

# Pull Ollama model
sudo docker-compose exec ollama ollama pull llama3
```

**4. Set up SSL with Let's Encrypt**

```bash
sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot certonly --standalone -d api.yourdomain.com
```

Then configure Nginx as shown in Section 2.3.

### 4.2 Option B: ECS (Fargate) + RDS

For a managed, scalable setup using AWS services.

**1. Create ECR repository and push the image**

```bash
# Create repository
aws ecr create-repository --repository-name ibms-api

# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com

# Build and push
docker build -t ibms-api:latest -f dockerfile .
docker tag ibms-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/ibms-api:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/ibms-api:latest
```

**2. Create RDS PostgreSQL instance**

```bash
aws rds create-db-instance \
  --db-instance-identifier ibms-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15 \
  --master-username postgres \
  --master-user-password <strong-password> \
  --allocated-storage 20 \
  --db-name bookdb \
  --vpc-security-group-ids <sg-id> \
  --publicly-accessible false
```

Update `DATABASE_URL` to point to the RDS endpoint:
```
postgresql+asyncpg://postgres:<password>@<rds-endpoint>:5432/bookdb
```

**3. Create ECS cluster and task definition**

```bash
aws ecs create-cluster --cluster-name ibms-cluster
```

Create `task-definition.json`:

```json
{
  "family": "ibms-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ibms-api",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/ibms-api:latest",
      "portMappings": [{ "containerPort": 8000, "protocol": "tcp" }],
      "environment": [
        { "name": "DATABASE_URL", "value": "postgresql+asyncpg://postgres:<pw>@<rds-endpoint>:5432/bookdb" },
        { "name": "OLLAMA_BASE_URL", "value": "http://<ollama-host>:11434" },
        { "name": "OLLAMA_MODEL", "value": "llama3" },
        { "name": "APP_ENV", "value": "production" },
        { "name": "SECRET_KEY", "value": "<strong-key>" },
        { "name": "LOG_LEVEL", "value": "WARNING" }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 40
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ibms-api",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

> **Note on Ollama:** Fargate does not support GPU. For production AI inference, consider running Ollama on a separate GPU-enabled EC2 instance (`g4dn.xlarge`) or switching to an API-based LLM service.

**4. Create ECS service with ALB**

```bash
aws ecs create-service \
  --cluster ibms-cluster \
  --service-name ibms-api-service \
  --task-definition ibms-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-ids>],securityGroups=[<sg-id>],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<tg-arn>,containerName=ibms-api,containerPort=8000"
```

### 4.3 Option C: AWS App Runner (Easiest Managed)

Ideal for quick deployments without managing infrastructure:

1. Push image to ECR (see 4.2 step 1)
2. Create App Runner service from the ECR image
3. Configure environment variables (`DATABASE_URL`, `SECRET_KEY`, `OLLAMA_BASE_URL`, etc.)
4. App Runner handles scaling, TLS, and load balancing automatically

> **Limitation:** App Runner cannot host Ollama. You still need a separate compute resource for the LLM.

---

## 5. CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install aiosqlite  # Required for test fixtures (SQLite async)

      - name: Run tests
        run: pytest --cov=app --cov-report=xml -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t ibms-api:${{ github.sha }} -f dockerfile .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag ibms-api:${{ github.sha }} ${{ secrets.DOCKER_USERNAME }}/ibms-api:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/ibms-api:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          ssh -i ${{ secrets.SSH_KEY }} -o StrictHostKeyChecking=no \
            ubuntu@${{ secrets.PROD_SERVER }} \
            'cd /opt/IBMS && docker-compose pull && docker-compose up -d'
```

---

## 6. Monitoring & Logging

### 6.1 Health Check

The API exposes a health endpoint at `/health`:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "OK",
  "service": "Intelligent Book Management System",
  "version": "1.0.0",
  "environment": "development"
}
```

Docker Compose configures healthchecks for both `api` (curl to `/health` every 30s) and `db` (`pg_isready` every 10s).

### 6.2 Application Logging

The app uses Python's standard `logging` module with a `QueueHandler`/`QueueListener` pattern (configured in `app/core/logging.py`) for non-blocking log output. Every HTTP request gets a unique `X-Request-ID` header via the middleware in `app/core/middleware.py`.

Log format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`

View logs:

```bash
# Docker
docker-compose logs -f api

# Local
# Logs output to stdout/stderr
```

### 6.3 Log Rotation (Linux production)

```bash
cat > /etc/logrotate.d/ibms <<EOF
/var/log/ibms/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
}
EOF
```

---

## 7. Backup & Recovery

### Database Backup

```bash
# Manual backup
docker-compose exec db pg_dump -U postgres bookdb > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres bookdb > "$BACKUP_DIR/backup_$DATE.sql"
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Retain last 30 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete
```

### Restore from Backup

```bash
# Restore
docker-compose exec -T db psql -U postgres bookdb < backup.sql

# Or from gzip
gunzip -c backup_20260222.sql.gz | docker-compose exec -T db psql -U postgres bookdb
```

### Ollama Model Data

Model weights are stored in the `ollama_data` Docker volume. To back up:

```bash
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama_models.tar.gz -C /data .
```

---

## 8. Troubleshooting

### Database Connection Refused

```bash
# Check db container status
docker-compose ps db
docker-compose logs db

# Verify connectivity from api container
docker-compose exec api python -c "import asyncpg; print('asyncpg OK')"

# Restart db
docker-compose restart db
```

**Local:** Ensure PostgreSQL is running and `DATABASE_URL` in `.env` points to `localhost` (not `db`).

### Ollama Model Not Found / Timeout

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull the model
docker-compose exec ollama ollama pull llama3

# Increase timeout if summarization fails on large texts
# Set OLLAMA_TIMEOUT=600 in .env
```

The AI service (`app/services/ai_service.py`) uses a map-reduce chunking strategy: texts are split into chunks of `OLLAMA_CHUNK_SIZE` words, summarized in parallel (up to `OLLAMA_MAX_CONCURRENCY`), then combined into a final summary.

### API Returns 401 Unauthorized

- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 min). Login again via `POST /api/v1/auth/login`.
- Ensure the `Authorization: Bearer <token>` header is present.
- Verify `SECRET_KEY` hasn't changed between token creation and validation.

### Tests Failing

Tests use an in-memory SQLite database and don't need PostgreSQL or Ollama:

```bash
# Clear cache and run
pytest --cache-clear -v

# Ensure aiosqlite is installed (needed by conftest.py)
pip install aiosqlite
```

### Out of Memory (Docker)

```bash
# Add resource limits to docker-compose.yaml under the api service:
# deploy:
#   resources:
#     limits:
#       memory: 4G

# Ollama with llama3 needs ~4-8 GB RAM depending on model size
```

### SECRET_KEY Validation Error on Startup

If `APP_ENV=production` and `SECRET_KEY` is the default value, the app will raise `ValueError: SECRET_KEY must be set in production!` (enforced in `app/core/config.py`). Generate a strong key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

**Last Updated:** February 22, 2026
