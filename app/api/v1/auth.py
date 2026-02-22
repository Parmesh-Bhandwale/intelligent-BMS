import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token, hash_password, verify_password, get_current_user
from app.db.session import get_db
from app.model.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.exception import AppException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user and return access token"""
    logger.info(f"Registering new user: {request.username}")
    
    # Check if user exists
    stmt = select(User).where(User.username == request.username)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.warning(f"User {request.username} already exists")
        raise AppException("User already exists", status.HTTP_409_CONFLICT)
    
    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(
        username=request.username,
        email=request.username,  # Use username as email for now
        hashed_password=hashed_password,
        roles="user"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"User {request.username} registered successfully")
    token = create_access_token({"sub": new_user.username, "user_id": new_user.id, "role": "user"})
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return access token"""
    logger.info(f"Login attempt for user: {request.username}")
    
    stmt = select(User).where(User.username == request.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise AppException("Invalid credentials", status.HTTP_401_UNAUTHORIZED)
    
    logger.info(f"User {request.username} logged in successfully")
    token = create_access_token({"sub": user.username, "user_id": user.id, "role": user.roles.split(",")[0]})
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=dict)
async def get_current_user_info(user = Depends(get_current_user)):
    """Get current authenticated user info"""
    logger.info(f"Fetching info for user: {user['username']}")
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }
