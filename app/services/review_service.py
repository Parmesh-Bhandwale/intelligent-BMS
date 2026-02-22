"""
Review Service Module

Handles all review-related business logic including:
- Creating and managing reviews
- Calculating aggregated ratings
- Retrieving reviews with filtering
"""

import logging
import uuid as _uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.model.models import Review, Book
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from app.utils.exception import NotFoundException, AppException

logger = logging.getLogger(__name__)


async def create_review(
    db: AsyncSession,
    book_id: str,
    user_id: int,
    review_data: ReviewCreate
) -> ReviewResponse:
    """
    Create a new review for a book
    
    Args:
        db: Database session
        book_id: ID of the book being reviewed
        user_id: ID of the user creating the review
        review_data: Review creation data
        
    Returns:
        Created review object
        
    Raises:
        NotFoundException: If book not found
        AppException: If validation fails
    """
    logger.info(f"Creating review for book {book_id} by user {user_id}")
    book_id = _uuid.UUID(book_id) if isinstance(book_id, str) else book_id
    
    # Verify book exists
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    
    if not book:
        logger.warning(f"Book {book_id} not found for review")
        raise NotFoundException(f"Book with id {book_id} not found")
    
    # Validate rating
    if review_data.rating < 0 or review_data.rating > 5:
        raise AppException("Rating must be between 0 and 5", 400)
    
    # Create review
    review = Review(
        book_id=book_id,
        user_id=user_id,
        review_text=review_data.review_text,
        rating=review_data.rating
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Review {review.id} created successfully")
    return ReviewResponse.from_orm(review)


async def get_reviews_by_book(
    db: AsyncSession,
    book_id: str,
    skip: int = 0,
    limit: int = 10
) -> dict:
    """
    Get all reviews for a specific book
    
    Args:
        db: Database session
        book_id: ID of the book
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        Dictionary with reviews and metadata
        
    Raises:
        NotFoundException: If book not found
    """
    logger.info(f"Fetching reviews for book {book_id}")
    book_id = _uuid.UUID(book_id) if isinstance(book_id, str) else book_id
    
    # Verify book exists
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    
    if not book:
        raise NotFoundException(f"Book with id {book_id} not found")
    
    # Get reviews
    stmt = select(Review).where(
        Review.book_id == book_id
    ).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    
    # Get total count
    count_stmt = select(func.count(Review.id)).where(Review.book_id == book_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()
    
    logger.info(f"Found {len(reviews)} reviews for book {book_id}")
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [ReviewResponse.from_orm(r) for r in reviews]
    }


async def get_review_by_id(db: AsyncSession, review_id: int) -> ReviewResponse:
    """
    Get a specific review by ID
    
    Args:
        db: Database session
        review_id: ID of the review
        
    Returns:
        Review object
        
    Raises:
        NotFoundException: If review not found
    """
    logger.info(f"Fetching review {review_id}")
    
    stmt = select(Review).where(Review.id == review_id)
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    
    if not review:
        logger.warning(f"Review {review_id} not found")
        raise NotFoundException(f"Review with id {review_id} not found")
    
    return ReviewResponse.from_orm(review)


async def update_review(
    db: AsyncSession,
    review_id: int,
    user_id: int,
    review_data: ReviewUpdate
) -> ReviewResponse:
    """
    Update a review
    
    Args:
        db: Database session
        review_id: ID of the review
        user_id: ID of the user updating (must own the review)
        review_data: Updated review data
        
    Returns:
        Updated review object
        
    Raises:
        NotFoundException: If review not found
        AppException: If user doesn't own the review or validation fails
    """
    logger.info(f"Updating review {review_id}")
    
    stmt = select(Review).where(Review.id == review_id)
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    
    if not review:
        logger.warning(f"Review {review_id} not found")
        raise NotFoundException(f"Review with id {review_id} not found")
    
    if review.user_id != user_id:
        logger.warning(f"User {user_id} unauthorized to update review {review_id}")
        raise AppException("You can only update your own reviews", 403)
    
    # Update fields
    if review_data.review_text is not None:
        review.review_text = review_data.review_text
    
    if review_data.rating is not None:
        if review_data.rating < 0 or review_data.rating > 5:
            raise AppException("Rating must be between 0 and 5", 400)
        review.rating = review_data.rating
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    logger.info(f"Review {review_id} updated successfully")
    return ReviewResponse.from_orm(review)


async def delete_review(
    db: AsyncSession,
    review_id: int,
    user_id: int
) -> dict:
    """
    Delete a review
    
    Args:
        db: Database session
        review_id: ID of the review
        user_id: ID of the user deleting (must own the review)
        
    Returns:
        Success message
        
    Raises:
        NotFoundException: If review not found
        AppException: If user doesn't own the review
    """
    logger.info(f"Deleting review {review_id}")
    
    stmt = select(Review).where(Review.id == review_id)
    result = await db.execute(stmt)
    review = result.scalar_one_or_none()
    
    if not review:
        logger.warning(f"Review {review_id} not found")
        raise NotFoundException(f"Review with id {review_id} not found")
    
    if review.user_id != user_id:
        logger.warning(f"User {user_id} unauthorized to delete review {review_id}")
        raise AppException("You can only delete your own reviews", 403)
    
    await db.delete(review)
    await db.commit()
    
    logger.info(f"Review {review_id} deleted successfully")
    return {"message": "Review deleted successfully"}


async def get_aggregated_rating(db: AsyncSession, book_id: str) -> dict:
    """
    Get aggregated rating statistics for a book
    
    Args:
        db: Database session
        book_id: ID of the book
        
    Returns:
        Dictionary with rating statistics
        
    Raises:
        NotFoundException: If book not found
    """
    logger.info(f"Fetching aggregated rating for book {book_id}")
    book_id = _uuid.UUID(book_id) if isinstance(book_id, str) else book_id
    
    # Verify book exists
    book_stmt = select(Book).where(Book.id == book_id)
    book_result = await db.execute(book_stmt)
    book = book_result.scalar_one_or_none()
    
    if not book:
        raise NotFoundException(f"Book with id {book_id} not found")
    
    # Calculate statistics
    stmt = select(
        func.avg(Review.rating).label("average_rating"),
        func.count(Review.id).label("total_reviews"),
        func.min(Review.rating).label("min_rating"),
        func.max(Review.rating).label("max_rating")
    ).where(Review.book_id == book_id)
    
    result = await db.execute(stmt)
    stats = result.one()
    
    return {
        "book_id": str(book_id),
        "average_rating": float(stats.average_rating) if stats.average_rating else 0,
        "total_reviews": stats.total_reviews,
        "min_rating": float(stats.min_rating) if stats.min_rating else 0,
        "max_rating": float(stats.max_rating) if stats.max_rating else 0
    }
