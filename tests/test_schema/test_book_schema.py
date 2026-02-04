# tests/test_schemas/test_book_schema.py
import pytest
from app.schemas.book import BookCreate
from pydantic import ValidationError

def test_book_create_valid():
    book = BookCreate(
        title="Clean Code",
        author="Robert Martin",
        year_published=2008
    )
    assert book.title == "Clean Code"

def test_book_create_missing_title():
    with pytest.raises(ValidationError):
        BookCreate(author="Someone")
