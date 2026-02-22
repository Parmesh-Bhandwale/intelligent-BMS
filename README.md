# Intelligent Book Management System (IBMS)

AI-powered book management platform with summarization, recommendations, and reviews — built on FastAPI, PostgreSQL, and Ollama (Llama3).

**Version:** 1.0.0

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Quick Start](#quick-start)
4. [API Endpoints](#api-endpoints)
5. [Project Structure](#project-structure)
6. [Configuration](#configuration)
7. [Database Schema](#database-schema)
8. [Architecture Details](#architecture-details)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Features

- **JWT Authentication** — Register/login with HS256 tokens, role-based access control (`admin`, `user`) via `require_role()` dependency
- **Book CRUD** — Full create/read/update/delete with UUID primary keys; update and delete restricted to `admin` role
- **AI Summarization** — Map-reduce chunked summarization via Ollama Llama3; content is split into configurable word chunks, summarized in parallel, then combined into a final summary
- **Background Job Queue** — `asyncio.Queue`-based worker processes book summaries asynchronously (status: `pending` → `processing` → `completed` / `failed`)
- **Review System** — User reviews with 0-5 float ratings, aggregated statistics (avg, count, min, max)
- **Smart Recommendations** — Genre-based filtering, minimum rating threshold, user interaction exclusion, top-rated and similar-book queries
- **Fully Async** — All database operations use `asyncpg` + SQLAlchemy async sessions with connection pooling (pool_size=10, max_overflow=20)
- **Request Tracking** — Every request gets a UUID `X-Request-ID` header via middleware
- **Structured Logging** — Non-blocking `QueueHandler`/`QueueListener` pattern
- **Custom Error Handling** — `AppException`, `NotFoundException`, `UnauthorizedException`, `InternalServerException` with global exception handlers
- **Docker Compose** — Three-service stack (API + PostgreSQL 15 + Ollama) with healthchecks and named volumes
- **Auto-generated API Docs** — Swagger UI with global Bearer auth scheme

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.104.1 |
| Server | Uvicorn | 0.24.0 |
| Database | PostgreSQL | 15 (alpine) |
| Async Driver | asyncpg | 0.29.0 |
| ORM | SQLAlchemy (async) | 2.0.23 |
| Validation | Pydantic | 2.5.0 |
| AI Model | Ollama / Llama3 | Latest |
| HTTP Client | httpx | 0.25.1 |
| Auth | python-jose (JWT HS256) + passlib (bcrypt) | 3.3.0 / 1.7.4 |
| Testing | pytest + pytest-asyncio | 7.4.3 / 0.21.1 |
| Container | Docker + Docker Compose | 20.10+ / 2.0+ |

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone <repository-url>
cd IBMS
cp .env.example .env          # edit values as needed
docker-compose build
docker-compose up -d
```

This starts three services:

| Service | Container | Port |
|---------|-----------|------|
| FastAPI API | `book_api` | 8000 |
| PostgreSQL 15 | `book_db` | 5432 |
| Ollama | `ollama` | 11434 |

After containers are running, pull the Llama3 model:

```bash
docker-compose exec ollama ollama pull llama3
```

Verify:

```bash
curl http://localhost:8000/health
# {"status":"OK","service":"Intelligent Book Management System","version":"1.0.0","environment":"development"}
```

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Option 2: Local Development

**Prerequisites:** Python 3.11+, PostgreSQL 13+, Ollama

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate         # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create database
createdb bookdb
# Optionally run: psql -U postgres -d bookdb -f app/db/init-db.sql

# 4. Create .env file
cp .env.example .env
# Set: DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb
# Set: OLLAMA_BASE_URL=http://localhost:11434

# 5. Start Ollama (separate terminal)
ollama serve
ollama pull llama3

# 6. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup, the application automatically creates all database tables via `Base.metadata.create_all` and starts 1 background worker for async summarization.

### Option 3: Quick Start Script

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Offers interactive choice between Docker Compose and local setup.

---

## API Endpoints

All endpoints (except health/root) require `Authorization: Bearer <token>` header.

### System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root — returns service info and docs link |
| GET | `/health` | Health check — returns status, version, environment |

### Authentication (`/api/v1/auth`)

| Method | Path | Description | Body |
|--------|------|-------------|------|
| POST | `/register` | Register new user, returns JWT | `{ "username": "...", "password": "..." }` |
| POST | `/login` | Login, returns JWT | `{ "username": "...", "password": "..." }` |
| GET | `/me` | Get current user info | — |

Token payload contains: `sub` (username), `user_id`, `role`, `exp`. Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30).

### Books (`/api/v1/books`)

| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/` | admin, user | Create a book |
| GET | `/` | admin, user | List all books |
| GET | `/{book_id}` | admin, user | Get book by UUID |
| PUT | `/{book_id}` | **admin only** | Update a book |
| DELETE | `/{book_id}` | **admin only** | Delete a book |

**Create Book body:**

```json
{
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt",
  "genre": "Technology",
  "year_published": 1999,
  "content": "Full book text..."
}
```

Books have a `status` field (`pending` → `processing` → `completed` / `failed`) that tracks background AI summarization progress.

### Reviews (`/api/v1/books`)

| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/{book_id}/reviews` | admin, user | Add a review (rating 0–5) |
| GET | `/{book_id}/reviews` | admin, user | Get all reviews for a book |

**Create Review body:**

```json
{
  "review_text": "Excellent book!",
  "rating": 4.5
}
```

### Recommendations (`/api/v1/recommendations`)

| Method | Path | Query Params | Description |
|--------|------|-------------|-------------|
| GET | `/` | `genre`, `limit` (1–50), `min_rating` (0–5) | Get recommendations filtered by genre/rating, excluding user's interacted books |
| GET | `/top-rated` | `genre`, `limit` (1–50), `min_reviews` | Get top-rated books by avg rating |
| GET | `/{book_id}/similar` | `limit` (1–50) | Get books similar to a specific book (same genre) |

### Summaries (`/api/v1/summary`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate summary from custom content via Ollama AI |
| GET | `/books/{book_id}` | Get book summary with aggregated ratings (auto-generates if missing) |
| POST | `/generate-summary` | Generate summary from title + content (query params) |

**Generate Summary body:**

```json
{
  "content": "Long text to summarize...",
  "title": "Optional title",
  "prompt": "Optional custom prompt"
}
```

---

## Project Structure

```
IBMS/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, lifespan, middleware, routers, health/root endpoints
│   ├── api/v1/
│   │   ├── auth.py                 # POST /register, /login, GET /me
│   │   ├── books.py                # CRUD endpoints with RBAC
│   │   ├── review.py               # POST/GET reviews per book
│   │   ├── recommendations.py      # Recommendations, top-rated, similar books
│   │   └── summary.py              # Summary generation and retrieval
│   ├── core/
│   │   ├── config.py               # Settings class (env vars, defaults, production validation)
│   │   ├── deps.py                 # get_current_user dependency wrapper
│   │   ├── job_store.py            # In-memory job status dict
│   │   ├── logging.py              # QueueHandler/QueueListener logging setup
│   │   ├── middleware.py           # X-Request-ID middleware (UUID per request)
│   │   ├── rbac.py                 # require_role() dependency factory
│   │   └── security.py            # hash_password, verify_password, create/decode JWT, get_current_user
│   ├── db/
│   │   ├── init_db.py              # Base.metadata.create_all via async engine
│   │   ├── init-db.sql             # uuid-ossp extension + indexes
│   │   └── session.py              # AsyncEngine (pool_size=10, max_overflow=20), AsyncSessionLocal, get_db
│   ├── model/
│   │   ├── base.py                 # declarative_base() + TimestampMixin (created_at, updated_at)
│   │   ├── models.py              # User, Book, Review, Recommendation, UserBookInteraction, AIModelUsage
│   │   └── user.py                 # Alternate User model definition
│   ├── schemas/
│   │   ├── __init__.py             # Re-exports: UserCreate, BookCreate, BookResponse, ReviewCreate, etc.
│   │   ├── ai.py                   # SummaryRequest, SummaryResponse
│   │   ├── auth.py                 # LoginRequest, TokenResponse
│   │   ├── book.py                 # BookBase, BookCreate, BookUpdate, BookResponse, BookListResponse
│   │   ├── common.py              # BaseSchema (Pydantic v2, from_attributes=True), TimestampMixin
│   │   ├── recommendation.py      # RecommendationResponse, SimilarBooksResponse
│   │   ├── review.py              # ReviewCreate, ReviewResponse, AggregatedRatingResponse
│   │   ├── summary.py             # GenerateSummaryRequest, BookSummaryResponse, GeneratedSummaryResponse
│   │   └── user.py                 # UserBase, UserCreate, UserResponse
│   ├── services/
│   │   ├── ai_service.py           # AIService: chunk text → parallel Ollama calls → reduce to final summary
│   │   ├── book_service.py         # CRUD operations on Book model
│   │   ├── queue.py                # asyncio.Queue task_queue, worker coroutine, task_status dict
│   │   ├── recommendation_service.py # Genre/rating/interaction-based recommendation queries
│   │   ├── review_service.py       # create_review, get_reviews_by_book with validation
│   │   └── summary_service.py      # Wraps AIService for book/custom/review summaries
│   ├── tasks/
│   │   └── task.py                 # process_book_summary using AIService + job_store
│   └── utils/
│       ├── exception.py            # AppException, NotFoundException, UnauthorizedException, InternalServerException
│       └── uitl.py                 # chunk_text() utility function
├── db/
│   └── init-db.sql/                # Docker-mounted init script directory
├── tests/
│   ├── conftest.py                 # In-memory SQLite fixtures (aiosqlite), sample_book, fiction_books
│   ├── test_book_schema.py
│   ├── test_book_service.py
│   ├── test_exception.py
│   ├── test_rbac.py
│   ├── test_recommendation_service.py
│   ├── test_review_schema.py
│   ├── test_review_service.py
│   └── test_security.py
├── dockerfile                      # Multi-stage build (python:3.11-slim), non-root appuser
├── docker-compose.yaml             # api + db (postgres:15-alpine) + ollama services
├── requirements.txt                # All Python dependencies
├── pytest.ini                      # pythonpath=., asyncio_mode=strict
├── quickstart.sh                   # Interactive setup script (Docker or local)
├── DEPLOYMENT_GUIDE.md             # Full deployment guide (Docker, local, AWS, CI/CD)
└── README.md
```

---

## Configuration

### Environment Variables

All variables are read via `os.getenv()` in `app/core/config.py` and `app/services/ai_service.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb` | SQLAlchemy async connection string |
| `APP_ENV` | `development` | Environment name (`development` / `production`) |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT HS256 signing key — **must change in production** |
| `ALGORITHM` | `HS256` | JWT algorithm (hardcoded) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API base URL (use `http://localhost:11434` for local dev) |
| `OLLAMA_MODEL` | `llama3` | Model name for Ollama |
| `OLLAMA_TIMEOUT` | `300.0` | HTTP timeout for Ollama requests (seconds) |
| `OLLAMA_MAX_CONCURRENCY` | `2` | Max parallel Ollama summarization requests |
| `OLLAMA_CHUNK_SIZE` | `1000` | Words per text chunk for map-reduce summarization |
| `OLLAMA_CHUNK_OVERLAP` | `100` | Word overlap between consecutive chunks |

**Production validation:** If `APP_ENV=production` and `SECRET_KEY` is still the default, the app raises `ValueError` on startup.

### Docker Compose Environment

When running via Docker Compose, the `api` service overrides:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/bookdb` (uses `db` service hostname)
- `OLLAMA_BASE_URL=http://ollama:11434` (uses `ollama` service hostname)

---

## Database Schema

Tables are auto-created by SQLAlchemy on startup via `Base.metadata.create_all`. The `init-db.sql` script adds the `uuid-ossp` extension and indexes.

### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key, auto-increment |
| username | String | Unique, not null, indexed |
| email | String | Unique, not null |
| hashed_password | String | Not null |
| roles | String | Not null (comma-separated, e.g. `"user"`, `"admin"`) |

### books

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary key (uuid4) |
| title | String | Not null |
| author | String | Not null |
| genre | String | Nullable, indexed |
| year_published | Integer | Nullable |
| content | Text | Not null |
| summary | Text | Nullable (populated by AI) |
| status | String | Default `"pending"` — tracks summarization state |
| created_at | DateTime | Auto-set |
| updated_at | DateTime | Auto-updated |

### reviews

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| book_id | UUID | FK → `books.id` (ON DELETE CASCADE), indexed |
| user_id | Integer | Not null, indexed |
| review_text | Text | Nullable |
| rating | Float | 0.0–5.0 |

### recommendations

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| book_id | UUID | FK → `books.id` (ON DELETE CASCADE) |
| recommended_book_id | UUID | FK → `books.id` (ON DELETE CASCADE) |

### user_book_interactions

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Not null |
| book_id | UUID | FK → `books.id` (ON DELETE CASCADE) |
| interaction_type | String | Not null |
| timestamp | String | Not null |

### ai_model_usages

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary key |
| model_name | String | Not null |
| usage_count | Integer | Default 0 |

---

## Architecture Details

### Application Lifecycle (`app/main.py`)

On startup:
1. Creates all database tables via `Base.metadata.create_all`
2. Runs `init_db_model()` for any additional initialization
3. Starts 1 background `asyncio` worker consuming from `task_queue`

On shutdown:
1. Disposes the async database engine

### AI Summarization Pipeline (`app/services/ai_service.py`)

Uses a **map-reduce** strategy:
1. **Chunk** — Split text into chunks of `OLLAMA_CHUNK_SIZE` words with `OLLAMA_CHUNK_OVERLAP` overlap
2. **Map** — Summarize each chunk concurrently (bounded by `asyncio.Semaphore(OLLAMA_MAX_CONCURRENCY)`) via `POST` to `{OLLAMA_BASE_URL}/api/generate`
3. **Reduce** — Combine all partial summaries and generate a final coherent summary

### Background Queue (`app/services/queue.py`)

- `task_queue` — `asyncio.Queue` holding `(task_id, book_id)` tuples
- `worker()` — Long-running coroutine that dequeues tasks, calls `AIService.generate_book_summary()`, and updates the book's `summary` and `status` fields
- `task_status` — In-memory dict tracking task state

### Security Flow

1. **Registration** — Password hashed with bcrypt via `passlib.CryptContext`, JWT token returned immediately
2. **Login** — Verify password → create JWT with `sub`, `user_id`, `role` claims
3. **Authorization** — `get_current_user` extracts and validates JWT from `Authorization: Bearer` header
4. **RBAC** — `require_role("admin", "user")` dependency checks the `role` claim against allowed roles

### Middleware

- **CORS** — Configured globally via `CORSMiddleware` (currently `allow_origins=["*"]`)
- **Request ID** — Every request gets a UUID stored in `contextvars` and returned as `X-Request-ID` header

### Custom Exception Hierarchy

| Exception | Status Code | Usage |
|-----------|-------------|-------|
| `AppException` | 400 (configurable) | Base exception, caught by global handler |
| `NotFoundException` | 404 | Book/resource not found |
| `UnauthorizedException` | 401 | Auth failures |
| `InternalServerException` | 500 | Internal errors |

---

## Testing

Tests use an **in-memory SQLite database** (`sqlite+aiosqlite:///:memory:`) configured in `tests/conftest.py`, so no external services are needed.

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific file
pytest tests/test_book_service.py

# Verbose
pytest -v

# Inside Docker
docker-compose exec api pytest
```

### Test Files

| File | Tests |
|------|-------|
| `test_security.py` | Password hashing, JWT creation/decoding, token validation |
| `test_rbac.py` | Role-based access control, `require_role()` dependency |
| `test_book_schema.py` | Pydantic `BookCreate`, `BookUpdate`, `BookResponse` validation |
| `test_book_service.py` | Book CRUD service functions with async DB |
| `test_review_schema.py` | `ReviewCreate`, `ReviewResponse`, `AggregatedRatingResponse` validation |
| `test_review_service.py` | Review creation, retrieval, rating validation |
| `test_recommendation_service.py` | Genre filtering, rating filtering, similar books |
| `test_exception.py` | Custom exception classes and status codes |

### Test Fixtures (`conftest.py`)

- `db_engine` — Function-scoped async SQLite engine
- `db` — Function-scoped `AsyncSession` with auto table create/drop
- `sample_book` — Single book fixture
- `fiction_books` — 4 books (3 Fiction + 1 Science) with reviews attached

Configuration: `pytest.ini` sets `pythonpath = .` and `asyncio_mode = strict`.

---

## Troubleshooting

**Ollama model not found or timeout**
```bash
# Pull model into container
docker-compose exec ollama ollama pull llama3

# Verify
curl http://localhost:11434/api/tags

# For large texts, increase timeout: OLLAMA_TIMEOUT=600
```

**Database connection refused**
```bash
docker-compose ps db          # Check container status
docker-compose logs db        # Check logs
docker-compose restart db     # Restart

# Local dev: ensure DATABASE_URL points to localhost, not "db"
```

**SECRET_KEY error on startup**
```
ValueError: SECRET_KEY must be set in production!
# Generate a strong key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Authentication token expired**
```
Tokens expire after ACCESS_TOKEN_EXPIRE_MINUTES (default: 30 min).
Login again via POST /api/v1/auth/login to get a new token.
```

**Tests failing**
```bash
# Ensure aiosqlite is installed (used by conftest.py for in-memory SQLite)
pip install aiosqlite
pytest --cache-clear -v
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Ollama](https://ollama.ai)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for Docker production hardening, AWS deployment, CI/CD, and backup/recovery

---

*Last Updated: February 22, 2026*
