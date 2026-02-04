from pydantic import BaseModel
from typing import Optional

class BookCreate(BaseModel):
    title: str
    author: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    content: str
    summary: Optional[str] = None
    
class BookResponse(BookCreate):
    id: int
    summary: Optional[str]

    class Config:
        from_attributes = True
