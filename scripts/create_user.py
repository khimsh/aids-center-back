"""
CLI script to create admin or editor users.

Usage:
    python scripts/create_user.py --email admin@example.com --full-name "Jane Doe" --password secret --role admin
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.database import Base

DATABASE_URL = os.getenv("DATABASE_URL")


async def _create_user(email: str, full_name: str, password: str, role: str):
    engine = create_async_engine(DATABASE_URL)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            click.echo(f"User with email '{email}' already exists.", err=True)
            await engine.dispose()
            raise SystemExit(1)

        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        click.echo(f"Created {role} user: {email} (id={user.id})")

    await engine.dispose()


@click.command()
@click.option("--email", required=True, help="User email address (used as login username)")
@click.option("--full-name", required=True, help="Display name")
@click.option("--password", required=True, help="Plain-text password (will be hashed)")
@click.option("--role", default="editor", show_default=True, type=click.Choice(["admin", "editor"]))
def main(email, full_name, password, role):
    asyncio.run(_create_user(email, full_name, password, role))


if __name__ == "__main__":
    main()
