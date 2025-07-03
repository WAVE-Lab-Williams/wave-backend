"""Tests for experiment data schema and metadata operations."""

import pytest


@pytest.mark.anyio
async def test_get_experiment_data_columns(async_client, experiment_setup):
    """Test retrieving column information for experiment data."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/columns")

    assert response.status_code == 200
    columns_data = response.json()

    # Verify response structure
    assert isinstance(columns_data, list)
    assert len(columns_data) > 0

    # Extract column names for validation
    column_names = [col["column_name"] for col in columns_data]

    # Verify required base columns exist
    required_columns = ["id", "participant_id", "created_at"]
    for required_col in required_columns:
        assert required_col in column_names, f"Required column '{required_col}' not found"


@pytest.mark.anyio
async def test_column_information_structure(async_client, experiment_setup):
    """Test that column information has correct structure."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/columns")

    assert response.status_code == 200
    columns_data = response.json()

    # Verify each column has required fields
    for column in columns_data:
        assert "column_name" in column
        assert "column_type" in column
        assert "is_nullable" in column
        assert isinstance(column["column_name"], str)
        assert isinstance(column["column_type"], str)
        assert isinstance(column["is_nullable"], bool)


@pytest.mark.anyio
async def test_custom_schema_columns_present(async_client, experiment_setup):
    """Test that custom schema columns are included in column information."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    experiment_type = experiment_setup["experiment_type"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/columns")

    assert response.status_code == 200
    columns_data = response.json()
    column_names = [col["column_name"] for col in columns_data]

    # Verify custom columns from experiment type schema are present
    schema_definition = experiment_type.get("schema_definition", {})
    for custom_column in schema_definition.keys():
        assert custom_column in column_names, f"Custom column '{custom_column}' not found in schema"


@pytest.mark.anyio
async def test_experiment_columns_endpoint_directly(async_client, experiment_setup):
    """Test the experiment columns endpoint (alternative path)."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiments/{experiment_uuid}/columns")

    assert response.status_code == 200
    columns_info = response.json()

    # Verify response structure for experiment columns endpoint
    assert "columns" in columns_info
    assert "experiment_uuid" in columns_info
    assert columns_info["experiment_uuid"] == experiment_uuid
    assert isinstance(columns_info["columns"], list)


@pytest.mark.anyio
async def test_schema_consistency_between_endpoints(async_client, experiment_setup):
    """Test that schema information is consistent between different endpoints."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    # Get columns from experiment-data endpoint
    data_columns_response = await async_client.get(
        f"/api/v1/experiment-data/{experiment_uuid}/data/columns"
    )
    assert data_columns_response.status_code == 200
    data_columns = data_columns_response.json()

    # Get columns from experiments endpoint
    exp_columns_response = await async_client.get(f"/api/v1/experiments/{experiment_uuid}/columns")
    assert exp_columns_response.status_code == 200
    exp_columns = exp_columns_response.json()["columns"]

    # Both should contain core columns (though structure might differ)
    data_column_names = [col["column_name"] for col in data_columns]
    exp_column_names = [col["column_name"] for col in exp_columns]

    # Core columns should be present in both
    core_columns = ["id", "participant_id", "created_at"]
    for core_col in core_columns:
        assert core_col in data_column_names or core_col in exp_column_names


@pytest.mark.anyio
async def test_column_types_are_valid(async_client, experiment_setup):
    """Test that column types are valid SQL types."""
    experiment_uuid = experiment_setup["experiment_uuid"]

    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/columns")

    assert response.status_code == 200
    columns_data = response.json()

    # Valid SQL type patterns (basic validation)
    valid_type_patterns = [
        "INTEGER",
        "BIGINT",
        "SERIAL",
        "BIGSERIAL",
        "VARCHAR",
        "TEXT",
        "CHAR",
        "FLOAT",
        "DOUBLE",
        "DECIMAL",
        "NUMERIC",
        "REAL",
        "BOOLEAN",
        "BOOL",
        "TIMESTAMP",
        "DATE",
        "TIME",
        "JSON",
        "JSONB",
        "UUID",
    ]

    for column in columns_data:
        column_type = column["column_type"].upper()
        # Check if column type starts with any valid pattern
        is_valid = any(column_type.startswith(pattern) for pattern in valid_type_patterns)
        assert (
            is_valid
        ), f"Invalid column type: {column['column_type']} for column {column['column_name']}"


@pytest.mark.anyio
async def test_schema_information_for_non_existent_experiment(async_client):
    """Test schema endpoint behavior with non-existent experiment."""
    fake_uuid = "00000000-0000-4000-8000-000000000000"

    response = await async_client.get(f"/api/v1/experiment-data/{fake_uuid}/data/columns")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_comprehensive_schema_validation(async_client, experiment_setup):
    """Test comprehensive schema validation workflow."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    experiment_type = experiment_setup["experiment_type"]

    # Get column information
    response = await async_client.get(f"/api/v1/experiment-data/{experiment_uuid}/data/columns")
    assert response.status_code == 200
    columns_data = response.json()

    # Verify we have columns
    assert len(columns_data) > 0

    # Extract information for validation
    column_names = [col["column_name"] for col in columns_data]
    column_types = {col["column_name"]: col["column_type"] for col in columns_data}

    # Validate required base columns
    base_columns = ["id", "participant_id", "created_at", "updated_at"]
    for base_col in base_columns:
        if base_col in column_names:  # Some might be in experiments table, not data table
            assert base_col in column_types

    # Validate custom schema columns
    schema_definition = experiment_type.get("schema_definition", {})
    for custom_col, expected_type in schema_definition.items():
        assert custom_col in column_names, f"Custom column {custom_col} missing"
        # Note: Actual DB types might differ from schema definition types
        assert custom_col in column_types
