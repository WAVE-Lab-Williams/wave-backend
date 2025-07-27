"""API routes for experiment operations."""

from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.auth.decorator import auth
from wave_backend.auth.roles import Role
from wave_backend.models.database import get_db
from wave_backend.schemas.schemas import (
    ExperimentColumnsResponse,
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)
from wave_backend.services.experiments import ExperimentService

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.post("/", response_model=ExperimentResponse)
@auth.role(Role.RESEARCHER)
async def create_experiment(
    experiment: ExperimentCreate, db: AsyncSession = Depends(get_db), auth: Tuple[str, Role] = None
):  # noqa: F841
    """Create a new experiment."""
    try:
        db_experiment = await ExperimentService.create_experiment(db, experiment)
        return db_experiment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{experiment_uuid}", response_model=ExperimentResponse)
@auth.role(Role.RESEARCHER)
async def get_experiment(
    experiment_uuid: UUID, db: AsyncSession = Depends(get_db), auth: Tuple[str, Role] = None
):  # noqa: F841
    """Get an experiment by UUID."""
    db_experiment = await ExperimentService.get_experiment(db, experiment_uuid)
    if not db_experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_experiment


@router.get("/", response_model=List[ExperimentResponse])
@auth.role(Role.RESEARCHER)
async def get_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    experiment_type_id: Optional[int] = Query(None),
    tags: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Get experiments with optional filtering."""
    experiments = await ExperimentService.get_experiments(
        db,
        skip=skip,
        limit=limit,
        experiment_type_id=experiment_type_id,
        tags=tags,
    )
    return experiments


@router.put("/{experiment_uuid}", response_model=ExperimentResponse)
@auth.role(Role.RESEARCHER)
async def update_experiment(
    experiment_uuid: UUID,
    experiment_update: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Update an experiment."""
    db_experiment = await ExperimentService.update_experiment(
        db, experiment_uuid, experiment_update
    )
    if not db_experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_experiment


@router.delete("/{experiment_uuid}")
@auth.role(Role.ADMIN)
async def delete_experiment(
    experiment_uuid: UUID, db: AsyncSession = Depends(get_db), auth: Tuple[str, Role] = None
):  # noqa: F841
    """Delete an experiment."""
    success = await ExperimentService.delete_experiment(db, experiment_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"message": "Experiment deleted successfully"}


@router.get("/{experiment_uuid}/columns", response_model=ExperimentColumnsResponse)
@auth.role(Role.RESEARCHER)
async def get_experiment_columns(
    experiment_uuid: UUID, db: AsyncSession = Depends(get_db), auth: Tuple[str, Role] = None
):  # noqa: F841
    """Get column information for an experiment."""
    columns_info = await ExperimentService.get_experiment_columns(
        db, experiment_uuid=experiment_uuid
    )
    if not columns_info:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return columns_info
