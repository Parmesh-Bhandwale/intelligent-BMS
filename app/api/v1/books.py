import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.book import BookCreate
from app.services.book_service import (
    create_book, get_all_books, get_book_by_id
)
from app.services.ai_service import AIService
from db.session import get_db
from app.services.queue import task_queue, task_status
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


# @router.post("/")
# async def add_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
#     logger.info("POST /books")
#     book.summary = await AIService().generate_book_summary(book.title, book.content)
#     book = await create_book(db, book)
#     return book

@router.get("/")
async def list_books(db: AsyncSession = Depends(get_db)):
    logger.info("GET /books")
    return await get_all_books(db)

@router.get("/{book_id}")
async def get_book(book_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"GET /books/{book_id}")
    return await get_book_by_id(db, book_id)

@router.post("/books/summarize")
async def summarize_book(
    title: str,
    content: str
):
    logger.info("POST /books/summarize")
    ai_service = AIService()
    summary = await ai_service.generate_book_summary(title, content)
    return {"title": title, "summary": summary}


@router.post("/add")
async def create_book_endpoint(book: BookCreate, db: AsyncSession = Depends(get_db)):

    logger.info("Creating new book")
    db_book = await create_book(db, book)

    # Queue summary job
    task_id = str(uuid.uuid4())

    task_status[task_id] = "queued"

    await task_queue.put((task_id, db_book.id))

    return {
        "book_id": db_book.id,
        "task_id": task_id,
        "status": "summary queued"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):

    status = task_status.get(task_id)

    if not status:
        return {"error": "Invalid task"}

    return {"status": status}

