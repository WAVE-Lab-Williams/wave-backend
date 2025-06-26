"""API routes for experiment type operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.models.database import get_db
from wave_backend.schemas.schemas import (
    ExperimentColumnsResponse,
    ExperimentTypeCreate,
    ExperimentTypeResponse,
    ExperimentTypeUpdate,
)
from wave_backend.services.experiment_types import ExperimentTypeService
from wave_backend.services.experiments import ExperimentService

router = APIRouter(prefix="/experiment-types", tags=["experiment-types"])


@router.post("/", response_model=ExperimentTypeResponse)
async def create_experiment_type(
    experiment_type: ExperimentTypeCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new experiment type."""
    # Check if experiment type with same name or table_name already exists
    existing_name = await ExperimentTypeService.get_experiment_type_by_name(
        db, experiment_type.name
    )
    if existing_name:
        raise HTTPException(status_code=400, detail="Experiment type with this name already exists")

    try:
        db_experiment_type = await ExperimentTypeService.create_experiment_type(db, experiment_type)
        return db_experiment_type
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{experiment_type_id}", response_model=ExperimentTypeResponse)
async def get_experiment_type(experiment_type_id: int, db: AsyncSession = Depends(get_db)):
    """Get an experiment type by ID."""
    db_experiment_type = await ExperimentTypeService.get_experiment_type(db, experiment_type_id)
    if not db_experiment_type:
        raise HTTPException(status_code=404, detail="Experiment type not found")
    return db_experiment_type


@router.get("/", response_model=List[ExperimentTypeResponse])
async def get_experiment_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get experiment types with pagination."""
    experiment_types = await ExperimentTypeService.get_experiment_types(db, skip=skip, limit=limit)
    return experiment_types


@router.put("/{experiment_type_id}", response_model=ExperimentTypeResponse)
async def update_experiment_type(
    experiment_type_id: int,
    experiment_type_update: ExperimentTypeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an experiment type."""
    # If updating name, check for conflicts
    if experiment_type_update.name:
        existing_name = await ExperimentTypeService.get_experiment_type_by_name(
            db, experiment_type_update.name
        )
        if existing_name and existing_name.id != experiment_type_id:
            raise HTTPException(
                status_code=400, detail="Experiment type with this name already exists"
            )

    db_experiment_type = await ExperimentTypeService.update_experiment_type(
        db, experiment_type_id, experiment_type_update
    )
    if not db_experiment_type:
        raise HTTPException(status_code=404, detail="Experiment type not found")
    return db_experiment_type


@router.delete("/{experiment_type_id}")
async def delete_experiment_type(experiment_type_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an experiment type."""
    success = await ExperimentTypeService.delete_experiment_type(db, experiment_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experiment type not found")
    return {"message": "Experiment type deleted successfully"}


@router.get("/name/{experiment_type_name}/columns", response_model=ExperimentColumnsResponse)
async def get_experiment_type_columns(
    experiment_type_name: str, db: AsyncSession = Depends(get_db)
):
    """Get column information for an experiment type."""
    columns_info = await ExperimentService.get_experiment_columns(
        db, experiment_type_name=experiment_type_name
    )
    if not columns_info:
        raise HTTPException(status_code=404, detail="Experiment type not found")
    return columns_info
