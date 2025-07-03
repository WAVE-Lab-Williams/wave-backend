"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base schema for tags."""

    name: str = Field(
        ...,
        max_length=100,
        description="Tag name",
        examples=["cognitive", "memory", "attention", "visual", "behavioral"],
    )
    description: Optional[str] = Field(
        None,
        description="Tag description",
        examples=["Cognitive performance test", "Memory assessment", "Attention span evaluation"],
    )


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

    name: str = Field(
        ...,
        max_length=100,
        description="Experiment type name",
        examples=["cognitive_test", "memory_assessment", "attention_span", "behavioral_study"],
    )
    description: Optional[str] = Field(
        None,
        description="Experiment type description",
        examples=[
            "Cognitive performance evaluation",
            "Memory capacity assessment",
            "Attention span measurement",
        ],
    )
    table_name: str = Field(
        ...,
        max_length=100,
        description="Database table name for storing experiment data",
        examples=["cognitive_test_data", "memory_test_results", "attention_measurements"],
    )
    schema_definition: Dict[str, Any] = Field(
        default_factory=dict,
        description="Schema definition for additional columns specific to this experiment type",
        examples=[
            {"reaction_time": "FLOAT", "accuracy": "FLOAT", "difficulty_level": "INTEGER"},
            {"score": "INTEGER", "completion_time": "FLOAT", "errors": "INTEGER"},
        ],
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

    participant_id: str = Field(
        ...,
        max_length=100,
        description="Unique identifier for the participant",
        examples=["PART-001", "STUDENT-12345", "VOLUNTEER-789", "SUBJ-2024-001"],
    )
    description: str = Field(
        ...,
        description="Human readable description of what this experiment involves",
        examples=[
            "Cognitive assessment test with visual stimuli",
            "Memory retention study with word lists",
            "Attention span measurement using visual cues",
            "Behavioral response test to audio prompts",
        ],
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of tags to categorize this experiment (max 10)",
        examples=[
            ["cognitive", "visual"],
            ["memory", "retention"],
            ["attention", "behavioral"],
            ["audio", "response"],
        ],
    )
    additional_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured data specific to this experiment",
        examples=[
            {"session_duration": 30, "difficulty_level": 2, "notes": "First session"},
            {"stimuli_count": 50, "response_time_limit": 5.0, "randomized": True},
            {"baseline_score": 85, "target_accuracy": 0.9},
        ],
    )


class ExperimentCreate(ExperimentBase):
    """Schema for creating experiments."""

    experiment_type_id: int = Field(
        ...,
        description="ID of the experiment type (must exist in experiment_types table)",
        examples=[1, 2, 3],
        gt=0,
    )


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
