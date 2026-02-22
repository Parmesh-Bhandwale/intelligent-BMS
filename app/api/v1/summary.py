"""
Summary API Endpoints

Handles:
- Book summary generation
- Summary retrieval for books
- Custom text summarization
- Review aggregation summaries
"""

import logging
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.db.session import get_db
from app.model.models import Book, Review
from app.schemas.summary import (
    GenerateSummaryRequest,
    BookSummaryResponse,
    GeneratedSummaryResponse
)
from app.services.summary_service import (
    generate_book_summary,
    generate_custom_summary
)
from app.utils.exception import NotFoundException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/summary", tags=["Summary & Recommendations"])


@router.post(
    "/generate",
    response_model=GeneratedSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate summary from content"
)
async def generate_summary_endpoint(
    request: GenerateSummaryRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("admin", "user"))
):
    """
    Generate a summary for provided content using Ollama AI.
    
    - **content**: Text content to summarize
    - **title**: Optional title for the content
    - **prompt**: Optional custom prompt for summarization
    """
    logger.info(f"User {user['id']} requested summary generation")
    
    try:
        summary = await generate_custom_summary(
            content=request.content,
            prompt=request.prompt
        )
        
        return GeneratedSummaryResponse(
            title=request.title,
            summary=summary,
            character_count=len(request.content),
            word_count=len(request.content.split())
        )
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary"
        )


@router.get(
    "/books/{book_id}",
    response_model=BookSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get book summary with ratings"
)
async def get_book_summary(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("admin", "user"))
):
    """
    Get summary and aggregated ratings for a specific book.
    
    - **book_id**: ID of the book
    """
    logger.info(f"User {user['id']} requested summary for book {book_id}")
    
    # Fetch book
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    
    if not book:
        raise NotFoundException(f"Book with id {book_id} not found")
    
    # Calculate aggregated ratings
    rating_stmt = select(
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("total_reviews")
    ).where(Review.book_id == book_id)
    
    rating_result = await db.execute(rating_stmt)
    avg_rating, total_reviews = rating_result.one()
    
    # If no summary exists, generate one
    if not book.summary and book.content:
        try:
            logger.info(f"Generating summary for book {book_id}")
            book.summary = await generate_book_summary(book.title, book.content)
            db.add(book)
            await db.commit()
            await db.refresh(book)
        except Exception as e:
            logger.warning(f"Could not generate summary for book {book_id}: {e}")
    
    return BookSummaryResponse(
        book_id=str(book.id),
        title=book.title,
        author=book.author,
        summary=book.summary or "No summary available",
        average_rating=float(avg_rating) if avg_rating else 0,
        total_reviews=total_reviews or 0
    )


# POST /generate-summary
@router.post("/generate-summary")
async def generate_summary(
    title: str,
    content: str,
    user=Depends(require_role("admin", "user"))
):

    ai = AIService()

    summary = await ai.generate_book_summary(title, content)

    return {"summary": summary}
