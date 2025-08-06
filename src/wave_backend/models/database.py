"""Database configuration and connection."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://wave_user:wave_password@localhost:5432/wave_dev"
)

# Control SQLAlchemy echo via environment variable (defaults to False for less verbosity)
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() in ("true", "1", "yes")

engine = create_async_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
