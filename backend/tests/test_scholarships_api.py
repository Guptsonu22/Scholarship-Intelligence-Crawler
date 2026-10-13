import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db
from app.db.database import SessionLocal
from app.db.models import Scholarship, FieldEvidence, CandidateURL

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_api_scholarships_crud_and_evidence():
    db = SessionLocal()
    try:
        # Create a test scholarship with evidence
        sch = Scholarship(
            stable_id="test_api_stable_id_123",
            name="AICTE Pragati Scholarship for Girls",
            provider="All India Council for Technical Education",
            official_source_url="https://www.aicte-india.org/pragati",
            source_category="CENTRAL_GOVERNMENT",
            is_official_source=True,
            amount_benefit="₹50,000 per annum",
            closing_date="2026-11-30",
            lifecycle_status="PENDING_VERIFICATION",
            page_type="SCHOLARSHIP_DETAIL",
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)

        ev = FieldEvidence(
            scholarship_id=sch.id,
            field_name="amount_benefit",
            extracted_value="₹50,000 per annum",
            source_url=sch.official_source_url,
            evidence_text="Amount of scholarship: ₹50,000 per annum",
            validation_status="VALID",
        )
        db.add(ev)
        db.commit()

        # 1. Test GET /api/scholarships
        res = client.get("/api/scholarships?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert any(item["name"] == "AICTE Pragati Scholarship for Girls" for item in data["items"])

        # 2. Test GET /api/scholarships/{id}
        res_detail = client.get(f"/api/scholarships/{sch.id}")
        assert res_detail.status_code == 200
        detail_data = res_detail.json()
        assert detail_data["scholarship"]["name"] == "AICTE Pragati Scholarship for Girls"
        assert len(detail_data["evidence_records"]) >= 1

        # 3. Test GET /api/scholarships/{id}/evidence
        res_ev = client.get(f"/api/scholarships/{sch.id}/evidence?field_name=amount_benefit")
        assert res_ev.status_code == 200
        ev_data = res_ev.json()
        assert len(ev_data) == 1
        assert ev_data[0]["extracted_value"] == "₹50,000 per annum"

        # 4. Test 404 for non-existent scholarship
        res_404 = client.get("/api/scholarships/999999")
        assert res_404.status_code == 404

        # Clean up
        db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == sch.id).delete()
        db.delete(sch)
        db.commit()

    finally:
        db.close()


def test_api_extraction_runs_endpoint():
    res = client.get("/api/extraction/runs?limit=5")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)
