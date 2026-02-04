Got it! I’ve cleaned up your Markdown, fixed typos, properly closed code blocks, and organized the steps clearly. Here’s a polished **`README.md`** for your dev deployment:

````markdown
# Book API - Development Deployment Guide

This guide explains how to quickly run the **Book API** locally.

---

## 1️⃣ Prerequisites

- Docker ≥ 20.x  
- Docker Compose ≥ 2.x  
- Python ≥ 3.11 (optional if you want to run outside Docker)  
- `.env` file in project root:

```env
# Database
POSTGRES_DB=bookdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bookdb

# App
APP_ENV=local
LOG_LEVEL=INFO

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300.0
OLLAMA_MAX_CONCURRENCY=2
OLLAMA_CHUNK_SIZE=1000
OLLAMA_CHUNK_OVERLAP=100
````

---

## 2️⃣ Build

From the project root, run:

```bash
docker-compose build
```

---

## 3️⃣ Run

From the project root, run:

```bash
docker-compose up
```

* API will be available at: `http://localhost:8000`
* PostgreSQL at: `localhost:5432`
* Ollama at: `http://localhost:11434`

---

## 4️⃣ Stop / Down

From the project root, run:

```bash
docker-compose down
```

Optional: Remove volumes as well:

```bash
docker-compose down -v
```

