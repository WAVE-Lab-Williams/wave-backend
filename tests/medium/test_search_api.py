"""Tests for search API endpoints."""

from datetime import datetime, timedelta

import pytest


@pytest.fixture
async def search_api_setup(async_client):
    """Create test data for search API tests."""
    # Create tags
    tag_responses = []
    for tag_data in [
        {"name": "neural", "description": "Neural studies"},
        {"name": "cognitive", "description": "Cognitive research"},
        {"name": "behavioral", "description": "Behavioral analysis"},
    ]:
        response = await async_client.post("/api/v1/tags/", json=tag_data)
        assert response.status_code == 200
        tag_responses.append(response.json())

    # Create experiment types
    exp_type_responses = []
    for exp_type_data in [
        {
            "name": "reaction_time_test",
            "description": "Test for measuring reaction times in cognitive tasks",
            "table_name": "reaction_time_test_table",
            "schema_definition": {
                "reaction_time": "FLOAT",
                "accuracy": "FLOAT",
                "stimulus_type": "STRING",
            },
        },
        {
            "name": "memory_test",
            "description": "Memory retention and recall experiments",
            "table_name": "memory_test_table",
            "schema_definition": {
                "recall_score": "FLOAT",
                "retention_time": "INTEGER",
                "word_count": "INTEGER",
            },
        },
    ]:
        response = await async_client.post("/api/v1/experiment-types/", json=exp_type_data)
        assert response.status_code == 200
        exp_type_responses.append(response.json())

    # Create experiments
    exp_responses = []
    for exp_data in [
        {
            "experiment_type_id": exp_type_responses[0]["id"],
            "description": "Reaction time study with visual stimuli",
            "tags": ["neural", "cognitive"],
        },
        {
            "experiment_type_id": exp_type_responses[0]["id"],
            "description": "Reaction time study with auditory stimuli",
            "tags": ["neural"],
        },
        {
            "experiment_type_id": exp_type_responses[1]["id"],
            "description": "Memory recall with word lists",
            "tags": ["cognitive", "behavioral"],
        },
    ]:
        response = await async_client.post("/api/v1/experiments/", json=exp_data)
        assert response.status_code == 200
        exp_responses.append(response.json())

    # Add experiment data
    data_entries = [
        {
            "experiment_uuid": exp_responses[0]["uuid"],
            "data": {
                "participant_id": "PARTICIPANT_001",
                "data": {"reaction_time": 1.23, "accuracy": 0.85, "stimulus_type": "visual"},
            },
        },
        {
            "experiment_uuid": exp_responses[1]["uuid"],
            "data": {
                "participant_id": "PARTICIPANT_002",
                "data": {"reaction_time": 0.98, "accuracy": 0.92, "stimulus_type": "audio"},
            },
        },
        {
            "experiment_uuid": exp_responses[2]["uuid"],
            "data": {
                "participant_id": "PARTICIPANT_003",
                "data": {"recall_score": 0.78, "retention_time": 300, "word_count": 20},
            },
        },
    ]

    for entry in data_entries:
        response = await async_client.post(
            f"/api/v1/experiment-data/{entry['experiment_uuid']}/data/", json=entry["data"]
        )
        assert response.status_code == 201

    return {
        "tags": tag_responses,
        "experiment_types": exp_type_responses,
        "experiments": exp_responses,
    }


@pytest.mark.anyio
async def test_search_experiments_by_tags_api(async_client, search_api_setup):
    """Test the experiments by tags search API endpoint."""
    # Test single tag search
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()

    assert "experiments" in data
    assert "total" in data
    assert "pagination" in data
    assert len(data["experiments"]) == 2

    # Test multiple tags with match_all=True
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural", "cognitive"], "match_all": True, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 1
    assert data["experiments"][0]["description"] == "Reaction time study with visual stimuli"

    # Test multiple tags with match_all=False
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural", "behavioral"], "match_all": False, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 3

    # Test with nonexistent tag
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["nonexistent"], "match_all": True, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 0


