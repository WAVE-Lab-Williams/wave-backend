"""Simple tests for experiment type operations."""

from fastapi.testclient import TestClient


class TestExperimentTypeAPI:
    """Test experiment type API endpoints."""

    def test_create_experiment_type_api(self, test_client: TestClient):
        """Test creating an experiment type via API."""
        exp_type_data = {
            "name": "simple-api-experiment",
            "description": "Experiment created via API",
            "table_name": "simple_api_experiment_table",
            "schema_definition": {"field1": "string"},
        }
        response = test_client.post("/api/v1/experiment-types/", json=exp_type_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "simple-api-experiment"
        assert data["description"] == "Experiment created via API"
        assert data["table_name"] == "simple_api_experiment_table"
        assert "id" in data
        assert "created_at" in data

    def test_get_experiment_types_api(self, test_client: TestClient):
        """Test getting experiment types via API."""
        # Create an experiment type first
        exp_type_data = {
            "name": "simple-list-experiment",
            "description": "Experiment for listing",
            "table_name": "simple_list_experiment_table",
        }
        test_client.post("/api/v1/experiment-types/", json=exp_type_data)

        response = test_client.get("/api/v1/experiment-types/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_duplicate_experiment_type_api(self, test_client: TestClient):
        """Test creating a duplicate experiment type via API."""
        exp_type_data = {
            "name": "simple-duplicate-experiment",
            "description": "First experiment",
            "table_name": "simple_duplicate_table",
        }
        test_client.post("/api/v1/experiment-types/", json=exp_type_data)

        # Try to create duplicate
        response = test_client.post("/api/v1/experiment-types/", json=exp_type_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
