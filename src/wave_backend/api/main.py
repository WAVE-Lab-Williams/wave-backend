"""
FastAPI main application module.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from wave_backend.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("WAVE Backend API is starting up...")
    yield
    # Shutdown
    logger.info("WAVE Backend API is shutting down...")


app = FastAPI(
    title="WAVE Backend API",
    description="FastAPI backend for the WAVE lab with Postgres database support",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def hello_world():
    """Hello world endpoint."""
    logger.info("Hello world endpoint accessed")
    return {"message": "Hello World from WAVE Backend!"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wave-backend"}
