from pydantic import BaseModel

class RecommendationResponse(BaseModel):
    book_id: int
    recommended_book_id: int

    class Config:
        from_attributes = True
