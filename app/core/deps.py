from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user as get_current_user_from_creds
from app.db.session import get_db


async def get_current_user(
    user: dict = Depends(get_current_user_from_creds),
):
    """
    Get the currently authenticated user from JWT token.
    Returns user dict with id, username and role.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )

    return user
