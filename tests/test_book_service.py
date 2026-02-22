"""
Module 3 – app.services.book_service   (Priority 2 – Data loss risk)

Tests cover:
  • create_book
  • get_all_books
  • get_book_by_id  (happy + not-found)
  • update_book_summary (happy + not-found)
  • update_book   (partial update + not-found)
  • delete_book   (happy + not-found + verify gone)
"""

import os
import sys
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.book_service import (
    create_book,
    get_all_books,
    get_book_by_id,
    update_book_summary,
    update_book,
    delete_book,
)
from app.schemas.book import BookCreate, BookUpdate
from app.model.models import Book
from app.utils.exception import NotFoundException


# ═══════════════ create_book ═══════════════


class TestCreateBook:

    @pytest.mark.asyncio
    async def test_persists_and_returns_book(self, db: AsyncSession):
        data = BookCreate(title="New Book", author="Auth", content="Cont")
        result = await create_book(db, data)

        assert isinstance(result, Book)
        assert result.title == "New Book"
        assert result.author == "Auth"

    @pytest.mark.asyncio
    async def test_sets_all_optional_fields(self, db: AsyncSession):
        data = BookCreate(
            title="Full", author="A",
            genre="Sci-Fi", year_published=2025, content="C",
        )
        book = await create_book(db, data)
        assert book.genre == "Sci-Fi"
        assert book.year_published == 2025


# ═══════════════ get_all_books ═══════════════


class TestGetAllBooks:

    @pytest.mark.asyncio
    async def test_empty_database(self, db: AsyncSession):
        result = await get_all_books(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_all_inserted(self, db: AsyncSession):
        for i in range(3):
            db.add(Book(title=f"B{i}", author="A", content="C"))
        await db.commit()

        result = await get_all_books(db)
        assert len(result) == 3


# ═══════════════ get_book_by_id ═══════════════


class TestGetBookById:

    @pytest.mark.asyncio
    async def test_existing_book(self, db: AsyncSession, sample_book: Book):
        result = await get_book_by_id(db, str(sample_book.id))
        assert result.title == sample_book.title

    @pytest.mark.asyncio
    async def test_nonexistent_raises_404(self, db: AsyncSession):
        with pytest.raises(NotFoundException, match="Book not found"):
            await get_book_by_id(db, str(uuid.uuid4()))


# ═══════════════ update_book_summary ═══════════════


class TestUpdateBookSummary:

    @pytest.mark.asyncio
    async def test_sets_summary(self, db: AsyncSession, sample_book: Book):
        result = await update_book_summary(db, str(sample_book.id), "AI summary")
        assert result.summary == "AI summary"

    @pytest.mark.asyncio
    async def test_nonexistent_raises_404(self, db: AsyncSession):
        with pytest.raises(NotFoundException):
            await update_book_summary(db, str(uuid.uuid4()), "s")


# ═══════════════ update_book ═══════════════


class TestUpdateBook:

    @pytest.mark.asyncio
    async def test_partial_update_title(self, db: AsyncSession, sample_book: Book):
        data = BookUpdate(title="Changed")
        result = await update_book(db, str(sample_book.id), data)
        assert result.title == "Changed"
        assert result.author == sample_book.author  # unchanged

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, db: AsyncSession, sample_book: Book):
        data = BookUpdate(title="T2", genre="Horror")
        result = await update_book(db, str(sample_book.id), data)
        assert result.title == "T2"
        assert result.genre == "Horror"

    @pytest.mark.asyncio
    async def test_nonexistent_raises_404(self, db: AsyncSession):
        with pytest.raises(NotFoundException):
            await update_book(db, str(uuid.uuid4()), BookUpdate(title="X"))


# ═══════════════ delete_book ═══════════════


class TestDeleteBook:

    @pytest.mark.asyncio
    async def test_success_message(self, db: AsyncSession, sample_book: Book):
        result = await delete_book(db, str(sample_book.id))
        assert "deleted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_book_gone_after_delete(self, db: AsyncSession, sample_book: Book):
        bid = str(sample_book.id)
        await delete_book(db, bid)
        with pytest.raises(NotFoundException):
            await get_book_by_id(db, bid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

    @pytest.mark.asyncio
    async def test_nonexistent_raises_404(self, db: AsyncSession):
        with pytest.raises(NotFoundException):
            await delete_book(db, str(uuid.uuid4()))
