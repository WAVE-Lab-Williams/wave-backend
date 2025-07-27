"""Reusable fixtures for experiment data E2E testing."""

import time
from typing import Dict, List

import pytest


@pytest.fixture
def timestamp():
    """Generate a unique timestamp for test isolation."""
    return str(int(time.time() * 1000))


@pytest.fixture
def test_tags_data():
    """Standard test tags for experiments."""
    return [
        {"name": "crud-test", "description": "Tag for CRUD testing"},
        {"name": "data-test", "description": "Tag for data testing"},
    ]


@pytest.fixture
def experiment_type_data(timestamp):
    """Standard experiment type configuration for testing."""
    return {
        "name": f"test-experiment-type-{timestamp}",
        "description": "Test experiment type for CRUD testing",
        "table_name": f"test_experiment_table_{timestamp}",
        "schema_definition": {
            "test_value": "STRING",
            "number": "INTEGER",
            "value": "STRING",
            "count": "INTEGER",
        },
    }


@pytest.fixture
async def created_tags(async_client, test_tags_data):
    """Create test tags and return their data."""
    created_tags = []
    headers = {"Authorization": "Bearer test_token"}
    for tag_data in test_tags_data:
        response = await async_client.post("/api/v1/tags/", json=tag_data, headers=headers)
        assert response.status_code == 200
        created_tags.append(response.json())
    return created_tags


@pytest.fixture
async def created_experiment_type(async_client, experiment_type_data):
    """Create an experiment type and return its data."""
    headers = {"Authorization": "Bearer test_token"}
    response = await async_client.post(
        "/api/v1/experiment-types/", json=experiment_type_data, headers=headers
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
async def experiment_setup(async_client, created_experiment_type, created_tags, timestamp):
    """Complete experiment setup with type, tags, and experiment."""
    experiment_data = {
        "experiment_type_id": created_experiment_type["id"],
        "description": "Test experiment for data CRUD",
        "tags": ["crud-test", "data-test"],
    }
    headers = {"Authorization": "Bearer test_token"}
    response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )
    assert response.status_code == 200
    experiment = response.json()

    return {
        "experiment_type": created_experiment_type,
        "tags": created_tags,
        "experiment": experiment,
        "experiment_uuid": experiment["uuid"],
        "participant_id": f"test-participant-{timestamp}",
    }


@pytest.fixture
def sample_experiment_data(timestamp):
    """Sample data for creating experiment data rows."""
    return {
        "participant_id": f"test-participant-{timestamp}",
        "data": {
            "test_value": "some test data",
            "number": 42,
        },
    }


@pytest.fixture
def updated_experiment_data(timestamp):
    """Sample data for updating experiment data rows."""
    return {
        "participant_id": f"test-participant-{timestamp}",
        "data": {
            "test_value": "updated test data",
            "number": 99,
        },
    }


@pytest.fixture
def additional_experiment_data(timestamp):
    """Additional data rows for bulk testing."""
    return [
        {
            "participant_id": f"test-participant-{timestamp}",
            "data": {"value": "data1", "count": 10},
        },
        {
            "participant_id": f"test-participant-{timestamp}",
            "data": {"value": "data2", "count": 20},
        },
    ]


@pytest.fixture
async def populated_experiment(
    async_client, experiment_setup, sample_experiment_data, additional_experiment_data
):
    """Experiment with sample data already created."""
    experiment_uuid = experiment_setup["experiment_uuid"]
    created_rows = []

    # Create initial data row
    headers = {"Authorization": "Bearer test_token"}
    response = await async_client.post(
        f"/api/v1/experiment-data/{experiment_uuid}/data/",
        json=sample_experiment_data,
        headers=headers,
    )
    assert response.status_code == 201
    created_rows.append(response.json())

    # Create additional rows
    for data in additional_experiment_data:
        response = await async_client.post(
            f"/api/v1/experiment-data/{experiment_uuid}/data/", json=data, headers=headers
        )
        assert response.status_code == 201
        created_rows.append(response.json())

    return {
        **experiment_setup,
        "data_rows": created_rows,
        "primary_row_id": created_rows[0]["id"],
    }


# Helper functions for common assertions
def assert_experiment_data_response(response_data: Dict, expected_participant_id: str):
    """Assert common fields in experiment data responses."""
    assert "id" in response_data
    assert "experiment_uuid" in response_data
    assert "created_at" in response_data
    assert response_data["participant_id"] == expected_participant_id


def assert_experiment_data_matches(actual: Dict, expected: Dict):
    """Assert that experiment data matches expected values."""
    for key, value in expected["data"].items():
        assert actual[key] == value


def assert_experiment_list_response(
    response_data: List[Dict], expected_count: int, participant_id: str
):
    """Assert experiment data list responses."""
    assert len(response_data) == expected_count
    assert all(row["participant_id"] == participant_id for row in response_data)


def assert_tag_lookup_contains_experiment(experiments: List[Dict], experiment_uuid: str):
    """Assert that experiment list contains specific experiment UUID."""
    assert any(exp["uuid"] == experiment_uuid for exp in experiments)