@pytest.mark.anyio
async def test_search_experiment_types_by_description_api(async_client, search_api_setup):
    """Test the experiment types by description search API endpoint."""
    # Test search by description
    response = await async_client.post(
        "/api/v1/search/experiment-types/by-description",
        json={"search_text": "reaction", "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()

    assert "experiment_types" in data
    assert "total" in data
    assert "pagination" in data
    assert len(data["experiment_types"]) == 1
    assert data["experiment_types"][0]["name"] == "reaction_time_test"

    # Test search by name
    response = await async_client.post(
        "/api/v1/search/experiment-types/by-description",
        json={"search_text": "memory", "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiment_types"]) == 1
    assert data["experiment_types"][0]["name"] == "memory_test"

    # Test case-insensitive search
    response = await async_client.post(
        "/api/v1/search/experiment-types/by-description",
        json={"search_text": "COGNITIVE", "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiment_types"]) == 1
    assert data["experiment_types"][0]["name"] == "reaction_time_test"


@pytest.mark.anyio
async def test_search_tags_by_name_api(async_client, search_api_setup):
    """Test the tags by name search API endpoint."""
    # Test search by name
    response = await async_client.post(
        "/api/v1/search/tags/by-name", json={"search_text": "neural", "skip": 0, "limit": 100}
    )
    assert response.status_code == 200
    data = response.json()

    assert "tags" in data
    assert "total" in data
    assert "pagination" in data
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "neural"

    # Test search by description
    response = await async_client.post(
        "/api/v1/search/tags/by-name", json={"search_text": "studies", "skip": 0, "limit": 100}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "neural"

    # Test partial match
    response = await async_client.post(
        "/api/v1/search/tags/by-name", json={"search_text": "cogn", "skip": 0, "limit": 100}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "cognitive"


@pytest.mark.anyio
async def test_search_experiments_by_description_and_type_api(async_client, search_api_setup):
    """Test the experiments by description and type search API endpoint."""
    experiment_types = search_api_setup["experiment_types"]
    reaction_time_type_id = experiment_types[0]["id"]

    # Test search within specific type
    response = await async_client.post(
        "/api/v1/search/experiments/by-description-and-type",
        json={
            "experiment_type_id": reaction_time_type_id,
            "search_text": "visual",
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "experiments" in data
    assert len(data["experiments"]) == 1
    assert data["experiments"][0]["description"] == "Reaction time study with visual stimuli"

    # Test search within specific type with no matches
    response = await async_client.post(
        "/api/v1/search/experiments/by-description-and-type",
        json={
            "experiment_type_id": reaction_time_type_id,
            "search_text": "memory",
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 0


@pytest.mark.anyio
async def test_advanced_experiment_search_api(async_client, search_api_setup):
    """Test the advanced experiment search API endpoint."""
    experiment_types = search_api_setup["experiment_types"]
    reaction_time_type_id = experiment_types[0]["id"]

    # Test search with text and tags
    response = await async_client.post(
        "/api/v1/search/experiments/advanced",
        json={
            "search_text": "visual",
            "tags": ["neural"],
            "match_all_tags": True,
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "experiments" in data
    assert len(data["experiments"]) == 1
    assert data["experiments"][0]["description"] == "Reaction time study with visual stimuli"

    # Test search with type filter
    response = await async_client.post(
        "/api/v1/search/experiments/advanced",
        json={
            "experiment_type_id": reaction_time_type_id,
            "tags": ["neural"],
            "match_all_tags": True,
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 2

    # Test search with conflicting criteria
    response = await async_client.post(
        "/api/v1/search/experiments/advanced",
        json={
            "search_text": "visual",
            "tags": ["behavioral"],
            "match_all_tags": True,
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 0


@pytest.mark.anyio
async def test_get_experiment_data_by_tags_api(async_client, search_api_setup):
    """Test the experiment data by tags API endpoint."""
    # Test getting data for neural experiments
    response = await async_client.post(
        "/api/v1/search/experiment-data/by-tags",
        json={"tags": ["neural"], "match_all": False, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "total_rows" in data
    assert "total_experiments" in data
    assert "experiment_info" in data
    assert "pagination" in data

    # Should have data from both neural experiments
    assert data["total_experiments"] == 2
    assert data["total_rows"] == 2
    assert len(data["data"]) == 2

    # Verify experiment metadata is included
    for row in data["data"]:
        assert "experiment_metadata" in row
        assert "experiment_uuid" in row["experiment_metadata"]
        assert "experiment_type_name" in row["experiment_metadata"]
        assert "experiment_tags" in row["experiment_metadata"]

    # Test with specific tag that has only one experiment
    response = await async_client.post(
        "/api/v1/search/experiment-data/by-tags",
        json={"tags": ["behavioral"], "match_all": True, "skip": 0, "limit": 100},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total_experiments"] == 1
    assert data["total_rows"] == 1
    assert len(data["data"]) == 1

    # Verify the data is from the correct experiment
    assert data["data"][0]["experiment_metadata"]["experiment_tags"] == ["cognitive", "behavioral"]


@pytest.mark.anyio
async def test_search_api_date_filtering(async_client, search_api_setup):
    """Test date filtering in search API endpoints."""
    # Test with future date (should return no results)
    future_date = (datetime.now() + timedelta(days=1)).isoformat()

    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={
            "tags": ["neural"],
            "match_all": True,
            "created_after": future_date,
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 0

    # Test with past date (should return results)
    past_date = (datetime.now() - timedelta(days=1)).isoformat()

    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={
            "tags": ["neural"],
            "match_all": True,
            "created_after": past_date,
            "skip": 0,
            "limit": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 2


@pytest.mark.anyio
async def test_search_api_pagination(async_client, search_api_setup):
    """Test pagination in search API endpoints."""
    # Test experiments pagination
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": 0, "limit": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 1

    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": 1, "limit": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 1

    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": 2, "limit": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["experiments"]) == 0


@pytest.mark.anyio
async def test_search_api_validation(async_client, search_api_setup):
    """Test validation in search API endpoints."""
    # Test missing required field
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"match_all": True, "skip": 0, "limit": 100},  # Missing tags
    )
    assert response.status_code == 422

    # Test empty tags list
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": [], "match_all": True, "skip": 0, "limit": 100},
    )
    assert response.status_code == 422

    # Test invalid limit (too high)
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": 0, "limit": 2000},
    )
    assert response.status_code == 422

    # Test invalid skip (negative)
    response = await async_client.post(
        "/api/v1/search/experiments/by-tags",
        json={"tags": ["neural"], "match_all": True, "skip": -1, "limit": 100},
    )
    assert response.status_code == 422
