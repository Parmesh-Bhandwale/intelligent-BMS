from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


def require_role(*allowed_roles):
    """
    Dependency for role-based access.
    Returns a FastAPI dependency that checks the user's role from JWT.

    Usage:
        Depends(require_role("admin"))
        Depends(require_role("admin", "user"))
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
