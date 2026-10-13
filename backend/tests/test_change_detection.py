"""Automated tests for Field-Level Change Detection, Evidence Retention, and Lifecycle Progression."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.models import (
    Scholarship,
    FieldEvidence,
    ScholarshipChangeHistory,
    CrawlRun,
    CandidateURL,
)
from app.services.lifecycle.change_detector import ChangeDetector, normalize_value
from app.services.lifecycle.lifecycle_manager import LifecycleManager
from app.services.crawling.scheduler import scheduler
from app.main import app

FIXED_NOW = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
REF_DATE = "2026-10-15"


@pytest.fixture
def db_session():
    """In-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_whitespace_normalization_noise_filter():
    """Whitespace and line-break variations should not produce changes."""
    assert normalize_value("  All India   Council  \n for Technical \t Education  ") == "All India Council for Technical Education"
    assert normalize_value(None) == ""
    assert normalize_value("₹50,000 per annum") == "₹50,000 per annum"


def test_identical_content_no_duplicate_change_entries(db_session):
    """When newly extracted values match existing fields, no change records should be created."""
    sch = Scholarship(
        stable_id="test_unchanged_id",
        name="Pragati Scholarship for Girls",
        provider="AICTE",
        amount_benefit="₹50,000 per annum",
        closing_date="2026-11-30",
        official_source_url="https://www.aicte-india.org/pragati",
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    # Extracted data identical with minor whitespace variation
    extracted = SimpleNamespace(
        name="  Pragati Scholarship for Girls  ",
        provider="AICTE",
        amount_benefit="₹50,000 per annum",
        amount_details=None,
        eligibility_summary=None,
        academic_requirements=None,
        course_level=None,
        income_criteria=None,
        age_criteria=None,
        gender_criteria=None,
        category_requirements=None,
        domicile_state=None,
        institution_requirements=None,
        opening_date=None,
        closing_date="2026-11-30",
        application_url=None,
        documents_required=None,
        selection_process=None,
        renewal_requirements=None,
        evidence_list=[],
    )

    changes = ChangeDetector.detect_and_apply_changes(
        db=db_session,
        scholarship=sch,
        extracted_data=extracted,
        new_content_hash="hash_same",
        evaluation_timestamp=FIXED_NOW,
    )

    assert len(changes) == 0
    history_count = db_session.query(ScholarshipChangeHistory).count()
    assert history_count == 0


def test_real_deadline_change_produces_history_and_reverification_flag(db_session):
    """A modified closing date must create an audit record flagged as CRITICAL_DEADLINE and requires_reverification."""
    sch = Scholarship(
        stable_id="test_deadline_change",
        name="Tata Trusts Grant",
        provider="Tata Trusts",
        closing_date="2026-10-31",
        official_source_url="https://www.tatatrusts.org/grant",
        source_category="CORPORATE_CSR",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    # Previous evidence attached
    old_ev = FieldEvidence(
        scholarship_id=sch.id,
        field_name="closing_date",
        extracted_value="2026-10-31",
        source_url=sch.official_source_url,
        evidence_text="Last date for application submission: 31st October 2026",
        is_current=True,
    )
    db_session.add(old_ev)
    db_session.commit()

    # New observation with extended deadline: 2026-12-15
    new_ev_item = SimpleNamespace(
        field_name="closing_date",
        extracted_value="2026-12-15",
        evidence_text="Application window extended to 15th December 2026",
        html_selector="div.deadline-box",
    )

    extracted = SimpleNamespace(
        name="Tata Trusts Grant",
        provider="Tata Trusts",
        amount_benefit=None,
        amount_details=None,
        eligibility_summary=None,
        academic_requirements=None,
        course_level=None,
        income_criteria=None,
        age_criteria=None,
        gender_criteria=None,
        category_requirements=None,
        domicile_state=None,
        institution_requirements=None,
        opening_date=None,
        closing_date="2026-12-15",
        application_url=None,
        documents_required=None,
        selection_process=None,
        renewal_requirements=None,
        evidence_list=[new_ev_item],
    )

    changes = ChangeDetector.detect_and_apply_changes(
        db=db_session,
        scholarship=sch,
        extracted_data=extracted,
        new_content_hash="hash_updated_deadline",
        evaluation_timestamp=FIXED_NOW,
    )

    assert len(changes) == 1
    ch = changes[0]
    assert ch.field_name == "closing_date"
    assert ch.previous_value == "2026-10-31"
    assert ch.new_value == "2026-12-15"
    assert ch.change_classification == "CRITICAL_DEADLINE"
    assert ch.requires_reverification is True
    assert ch.previous_evidence_id == old_ev.id
    assert ch.new_evidence_id is not None

    # Check that previous evidence is preserved but flagged as superseded
    db_session.refresh(old_ev)
    assert old_ev.is_current is False

    # Check that scholarship value was updated
    assert sch.closing_date == "2026-12-15"


def test_insufficient_observation_does_not_erase_existing_value(db_session):
    """When a new crawl fails to find a previously known field, the system must retain prior data without deletion."""
    sch = Scholarship(
        stable_id="test_retention",
        name="National Means Scholarship",
        provider="Ministry of Education",
        amount_benefit="₹12,000 per annum",
        income_criteria="< ₹3,50,000 per annum",
        official_source_url="https://scholarships.gov.in/nmmss",
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    # New crawl where amount_benefit is None / empty
    extracted = SimpleNamespace(
        name="National Means Scholarship",
        provider="Ministry of Education",
        amount_benefit=None,  # Not found on re-crawl
        amount_details=None,
        eligibility_summary=None,
        academic_requirements=None,
        course_level=None,
        income_criteria="< ₹3,50,000 per annum",
        age_criteria=None,
        gender_criteria=None,
        category_requirements=None,
        domicile_state=None,
        institution_requirements=None,
        opening_date=None,
        closing_date=None,
        application_url=None,
        documents_required=None,
        selection_process=None,
        renewal_requirements=None,
        evidence_list=[],
    )

    changes = ChangeDetector.detect_and_apply_changes(
        db=db_session,
        scholarship=sch,
        extracted_data=extracted,
        new_content_hash="hash_partial",
        evaluation_timestamp=FIXED_NOW,
    )

    assert len(changes) == 0
    # Prior amount must still be preserved
    assert sch.amount_benefit == "₹12,000 per annum"


def test_amount_and_eligibility_changes(db_session):
    """Benefit amount and eligibility changes must be correctly detected and classified."""
    sch = Scholarship(
        stable_id="test_benefit_change",
        name="Merit Fellowship",
        provider="UGC",
        amount_benefit="₹25,000 per month",
        income_criteria="< ₹5 Lakhs",
        official_source_url="https://www.ugc.gov.in/fellowship",
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    extracted = SimpleNamespace(
        name="Merit Fellowship",
        provider="UGC",
        amount_benefit="₹31,000 per month",  # Increased stipend
        amount_details=None,
        eligibility_summary=None,
        academic_requirements=None,
        course_level=None,
        income_criteria="< ₹8 Lakhs",  # Relaxed income criteria
        age_criteria=None,
        gender_criteria=None,
        category_requirements=None,
        domicile_state=None,
        institution_requirements=None,
        opening_date=None,
        closing_date=None,
        application_url=None,
        documents_required=None,
        selection_process=None,
        renewal_requirements=None,
        evidence_list=[],
    )

    changes = ChangeDetector.detect_and_apply_changes(
        db=db_session,
        scholarship=sch,
        extracted_data=extracted,
        new_content_hash="hash_hike",
        evaluation_timestamp=FIXED_NOW,
    )

    assert len(changes) == 2
    classifications = {ch.field_name: ch.change_classification for ch in changes}
    assert classifications["amount_benefit"] == "BENEFIT_UPDATE"
    assert classifications["income_criteria"] == "ELIGIBILITY_REVISION"


def test_lifecycle_manager_transitions_and_history(db_session):
    """Lifecycle transitions must be detected and recorded in change history."""
    sch = Scholarship(
        stable_id="test_lc_trans",
        name="State Scholarship",
        provider="Karnataka Post-Matric",
        closing_date="2026-10-10",  # Expired relative to 2026-10-15
        lifecycle_status="ACTIVE",
        official_source_url="https://ssp.karnataka.gov.in",
        source_category="STATE_GOVERNMENT",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    # Evaluate lifecycle against 2026-10-15
    new_status, reason = LifecycleManager.evaluate_lifecycle(
        scholarship=sch,
        reference_date="2026-10-15",
        now=FIXED_NOW,
        db=db_session,
    )

    assert new_status == "EXPIRED"
    assert sch.lifecycle_status == "EXPIRED"

    # History record should exist
    hist = db_session.query(ScholarshipChangeHistory).filter_by(scholarship_id=sch.id).first()
    assert hist is not None
    assert hist.field_name == "lifecycle_status"
    assert hist.previous_value == "ACTIVE"
    assert hist.new_value == "EXPIRED"
    assert hist.change_classification == "LIFECYCLE_TRANSITION"


def test_temporary_network_error_not_implying_withdrawal(db_session):
    """A temporary network error (HTTP 500, timeout) should not transition status to NO_LONGER_VERIFIABLE."""
    sch = Scholarship(
        stable_id="test_temp_err",
        name="Ongoing Fellowship",
        provider="DST",
        closing_date="2026-12-31",
        lifecycle_status="ACTIVE",
        official_source_url="https://dst.gov.in/fellowship",
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
    )
    db_session.add(sch)
    db_session.commit()

    # HTTP 500 server error
    status_500, _ = LifecycleManager.evaluate_lifecycle(
        scholarship=sch,
        reference_date=REF_DATE,
        now=FIXED_NOW,
        crawl_http_status=500,
        db=db_session,
    )
    assert status_500 == "ACTIVE"  # Retains active state!

    # HTTP 404 should transition to NO_LONGER_VERIFIABLE
    status_404, _ = LifecycleManager.evaluate_lifecycle(
        scholarship=sch,
        reference_date=REF_DATE,
        now=FIXED_NOW,
        crawl_http_status=404,
        db=db_session,
    )
    assert status_404 == "NO_LONGER_VERIFIABLE"


def test_scheduler_overlap_prevention():
    """Concurrent scheduler runs must be prevented from overlapping."""
    # Simulate scheduler is already running a job
    scheduler.is_running_job = True
    try:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        sess = Session()

        result = scheduler.run_pipeline(db=sess, max_candidates=1)
        assert result["status"] == "OVERLAPPING_REJECTED"
        sess.close()
    finally:
        scheduler.is_running_job = False


def test_scheduler_api_routes():
    """Validate scheduler control and status API endpoints."""
    client = TestClient(app)

    # 1. GET /api/scheduler/status
    res_st = client.get("/api/scheduler/status")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert "is_active" in st_data
    assert "is_running_job" in st_data

    # 2. POST /api/scheduler/start
    res_start = client.post("/api/scheduler/start")
    assert res_start.status_code == 200
    assert res_start.json()["status"] in ("STARTED", "ALREADY_ACTIVE")

    # 3. POST /api/scheduler/stop
    res_stop = client.post("/api/scheduler/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] in ("STOPPED", "ALREADY_STOPPED")

    # 4. GET /api/crawl/status
    res_crawl_st = client.get("/api/crawl/status")
    assert res_crawl_st.status_code == 200

    # 5. GET /api/changes/recent
    res_changes = client.get("/api/changes/recent?page=1&page_size=10")
    assert res_changes.status_code == 200
    changes_data = res_changes.json()
    assert "items" in changes_data
    assert "total" in changes_data
