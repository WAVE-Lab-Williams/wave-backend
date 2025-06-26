import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wave_backend.api.main import app
from wave_backend.models.database import Base, get_db
from wave_backend.models.models import Experiment, ExperimentType, Tag

# Test database URL - uses test database on port 5433
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://wave_user:wave_password@localhost:5433/wave_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Set up the dependency override
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def test_db_setup():
    """Set up test database tables."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up after each test
    async with test_engine.begin() as conn:
        # Clean data but keep tables
        from sqlalchemy import text

        await conn.execute(text("TRUNCATE TABLE experiments RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE TABLE experiment_types RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE TABLE tags RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session(test_db_setup):
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def test_client() -> TestClient:
    """Test client fixture."""
    return TestClient(app)


@pytest_asyncio.fixture
async def sample_tag(db_session: AsyncSession):
    """Create a sample tag for testing."""
    tag = Tag(name="test-tag", description="A test tag")
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def sample_experiment_type(db_session: AsyncSession):
    """Create a sample experiment type for testing."""
    exp_type = ExperimentType(
        name="memory-test",
        description="A memory test experiment",
        table_name="memory_test_experiments",
        schema_definition={"additional_field": "string"},
    )
    db_session.add(exp_type)
    await db_session.commit()
    await db_session.refresh(exp_type)
    return exp_type


@pytest_asyncio.fixture
async def sample_experiment(db_session: AsyncSession, sample_experiment_type: ExperimentType):
    """Create a sample experiment for testing."""
    experiment = Experiment(
        experiment_type_id=sample_experiment_type.id,
        participant_id="participant-123",
        description="A test experiment",
        tags=["tag1", "tag2"],
        additional_data={"custom_field": "test_value"},
    )
    db_session.add(experiment)
    await db_session.commit()
    await db_session.refresh(experiment)
    return experiment