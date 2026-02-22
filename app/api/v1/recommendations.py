import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.recommendation_service import (
    get_recommendations,
    get_similar_books,
    get_top_rated_books
)
from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.db.session import get_db
from app.schemas.recommendation import RecommendationResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/",
    response_model=list[RecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get book recommendations"
)
async def recommend(
    genre: Optional[str] = Query(None, description="Filter by genre"),
    limit: int = Query(5, ge=1, le=50, description="Number of recommendations"),
    min_rating: float = Query(0.0, ge=0, le=5, description="Minimum average rating"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("admin", "user"))
):
    """
    Get personalized book recommendations based on user preferences.
    
    - **genre**: Optional genre filter (e.g., "Fiction", "Science")
    - **limit**: Maximum number of recommendations (default: 5, max: 50)
    - **min_rating**: Filter books with minimum average rating
    """
    logger.info(f"User {user['id']} requested recommendations")
    return await get_recommendations(
        db,
        user_id=user["id"],
        genre=genre,
        limit=limit,
        min_rating=min_rating
    )


@router.get(
    "/top-rated",
    response_model=list[RecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get top-rated books"
)
async def get_top_rated(
    genre: Optional[str] = Query(None, description="Filter by genre"),
    limit: int = Query(5, ge=1, le=50, description="Number of books"),
    min_reviews: int = Query(1, ge=1, description="Minimum number of reviews"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("admin", "user"))
):
    """
    Get top-rated books, optionally filtered by genre.
    
    - **genre**: Optional genre filter
    - **limit**: Maximum number of books to return
    - **min_reviews**: Minimum number of reviews required
    """
    logger.info(f"User {user['id']} requested top-rated books")
    return await get_top_rated_books(
        db,
        genre=genre,
        limit=limit,
        min_reviews=min_reviews
    )


@router.get(
    "/{book_id}/similar",
    response_model=list[RecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get similar books"
)
async def similar_books(
    book_id: str,
    limit: int = Query(5, ge=1, le=50, description="Number of similar books"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role("admin", "user"))
):
    """
    Get books similar to a specific book.
    
    - **book_id**: ID of the reference book
    - **limit**: Maximum number of similar books to return
    """
    logger.info(f"User {user['id']} requested similar books for {book_id}")
    return await get_similar_books(db, book_id=book_id, limit=limit)
