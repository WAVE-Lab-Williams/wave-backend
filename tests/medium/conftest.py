import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wave_backend.api.main import app
from wave_backend.auth.roles import Role
from wave_backend.models.database import Base, get_db

# Test database configuration - builds URL from environment variables
# These match the environment variables set in CI and can be overridden locally
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_TEST_PORT", "5433")
POSTGRES_USER = os.getenv("POSTGRES_USER", "wave_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "wave_password")
POSTGRES_DB = os.getenv("POSTGRES_TEST_DB", "wave_test")

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    (
        "postgresql+asyncpg://"
        f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    ),
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


@pytest.fixture(autouse=True)
def mock_auth():
    """Mock authentication for all medium tests."""
    from unittest.mock import patch

    from wave_backend.auth.unkey_client import UnkeyClient, UnkeyValidationResult

    async def mock_validate(key: str, required_role=None):
        """Mock validation that always returns TEST role."""
        return UnkeyValidationResult(
            valid=True,
            key_id="test_key_id",
            role=Role.TEST,
            permissions=["test"],
            roles=["test"],
        )

    # Clear the LRU cache to avoid using cached real client
    from wave_backend.auth.unkey_client import get_unkey_client

    get_unkey_client.cache_clear()

    # Patch the UnkeyClient.validate_key method directly
    with patch.object(UnkeyClient, "validate_key") as mock_validate_method:
        mock_validate_method.side_effect = mock_validate
        yield

    # Clear cache after test to ensure clean state
    get_unkey_client.cache_clear()


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


@pytest.fixture(autouse=True)
def clean_database_between_tests():
    """Clean database between each test to avoid conflicts."""
    import asyncio

    yield  # Run test first

    # Clean up after each test
    async def cleanup():
        test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with test_engine.begin() as conn:
            from sqlalchemy import text

            # Clean data but keep tables
            await conn.execute(text("TRUNCATE TABLE experiments RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE experiment_types RESTART IDENTITY CASCADE"))
            await conn.execute(text("TRUNCATE TABLE tags RESTART IDENTITY CASCADE"))
        await test_engine.dispose()

    asyncio.run(cleanup())


@pytest.fixture
async def async_client():
    """Provide an async HTTP client for testing the API."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def db_session():
    """Provide a database session for service tests."""
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    await test_engine.dispose()
