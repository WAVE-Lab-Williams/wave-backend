import pytest
from fastapi.testclient import TestClient

from wave_backend.api.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Test client fixture for unit tests."""
    return TestClient(app)
