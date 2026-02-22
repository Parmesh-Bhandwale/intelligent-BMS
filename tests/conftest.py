# new_tests/conftest.py
"""
Shared fixtures for critical-module unit tests.
Uses an in-memory SQLite database so tests run without
any external infrastructure.
"""

import os
import sys

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from app.model.base import Base
from app.model.models import User, Book, Review
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ── event loop (session-scoped) ──

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── engine & session (function-scoped → clean DB per test) ──

@pytest.fixture(scope="function")
def db_engine():
    return create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest_asyncio.fixture(scope="function")
async def db(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── helper data ──

@pytest_asyncio.fixture
async def sample_book(db: AsyncSession) -> Book:
    book = Book(
        title="Sample Book",
        author="Sample Author",
        genre="Fiction",
        year_published=2024,
        content="Sample content for testing.",
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@pytest_asyncio.fixture
async def fiction_books(db: AsyncSession) -> list[Book]:
    """Three fiction + one science book, with reviews on the first two."""
    books = [
        Book(title="Fiction A", author="A1", genre="Fiction", year_published=2023, content="CA"),
        Book(title="Fiction B", author="A2", genre="Fiction", year_published=2024, content="CB"),
        Book(title="Fiction C", author="A3", genre="Fiction", year_published=2024, content="CC"),
        Book(title="Science D", author="A4", genre="Science", year_published=2024, content="CD"),
    ]
    for b in books:
        db.add(b)
    await db.commit()
    for b in books:
        await db.refresh(b)

    reviews = [
        Review(book_id=books[0].id, user_id=1, review_text="Great", rating=5.0),
        Review(book_id=books[0].id, user_id=2, review_text="Nice",  rating=4.0),
        Review(book_id=books[1].id, user_id=1, review_text="OK",    rating=3.0),
    ]
    for r in reviews:
        db.add(r)
    await db.commit()

    return books


