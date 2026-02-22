from typing import Optional, List
from app.schemas.common import BaseSchema


class RecommendationResponse(BaseSchema):
    """Schema for book recommendation response"""
    id: str
    title: str
    author: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None
    average_rating: float = 0.0
    review_count: int = 0
    reason: str  # Why this book is recommended


class RecommendationsListResponse(BaseSchema):
    """Schema for paginated recommendations list"""
    total: int
    recommendations: List[RecommendationResponse]


class SimilarBooksResponse(BaseSchema):
    """Schema for similar books response"""
    reference_book_id: str
    similar_books: List[RecommendationResponse]
