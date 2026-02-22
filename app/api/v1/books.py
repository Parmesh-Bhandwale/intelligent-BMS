from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import BookCreate, BookResponse, BookUpdate
from app.services.book_service import *
from app.core.deps import get_current_user
from app.core.rbac import require_role
from app.db.session import get_db


router = APIRouter(prefix="/books", tags=["Books"])


# POST /books — any authenticated user
@router.post("/", response_model=BookResponse)
async def add_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "user")),
):
    return await create_book(db, book)


# GET /books — any authenticated user
@router.get("/",response_model=list[BookResponse])
async def get_books(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "user")),
):
    return await get_all_books(db)


# GET /books/{id} — any authenticated user
@router.get("/{book_id}",response_model=BookResponse)
async def get_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "user")),
):
    return await get_book_by_id(db, book_id)


# PUT /books/{id} — admin only
@router.put("/{book_id}")
async def update_book_api(
    book_id: str,
    book: BookUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin")),
):
    return await update_book(db, book_id, book)


# DELETE /books/{id} — admin only
@router.delete("/{book_id}")
async def delete_book_api(
    book_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin"))
):
    return await delete_book(db, book_id)
