import logging
from fastapi import APIRouter
from app.core.security import create_access_token

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login")
async def login():
    logger.info("User login")
    token = create_access_token({"sub": "user1", "role": "admin"})
    return {"access_token": token}
