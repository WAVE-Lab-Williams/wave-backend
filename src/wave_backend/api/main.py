"""
FastAPI main application module.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header

from wave_backend.api.middleware.versioning import VersioningMiddleware
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
from wave_backend.utils.versioning import (
    API_VERSION,
    get_compatibility_warning,
    is_compatible_version,
)

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
    version=API_VERSION,
    lifespan=lifespan,
)

# Add versioning middleware
app.add_middleware(VersioningMiddleware)

# Include routers - order determines Swagger UI display order
app.include_router(experiment_types.router)  # 1st: Create experiment types
app.include_router(tags.router)  # 2nd: Create tags (optional)
app.include_router(experiments.router)  # 3rd: Create experiments (requires types)
app.include_router(experiment_data.router)  # 4th: Manage experiment data
app.include_router(search.router)  # 5th: Search and query endpoints


@app.get("/", summary="API Root", description="Welcome endpoint for the WAVE Backend API")
async def root():
    """API root endpoint providing welcome information."""
    logger.info("API root endpoint accessed")
    return {"message": "Welcome to the WAVE Backend API", "version": API_VERSION}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "wave-backend"}


@app.get(
    "/version",
    summary="Version Information",
    description="Get API version and client compatibility information",
)
async def version_info(
    x_wave_client_version: Optional[str] = Header(None, alias="X-WAVE-Client-Version")
):
    """
    Get version information and compatibility status.

    Uses semantic versioning for compatibility checking:
    - Same major version = compatible (1.x.x ↔ 1.y.z)
    - Different major version = incompatible (1.x.x ↔ 2.y.z)

    Args:
        x_wave_client_version: Client version from header (optional)

    Returns:
        Version information and compatibility status
    """
    response = {
        "api_version": API_VERSION,
        "client_version": x_wave_client_version,
        "compatibility_rule": "Semantic versioning: same major version = compatible",
    }

    if x_wave_client_version:
        response["compatible"] = is_compatible_version(x_wave_client_version, API_VERSION)
        warning = get_compatibility_warning(x_wave_client_version, API_VERSION)
        if warning:
            response["warning"] = warning
    else:
        response["compatible"] = None
        response["warning"] = "No client version provided"

    return response
