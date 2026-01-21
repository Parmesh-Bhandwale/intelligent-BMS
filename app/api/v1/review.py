import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{book_id}/reviews")
async def add_review(book_id: str):
    logger.info(f"Adding review for book {book_id}")
    return {"message": "Review added (mocked)"}
