import pytest
from fastapi.testclient import TestClient

from wave_backend.api.main import app

client = TestClient(app)


@pytest.fixture
def test_client() -> TestClient:
    """Test client fixture."""
    return client
