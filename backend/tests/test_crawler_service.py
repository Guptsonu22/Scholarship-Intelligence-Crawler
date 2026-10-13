import pytest
from unittest.mock import MagicMock
from app.db.database import SessionLocal
from app.db.models import CandidateURL, CrawlAttempt
from app.db.init_db import init_db
from app.services.crawling.crawler_service import CrawlerService
from app.services.crawling.http_client import CrawlResult


SECONDARY_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h2>Scholarship Eligibility & Guidelines</h2>
    <p>Eligible candidates can check awards and details.</p>
    <a href="/schemes/post-matric-detail">Detailed Scheme Criteria</a>
</body>
</html>
"""


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_crawler_service_crawl_candidate(monkeypatch):
    db = SessionLocal()
    try:
        cand = CandidateURL(
            url="https://scholarships.gov.in/schemes/post-matric",
            normalized_url="https://scholarships.gov.in/schemes/post-matric",
            discovery_source_url="https://scholarships.gov.in/",
            discovery_method="SEED_PORTAL",
            source_category="CENTRAL_GOVERNMENT",
            relevance_score=0.9,
            status="QUEUED",
            is_official_source=True,
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)

        mock_http = MagicMock()
        mock_http.fetch.return_value = CrawlResult(
            url=cand.normalized_url,
            final_url=cand.normalized_url,
            status="SUCCESS",
            http_status=200,
            content_type="text/html",
            content_length=len(SECONDARY_HTML),
            content_hash="mocked_hash_1234567890abcdef",
            html=SECONDARY_HTML,
            response_time_ms=120,
        )

        crawler = CrawlerService(http_client=mock_http)
        attempt = crawler.crawl_candidate(db, cand)

        assert attempt.status == "SUCCESS"
        assert attempt.http_status == 200
        assert attempt.content_hash == "mocked_hash_1234567890abcdef"

        # Check candidate updated status
        db.refresh(cand)
        assert cand.status == "CRAWLED"

        # Clean up
        db.query(CrawlAttempt).filter(CrawlAttempt.candidate_id == cand.id).delete()
        db.query(CandidateURL).filter(CandidateURL.discovery_source_url == cand.normalized_url).delete()
        db.delete(cand)
        db.commit()
    finally:
        db.close()
