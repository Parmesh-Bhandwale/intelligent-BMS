import asyncio
import logging
import db
from db.session import AsyncSessionLocal

from app.services.ai_service import AIService
from app.model.models import Book

service = AIService()

logger = logging.getLogger(__name__)

task_queue = asyncio.Queue()
task_status = {}


async def process_task(task_id: str, book_id: str):
    async with AsyncSessionLocal() as db:
        book = None

        try:
            book = await db.get(Book, book_id)

            if not book:
                raise Exception("Book not found")

            book.status = "processing"
            await db.commit()

            summary = await service.generate_book_summary(
                book.title,
                book.content
            )

            book.summary = summary
            book.status = "completed"

            await db.commit()

        except Exception:
            logger.exception("Task failed")

            if book:
                book.status = "failed"
                await db.commit()


async def worker(worker_id: int):

    logger.info(f"Worker-{worker_id} started")

    while True:

        task_id, book_id = await task_queue.get()

        try:
            task_status[task_id] = "processing"

            await process_task(task_id, book_id)

            task_status[task_id] = "done"

        finally:
            task_queue.task_done()
