# tests/test_services/test_book_service.py
import pytest
from unittest.mock import AsyncMock
from app.services.book_service import create_book
from app.schemas.book import BookCreate

@pytest.mark.asyncio
async def test_create_book():
    mock_db = AsyncMock()

    book_data = BookCreate(
        title="1984",
        author="George Orwell"
    )

    result = await create_book(mock_db, book_data)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
