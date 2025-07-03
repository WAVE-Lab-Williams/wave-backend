"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wave_backend.schemas.column_types import TYPE_MAPPING

# Supported column types for experiment data tables
SUPPORTED_COLUMN_TYPES = list(TYPE_MAPPING.keys())


class ColumnDefinition(BaseModel):
    """Schema for defining a column in an experiment table."""

    type: str = Field(
        ...,
        description=f"Column data type. Supported types: {', '.join(SUPPORTED_COLUMN_TYPES)}",
        examples=["INTEGER", "FLOAT", "STRING", "TEXT", "BOOLEAN", "DATETIME", "JSON"],
    )
    nullable: bool = Field(default=True, description="Whether the column can contain null values")

    @field_validator("type")
    def validate_column_type(cls, v):
        if v.upper() not in SUPPORTED_COLUMN_TYPES:
            raise ValueError(
                f"Unsupported column type: {v}. "
                f"Supported types: {', '.join(SUPPORTED_COLUMN_TYPES)}"
            )
        return v.upper()


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
    schema_definition: Dict[str, Union[str, ColumnDefinition]] = Field(
        default_factory=dict,
        description="Schema definition for additional columns specific to this experiment type. "
        "Can be either a string (column type) or a ColumnDefinition object.",
        examples=[
            {"reaction_time": "FLOAT", "accuracy": "FLOAT", "difficulty_level": "INTEGER"},
            {
                "score": {"type": "INTEGER", "nullable": False},
                "completion_time": "FLOAT",
                "errors": "INTEGER",
            },
        ],
    )

    @field_validator("schema_definition")
    def validate_schema_definition(cls, v):
        """Validate that all column types are supported and reserved names are not used."""
        reserved_names = {"id", "participant_id", "created_at", "updated_at"}

        for column_name, column_def in v.items():
            if column_name.lower() in reserved_names:
                raise ValueError(f"Column name '{column_name}' is reserved and cannot be used")

            if isinstance(column_def, str):
                if column_def.upper() not in SUPPORTED_COLUMN_TYPES:
                    raise ValueError(
                        f"Unsupported column type: {column_def}. "
                        f"Supported types: {', '.join(SUPPORTED_COLUMN_TYPES)}"
                    )
            elif isinstance(column_def, dict):
                if "type" not in column_def:
                    raise ValueError(
                        f"Column definition for '{column_name}' must include 'type' field"
                    )
                if column_def["type"].upper() not in SUPPORTED_COLUMN_TYPES:
                    raise ValueError(
                        f"Unsupported column type: {column_def['type']}. "
                        f"Supported types: {', '.join(SUPPORTED_COLUMN_TYPES)}"
                    )

        return v


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


class ExperimentDataCreate(BaseModel):
    """Schema for creating experiment data rows."""

    participant_id: str = Field(
        ...,
        max_length=100,
        description="Participant ID for the experiment data row",
        examples=["PART-001", "STUDENT-12345", "VOLUNTEER-789"],
    )
    data: Dict[str, Any] = Field(
        ...,
        description="The experiment data values for custom columns defined in the experiment type",
        examples=[
            {"reaction_time": 1.23, "accuracy": 0.85, "difficulty_level": 2},
            {"score": 95, "completion_time": 45.6, "errors": 2},
        ],
    )


class ExperimentDataUpdate(BaseModel):
    """Schema for updating experiment data rows."""

    participant_id: Optional[str] = Field(
        None, max_length=100, description="Participant ID for the experiment data row"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="The experiment data values to update")


class ExperimentDataResponse(BaseModel):
    """Schema for experiment data row responses with detailed metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Unique identifier for this experiment data row",
        examples=[1, 42, 123],
    )
    participant_id: str = Field(
        ...,
        max_length=100,
        description="Unique identifier for the participant who generated this data",
        examples=["PART-001", "STUDENT-12345", "VOLUNTEER-789", "SUBJ-2024-001"],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when this data row was created",
        examples=["2024-01-15T10:30:00Z", "2024-03-22T14:45:30Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when this data row was last updated",
        examples=["2024-01-15T10:30:00Z", "2024-03-22T16:20:15Z"],
    )


class ExperimentDataQueryRequest(BaseModel):
    """Schema for querying experiment data with advanced filtering."""

    participant_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Filter results by specific participant ID",
        examples=["PART-001", "STUDENT-12345"],
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom column filters based on the experiment type schema. "
        "Keys should match column names, values should match the expected data type.",
        examples=[
            {"score": 95, "accuracy": 0.85},
            {"difficulty_level": 2, "completion_time": 45.6},
            {"reaction_time": 1.23, "errors": 0},
        ],
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Only return rows created after this timestamp",
        examples=["2024-01-01T00:00:00Z", "2024-03-15T09:00:00Z"],
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Only return rows created before this timestamp",
        examples=["2024-12-31T23:59:59Z", "2024-03-30T17:00:00Z"],
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return (1-1000)",
        examples=[10, 50, 100, 500],
    )
    offset: int = Field(
        0,
        ge=0,
        description="Number of rows to skip for pagination",
        examples=[0, 10, 50, 100],
    )


class ExperimentDataCountResponse(BaseModel):
    """Schema for experiment data count responses."""

    count: int = Field(
        ...,
        ge=0,
        description="Total number of experiment data rows matching the criteria",
        examples=[0, 1, 25, 150, 1000],
    )
    participant_id: Optional[str] = Field(
        None,
        description="Participant ID filter that was applied (if any)",
        examples=["PART-001", "STUDENT-12345"],
    )
    experiment_id: UUID = Field(
        ...,
        description="UUID of the experiment this count applies to",
        examples=[
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
        ],
    )


class ExperimentDataDeleteResponse(BaseModel):
    """Schema for experiment data deletion responses."""

    message: str = Field(
        ...,
        description="Confirmation message for successful deletion",
        examples=["Experiment data row deleted successfully"],
    )
    deleted_id: int = Field(
        ...,
        description="ID of the deleted experiment data row",
        examples=[1, 42, 123],
    )
    experiment_id: UUID = Field(
        ...,
        description="UUID of the experiment this deletion applies to",
        examples=[
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
        ],
    )
