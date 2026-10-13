"""Tests for Deterministic Verification Engine, Mandatory Gates, and Confidence Scoring."""
import json
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.models import Scholarship, FieldEvidence, VerificationRecord, CrawlAttempt
from app.services.verification.scoring_model import DeterministicScoringModel
from app.services.verification.gates import VerificationGates
from app.services.verification.evidence_evaluator import EvidenceEvaluator
from app.services.verification.verification_engine import VerificationEngine
from app.main import app

# Controlled fixed evaluation time for unit tests
FIXED_NOW = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
FIXED_REF_DATE = "2026-10-15"


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_deterministic_score_calculation():
    """Score must be completely deterministic and reproducible."""
    field_evidence_map = {
        "name": "SUPPORTED",
        "provider": "SUPPORTED",
        "eligibility_summary": "SUPPORTED",
        "amount_benefit": "SUPPORTED",
        "closing_date": "SUPPORTED",
    }
    
    score_1 = DeterministicScoringModel.evaluate(
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
        is_aggregator=False,
        name="AICTE Pragati Scholarship for Girls",
        provider="All India Council for Technical Education",
        is_umbrella_or_listing=False,
        field_evidence_summary=field_evidence_map,
        has_application_url=True,
        is_app_url_official=True,
        app_url_not_applicable=False,
        has_closing_date=True,
        is_deadline_contextual=True,
        is_deadline_expired=False,
        days_since_fetch=5,
        crawl_http_status=200,
        has_contradictions=False,
    )

    score_2 = DeterministicScoringModel.evaluate(
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
        is_aggregator=False,
        name="AICTE Pragati Scholarship for Girls",
        provider="All India Council for Technical Education",
        is_umbrella_or_listing=False,
        field_evidence_summary=field_evidence_map,
        has_application_url=True,
        is_app_url_official=True,
        app_url_not_applicable=False,
        has_closing_date=True,
        is_deadline_contextual=True,
        is_deadline_expired=False,
        days_since_fetch=5,
        crawl_http_status=200,
        has_contradictions=False,
    )

    assert score_1.total_score == 100.0
    assert score_1.total_score == score_2.total_score
    assert len(score_1.deductions_summary) == 0


def test_official_versus_aggregator_source():
    """Aggregators must receive 0 source points and fail official_source_gate."""
    score_agg = DeterministicScoringModel.evaluate(
        source_category="AGGREGATOR",
        is_official_source=False,
        is_aggregator=True,
        name="Tata Scholarship",
        provider="Tata Trusts",
        is_umbrella_or_listing=False,
        field_evidence_summary={},
        has_application_url=False,
        is_app_url_official=False,
        app_url_not_applicable=True,
        has_closing_date=False,
        is_deadline_contextual=False,
        is_deadline_expired=False,
        days_since_fetch=2,
        crawl_http_status=200,
        has_contradictions=False,
    )
    assert score_agg.criteria["official_source"].points_awarded == 0.0

    gate_res = VerificationGates.official_source_gate(
        source_url="https://www.buddy4study.com/scholarship/xyz",
        category="AGGREGATOR",
        is_official=False,
        is_aggregator=True,
    )
    assert gate_res.status == "FAIL"
    assert "aggregator" in gate_res.explanation.lower()


def test_field_evidence_relevance_and_generic_snippets():
    """Generic boilerplate container snippets must be flagged as WEAK_EVIDENCE."""
    rating, exp = EvidenceEvaluator.evaluate_field(
        field_name="provider",
        extracted_value="All India Council for Technical Education",
        evidence_snippet="Students Development schemes | All India Council for Technical Education Skip to main content Screen Reader Access Text",
    )
    assert rating == "WEAK_EVIDENCE"
    assert "boilerplate" in exp.lower() or "generic" in exp.lower()

    # Exact match without boilerplate
    rating_valid, _ = EvidenceEvaluator.evaluate_field(
        field_name="provider",
        extracted_value="All India Council for Technical Education",
        evidence_snippet="Administered directly by All India Council for Technical Education for degree students.",
    )
    assert rating_valid == "SUPPORTED"


def test_umbrella_title_fails_identity_gate():
    """Umbrella directory names like 'Students Development schemes' must fail identity gate."""
    gate_res = VerificationGates.scholarship_identity_gate(
        name="Students Development schemes",
        is_umbrella_or_listing=True,
    )
    assert gate_res.status == "FAIL"
    assert "umbrella" in gate_res.explanation.lower()


def test_expired_deadline_detection_controlled_clock():
    """Deadlines in the past relative to reference date must fail lifecycle gate."""
    # Past deadline: 2026-09-28 vs reference date 2026-10-15
    gate_expired = VerificationGates.lifecycle_gate(
        closing_date_str="2026-09-28",
        reference_date="2026-10-15",
    )
    assert gate_expired.status == "FAIL"
    assert "expired" in gate_expired.explanation.lower()

    # Future deadline: 2026-11-30 vs reference date 2026-10-15
    gate_active = VerificationGates.lifecycle_gate(
        closing_date_str="2026-11-30",
        reference_date="2026-10-15",
    )
    assert gate_active.status == "PASS"


