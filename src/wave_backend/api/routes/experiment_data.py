"""API routes for experiment data operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.models.database import get_db
from wave_backend.schemas.schemas import (
    ColumnTypeInfo,
    ExperimentDataCountResponse,
    ExperimentDataCreate,
    ExperimentDataDeleteResponse,
    ExperimentDataQueryRequest,
    ExperimentDataUpdate,
)
from wave_backend.services.experiment_data import ExperimentDataService
from wave_backend.services.experiments import ExperimentService

router = APIRouter(prefix="/experiment-data", tags=["experiment-data"])


@router.post(
    "/{experiment_id}/data/",
    response_model=Dict[str, Any],
    summary="Create experiment data row",
    description="Create a new data row for the specified experiment. "
    "The data fields should match the schema definition of the experiment type. "
    "Returns the created row with all fields including id, participant_id, "
    "created_at, updated_at, and custom data fields.",
    status_code=201,
    responses={
        201: {
            "description": "Successfully created experiment data row",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "participant_id": "SUBJ-2024-001",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "reaction_time": 1.23,
                        "accuracy": 0.85,
                        "difficulty_level": 2,
                        "stimulus_type": "visual",
                    }
                }
            },
        }
    },
)
async def create_experiment_data(
    experiment_id: UUID,
    data: ExperimentDataCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new experiment data row with the provided data values."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Insert the data row
    try:
        row_id = await ExperimentDataService.insert_data_row(
            experiment.experiment_type.table_name,
            str(experiment_id),
            data.participant_id,
            data.data,
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if row_id is None:
        raise HTTPException(status_code=400, detail="Failed to create experiment data row")

    # Return the created row
    row = await ExperimentDataService.get_data_row_by_id(
        experiment.experiment_type.table_name, row_id, db, str(experiment_id)
    )
    return row


@router.get(
    "/{experiment_id}/data/",
    response_model=List[Dict[str, Any]],
    summary="List experiment data rows",
    description="Retrieve experiment data rows with optional filtering by participant ID, "
    "date range, and pagination. Returns all data fields defined in the experiment type schema. "
    "Each row includes standard fields (id, participant_id, created_at, updated_at) "
    "plus custom experiment data fields.",
    responses={
        200: {
            "description": "Successfully retrieved experiment data rows",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "participant_id": "SUBJ-2024-001",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                            "reaction_time": 1.23,
                            "accuracy": 0.85,
                            "difficulty_level": 2,
                            "stimulus_type": "visual",
                        },
                        {
                            "id": 2,
                            "participant_id": "SUBJ-2024-002",
                            "created_at": "2024-01-15T11:45:00Z",
                            "updated_at": "2024-01-15T11:45:00Z",
                            "reaction_time": 1.45,
                            "accuracy": 0.92,
                            "difficulty_level": 3,
                            "stimulus_type": "audio",
                        },
                    ]
                }
            },
        }
    },
)
async def get_experiment_data(
    experiment_id: UUID,
    participant_id: Optional[str] = Query(None, description="Filter by participant ID"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date (after)"),
    created_before: Optional[datetime] = Query(
        None, description="Filter by creation date (before)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
    db: AsyncSession = Depends(get_db),
):
    """Get experiment data rows with filtering and pagination options."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get the data rows
    rows = await ExperimentDataService.get_data_rows(
        experiment.experiment_type.table_name,
        db,
        experiment_uuid=str(experiment_id),
        participant_id=participant_id,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )

    return rows


