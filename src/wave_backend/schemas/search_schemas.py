"""Schemas for search API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from wave_backend.schemas.schemas import (
    ExperimentResponse,
    ExperimentTypeResponse,
    TagResponse,
)


class SearchFilters(BaseModel):
    """Base search filter parameters."""

    created_after: Optional[datetime] = Field(
        None, description="Filter results created after this date"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter results created before this date"
    )
    skip: int = Field(0, ge=0, description="Number of results to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results to return")


class ExperimentTagSearchRequest(SearchFilters):
    """Search experiments by tags."""

    tags: List[str] = Field(..., min_length=1, description="List of tag names to search for")
    match_all: bool = Field(True, description="If true, match ALL tags; if false, match ANY tag")


class ExperimentTypeSearchRequest(SearchFilters):
    """Search experiment types by description."""

    search_text: str = Field(
        ..., min_length=1, description="Text to search for in name and description"
    )


class TagSearchRequest(SearchFilters):
    """Search tags by name."""

    search_text: str = Field(
        ..., min_length=1, description="Text to search for in tag name and description"
    )


class ExperimentDescriptionSearchRequest(SearchFilters):
    """Search experiment descriptions within a specific type."""

    experiment_type_id: int = Field(..., description="ID of the experiment type to search within")
    search_text: str = Field(
        ..., min_length=1, description="Text to search for in experiment descriptions"
    )


class AdvancedExperimentSearchRequest(SearchFilters):
    """Advanced search combining multiple criteria."""

    search_text: Optional[str] = Field(
        None, description="Text to search for in experiment descriptions"
    )
    tags: Optional[List[str]] = Field(None, description="List of tag names to search for")
    match_all_tags: bool = Field(
        True, description="If true, match ALL tags; if false, match ANY tag"
    )
    experiment_type_id: Optional[int] = Field(None, description="Filter by experiment type ID")


class ExperimentDataByTagsRequest(SearchFilters):
    """Get experiment data by tags."""

    tags: List[str] = Field(..., min_length=1, description="List of tag names to search for")
    match_all: bool = Field(True, description="If true, match ALL tags; if false, match ANY tag")


class ExperimentTagSearchResponse(BaseModel):
    """Response for experiment tag search."""

    experiments: List[ExperimentResponse]
    total: int
    pagination: Dict[str, int]


class ExperimentTypeSearchResponse(BaseModel):
    """Response for experiment type search."""

    experiment_types: List[ExperimentTypeResponse]
    total: int
    pagination: Dict[str, int]


class TagSearchResponse(BaseModel):
    """Response for tag search."""

    tags: List[TagResponse]
    total: int
    pagination: Dict[str, int]


class ExperimentDataByTagsResponse(BaseModel):
    """Response for experiment data by tags."""

    data: List[Dict[str, Any]]
    total_rows: int
    total_experiments: int
    experiment_info: Dict[str, Dict[str, Any]]
    pagination: Dict[str, int]
