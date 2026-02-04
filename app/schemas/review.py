from pydantic import BaseModel
from typing import Optional

class ReviewCreate(BaseModel):
    book_id: int
    review_text: Optional[str] = None
    rating: float

class ReviewResponse(ReviewCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
