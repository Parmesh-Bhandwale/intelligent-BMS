from typing import Optional
from app.schemas.common import BaseSchema


class GenerateSummaryRequest(BaseSchema):
    """Schema for summary generation request"""
    content: str
    title: Optional[str] = "Content"
    prompt: Optional[str] = None


class BookSummaryResponse(BaseSchema):
    """Schema for book summary response with ratings"""
    book_id: str
    title: str
    author: Optional[str] = None
    summary: str
    average_rating: float = 0.0
    total_reviews: int = 0


class GeneratedSummaryResponse(BaseSchema):
    """Schema for generated summary response"""
    title: str
    summary: str
    character_count: int
    word_count: int


class ReviewSummaryResponse(BaseSchema):
    """Schema for aggregated review summary"""
    book_id: str
    total_reviews: int
    summary: str
    common_themes: list[str] = []
    positive_aspects: list[str] = []
    improvement_areas: list[str] = []
