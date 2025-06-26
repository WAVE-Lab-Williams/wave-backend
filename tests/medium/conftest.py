import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wave_backend.api.main import app
from wave_backend.models.database import Base, get_db
from wave_backend.models.models import Experiment, ExperimentType, Tag

# Test database URL - uses test database on port 5433
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://wave_user:wave_password@localhost:5433/wave_test"
)


async def override_get_db():
    """Override database dependency for testing."""
    # Create engine and session inside the async function to avoid event loop issues
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Set up the dependency override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database tables once per session."""
    import asyncio

    async def setup():
        test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await test_engine.dispose()

    # Run setup
    asyncio.run(setup())
    yield

    # Cleanup
    async def cleanup():
        test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()

    asyncio.run(cleanup())