@router.get(
    "/{experiment_id}/data/count",
    response_model=ExperimentDataCountResponse,
    summary="Count experiment data rows",
    description="Get the total count of experiment data rows, "
    "optionally filtered by participant ID.",
)
async def count_experiment_data(
    experiment_id: UUID,
    participant_id: Optional[str] = Query(None, description="Filter by participant ID"),
    db: AsyncSession = Depends(get_db),
):
    """Count experiment data rows with optional participant filtering."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Count the rows
    count = await ExperimentDataService.count_data_rows(
        experiment.experiment_type.table_name,
        db,
        experiment_uuid=str(experiment_id),
        participant_id=participant_id,
    )

    return ExperimentDataCountResponse(
        count=count,
        participant_id=participant_id,
        experiment_id=experiment_id,
    )


@router.get(
    "/{experiment_id}/data/columns",
    response_model=List[ColumnTypeInfo],
    summary="Get experiment data columns",
    description="Retrieve detailed information about all columns in the experiment's data table, "
    "including data types, nullable status, and default values.",
)
async def get_experiment_data_columns(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed column information for an experiment's data table schema."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get column information
    columns = await ExperimentDataService.get_table_columns(
        experiment.experiment_type.table_name, db
    )

    return [
        ColumnTypeInfo(
            column_name=col["column_name"],
            column_type=col["column_type"],
            is_nullable=col["is_nullable"],
            default_value=col["default_value"],
        )
        for col in columns
    ]


@router.get(
    "/{experiment_id}/data/row/{row_id}",
    response_model=Dict[str, Any],
    summary="Get experiment data row",
    description="Retrieve a specific experiment data row by its ID. "
    "Returns all data fields defined in the experiment type schema, "
    "including standard fields and custom experiment data.",
    responses={
        200: {
            "description": "Successfully retrieved experiment data row",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "participant_id": "SUBJ-2024-001",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "reaction_time": 1.23,
                        "accuracy": 0.85,
                        "difficulty_level": 2,
                        "stimulus_type": "visual",
                    }
                }
            },
        }
    },
)
async def get_experiment_data_row(
    experiment_id: UUID,
    row_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific experiment data row by its unique ID."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get the data row
    row = await ExperimentDataService.get_data_row_by_id(
        experiment.experiment_type.table_name, row_id, db, str(experiment_id)
    )

    if not row:
        raise HTTPException(status_code=404, detail="Experiment data row not found")

    return row


@router.put(
    "/{experiment_id}/data/row/{row_id}",
    response_model=Dict[str, Any],
    summary="Update experiment data row",
    description="Update a specific experiment data row with new values. "
    "Only provided fields will be updated, leaving others unchanged. "
    "Returns the complete updated row with all fields including the modified values.",
    responses={
        200: {
            "description": "Successfully updated experiment data row",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "participant_id": "SUBJ-2024-001",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T14:22:00Z",
                        "reaction_time": 1.45,
                        "accuracy": 0.90,
                        "difficulty_level": 2,
                        "stimulus_type": "visual",
                    }
                }
            },
        }
    },
)
async def update_experiment_data(
    experiment_id: UUID,
    row_id: int,
    data: ExperimentDataUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an experiment data row with partial or complete data changes."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Prepare update data
    update_data = {}
    if data.participant_id is not None:
        update_data["participant_id"] = data.participant_id
    if data.data is not None:
        update_data.update(data.data)

    # Update the data row
    success = await ExperimentDataService.update_data_row(
        experiment.experiment_type.table_name, row_id, update_data, db, str(experiment_id)
    )

    if not success:
        raise HTTPException(status_code=404, detail="Experiment data row not found")

    # Return the updated row
    row = await ExperimentDataService.get_data_row_by_id(
        experiment.experiment_type.table_name, row_id, db, str(experiment_id)
    )
    return row


@router.delete(
    "/{experiment_id}/data/row/{row_id}",
    response_model=ExperimentDataDeleteResponse,
    summary="Delete experiment data row",
    description="Delete a specific experiment data row by its ID.",
)
async def delete_experiment_data(
    experiment_id: UUID,
    row_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an experiment data row and return confirmation details."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Delete the data row
    success = await ExperimentDataService.delete_data_row(
        experiment.experiment_type.table_name, row_id, db, str(experiment_id)
    )

    if not success:
        raise HTTPException(status_code=404, detail="Experiment data row not found")

    return ExperimentDataDeleteResponse(
        message="Experiment data row deleted successfully",
        deleted_id=row_id,
        experiment_id=experiment_id,
    )


@router.post(
    "/{experiment_id}/data/query",
    response_model=List[Dict[str, Any]],
    summary="Query experiment data with advanced filtering",
    description="Execute a custom query on experiment data with flexible filtering options. "
    "Supports filtering by participant ID, custom column values, date ranges, and pagination. "
    "Returns matching rows with all standard and custom fields based on the applied filters.",
    responses={
        200: {
            "description": "Successfully executed query and returned matching rows",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "participant_id": "SUBJ-2024-001",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                            "reaction_time": 1.23,
                            "accuracy": 0.85,
                            "difficulty_level": 2,
                            "stimulus_type": "visual",
                        },
                        {
                            "id": 3,
                            "participant_id": "SUBJ-2024-003",
                            "created_at": "2024-01-15T12:15:00Z",
                            "updated_at": "2024-01-15T12:15:00Z",
                            "reaction_time": 1.34,
                            "accuracy": 0.88,
                            "difficulty_level": 2,
                            "stimulus_type": "visual",
                        },
                    ]
                }
            },
        }
    },
)
async def query_experiment_data(
    experiment_id: UUID,
    query_request: ExperimentDataQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run an advanced query on experiment data with custom filters and pagination."""
    # Get the experiment to get the table name
    experiment = await ExperimentService.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Extract query parameters from the request model
    participant_id = query_request.participant_id
    filters = query_request.filters
    created_after = query_request.created_after
    created_before = query_request.created_before
    limit = query_request.limit
    offset = query_request.offset

    # Run the query
    rows = await ExperimentDataService.get_data_rows(
        experiment.experiment_type.table_name,
        db,
        experiment_uuid=str(experiment_id),
        participant_id=participant_id,
        filters=filters,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )

    return rows
