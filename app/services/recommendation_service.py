"""
Recommendation Service Module

Handles book recommendations based on:
- Genre similarity
- User reading history
- Rating patterns
- Collaborative filtering
"""

import logging
import uuid as _uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_

from app.model.models import Book, Review, UserBookInteraction
from app.schemas.recommendation import RecommendationResponse

logger = logging.getLogger(__name__)


async def get_recommendations(
    db: AsyncSession,
    user_id: Optional[int] = None,
    genre: Optional[str] = None,
    limit: int = 5,
    min_rating: float = 0.0
) -> List[RecommendationResponse]:
    """
    Get book recommendations based on user preferences and patterns
    
    Args:
        db: Database session
        user_id: ID of the user (optional, for personalized recommendations)
        genre: Filter by genre (optional)
        limit: Maximum number of recommendations
        min_rating: Minimum average rating for books
        
    Returns:
        List of recommended books
    """
    logger.info(f"Getting recommendations for user {user_id}, genre {genre}, limit {limit}")
    
    # Build the base query with rating subquery
    avg_rating_subquery = select(
        Review.book_id,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).group_by(Review.book_id).subquery()
    
    # Start building the query
    query = select(Book).outerjoin(
        avg_rating_subquery,
        Book.id == avg_rating_subquery.c.book_id
    )
    
    # Apply filters
    conditions = []
    
    if genre:
        conditions.append(Book.genre == genre)
    
    # Filter by minimum rating if provided
    if min_rating > 0:
        conditions.append(avg_rating_subquery.c.avg_rating >= min_rating)
    
    # Exclude books the user has already interacted with
    if user_id:
        user_interactions = select(UserBookInteraction.book_id).where(
            UserBookInteraction.user_id == user_id
        )
        conditions.append(~Book.id.in_(user_interactions))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Order by average rating descending, then by popularity
    query = query.order_by(
        avg_rating_subquery.c.avg_rating.desc().nullslast(),
        avg_rating_subquery.c.review_count.desc().nullslast()
    ).limit(limit)
    
    result = await db.execute(query)
    books = result.scalars().all()
    
    logger.info(f"Found {len(books)} recommendations")
    
    recommendations = []
    for book in books:
        # Get average rating for this book
        rating_stmt = select(
            func.avg(Review.rating),
            func.count(Review.id)
        ).where(Review.book_id == book.id)
        
        rating_result = await db.execute(rating_stmt)
        avg_rating, review_count = rating_result.one()
        
        rec = RecommendationResponse(
            id=str(book.id),
            title=book.title,
            author=book.author,
            genre=book.genre,
            year_published=book.year_published,
            summary=book.summary,
            average_rating=float(avg_rating) if avg_rating else 0,
            review_count=review_count,
            reason="Matches your preferences" if genre or user_id else "Highly rated"
        )
        recommendations.append(rec)
    
    return recommendations


async def get_similar_books(
    db: AsyncSession,
    book_id: str,
    limit: int = 5
) -> List[RecommendationResponse]:
    """
    Get books similar to a given book (same genre, similar authors)
    
    Args:
        db: Database session
        book_id: ID of the reference book
        limit: Maximum number of recommendations
        
    Returns:
        List of similar books
    """
    logger.info(f"Getting similar books to {book_id}")
    book_id = _uuid.UUID(book_id) if isinstance(book_id, str) else book_id
    
    # Get the reference book
    ref_book_stmt = select(Book).where(Book.id == book_id)
    ref_result = await db.execute(ref_book_stmt)
    ref_book = ref_result.scalar_one_or_none()
    
    if not ref_book:
        logger.warning(f"Book {book_id} not found")
        return []
    
    # Find similar books (same genre, exclude the reference book)
    similar_stmt = select(Book).where(
        and_(
            Book.genre == ref_book.genre,
            Book.id != book_id
        )
    ).limit(limit)
    
    similar_result = await db.execute(similar_stmt)
    books = similar_result.scalars().all()
    
    recommendations = []
    for book in books:
        # Get average rating
        rating_stmt = select(
            func.avg(Review.rating),
            func.count(Review.id)
        ).where(Review.book_id == book.id)
        
        rating_result = await db.execute(rating_stmt)
        avg_rating, review_count = rating_result.one()
        
        rec = RecommendationResponse(
            id=str(book.id),
            title=book.title,
            author=book.author,
            genre=book.genre,
            year_published=book.year_published,
            summary=book.summary,
            average_rating=float(avg_rating) if avg_rating else 0,
            review_count=review_count,
            reason=f"Similar to {ref_book.title}"
        )
        recommendations.append(rec)
    
    return recommendations


async def get_top_rated_books(
    db: AsyncSession,
    genre: Optional[str] = None,
    limit: int = 5,
    min_reviews: int = 1
) -> List[RecommendationResponse]:
    """
    Get top-rated books, optionally filtered by genre
    
    Args:
        db: Database session
        genre: Optional genre filter
        limit: Maximum number of books
        min_reviews: Minimum number of reviews required
        
    Returns:
        List of top-rated books
    """
    logger.info(f"Getting top-rated books, genre {genre}, min_reviews {min_reviews}")
    
    # Subquery for average rating and review count
    rating_stats = select(
        Review.book_id,
        func.avg(Review.rating).label("avg_rating"),
        func.count(Review.id).label("review_count")
    ).group_by(Review.book_id).subquery()
    
    # Main query
    query = select(Book).join(
        rating_stats,
        Book.id == rating_stats.c.book_id
    )
    
    conditions = [rating_stats.c.review_count >= min_reviews]
    
    if genre:
        conditions.append(Book.genre == genre)
    
    query = query.where(and_(*conditions)).order_by(
        rating_stats.c.avg_rating.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    books = result.scalars().all()
    
    recommendations = []
    for book in books:
        # Get stats for this book
        stats_stmt = select(rating_stats).where(rating_stats.c.book_id == book.id)
        stats_result = await db.execute(stats_stmt)
        stats = stats_result.one()
        
        rec = RecommendationResponse(
            id=str(book.id),
            title=book.title,
            author=book.author,
            genre=book.genre,
            year_published=book.year_published,
            summary=book.summary,
            average_rating=float(stats.avg_rating),
            review_count=stats.review_count,
            reason="Top rated in this category"
        )
        recommendations.append(rec)
    
    return recommendations
