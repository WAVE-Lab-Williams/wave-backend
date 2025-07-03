"""Unit tests for schema validation of experiment data."""

import pytest
from pydantic import ValidationError

from wave_backend.schemas.schemas import (
    SUPPORTED_COLUMN_TYPES,
    ColumnDefinition,
    ExperimentDataCreate,
    ExperimentDataUpdate,
    ExperimentTypeCreate,
)


class TestColumnDefinition:
    """Test cases for ColumnDefinition schema validation."""

    def test_valid_column_definition(self):
        """Test valid column definition."""
        column = ColumnDefinition(type="INTEGER", nullable=False)
        assert column.type == "INTEGER"
        assert column.nullable is False

    def test_column_type_case_insensitive(self):
        """Test that column type is case insensitive."""
        column = ColumnDefinition(type="integer")
        assert column.type == "INTEGER"

    def test_invalid_column_type(self):
        """Test invalid column type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ColumnDefinition(type="INVALID_TYPE")

        assert "Unsupported column type" in str(exc_info.value)

    def test_nullable_default_true(self):
        """Test that nullable defaults to True."""
        column = ColumnDefinition(type="STRING")
        assert column.nullable is True

    def test_all_supported_types(self):
        """Test all supported column types."""
        for col_type in SUPPORTED_COLUMN_TYPES:
            column = ColumnDefinition(type=col_type)
            assert column.type == col_type


class TestExperimentTypeCreate:
    """Test cases for ExperimentTypeCreate schema validation."""

    def test_valid_experiment_type_simple_schema(self):
        """Test valid experiment type with simple schema definition."""
        experiment_type = ExperimentTypeCreate(
            name="test_experiment",
            description="Test experiment",
            table_name="test_data",
            schema_definition={
                "reaction_time": "FLOAT",
                "accuracy": "FLOAT",
                "difficulty_level": "INTEGER",
            },
        )
        assert experiment_type.name == "test_experiment"
        assert experiment_type.table_name == "test_data"
        assert len(experiment_type.schema_definition) == 3

    def test_valid_experiment_type_complex_schema(self):
        """Test valid experiment type with complex schema definition."""
        experiment_type = ExperimentTypeCreate(
            name="test_experiment",
            table_name="test_data",
            schema_definition={
                "score": {"type": "INTEGER", "nullable": False},
                "notes": "TEXT",
                "completion_time": "FLOAT",
            },
        )
        assert experiment_type.name == "test_experiment"
        assert experiment_type.schema_definition["score"].type == "INTEGER"
        assert experiment_type.schema_definition["notes"] == "TEXT"

    def test_reserved_column_names_rejected(self):
        """Test that reserved column names are rejected."""
        reserved_names = ["id", "participant_id", "created_at", "updated_at"]

        for reserved_name in reserved_names:
            with pytest.raises(ValidationError) as exc_info:
                ExperimentTypeCreate(
                    name="test_experiment",
                    table_name="test_data",
                    schema_definition={reserved_name: "STRING"},
                )
            assert "reserved and cannot be used" in str(exc_info.value)

    def test_invalid_column_type_in_schema(self):
        """Test that invalid column types in schema are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentTypeCreate(
                name="test_experiment",
                table_name="test_data",
                schema_definition={"test_column": "INVALID_TYPE"},
            )
        assert "Unsupported column type" in str(exc_info.value)

    def test_invalid_complex_column_definition(self):
        """Test invalid complex column definition."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentTypeCreate(
                name="test_experiment",
                table_name="test_data",
                schema_definition={"test_column": {"nullable": False}},  # Missing 'type' field
            )
        assert "Field required" in str(exc_info.value)

    def test_empty_schema_definition(self):
        """Test that empty schema definition is valid."""
        experiment_type = ExperimentTypeCreate(
            name="test_experiment", table_name="test_data", schema_definition={}
        )
        assert experiment_type.schema_definition == {}

    def test_case_insensitive_reserved_names(self):
        """Test that reserved names are case insensitive."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentTypeCreate(
                name="test_experiment",
                table_name="test_data",
                schema_definition={"ID": "INTEGER"},  # Should be rejected (case insensitive)
            )
        assert "reserved and cannot be used" in str(exc_info.value)


class TestExperimentDataCreate:
    """Test cases for ExperimentDataCreate schema validation."""

    def test_valid_experiment_data_create(self):
        """Test valid experiment data creation."""
        data = ExperimentDataCreate(
            participant_id="PART-001",
            data={"reaction_time": 1.23, "accuracy": 0.85, "difficulty_level": 2},
        )
        assert data.participant_id == "PART-001"
        assert data.data["reaction_time"] == 1.23
        assert data.data["accuracy"] == 0.85
        assert data.data["difficulty_level"] == 2

    def test_empty_data_dictionary(self):
        """Test experiment data with empty data dictionary."""
        data = ExperimentDataCreate(participant_id="PART-001", data={})
        assert data.participant_id == "PART-001"
        assert data.data == {}

    def test_participant_id_required(self):
        """Test that participant_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentDataCreate(data={"reaction_time": 1.23})
        assert "participant_id" in str(exc_info.value)

    def test_data_required(self):
        """Test that data is required."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentDataCreate(participant_id="PART-001")
        assert "data" in str(exc_info.value)

    def test_participant_id_max_length(self):
        """Test participant_id max length validation."""
        long_participant_id = "A" * 101  # 101 characters, should exceed max_length of 100

        with pytest.raises(ValidationError) as exc_info:
            ExperimentDataCreate(participant_id=long_participant_id, data={"test": "value"})
        assert "String should have at most 100 characters" in str(exc_info.value)


class TestExperimentDataUpdate:
    """Test cases for ExperimentDataUpdate schema validation."""

    def test_valid_experiment_data_update(self):
        """Test valid experiment data update."""
        data = ExperimentDataUpdate(
            participant_id="PART-002", data={"reaction_time": 1.45, "accuracy": 0.90}
        )
        assert data.participant_id == "PART-002"
        assert data.data["reaction_time"] == 1.45
        assert data.data["accuracy"] == 0.90

    def test_optional_fields(self):
        """Test that all fields are optional in update."""
        data = ExperimentDataUpdate()
        assert data.participant_id is None
        assert data.data is None

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = ExperimentDataUpdate(data={"accuracy": 0.95})
        assert data.participant_id is None
        assert data.data["accuracy"] == 0.95

    def test_participant_id_only_update(self):
        """Test update with only participant_id."""
        data = ExperimentDataUpdate(participant_id="PART-003")
        assert data.participant_id == "PART-003"
        assert data.data is None
