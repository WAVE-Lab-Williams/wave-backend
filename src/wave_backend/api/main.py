"""
FastAPI main application module.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from wave_backend.api.routes import (
    experiment_data,
    experiment_types,
    experiments,
    search,
    tags,
)
from wave_backend.models.database import engine
from wave_backend.models.models import Base
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


def load_api_description() -> str:
    """Load API description from markdown file."""
    try:
        docs_path = Path(__file__).parents[3] / "docs" / "api-usage.md"
        if docs_path.exists():
            return docs_path.read_text()
        else:
            logger.warning(f"API documentation file not found at {docs_path}")
            return "FastAPI backend for the WAVE lab with PostgreSQL database support."
    except Exception as e:
        logger.error(f"Error loading API documentation: {e}")
        return "FastAPI backend for the WAVE lab with PostgreSQL database support."


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("WAVE Backend API is starting up...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("WAVE Backend API is shutting down...")


app = FastAPI(
    title="WAVE Backend API",
    description=load_api_description(),
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers - order determines Swagger UI display order
app.include_router(experiment_types.router, prefix="/api/v1")  # 1st: Create experiment types
app.include_router(tags.router, prefix="/api/v1")  # 2nd: Create tags (optional)
app.include_router(experiments.router, prefix="/api/v1")  # 3rd: Create experiments (requires types)
app.include_router(experiment_data.router, prefix="/api/v1")  # 4th: Manage experiment data
app.include_router(search.router, prefix="/api/v1/search")  # 5th: Search and query endpoints


@app.get("/", summary="API Root", description="Welcome endpoint for the WAVE Backend API")
async def root():
    """API root endpoint providing welcome information."""
    logger.info("API root endpoint accessed")
    return {"message": "Welcome to the WAVE Backend API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wave-backend"}
