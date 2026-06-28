"""Simple tests for experiment operations."""

import time
from contextlib import contextmanager
from unittest.mock import patch

import pytest

from wave_backend.auth.roles import Role


async def _create_experiment_type(async_client, headers, suffix=""):
    """Helper: create an experiment type and return its id."""
    timestamp = str(int(time.time() * 1000)) + suffix
    exp_type_data = {
        "name": f"config-experiment-type-{timestamp}",
        "description": "Test experiment type",
        "table_name": f"config_experiment_table_{timestamp}",
    }
    resp = await async_client.post("/api/v1/experiment-types/", json=exp_type_data, headers=headers)
    return resp.json()["id"]


@contextmanager
def _as_role(role: Role):
    """Override the autouse auth mock to authenticate as a specific role."""
    from wave_backend.auth.unkey_client import (
        UnkeyClient,
        UnkeyValidationResult,
        get_unkey_client,
    )

    async def mock_validate(key: str, required_role=None):
        return UnkeyValidationResult(
            valid=True,
            key_id="test_key_id",
            role=role,
            permissions=[str(role)],
            roles=[str(role)],
        )

    get_unkey_client.cache_clear()
    with patch.object(UnkeyClient, "validate_key") as m:
        m.side_effect = mock_validate
        yield
    get_unkey_client.cache_clear()


