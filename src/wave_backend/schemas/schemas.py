"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base schema for tags."""

    name: str = Field(..., max_length=100, description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")


class TagCreate(TagBase):
    """Schema for creating tags."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating tags."""

    name: Optional[str] = Field(None, max_length=100, description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")


class TagResponse(TagBase):
    """Schema for tag responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ExperimentTypeBase(BaseModel):
    """Base schema for experiment types."""

    name: str = Field(..., max_length=100, description="Experiment type name")
    description: Optional[str] = Field(None, description="Experiment type description")
    table_name: str = Field(..., max_length=100, description="Database table name")
    schema_definition: Dict[str, Any] = Field(
        default_factory=dict, description="Schema definition for additional columns"
    )


class ExperimentTypeCreate(ExperimentTypeBase):
    """Schema for creating experiment types."""

    pass


class ExperimentTypeUpdate(BaseModel):
    """Schema for updating experiment types."""

    name: Optional[str] = Field(None, max_length=100, description="Experiment type name")
    description: Optional[str] = Field(None, description="Experiment type description")
    schema_definition: Optional[Dict[str, Any]] = Field(
        None, description="Schema definition for additional columns"
    )


class ExperimentTypeResponse(ExperimentTypeBase):
    """Schema for experiment type responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ExperimentBase(BaseModel):
    """Base schema for experiments."""

    participant_id: str = Field(..., max_length=100, description="Participant identifier")
    description: str = Field(..., description="Human readable experiment description")
    tags: List[str] = Field(
        default_factory=list, max_length=10, description="List of tags (max 10)"
    )
    additional_data: Dict[str, Any] = Field(
        default_factory=dict, description="Additional experiment data"
    )


class ExperimentCreate(ExperimentBase):
    """Schema for creating experiments."""

    experiment_type_id: int = Field(..., description="ID of the experiment type")


class ExperimentUpdate(BaseModel):
    """Schema for updating experiments."""

    participant_id: Optional[str] = Field(
        None, max_length=100, description="Participant identifier"
    )
    description: Optional[str] = Field(None, description="Human readable experiment description")
    tags: Optional[List[str]] = Field(None, max_length=10, description="List of tags (max 10)")
    additional_data: Optional[Dict[str, Any]] = Field(
        None, description="Additional experiment data"
    )


class ExperimentResponse(ExperimentBase):
    """Schema for experiment responses."""

    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    experiment_type_id: int
    created_at: datetime
    updated_at: datetime
    experiment_type: ExperimentTypeResponse


class ColumnTypeInfo(BaseModel):
    """Schema for column type information."""

    column_name: str
    column_type: str
    is_nullable: bool
    default_value: Optional[Any] = None


class ExperimentColumnsResponse(BaseModel):
    """Schema for experiment column information."""

    experiment_uuid: Optional[UUID] = None
    experiment_type: Optional[str] = None
    columns: List[ColumnTypeInfo]
