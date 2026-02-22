import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger("db")

# Create async engine with proper pool configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
    connect_args={
        "timeout": 10,
        "server_settings": {"jit": "off"},
    }
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db():
    """Database session dependency for FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.exception(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Close database connection"""
    await engine.dispose()
