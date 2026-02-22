import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi

from app.core.logging import setup_logging
from app.core.middleware import request_id_middleware
from app.core.config import settings
from app.utils.exception import AppException

from app.api.v1 import auth, books, review, recommendations, summary
from app.db.init_db import init_db_model
from app.db.session import close_db, engine, AsyncSessionLocal
from app.services.queue import worker


# ==================== CONFIG ==================== #

WORKERS = 1
API_V1_PREFIX = "/api/v1"

# Security scheme for Swagger
security = HTTPBearer()


# ==================== LOGGING ==================== #

setup_logging()
logger = logging.getLogger(__name__)


# ==================== LIFECYCLE EVENTS ==================== #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database and tables
    async with engine.begin() as conn:
        from app.model.base import Base
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # Create a session for initialization
    async with AsyncSessionLocal() as db:
        await init_db_model(db, engine)
    logger.info("Database initialized")
    
    # Start background workers
    for i in range(WORKERS):
        asyncio.create_task(worker(i + 1))
    logger.info(f"{WORKERS} background workers started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")


# ==================== APP CREATION ==================== #

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)


# ==================== CORS MIDDLEWARE ==================== #

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== CUSTOM MIDDLEWARE ==================== #

app.middleware("http")(request_id_middleware)


# ==================== EXCEPTION HANDLERS ==================== #

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException
):
    """Handle custom application exceptions"""
    logger.error(f"Handled exception: {exc.message}", extra={
        "status_code": exc.status_code,
        "path": request.url.path
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {exc}", extra={
        "path": request.url.path
    })
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ==================== ROUTERS ==================== #

app.include_router(
    auth.router,
    prefix=f"{API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    books.router,
    prefix=f"{API_V1_PREFIX}/books",
    tags=["Books"]
)

app.include_router(
    review.router,
    prefix=f"{API_V1_PREFIX}/books",
    tags=["Reviews"]
)

app.include_router(
    recommendations.router,
    prefix=f"{API_V1_PREFIX}",
    tags=["Recommendations"]
)

app.include_router(
    summary.router,
    prefix=f"{API_V1_PREFIX}",
    tags=["Summary & Recommendations"]
)


# ==================== HEALTH CHECK ==================== #

@app.get(
    "/health",
    tags=["System"],
    summary="Health check endpoint"
)
async def health():
    """
    Health check endpoint for monitoring.
    Returns current service status.
    """
    logger.info("Health check")
    
    return {
        "status": "OK",
        "service": "Intelligent Book Management System",
        "version": settings.API_VERSION,
        "environment": settings.APP_ENV
    }


# ==================== ROOT ENDPOINT ==================== #

@app.get(
    "/",
    tags=["System"],
    summary="API root endpoint"
)
async def root():
    """
    Welcome to the Intelligent Book Management System API.
    
    Visit `/docs` for interactive API documentation.
    """
    return {
        "message": "Welcome to Intelligent Book Management System",
        "docs": "/docs",
        "api_version": settings.API_VERSION,
        "service": settings.API_TITLE
    }


# ==================== CUSTOM OPENAPI SCHEMA ==================== #

def custom_openapi():
    """Customize OpenAPI schema with Bearer auth"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Add Bearer token security scheme — name MUST be "HTTPBearer" to match
    # what FastAPI auto-generates on each endpoint from HTTPBearer() dependency
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (without 'Bearer ' prefix)"
        }
    }
    
    # Apply globally to all endpoints
    openapi_schema["security"] = [{"HTTPBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
