import pytest
from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.db.models import CandidateURL, Scholarship, FieldEvidence, CrawlAttempt
from app.services.extraction.extraction_service import ExtractionService

TEST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Central Sector Scheme of Scholarships</title></head>
<body>
    <h1>Central Sector Scheme of Scholarships for College and University Students</h1>
    <p>Administered by the Department of Higher Education.</p>
    <p>Financial Support: Rate of scholarship is ₹12,000 per annum for graduation.</p>
    <p>Eligibility: Students pursuing Undergraduate / Bachelor's degrees with income below ₹4,50,000 per annum.</p>
    <p>Deadline: Closing Date is 31/12/2026.</p>
    <a href="https://scholarships.gov.in/apply">Apply Online</a>
</body>
</html>
"""


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_process_candidate_persists_scholarship_and_traceable_evidence():
    db = SessionLocal()
    try:
        cand = CandidateURL(
            url="https://scholarships.gov.in/schemes/central-sector",
            normalized_url="https://scholarships.gov.in/schemes/central-sector",
            discovery_source_url="https://scholarships.gov.in/",
            discovery_method="SEED_PORTAL",
            source_category="CENTRAL_GOVERNMENT",
            relevance_score=0.9,
            status="CRAWLED",
            is_official_source=True,
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)

        service = ExtractionService()
        scholarship, outcome = service.process_candidate(
            db=db,
            candidate=cand,
            html=TEST_HTML,
            content_hash="test_sha256_hash_abcdef",
        )

        assert outcome == "SCHOLARSHIP_DETAIL"
        assert scholarship is not None
        assert scholarship.name == "Central Sector Scheme of Scholarships for College and University Students"
        assert scholarship.official_source_url == cand.normalized_url
        assert scholarship.closing_date == "2026-12-31"
        assert "12,000" in scholarship.amount_benefit
        assert scholarship.stable_id is not None

        # Verify Traceable Evidence: Scholarship -> Extracted field -> Evidence record -> Original URL
        evidence_records = db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == scholarship.id).all()
        assert len(evidence_records) >= 4

        fields = {ev.field_name: ev for ev in evidence_records}
        assert "name" in fields
        assert "closing_date" in fields
        assert "amount_benefit" in fields

        # Check evidence points back to source URL and content hash
        date_ev = fields["closing_date"]
        assert date_ev.source_url == cand.normalized_url
        assert date_ev.content_hash == "test_sha256_hash_abcdef"
        assert "31/12/2026" in date_ev.evidence_text

        # Clean up
        db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == scholarship.id).delete()
        db.delete(scholarship)
        db.delete(cand)
        db.commit()

    finally:
        db.close()


def test_process_candidate_deduplication():
    db = SessionLocal()
    try:
        cand = CandidateURL(
            url="https://scholarships.gov.in/schemes/dedup-test",
            normalized_url="https://scholarships.gov.in/schemes/dedup-test",
            discovery_source_url="https://scholarships.gov.in/",
            status="CRAWLED",
        )
        db.add(cand)
        db.commit()
        db.refresh(cand)

        service = ExtractionService()

        # Run extraction 1st time
        s1, out1 = service.process_candidate(db, cand, html=TEST_HTML, content_hash="hash_1")
        assert s1 is not None

        count_before = db.query(Scholarship).filter(Scholarship.official_source_url == cand.normalized_url).count()

        # Run extraction 2nd time on same URL
        s2, out2 = service.process_candidate(db, cand, html=TEST_HTML, content_hash="hash_2")
        assert s2 is not None

        count_after = db.query(Scholarship).filter(Scholarship.official_source_url == cand.normalized_url).count()

        # Deduplication must ensure only 1 row exists
        assert count_before == 1
        assert count_after == 1
        assert s1.id == s2.id

        # Clean up
        db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == s1.id).delete()
        db.delete(s1)
        db.delete(cand)
        db.commit()

    finally:
        db.close()
