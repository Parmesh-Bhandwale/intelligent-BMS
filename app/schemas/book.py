from typing import Optional, List
from uuid import UUID
from app.schemas.common import BaseSchema


# ---------- Base ----------

class BookBase(BaseSchema):

    title: str
    author: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    content: Optional[str] = None


# ---------- Requests ----------

class BookCreate(BookBase):
    pass


class BookUpdate(BaseSchema):

    title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    year_published: Optional[int] = None
    content: Optional[str] = None


# ---------- Responses ----------

class BookResponse(BookBase):

    id: UUID
    summary: Optional[str] = None


class BookListResponse(BaseSchema):

    total: int
    items: List[BookResponse]
