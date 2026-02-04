Perfect! Here’s the updated **Deployment Guide** in proper Markdown with the Ollama model check and pull steps added:

````markdown
# Book API - Development Deployment Guide

This guide explains how to quickly run the **Book API** locally.

---

## 1️ Prerequisites

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

---

## 4️⃣ Setup Ollama Model

Once the Ollama server is up, check the list of locally available models:

```bash
curl http://localhost:11434/models
```

* If the response is empty or your model (`llama3`) is not listed, pull it manually:

```bash
ollama pull llama3
```

* Verify the model is loaded:

```bash
curl http://localhost:11434/models
```

Now the model is ready for inference.

---

## 5️⃣ Stop / Down

Stop the services:

```bash
docker-compose down
```

Optional: remove volumes if you want a clean start:

```bash
docker-compose down -v
```

---

## ✅ Summary

1. Build containers → `docker-compose build`
2. Start services → `docker-compose up`
3. Check/pull Ollama model → `curl ...` + `ollama pull`
4. Stop services → `docker-compose down`
5. Clean volumes (optional) → `docker-compose down -v`


