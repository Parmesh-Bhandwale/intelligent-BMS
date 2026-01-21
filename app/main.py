from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from app.core.logging import setup_logging
from app.core.middleware import request_id_middleware
from app.utils.exceptions import AppException
from app.api.v1 import auth, books, reviews, recommendations

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Intelligent Book Management System",
    version="1.0.0"
)

app.middleware("http")(request_id_middleware)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"Handled exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

# Versioned API
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_V1_PREFIX}/auth", tags=["Auth"])
app.include_router(books.router, prefix=f"{API_V1_PREFIX}/books", tags=["Books"])
app.include_router(reviews.router, prefix=f"{API_V1_PREFIX}/books", tags=["Reviews"])
app.include_router(
    recommendations.router,
    prefix=f"{API_V1_PREFIX}",
    tags=["Recommendations"]
)

@app.get("/health")
async def health():
    logger.info("Health check")
    return {"status": "OK"}
