import pytest
from unittest.mock import MagicMock
from app.db.database import SessionLocal
from app.db.models import SeedSource, CandidateURL
from app.db.init_db import init_db
from app.services.discovery.discovery_service import DiscoveryService
from app.services.crawling.http_client import CrawlResult


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>National Scholarship Portal - Ministry Schemes</title></head>
<body>
    <header>
        <a href="/home">Home</a>
        <a href="/terms">Terms of Use</a>
    </header>
    <main>
        <h1>Central Sector Scholarship Schemes</h1>
        <ul>
            <li>
                <a href="/schemes/post-matric-sc">Post Matric Scholarship Scheme for SC Students</a>
            </li>
            <li>
                <a href="/schemes/national-fellowship">National Fellowship for Higher Education of ST Students</a>
            </li>
            <li>
                <a href="https://www.ugc.gov.in/fellowship">UGC Junior Research Fellowship Portal</a>
            </li>
            <li>
                <a href="/download/guidelines.pdf">Scheme Guidelines Document</a>
            </li>
        </ul>
    </main>
</body>
</html>
"""


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_extract_candidate_links_from_html():
    service = DiscoveryService()
    links = service.extract_candidate_links_from_html(
        html=SAMPLE_HTML,
        base_url="https://scholarships.gov.in/schemes",
    )

    # Should discover post-matric, national-fellowship, and ugc fellowship
    discovered_urls = [l.normalized_url for l in links]
    assert "https://scholarships.gov.in/schemes/post-matric-sc" in discovered_urls
    assert "https://scholarships.gov.in/schemes/national-fellowship" in discovered_urls
    assert "https://www.ugc.gov.in/fellowship" in discovered_urls

    # PDF should be excluded
    assert not any(l.normalized_url.endswith(".pdf") for l in links)

    # Scholarship links should be marked relevant with high score
    sc_link = next(l for l in links if "post-matric" in l.normalized_url)
    assert sc_link.is_relevant is True
    assert sc_link.relevance_score >= 0.3


def test_run_discovery_on_seed_deduplication(monkeypatch):
    db = SessionLocal()
    try:
        # Create a unique test seed
        test_seed = SeedSource(
            name="Test National Portal",
            base_url="https://test-scholarships.gov.in/",
            category="CENTRAL_GOVERNMENT",
            scrape_depth=1,
        )
        db.add(test_seed)
        db.commit()
        db.refresh(test_seed)

        mock_http = MagicMock()
        mock_http.fetch.return_value = CrawlResult(
            url=test_seed.base_url,
            final_url=test_seed.base_url,
            status="SUCCESS",
            http_status=200,
            html=SAMPLE_HTML,
        )

        service = DiscoveryService(http_client=mock_http)

        # Run discovery 1st time
        total1, added1 = service.run_discovery_on_seed(db, test_seed)
        assert added1 > 0

        count_after_first = db.query(CandidateURL).filter(
            CandidateURL.discovery_source_url == test_seed.base_url
        ).count()

        # Run discovery 2nd time on identical content
        total2, added2 = service.run_discovery_on_seed(db, test_seed)
        assert added2 == 0  # No duplicate rows inserted!

        count_after_second = db.query(CandidateURL).filter(
            CandidateURL.discovery_source_url == test_seed.base_url
        ).count()

        assert count_after_first == count_after_second

        # Clean up test seed
        db.query(CandidateURL).filter(CandidateURL.discovery_source_url == test_seed.base_url).delete()
        db.delete(test_seed)
        db.commit()

    finally:
        db.close()
