import logging
from db.session import engine
from app.model.base import Base

# IMPORTANT: import models so SQLAlchemy registers them
from app.model.models import (
    User,
    Book,
    Review,
    Recommendation,
    UserBookInteraction,
    AIModelUsage,
)

logger = logging.getLogger(__name__)

import asyncio
from sqlalchemy.exc import OperationalError

async def init_db_model():
    for i in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except OperationalError:
            await asyncio.sleep(2)
    raise RuntimeError("Database not ready after retries")
