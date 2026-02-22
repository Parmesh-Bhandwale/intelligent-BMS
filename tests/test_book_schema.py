"""
Module 5 – app.schemas.book   (Priority 3 – Invalid data ingestion)

Tests cover:
  • BookCreate  (valid, missing title, missing author, all fields)
  • BookUpdate  (all optional, partial)
  • BookResponse  (id+summary, defaults)
  • BookListResponse
"""

import os
import sys

import pytest
from uuid import uuid4
from pydantic import ValidationError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from app.schemas.book import BookCreate, BookUpdate, BookResponse, BookListResponse


# ═══════════════ BookCreate ═══════════════


class TestBookCreate:

    def test_minimal_valid(self):
        b = BookCreate(title="T", author="A")
        assert b.title == "T"
        assert b.genre is None
        assert b.year_published is None
        assert b.content is None

    def test_all_fields(self):
        b = BookCreate(title="T", author="A", genre="Fiction", year_published=2025, content="C")
        assert b.genre == "Fiction"
        assert b.year_published == 2025

    def test_missing_title_rejected(self):
        with pytest.raises(ValidationError):
            BookCreate(author="A")

    def test_missing_author_rejected(self):
        with pytest.raises(ValidationError):
            BookCreate(title="T")

    def test_empty_strings_accepted(self):
        """Pydantic str type accepts empty strings by default."""
        b = BookCreate(title="", author="")
        assert b.title == ""


# ═══════════════ BookUpdate ═══════════════


class TestBookUpdate:

    def test_all_fields_optional(self):
        u = BookUpdate()
        assert u.title is None
        assert u.author is None
        assert u.genre is None
        assert u.year_published is None
        assert u.content is None

    def test_partial_update(self):
        u = BookUpdate(title="New")
        assert u.title == "New"
        assert u.author is None

    def test_exclude_unset_behaviour(self):
        u = BookUpdate(genre="Drama")
        d = u.dict(exclude_unset=True)
        assert d == {"genre": "Drama"}


# ═══════════════ BookResponse ═══════════════


class TestBookResponse:

    def test_with_uuid(self):
        bid = uuid4()
        r = BookResponse(id=bid, title="T", author="A")
        assert r.id == bid
        assert r.summary is None

    def test_with_summary(self):
        r = BookResponse(id=uuid4(), title="T", author="A", summary="Sum")
        assert r.summary == "Sum"


# ═══════════════ BookListResponse ═══════════════


class TestBookListResponse:

    def test_empty_list(self):
        r = BookListResponse(total=0, items=[])
        assert r.total == 0
        assert r.items == []

    def test_with_items(self):
        items = [
            BookResponse(id=uuid4(), title="A", author="A1"),
            BookResponse(id=uuid4(), title="B", author="A2"),
        ]
        r = BookListResponse(total=2, items=items)
        assert r.total == 2
        assert len(r.items) == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
    