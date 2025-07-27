"""Search API endpoints for advanced querying capabilities."""

from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.auth.decorator import auth
from wave_backend.auth.roles import Role
from wave_backend.models.database import get_db
from wave_backend.schemas.schemas import (
    ExperimentResponse,
    ExperimentTypeResponse,
    TagResponse,
)
from wave_backend.schemas.search_schemas import (
    AdvancedExperimentSearchRequest,
    ExperimentDataByTagsRequest,
    ExperimentDataByTagsResponse,
    ExperimentDescriptionSearchRequest,
    ExperimentTagSearchRequest,
    ExperimentTagSearchResponse,
    ExperimentTypeSearchRequest,
    ExperimentTypeSearchResponse,
    TagSearchRequest,
    TagSearchResponse,
)
from wave_backend.services.search import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["Search"])


@router.post("/experiments/by-tags", response_model=ExperimentTagSearchResponse)
@auth.role(Role.RESEARCHER)
async def search_experiments_by_tags(
    request: ExperimentTagSearchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Search experiments by tags with optional date filtering."""
    try:
        experiments = await SearchService.search_experiments_by_tags(
            db=db,
            tags=request.tags,
            match_all=request.match_all,
            skip=request.skip,
            limit=request.limit,
            created_after=request.created_after,
            created_before=request.created_before,
        )

        return ExperimentTagSearchResponse(
            experiments=[ExperimentResponse.model_validate(exp) for exp in experiments],
            total=len(experiments),
            pagination={"skip": request.skip, "limit": request.limit, "total": len(experiments)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/experiment-types/by-description", response_model=ExperimentTypeSearchResponse)
@auth.role(Role.RESEARCHER)
async def search_experiment_types_by_description(
    request: ExperimentTypeSearchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Search experiment types by description text."""
    try:
        experiment_types = await SearchService.search_experiment_types_by_description(
            db=db,
            search_text=request.search_text,
            skip=request.skip,
            limit=request.limit,
            created_after=request.created_after,
            created_before=request.created_before,
        )

        return ExperimentTypeSearchResponse(
            experiment_types=[ExperimentTypeResponse.model_validate(et) for et in experiment_types],
            total=len(experiment_types),
            pagination={
                "skip": request.skip,
                "limit": request.limit,
                "total": len(experiment_types),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/tags/by-name", response_model=TagSearchResponse)
@auth.role(Role.RESEARCHER)
async def search_tags_by_name(
    request: TagSearchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Search tags by name or description."""
    try:
        tags = await SearchService.search_tags_by_name(
            db=db,
            search_text=request.search_text,
            skip=request.skip,
            limit=request.limit,
            created_after=request.created_after,
            created_before=request.created_before,
        )

        return TagSearchResponse(
            tags=[TagResponse.model_validate(tag) for tag in tags],
            total=len(tags),
            pagination={"skip": request.skip, "limit": request.limit, "total": len(tags)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/experiments/by-description-and-type", response_model=ExperimentTagSearchResponse)
@auth.role(Role.RESEARCHER)
async def search_experiments_by_description_and_type(
    request: ExperimentDescriptionSearchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Search experiment descriptions within a specific experiment type."""
    try:
        experiments = await SearchService.search_experiments_by_description_and_type(
            db=db,
            experiment_type_id=request.experiment_type_id,
            search_text=request.search_text,
            skip=request.skip,
            limit=request.limit,
            created_after=request.created_after,
            created_before=request.created_before,
        )

        return ExperimentTagSearchResponse(
            experiments=[ExperimentResponse.model_validate(exp) for exp in experiments],
            total=len(experiments),
            pagination={"skip": request.skip, "limit": request.limit, "total": len(experiments)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/experiments/advanced", response_model=ExperimentTagSearchResponse)
@auth.role(Role.RESEARCHER)
async def advanced_experiment_search(
    request: AdvancedExperimentSearchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Advanced search combining multiple criteria."""
    try:
        experiments = await SearchService.advanced_experiment_search(
            db=db,
            search_text=request.search_text,
            tags=request.tags,
            match_all_tags=request.match_all_tags,
            experiment_type_id=request.experiment_type_id,
            created_after=request.created_after,
            created_before=request.created_before,
            skip=request.skip,
            limit=request.limit,
        )

        return ExperimentTagSearchResponse(
            experiments=[ExperimentResponse.model_validate(exp) for exp in experiments],
            total=len(experiments),
            pagination={"skip": request.skip, "limit": request.limit, "total": len(experiments)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/experiment-data/by-tags", response_model=ExperimentDataByTagsResponse)
@auth.role(Role.RESEARCHER)
async def get_experiment_data_by_tags(
    request: ExperimentDataByTagsRequest,
    db: AsyncSession = Depends(get_db),
    auth: Tuple[str, Role] = None,  # noqa: F841
):
    """Get all experiment data for experiments matching specific tags."""
    try:
        result = await SearchService.get_experiment_data_by_tags(
            db=db,
            tags=request.tags,
            match_all=request.match_all,
            created_after=request.created_after,
            created_before=request.created_before,
            skip=request.skip,
            limit=request.limit,
        )

        return ExperimentDataByTagsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
