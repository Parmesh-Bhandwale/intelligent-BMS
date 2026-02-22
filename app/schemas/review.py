from typing import Optional
from uuid import UUID
from app.schemas.common import BaseSchema


class ReviewBase(BaseSchema):
    """Base schema for review"""
    review_text: str
    rating: float


class ReviewCreate(ReviewBase):
    """Schema for creating a review"""
    pass


class ReviewUpdate(BaseSchema):
    """Schema for updating a review"""
    review_text: Optional[str] = None
    rating: Optional[float] = None


class ReviewResponse(ReviewBase):
    """Schema for review response"""
    id: int
    user_id: int
    book_id: UUID


class ReviewListResponse(BaseSchema):
    """Schema for paginated review list response"""
    total: int
    skip: int
    limit: int
    items: list[ReviewResponse]


class AggregatedRatingResponse(BaseSchema):
    """Schema for aggregated rating statistics"""
    book_id: UUID
    average_rating: float
    total_reviews: int
    min_rating: float
    max_rating: float
