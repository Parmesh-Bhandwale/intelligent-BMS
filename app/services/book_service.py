import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.model.models import Book
from app.utils.exception import NotFoundException

logger = logging.getLogger(__name__)

async def create_book(db: AsyncSession, data):
    logger.info("Creating book")
    book = Book(id=str(uuid.uuid4()), **data.dict())
    db.add(book)
    await db.commit()
    return book

async def get_all_books(db: AsyncSession):
    logger.info("Fetching all books")
    result = await db.execute(select(Book))
    return result.scalars().all()

async def get_book_by_id(db: AsyncSession, book_id: str):
    logger.info(f"Fetching book {book_id}")
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        logger.warning("Book not found")
        raise NotFoundException("Book not found")
    return book

async def update_book_summary(db: AsyncSession, book_id: str, summary: str):
    logger.info(f"Updating summary for book {book_id}")
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        logger.warning("Book not found for summary update")
        raise NotFoundException("Book not found")
    book.summary = summary
    db.add(book)
    await db.commit()
    return book