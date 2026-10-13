import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.db.init_db import init_db
from app.db.database import SessionLocal
from app.db.models import SeedSource, CandidateURL, CrawlRun
from app.services.crawling.http_client import CrawlResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_api_list_seed_sources():
    response = client.get("/api/discovery/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 5
    categories = {s["category"] for s in sources}
    assert "CENTRAL_GOVERNMENT" in categories
    assert "STATE_GOVERNMENT" in categories
    assert "CORPORATE_CSR" in categories


def test_api_trigger_discovery_run(monkeypatch):
    from app.services.discovery.discovery_service import DiscoveryService

    mock_crawl_run = MagicMock()
    mock_crawl_run.id = 999
    mock_crawl_run.status = "COMPLETED"
    mock_crawl_run.pages_crawled = 2
    mock_crawl_run.pages_failed = 0
    mock_crawl_run.candidates_discovered = 10

    monkeypatch.setattr(
        DiscoveryService,
        "run_discovery_session",
        lambda *args, **kwargs: mock_crawl_run,
    )

    response = client.post("/api/discovery/run", json={"max_seeds": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == 999
    assert data["status"] == "COMPLETED"
    assert data["candidates_discovered"] == 10


def test_api_list_candidates_pagination():
    response = client.get("/api/discovery/candidates?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_api_crawl_runs_list():
    response = client.get("/api/crawl/runs?limit=5")
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)
