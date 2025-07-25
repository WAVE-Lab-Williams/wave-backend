"""End-to-end tests for authentication with FastAPI routes.

Tests the complete authentication flow through FastAPI endpoints
with various auth decorator combinations.
"""

import asyncio
from typing import Optional

import httpx
import pytest
from fastapi import Depends, FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from wave_backend.auth.decorator import auth
from wave_backend.auth.roles import Role
from wave_backend.auth.unkey_client import UnkeyValidationResult
from wave_backend.models.database import get_db


@pytest.fixture
async def basic_test_app():
    """Create a basic test FastAPI app with auth-protected endpoints."""
    app = FastAPI()

    @app.get("/public")
    @auth.any
    async def public_endpoint(auth: tuple[str, Optional[Role]]):
        key_id, role = auth
        return {
            "message": "public access",
            "key_id": key_id,
            "role": str(role) if role else None,
        }

    @app.get("/researcher-only")
    @auth.role(Role.RESEARCHER)
    async def researcher_endpoint(auth: tuple[str, Role]):
        key_id, role = auth
        return {"message": "researcher access", "key_id": key_id, "role": str(role)}

    @app.get("/admin-only")
    @auth.role(Role.ADMIN)
    async def admin_endpoint(auth: tuple[str, Role]):
        key_id, role = auth
        return {"message": "admin access", "key_id": key_id, "role": str(role)}

    @app.post("/with-db")
    @auth.role(Role.RESEARCHER)
    async def endpoint_with_db(
        data: dict, db: AsyncSession = Depends(get_db), auth: tuple[str, Role] = None
    ):
        key_id, role = auth
        return {
            "message": "database endpoint",
            "key_id": key_id,
            "role": str(role),
            "data": data,
        }

    return app


@pytest.fixture
async def simple_test_app():
    """Create a simple test app for error testing scenarios."""
    app = FastAPI()

    @app.get("/test-endpoint")
    @auth.role(Role.RESEARCHER)
    async def test_endpoint(auth: tuple[str, Role]):
        return {"success": True}

    return app


@pytest.fixture
async def concurrent_test_app():
    """Create test app for concurrent authentication testing."""
    app = FastAPI()

    @app.get("/concurrent-test")
    @auth.role(Role.RESEARCHER)
    async def concurrent_endpoint(auth: tuple[str, Role]):
        key_id, role = auth
        return {"key_id": key_id, "role": str(role), "success": True}

    return app


