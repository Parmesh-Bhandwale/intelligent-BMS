"""
Module 6 – app.schemas.review   (Priority 3 – Invalid data ingestion)

Tests cover:
  • ReviewCreate  (valid, missing fields)
  • ReviewUpdate  (all optional, partial)
  • ReviewResponse
  • ReviewListResponse
  • AggregatedRatingResponse
"""

import os
import sys

import pytest
from uuid import uuid4
from pydantic import ValidationError

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    ReviewListResponse,
    AggregatedRatingResponse,
)


# ═══════════════ ReviewCreate ═══════════════


class TestReviewCreate:

    def test_valid(self):
        r = ReviewCreate(review_text="Great!", rating=4.5)
        assert r.review_text == "Great!"
        assert r.rating == 4.5

    def test_missing_review_text(self):
        with pytest.raises(ValidationError):
            ReviewCreate(rating=3.0)

    def test_missing_rating(self):
        with pytest.raises(ValidationError):
            ReviewCreate(review_text="Text only")

    def test_zero_rating_accepted(self):
        r = ReviewCreate(review_text="T", rating=0.0)
        assert r.rating == 0.0

    def test_float_rating(self):
        r = ReviewCreate(review_text="T", rating=3.14)
        assert r.rating == pytest.approx(3.14)


# ═══════════════ ReviewUpdate ═══════════════


class TestReviewUpdate:

    def test_all_optional(self):
        u = ReviewUpdate()
        assert u.review_text is None
        assert u.rating is None

    def test_update_text_only(self):
        u = ReviewUpdate(review_text="Changed")
        assert u.review_text == "Changed"
        assert u.rating is None

    def test_update_rating_only(self):
        u = ReviewUpdate(rating=5.0)
        assert u.rating == 5.0
        assert u.review_text is None


# ═══════════════ ReviewResponse ═══════════════


class TestReviewResponse:

    def test_all_fields_present(self):
        bid = uuid4()
        r = ReviewResponse(id=1, user_id=10, book_id=bid, review_text="X", rating=3.0)
        assert r.id == 1
        assert r.user_id == 10
        assert r.book_id == bid

    def test_missing_id_rejected(self):
        with pytest.raises(ValidationError):
            ReviewResponse(user_id=1, book_id=uuid4(), review_text="X", rating=3.0)


# ═══════════════ ReviewListResponse ═══════════════


class TestReviewListResponse:

    def test_empty(self):
        r = ReviewListResponse(total=0, skip=0, limit=10, items=[])
        assert r.total == 0

    def test_with_items(self):
        bid = uuid4()
        items = [ReviewResponse(id=1, user_id=1, book_id=bid, review_text="T", rating=4.0)]
        r = ReviewListResponse(total=1, skip=0, limit=10, items=items)
        assert len(r.items) == 1


# ═══════════════ AggregatedRatingResponse ═══════════════


class TestAggregatedRatingResponse:

    def test_valid(self):
        bid = uuid4()
        r = AggregatedRatingResponse(
            book_id=bid, average_rating=4.2,
            total_reviews=10, min_rating=1.0, max_rating=5.0,
        )
        assert r.average_rating == 4.2
        assert r.total_reviews == 10

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            AggregatedRatingResponse(book_id=uuid4(), average_rating=3.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
