"""
Integration tests for versioning middleware and endpoints.
"""

from fastapi.testclient import TestClient

from wave_backend.api.main import app
from wave_backend.utils.versioning import API_VERSION

client = TestClient(app)


class TestVersioningMiddleware:
    """Test versioning middleware functionality."""

    def test_api_version_header_added(self):
        """Test that API version header is added to responses."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-WAVE-API-Version" in response.headers
        assert response.headers["X-WAVE-API-Version"] == API_VERSION

    def test_cors_headers_for_version(self):
        """Test that CORS headers expose version header."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "Access-Control-Expose-Headers" in response.headers
        assert "X-WAVE-API-Version" in response.headers["Access-Control-Expose-Headers"]

    def test_client_version_header_processing(self):
        """Test that client version headers are processed."""
        headers = {"X-WAVE-Client-Version": "1.0.0"}
        response = client.get("/health", headers=headers)
        assert response.status_code == 200
        assert response.headers["X-WAVE-API-Version"] == API_VERSION


class TestVersionEndpoint:
    """Test the version information endpoint."""

    def test_version_endpoint_no_client_version(self):
        """Test version endpoint without client version."""
        response = client.get("/version")
        assert response.status_code == 200

        data = response.json()
        assert data["api_version"] == API_VERSION
        assert data["client_version"] is None
        assert data["compatible"] is None
        assert "warning" in data

    def test_version_endpoint_with_compatible_client(self):
        """Test version endpoint with compatible client version."""
        headers = {"X-WAVE-Client-Version": "1.0.0"}
        response = client.get("/version", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["api_version"] == API_VERSION
        assert data["client_version"] == "1.0.0"
        assert data["compatible"] is True
        assert "warning" not in data or data["warning"] is None

    def test_version_endpoint_with_incompatible_client(self):
        """Test version endpoint with incompatible client version."""
        headers = {"X-WAVE-Client-Version": "2.0.0"}
        response = client.get("/version", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["api_version"] == API_VERSION
        assert data["client_version"] == "2.0.0"
        assert data["compatible"] is False
        assert "warning" in data
        assert data["warning"] is not None

    def test_version_endpoint_with_invalid_client_version(self):
        """Test version endpoint with invalid client version."""
        headers = {"X-WAVE-Client-Version": "invalid"}
        response = client.get("/version", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["api_version"] == API_VERSION
        assert data["client_version"] == "invalid"
        assert data["compatible"] is False
        assert "warning" in data
        assert "Invalid version format" in data["warning"]


class TestVersioningOnAPIEndpoints:
    """Test versioning on actual API endpoints."""

    def test_experiment_types_endpoint_with_versioning(self):
        """Test that experiment types endpoint includes version headers."""
        response = client.get("/api/v1/experiment-types/")
        # Should return 401 due to auth, but headers should be present
        assert "X-WAVE-API-Version" in response.headers
        assert response.headers["X-WAVE-API-Version"] == API_VERSION

    def test_health_endpoint_version_consistency(self):
        """Test that health endpoint maintains version consistency."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["X-WAVE-API-Version"] == API_VERSION

        # Test multiple requests for consistency
        for _ in range(3):
            resp = client.get("/health")
            assert resp.headers["X-WAVE-API-Version"] == API_VERSION