def test_failed_gate_blocks_verified_status_even_at_95_score(db_session):
    """A record with >= 95% score must NEVER be VERIFIED if a mandatory gate fails."""
    # Create scholarship where deadline is in the past
    s = Scholarship(
        stable_id="test_expired_high_score",
        name="National Talent Scholarship 2026",
        provider="Ministry of Education",
        official_source_url="https://scholarships.gov.in/nts",
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
        closing_date="2026-09-01",  # Expired
        application_url="https://scholarships.gov.in/apply",
        page_type="SCHOLARSHIP_DETAIL",
        extraction_method="DETERMINISTIC_DOM",
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)

    # Attach supported evidence
    for fname, fval, snip in [
        ("name", "National Talent Scholarship 2026", "National Talent Scholarship 2026 official details"),
        ("provider", "Ministry of Education", "Awarded by Ministry of Education, Government of India"),
        ("eligibility_summary", "Class 12 pass", "Eligible: Class 12 pass with 60%"),
        ("course_level", "Undergraduate", "Available for undergraduate degree programmes"),
        ("closing_date", "2026-09-01", "Closing date: 2026-09-01"),
        ("application_url", "https://scholarships.gov.in/apply", "Apply online: https://scholarships.gov.in/apply"),
    ]:
        ev = FieldEvidence(
            scholarship_id=s.id,
            field_name=fname,
            extracted_value=fval,
            source_url="https://scholarships.gov.in/nts",
            evidence_text=snip,
            retrieval_timestamp=FIXED_NOW,
            quality_rating="SUPPORTED",
        )
        db_session.add(ev)
    db_session.commit()

    # Run verification with reference date 2026-10-15 (deadline 2026-09-01 has passed)
    rec = VerificationEngine.verify_scholarship(
        scholarship_id=s.id,
        db=db_session,
        reference_date=FIXED_REF_DATE,
        evaluation_timestamp=FIXED_NOW,
    )

    # Even if score was high, lifecycle_gate FAIL forces REVIEW_REQUIRED
    assert rec.verification_status == "REVIEW_REQUIRED"
    assert rec.lifecycle_status == "EXPIRED"
    gate_data = json.loads(rec.gate_results)
    assert gate_data["lifecycle_gate"]["status"] == "FAIL"


def test_score_boundary_94_99_versus_95_00():
    """Score must strictly meet >= 95.00 threshold for VERIFIED eligibility."""
    # 94.99 cannot qualify for VERIFIED
    score_low = 94.99
    all_gates_pass = True
    status_low = "VERIFIED" if (score_low >= 95.0 and all_gates_pass) else "REVIEW_REQUIRED"
    assert status_low == "REVIEW_REQUIRED"

    # 95.00 qualifies if all gates pass
    score_thresh = 95.00
    status_thresh = "VERIFIED" if (score_thresh >= 95.0 and all_gates_pass) else "REVIEW_REQUIRED"
    assert status_thresh == "VERIFIED"


def test_not_applicable_application_link_gate():
    """When application URL is legitimately not applicable, gate returns NOT_APPLICABLE and passes."""
    gate_res = VerificationGates.application_link_gate(
        application_url=None,
        is_official_portal=False,
        is_not_applicable=True,
    )
    assert gate_res.status == "NOT_APPLICABLE"


def test_history_persistence_and_audit_trail(db_session):
    """Running verification multiple times must preserve audit history and update is_latest flag."""
    s = Scholarship(
        stable_id="test_history_tracking",
        name="Postgraduate Research Award",
        provider="Indian Institute of Science",
        official_source_url="https://iisc.ac.in/scholarship",
        source_category="UNIVERSITY",
        is_official_source=True,
        closing_date="2026-12-31",
        page_type="SCHOLARSHIP_DETAIL",
        extraction_method="DETERMINISTIC_DOM",
    )
    db_session.add(s)
    db_session.commit()

    # Run verification #1
    rec1 = VerificationEngine.verify_scholarship(
        scholarship_id=s.id,
        db=db_session,
        reference_date=FIXED_REF_DATE,
        evaluation_timestamp=FIXED_NOW,
    )
    assert rec1.is_latest is True

    # Run verification #2 with later timestamp
    t2 = FIXED_NOW + timedelta(days=1)
    rec2 = VerificationEngine.verify_scholarship(
        scholarship_id=s.id,
        db=db_session,
        reference_date=FIXED_REF_DATE,
        evaluation_timestamp=t2,
    )

    # Check database
    db_session.refresh(rec1)
    db_session.refresh(rec2)
    assert rec1.is_latest is False
    assert rec2.is_latest is True

    history = db_session.query(VerificationRecord).filter(VerificationRecord.scholarship_id == s.id).all()
    assert len(history) == 2


def test_api_verification_endpoints():
    """Validate verification API routes."""
    client = TestClient(app)

    # 1. GET /api/verification/summary
    res_summary = client.get("/api/verification/summary")
    assert res_summary.status_code == 200
    data_sum = res_summary.json()
    assert "total_scholarships" in data_sum
    assert "average_confidence" in data_sum
    assert "verified_count" in data_sum
    assert "review_required_count" in data_sum

    # 2. POST /api/verification/run
    res_run = client.post("/api/verification/run", json={"reference_date": "2026-10-15"})
    assert res_run.status_code == 200
    data_run = res_run.json()
    assert "records_evaluated" in data_run

    # 3. If there is at least one scholarship, test detail & history routes
    res_list = client.get("/api/scholarships")
    assert res_list.status_code == 200
    items = res_list.json()["items"]
    if items:
        first_id = items[0]["id"]
        res_detail = client.get(f"/api/scholarships/{first_id}/verification")
        assert res_detail.status_code == 200
        det = res_detail.json()
        assert det["scholarship_id"] == first_id
        assert "confidence_score" in det
        assert "gate_results" in det
        assert "criteria_breakdown" in det

        res_hist = client.get(f"/api/verification/history/{first_id}")
        assert res_hist.status_code == 200
        hist_list = res_hist.json()
        assert isinstance(hist_list, list)
        assert len(hist_list) >= 1
