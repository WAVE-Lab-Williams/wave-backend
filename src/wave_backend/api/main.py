"""
FastAPI main application module.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from wave_backend.api.routes import experiment_types, experiments, tags
from wave_backend.models.database import engine
from wave_backend.models.models import Base
from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


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
    description="FastAPI backend for the WAVE lab with Postgres database support",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(experiment_types.router, prefix="/api/v1")


@app.get("/", summary="API Root", description="Welcome endpoint for the WAVE Backend API")
async def root():
    """API root endpoint providing welcome information."""
    logger.info("API root endpoint accessed")
    return {"message": "Welcome to the WAVE Backend API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wave-backend"}
