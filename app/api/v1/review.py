from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.review import ReviewCreate
from app.services.review_service import *
from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.db.session import get_db


router = APIRouter(prefix="/books", tags=["Reviews"])


# POST /books/{id}/reviews — any authenticated user
@router.post("/{book_id}/reviews")
async def add_review(
    book_id: str,
    review: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "user"))
):

    return await create_review(
        db,
        book_id,
        user["id"],
        review
    )


# GET /books/{id}/reviews — any authenticated user
@router.get("/{book_id}/reviews")
async def get_reviews(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "user"))
):

    return await get_reviews_by_book(db, book_id)