@pytest.mark.asyncio
async def test_create_experiment_api(async_client):
    """Test creating an experiment via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-experiment-type-{timestamp}",
        "description": "Test experiment type",
        "table_name": f"simple_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create tags first (proper workflow)
    tag_data_1 = {"name": "simple-tag1", "description": "Simple tag 1 for testing"}
    tag_data_2 = {"name": "simple-tag2", "description": "Simple tag 2 for testing"}
    await async_client.post("/api/v1/tags/", json=tag_data_1, headers=headers)
    await async_client.post("/api/v1/tags/", json=tag_data_2, headers=headers)

    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Simple test experiment",
        "tags": ["simple-tag1", "simple-tag2"],
        "additional_data": {"test": True},
    }
    response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Simple test experiment"
    assert data["tags"] == ["simple-tag1", "simple-tag2"]
    assert "uuid" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_experiments_api(async_client):
    """Test getting experiments via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-list-experiment-type-{timestamp}",
        "description": "Test experiment type for listing",
        "table_name": f"simple_list_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create an experiment
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Experiment for listing",
    }
    await async_client.post("/api/v1/experiments/", json=experiment_data, headers=headers)

    response = await async_client.get("/api/v1/experiments/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_experiment_columns_api(async_client):
    """Test getting experiment columns via API."""
    headers = {"Authorization": "Bearer test_token"}
    # Create experiment type first
    timestamp = str(int(time.time() * 1000))
    exp_type_data = {
        "name": f"simple-columns-experiment-type-{timestamp}",
        "description": "Test experiment type for columns",
        "table_name": f"simple_columns_experiment_table_{timestamp}",
    }
    exp_type_response = await async_client.post(
        "/api/v1/experiment-types/", json=exp_type_data, headers=headers
    )
    exp_type_id = exp_type_response.json()["id"]

    # Create an experiment
    experiment_data = {
        "experiment_type_id": exp_type_id,
        "description": "Experiment for column testing",
    }
    create_response = await async_client.post(
        "/api/v1/experiments/", json=experiment_data, headers=headers
    )
    experiment_uuid = create_response.json()["uuid"]

    # Get columns for the experiment
    response = await async_client.get(
        f"/api/v1/experiments/{experiment_uuid}/columns", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert data["experiment_uuid"] == experiment_uuid
    assert len(data["columns"]) > 0


# ---------------------------------------------------------------------------
# Experiment config (hyperparameters)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_experiment_config_defaults_empty(async_client):
    """Omitting config on create yields an empty object (backwards compatible)."""
    headers = {"Authorization": "Bearer test_token"}
    exp_type_id = await _create_experiment_type(async_client, headers, "a")

    resp = await async_client.post(
        "/api/v1/experiments/",
        json={"experiment_type_id": exp_type_id, "description": "no config"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["config"] == {}


@pytest.mark.asyncio
async def test_create_experiment_with_config(async_client):
    """Config supplied at create time is stored and returned."""
    headers = {"Authorization": "Bearer test_token"}
    exp_type_id = await _create_experiment_type(async_client, headers, "b")

    config = {"number_of_repetitions": 2}
    resp = await async_client.post(
        "/api/v1/experiments/",
        json={
            "experiment_type_id": exp_type_id,
            "description": "with config",
            "config": config,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["config"] == config


@pytest.mark.asyncio
async def test_get_and_put_experiment_config(async_client):
    """GET returns current config; PUT replaces it; narrow response shape."""
    headers = {"Authorization": "Bearer test_token"}
    exp_type_id = await _create_experiment_type(async_client, headers, "c")
    create = await async_client.post(
        "/api/v1/experiments/",
        json={"experiment_type_id": exp_type_id, "description": "cfg"},
        headers=headers,
    )
    uuid = create.json()["uuid"]

    # Initially empty
    get1 = await async_client.get(f"/api/v1/experiments/{uuid}/config", headers=headers)
    assert get1.status_code == 200
    assert get1.json() == {"experiment_uuid": uuid, "config": {}}

    # Replace via PUT
    new_config = {"number_of_repetitions": 3}
    put = await async_client.put(
        f"/api/v1/experiments/{uuid}/config",
        json={"config": new_config},
        headers=headers,
    )
    assert put.status_code == 200
    assert put.json() == {"experiment_uuid": uuid, "config": new_config}

    # GET reflects the update
    get2 = await async_client.get(f"/api/v1/experiments/{uuid}/config", headers=headers)
    assert get2.json()["config"] == new_config


@pytest.mark.asyncio
async def test_get_config_missing_experiment_404(async_client):
    """Unknown experiment returns 404."""
    headers = {"Authorization": "Bearer test_token"}
    resp = await async_client.get(
        "/api/v1/experiments/00000000-0000-0000-0000-000000000000/config", headers=headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_legacy_null_config_returns_empty_object(async_client, db_session):
    """Rows created before the column existed store NULL; API exposes {}."""
    from sqlalchemy import text

    headers = {"Authorization": "Bearer test_token"}
    exp_type_id = await _create_experiment_type(async_client, headers, "d")
    create = await async_client.post(
        "/api/v1/experiments/",
        json={"experiment_type_id": exp_type_id, "description": "legacy"},
        headers=headers,
    )
    uuid = create.json()["uuid"]

    # Simulate a legacy row: force config back to NULL directly in the DB.
    await db_session.execute(
        text("UPDATE experiments SET config = NULL WHERE uuid = :u"), {"u": uuid}
    )
    await db_session.commit()

    get = await async_client.get(f"/api/v1/experiments/{uuid}/config", headers=headers)
    assert get.status_code == 200
    assert get.json()["config"] == {}

    # Full experiment response also coerces NULL -> {}
    full = await async_client.get(f"/api/v1/experiments/{uuid}", headers=headers)
    assert full.json()["config"] == {}


@pytest.mark.asyncio
async def test_config_role_gating(async_client):
    """Experimentee may GET config but not PUT it (researcher-only)."""
    headers = {"Authorization": "Bearer test_token"}
    # Use TEST role (autouse mock) to set up the experiment.
    exp_type_id = await _create_experiment_type(async_client, headers, "e")
    create = await async_client.post(
        "/api/v1/experiments/",
        json={"experiment_type_id": exp_type_id, "description": "roles"},
        headers=headers,
    )
    uuid = create.json()["uuid"]

    with _as_role(Role.EXPERIMENTEE):
        get = await async_client.get(f"/api/v1/experiments/{uuid}/config", headers=headers)
        assert get.status_code == 200

        put = await async_client.put(
            f"/api/v1/experiments/{uuid}/config",
            json={"config": {"x": 1}},
            headers=headers,
        )
        assert put.status_code == 403
