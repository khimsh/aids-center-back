from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_token_payload
from app.database import get_db
from app.models.user import User


async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolves the JWT to a live, active User row."""
    user_id = int(payload.get("sub", 0))
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


async def require_editor(user: User = Depends(get_current_user)) -> User:
    """Requires admin or editor role."""
    if user.role not in ("admin", "editor"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Requires admin role only."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user
