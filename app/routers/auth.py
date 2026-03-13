from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, get_token_payload, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, MeResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == body.username, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


@router.post("/logout")
async def logout():
    # JWT is stateless — client drops the token
    return {"ok": True}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(payload.get("sub", 0))
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })
    return TokenResponse(access_token=token)
