import asyncio
import os
from pathlib import Path
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.article import Article  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.job_posting import JobPosting  # noqa: F401
from app.models.user import User
from app.routers import articles as articles_router
from app.routers import uploads as uploads_router

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "120")

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())
    yield engine

    async def _dispose() -> None:
        await engine.dispose()

    asyncio.run(_dispose())


@pytest.fixture(scope="session")
def session_maker(async_engine):
    return async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
def reset_db(session_maker):
    async def _reset() -> None:
        async with session_maker() as session:
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()

    asyncio.run(_reset())


@pytest.fixture
def uploads_dir(tmp_path: Path) -> Path:
    test_uploads = tmp_path / "uploads"
    test_uploads.mkdir(parents=True, exist_ok=True)

    # Route modules cache this path at import time, so patch both.
    uploads_router.UPLOADS_DIR = test_uploads
    articles_router.UPLOADS_DIR = test_uploads
    return test_uploads


@pytest.fixture
def client(session_maker, uploads_dir):
    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def create_user(session_maker) -> Callable[..., dict]:
    def _create_user(
        email: str,
        password: str,
        role: str = "editor",
        full_name: str = "Test User",
        is_active: bool = True,
    ) -> dict:
        async def _insert() -> dict:
            async with session_maker() as session:
                user = User(
                    email=email,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=is_active,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                }

        return asyncio.run(_insert())

    return _create_user


@pytest.fixture
def auth_headers(client) -> Callable[[str, str], dict[str, str]]:
    def _headers(email: str, password: str) -> dict[str, str]:
        res = client.post(
            "/auth/login",
            json={"username": email, "password": password},
        )
        assert res.status_code == 200, res.text
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
