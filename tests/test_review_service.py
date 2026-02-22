"""
Module 4 – app.services.review_service   (Priority 2 – Data integrity + authz)

Tests cover:
  • create_review  (happy, book-not-found, rating boundary, invalid rating)
  • get_reviews_by_book  (happy, pagination, empty, book-not-found)
  • get_review_by_id  (happy, not-found)
  • update_review  (happy, wrong-user 403, invalid rating, not-found)
  • delete_review  (happy, wrong-user 403, not-found)
  • get_aggregated_rating  (with reviews, no reviews, book-not-found)
"""

import os
import sys
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from app.services.review_service import (
    create_review,
    get_reviews_by_book,
    get_review_by_id,
    update_review,
    delete_review,
    get_aggregated_rating,
)
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.model.models import Book
from app.utils.exception import NotFoundException, AppException


@pytest_asyncio.fixture
async def rev_book(db: AsyncSession) -> Book:
    book = Book(title="Reviewable", author="A", content="C")
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


# ═══════════════ create_review ═══════════════


class TestCreateReview:

    @pytest.mark.asyncio
    async def test_success(self, db, rev_book):
        r = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="Good", rating=4.0))
        assert r.review_text == "Good"
        assert r.rating == 4.0
        assert r.user_id == 1

    @pytest.mark.asyncio
    async def test_book_not_found(self, db):
        with pytest.raises(NotFoundException):
            await create_review(db, str(uuid.uuid4()), 1, ReviewCreate(review_text="X", rating=3.0))

    @pytest.mark.asyncio
    async def test_rating_zero_ok(self, db, rev_book):
        r = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=0.0))
        assert r.rating == 0.0

    @pytest.mark.asyncio
    async def test_rating_five_ok(self, db, rev_book):
        r = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=5.0))
        assert r.rating == 5.0

    @pytest.mark.asyncio
    async def test_rating_above_five_rejected(self, db, rev_book):
        with pytest.raises(AppException, match="between 0 and 5"):
            await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=5.1))

    @pytest.mark.asyncio
    async def test_rating_negative_rejected(self, db, rev_book):
        with pytest.raises(AppException):
            await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=-0.1))


# ═══════════════ get_reviews_by_book ═══════════════


class TestGetReviewsByBook:

    @pytest.mark.asyncio
    async def test_empty_list(self, db, rev_book):
        result = await get_reviews_by_book(db, str(rev_book.id))
        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_returns_items(self, db, rev_book):
        await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="A", rating=3.0))
        await create_review(db, str(rev_book.id), 2, ReviewCreate(review_text="B", rating=4.0))
        result = await get_reviews_by_book(db, str(rev_book.id))
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_pagination(self, db, rev_book):
        for i in range(5):
            await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text=f"R{i}", rating=3.0))
        result = await get_reviews_by_book(db, str(rev_book.id), skip=0, limit=2)
        assert len(result["items"]) == 2
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_book_not_found(self, db):
        with pytest.raises(NotFoundException):
            await get_reviews_by_book(db, str(uuid.uuid4()))


# ═══════════════ get_review_by_id ═══════════════


class TestGetReviewById:

    @pytest.mark.asyncio
    async def test_found(self, db, rev_book):
        created = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="X", rating=2.0))
        result = await get_review_by_id(db, created.id)
        assert result.id == created.id

    @pytest.mark.asyncio
    async def test_not_found(self, db):
        with pytest.raises(NotFoundException):
            await get_review_by_id(db, 999999)


# ═══════════════ update_review ═══════════════


class TestUpdateReview:

    @pytest.mark.asyncio
    async def test_update_text(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="Old", rating=3.0))
        r = await update_review(db, c.id, 1, ReviewUpdate(review_text="New"))
        assert r.review_text == "New"
        assert r.rating == 3.0  # unchanged

    @pytest.mark.asyncio
    async def test_update_rating(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=2.0))
        r = await update_review(db, c.id, 1, ReviewUpdate(rating=5.0))
        assert r.rating == 5.0

    @pytest.mark.asyncio
    async def test_wrong_user_403(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=3.0))
        with pytest.raises(AppException) as exc:
            await update_review(db, c.id, 999, ReviewUpdate(review_text="Hacked"))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_rating_rejected(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=3.0))
        with pytest.raises(AppException, match="between 0 and 5"):
            await update_review(db, c.id, 1, ReviewUpdate(rating=6.0))

    @pytest.mark.asyncio
    async def test_not_found(self, db):
        with pytest.raises(NotFoundException):
            await update_review(db, 999999, 1, ReviewUpdate(review_text="X"))


# ═══════════════ delete_review ═══════════════


class TestDeleteReview:

    @pytest.mark.asyncio
    async def test_success(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=3.0))
        result = await delete_review(db, c.id, 1)
        assert "deleted" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_wrong_user_403(self, db, rev_book):
        c = await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="T", rating=3.0))
        with pytest.raises(AppException) as exc:
            await delete_review(db, c.id, 999)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found(self, db):
        with pytest.raises(NotFoundException):
            await delete_review(db, 999999, 1)


# ═══════════════ get_aggregated_rating ═══════════════


class TestGetAggregatedRating:

    @pytest.mark.asyncio
    async def test_with_reviews(self, db, rev_book):
        for rating in [2.0, 4.0, 5.0]:
            await create_review(db, str(rev_book.id), 1, ReviewCreate(review_text="R", rating=rating))
        stats = await get_aggregated_rating(db, str(rev_book.id))
        assert stats["total_reviews"] == 3
        assert stats["average_rating"] == pytest.approx(3.666, abs=0.01)
        assert stats["min_rating"] == 2.0
        assert stats["max_rating"] == 5.0

    @pytest.mark.asyncio
    async def test_no_reviews(self, db, rev_book):
        stats = await get_aggregated_rating(db, str(rev_book.id))
        assert stats["total_reviews"] == 0
        assert stats["average_rating"] == 0

    @pytest.mark.asyncio
    async def test_book_not_found(self, db):
        with pytest.raises(NotFoundException):
            await get_aggregated_rating(db, str(uuid.uuid4()))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))