class TestAuthenticatedEndpoints:
    """Test auth decorators on actual FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_public_endpoint_with_valid_key(self, basic_test_app, mock_auth_success):
        """Test public endpoint with valid API key."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/public", headers={"Authorization": "Bearer researcher_key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "public access"
            assert data["key_id"] == "mock_researcher_key_id"
            assert data["role"] == "researcher"

    @pytest.mark.asyncio
    async def test_public_endpoint_with_invalid_key(self, basic_test_app, mock_auth_success):
        """Test public endpoint with invalid API key."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get("/public", headers={"Authorization": "Bearer invalid_key"})

            assert response.status_code == 401
            assert "Authentication failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_researcher_endpoint_with_researcher_key(self, basic_test_app, mock_auth_success):
        """Test researcher endpoint with researcher-level key."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/researcher-only", headers={"Authorization": "Bearer researcher_key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "researcher access"
            assert data["role"] == "researcher"

    @pytest.mark.asyncio
    async def test_researcher_endpoint_with_admin_key(self, basic_test_app, mock_auth_success):
        """Test researcher endpoint with admin-level key (should work due to hierarchy)."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/researcher-only", headers={"Authorization": "Bearer admin_key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "researcher access"
            assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_admin_endpoint_with_insufficient_permissions(
        self, basic_test_app, mock_insufficient_permissions
    ):
        """Test admin endpoint with insufficient permissions."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/admin-only", headers={"Authorization": "Bearer experimentee_key"}
            )

            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_endpoint_without_auth_header(self, basic_test_app):
        """Test endpoint access without Authorization header."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get("/public")

            assert response.status_code == 403
            assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_endpoint_with_malformed_auth_header(self, basic_test_app):
        """Test endpoint with malformed Authorization header."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/public", headers={"Authorization": "NotBearer invalid_format"}
            )

            assert response.status_code == 403
            assert "Invalid authentication credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_endpoint_with_empty_token(self, basic_test_app):
        """Test endpoint with empty bearer token."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.get("/public", headers={"Authorization": "Bearer "})

            assert response.status_code == 403
            assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_endpoint_with_database_dependency(self, basic_test_app, mock_auth_success):
        """Test endpoint that combines auth and database dependencies."""
        async with AsyncClient(
            transport=httpx.ASGITransport(app=basic_test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/with-db",
                headers={"Authorization": "Bearer researcher_key"},
                json={"test": "data"},
            )

            # This might fail due to database setup, but should get past auth
            assert response.status_code != 401  # Not an auth error
            assert response.status_code != 403  # Not a permissions error


class TestAuthErrorHandling:
    """Test comprehensive error handling in auth system."""

    @pytest.mark.asyncio
    async def test_network_timeout_error(self, mock_network_failure):
        """Test behavior when Unkey API times out."""
        # Create test app with mock dependency
        app = FastAPI()

        @app.get("/test-endpoint")
        @auth.role(Role.RESEARCHER)
        async def test_endpoint(auth: tuple[str, Role]):
            return {"success": True}

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/test-endpoint", headers={"Authorization": "Bearer test_key"}
            )

            # Should return 401 with timeout error message
            assert response.status_code == 401
            assert "Timeout connecting to Unkey API" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unkey_service_error(self, mock_unkey_client):
        """Test behavior when Unkey service returns error."""
        # Configure mock for service error
        mock_unkey_client.side_effect = None
        mock_unkey_client.return_value = UnkeyValidationResult(
            valid=False, error="Unkey service temporarily unavailable"
        )

        # Create test app
        app = FastAPI()

        @app.get("/test-endpoint")
        @auth.role(Role.RESEARCHER)
        async def test_endpoint(auth: tuple[str, Role]):
            return {"success": True}

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/test-endpoint", headers={"Authorization": "Bearer test_key"}
            )

            assert response.status_code == 401
            assert "Authentication failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_missing_role_in_response(self, mock_unkey_client):
        """Test behavior when Unkey response is valid but has no role."""
        # Configure mock for missing role
        mock_unkey_client.side_effect = None
        mock_unkey_client.return_value = UnkeyValidationResult(
            valid=True, key_id="test_key", role=None  # No role in response
        )

        # Create test app
        app = FastAPI()

        @app.get("/test-endpoint")
        @auth.role(Role.RESEARCHER)
        async def test_endpoint(auth: tuple[str, Role]):
            return {"success": True}

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/test-endpoint", headers={"Authorization": "Bearer test_key"}
            )

            assert response.status_code == 403
            assert "No role assigned" in response.json()["detail"]


class TestRealEndpointIntegration:
    """Test authentication on real application endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth_required(self):
        """Test that health endpoint doesn't require auth."""
        from wave_backend.api.main import app

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint_no_auth_required(self):
        """Test that root endpoint doesn't require auth."""
        from wave_backend.api.main import app

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert "Welcome to the WAVE Backend API" in data["message"]

    @pytest.mark.asyncio
    async def test_openapi_docs_accessible(self):
        """Test that OpenAPI documentation is accessible."""
        from wave_backend.api.main import app

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/docs")

            # Should redirect or serve docs page
            assert response.status_code in [200, 307]

    @pytest.mark.skip(
        reason="Routes don't have auth decorators yet - will be enabled after route updates"
    )
    @pytest.mark.asyncio
    async def test_experiments_endpoint_requires_auth(self, mock_auth_success):
        """Test that experiments endpoint requires authentication."""
        from wave_backend.api.main import app

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Without auth header
            response = await client.get("/api/v1/experiments")
            assert response.status_code == 401

            # With valid auth header
            response = await client.get(
                "/api/v1/experiments", headers={"Authorization": "Bearer researcher_key"}
            )
            # Should get past auth (might fail on other dependencies)
            assert response.status_code != 401


class TestConcurrentAuthRequests:
    """Test auth system under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_auth_requests(self, concurrent_test_app, mock_auth_success):
        """Test multiple concurrent authentication requests."""

        async def make_request(client, key_suffix):
            response = await client.get(
                "/concurrent-test", headers={"Authorization": f"Bearer researcher_key_{key_suffix}"}
            )
            return response

        async with AsyncClient(
            transport=httpx.ASGITransport(app=concurrent_test_app), base_url="http://test"
        ) as client:
            # Make 20 concurrent requests
            tasks = [make_request(client, i) for i in range(20)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed
            for i, response in enumerate(responses):
                assert not isinstance(response, Exception), f"Request {i} failed: {response}"
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
