from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


# ======================
# Password Hashing
# ======================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# ======================
# JWT Config
# ======================

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """
    data = {
        "sub": username,
        "user_id": user_id,
        "role": "admin" | "user"
    }
    """

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# ======================
# JWT Validation
# ======================

def decode_token(token: str) -> dict:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ======================
# Get Current User
# ======================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:

    token = credentials.credentials

    payload = decode_token(token)

    username: Optional[str] = payload.get("sub")
    user_id = payload.get("user_id")
    role: Optional[str] = payload.get("role")

    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {
        "id": user_id,
        "username": username,
        "role": role,
    }


# ======================
# Role-Based Access
# ======================

def require_roles(*allowed_roles: str):
    """
    Usage:
    Depends(require_roles("admin"))
    Depends(require_roles("admin", "user"))
    """

    def role_checker(
        user: dict = Depends(get_current_user),
    ):

        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return role_checker
