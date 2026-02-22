from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy import select
from app.model.base import Base
from app.model.models import User

async def init_db_model(db: AsyncSession, async_engine: AsyncEngine):
    """Initialize database tables"""
    
    # Create all tables asynchronously
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables initialized successfully")