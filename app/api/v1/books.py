import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.book import BookCreate
from app.services.book_service import (
    create_book, get_all_books, get_book_by_id
)
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/")
async def add_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
    logger.info("POST /books")
    new_book = await create_book(db, book)
    new_book.summary = await AIService.generate_summary(book.title)
    return new_book

@router.get("/")
async def list_books(db: AsyncSession = Depends(get_db)):
    logger.info("GET /books")
    return await get_all_books(db)

@router.get("/{book_id}")
async def get_book(book_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"GET /books/{book_id}")
    return await get_book_by_id(db, book_id)
