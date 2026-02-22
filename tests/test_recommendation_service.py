"""
Module 8 – app.services.recommendation_service   (Priority 2 – Complex query bugs)

Tests cover:
  • get_recommendations  (default, genre filter, limit, min_rating, empty DB, reason text)
  • get_similar_books  (same genre, excludes self, limit, nonexistent book, reason text)
  • get_top_rated_books  (returns list, genre filter, limit, descending order, empty DB)
"""
import os
import sys
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.recommendation_service import (
    get_recommendations,
    get_similar_books,
    get_top_rated_books,
)
from app.model.models import Book, Review


# ═══════════════ get_recommendations ═══════════════


class TestGetRecommendations:

    @pytest.mark.asyncio
    async def test_default_returns_list(self, db, fiction_books):
        result = await get_recommendations(db)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_limit_respected(self, db, fiction_books):
        result = await get_recommendations(db, limit=2)
        assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_genre_filter(self, db, fiction_books):
        result = await get_recommendations(db, genre="Fiction")
        for rec in result:
            assert rec.genre == "Fiction"

    @pytest.mark.asyncio
    async def test_min_rating_filter(self, db, fiction_books):
        result = await get_recommendations(db, min_rating=4.0)
        for rec in result:
            assert rec.average_rating >= 4.0

    @pytest.mark.asyncio
    async def test_empty_database(self, db):
        result = await get_recommendations(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_reason_with_genre(self, db, fiction_books):
        result = await get_recommendations(db, genre="Fiction")
        for rec in result:
            assert rec.reason  # non-empty string

    @pytest.mark.asyncio
    async def test_reason_without_genre(self, db, fiction_books):
        result = await get_recommendations(db)
        for rec in result:
            assert rec.reason == "Highly rated"


# ═══════════════ get_similar_books ═══════════════


class TestGetSimilarBooks:

    @pytest.mark.asyncio
    async def test_same_genre_returned(self, db, fiction_books):
        ref = fiction_books[0]  # Fiction A
        result = await get_similar_books(db, str(ref.id))
        for rec in result:
            assert rec.genre == "Fiction"

    @pytest.mark.asyncio
    async def test_excludes_reference_book(self, db, fiction_books):
        ref = fiction_books[0]
        result = await get_similar_books(db, str(ref.id))
        assert str(ref.id) not in [r.id for r in result]

    @pytest.mark.asyncio
    async def test_limit_respected(self, db, fiction_books):
        result = await get_similar_books(db, str(fiction_books[0].id), limit=1)
        assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_nonexistent_book_returns_empty(self, db):
        result = await get_similar_books(db, str(uuid.uuid4()))
        assert result == []

    @pytest.mark.asyncio
    async def test_reason_mentions_reference(self, db, fiction_books):
        ref = fiction_books[0]
        result = await get_similar_books(db, str(ref.id))
        for rec in result:
            assert f"Similar to {ref.title}" == rec.reason


# ═══════════════ get_top_rated_books ═══════════════


class TestGetTopRatedBooks:

    @pytest.mark.asyncio
    async def test_returns_list(self, db, fiction_books):
        result = await get_top_rated_books(db)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_genre_filter(self, db, fiction_books):
        result = await get_top_rated_books(db, genre="Fiction")
        for rec in result:
            assert rec.genre == "Fiction"

    @pytest.mark.asyncio
    async def test_limit_respected(self, db, fiction_books):
        result = await get_top_rated_books(db, limit=1)
        assert len(result) <= 1

    @pytest.mark.asyncio
    async def test_descending_order(self, db, fiction_books):
        result = await get_top_rated_books(db, limit=10)
        if len(result) >= 2:
            for i in range(len(result) - 1):
                assert result[i].average_rating >= result[i + 1].average_rating

    @pytest.mark.asyncio
    async def test_empty_database(self, db):
        result = await get_top_rated_books(db)
        assert result == []

    @pytest.mark.asyncio
    async def test_reason_text(self, db, fiction_books):
        result = await get_top_rated_books(db)
        for rec in result:
            assert rec.reason == "Top rated in this category"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))