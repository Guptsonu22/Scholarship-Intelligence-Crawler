from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root info endpoint returns valid metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["health_check"] == "/api/health"


def test_health_check_endpoint():
    """Verify that GET /api/health returns HTTP 200 with ok status and db connected."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["environment"] == "development"
    assert "timestamp" in data
    assert "version" in data
