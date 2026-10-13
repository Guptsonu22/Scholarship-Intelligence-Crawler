"""Verification API Routes.

Exposes deterministic verification triggers, audit history, and summary statistics.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Scholarship, VerificationRecord
from app.models.schemas import (
    VerificationRunRequest,
    VerificationRunResponse,
    VerificationSummaryResponse,
    VerificationRecordSchema,
    ScholarshipVerificationDetailResponse,
)
from app.services.verification.verification_engine import VerificationEngine

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/run", response_model=VerificationRunResponse)
def run_verification(
    payload: Optional[VerificationRunRequest] = None,
    db: Session = Depends(get_db),
):
    """Triggers deterministic verification on extracted scholarships.
    
    Evaluates authenticity, completeness, freshness, and enforces mandatory gates.
    """
    scholarship_ids = payload.scholarship_ids if payload else None
    ref_date = payload.reference_date if payload else None

    if scholarship_ids:
        records_to_verify = db.query(Scholarship).filter(Scholarship.id.in_(scholarship_ids)).all()
    else:
        records_to_verify = db.query(Scholarship).all()

    if not records_to_verify:
        return VerificationRunResponse(
            records_evaluated=0,
            verified_count=0,
            review_required_count=0,
            message="No scholarship records available for verification.",
        )

    verified_count = 0
    review_required_count = 0

    for s in records_to_verify:
        rec = VerificationEngine.verify_scholarship(
            scholarship_id=s.id,
            db=db,
            reference_date=ref_date,
        )
        if rec.verification_status == "VERIFIED":
            verified_count += 1
        else:
            review_required_count += 1

    return VerificationRunResponse(
        records_evaluated=len(records_to_verify),
        verified_count=verified_count,
        review_required_count=review_required_count,
        message=f"Evaluated {len(records_to_verify)} records: {verified_count} VERIFIED, {review_required_count} REVIEW_REQUIRED.",
    )


@router.get("/summary", response_model=VerificationSummaryResponse)
def get_verification_summary(
    db: Session = Depends(get_db),
):
    """Retrieve actual verification aggregate statistics and average confidence."""
    summary_data = VerificationEngine.get_summary(db)
    return VerificationSummaryResponse(**summary_data)


@router.get("/history/{scholarship_id}", response_model=List[VerificationRecordSchema])
def get_verification_history(
    scholarship_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve complete audit history of all verification evaluations for a scholarship."""
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholarship #{scholarship_id} not found",
        )

    history = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.scholarship_id == scholarship_id)
        .order_by(VerificationRecord.verified_at.desc())
        .all()
    )

    return [VerificationRecordSchema.model_validate(h) for h in history]


@router.get("/detail/{scholarship_id}", response_model=ScholarshipVerificationDetailResponse)
def get_scholarship_verification_detail(
    scholarship_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve decoded latest verification result with criteria breakdown, gates, and deductions."""
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholarship #{scholarship_id} not found",
        )

    latest_record = (
        db.query(VerificationRecord)
        .filter(
            VerificationRecord.scholarship_id == scholarship_id,
            VerificationRecord.is_latest == True,
        )
        .first()
    )

    if not latest_record:
        # Run on-demand verification if not yet verified
        latest_record = VerificationEngine.verify_scholarship(
            scholarship_id=scholarship_id,
            db=db,
        )

    try:
        criteria_dict = json.loads(latest_record.scoring_breakdown)
    except Exception:
        criteria_dict = {}

    try:
        gate_dict = json.loads(latest_record.gate_results)
    except Exception:
        gate_dict = {}

    try:
        deductions_list = json.loads(latest_record.deductions_reasons)
    except Exception:
        deductions_list = []

    try:
        evidence_list = json.loads(latest_record.evidence_references) if latest_record.evidence_references else []
    except Exception:
        evidence_list = []

    return ScholarshipVerificationDetailResponse(
        scholarship_id=latest_record.scholarship_id,
        confidence_score=latest_record.confidence_score,
        verification_status=latest_record.verification_status,
        lifecycle_status=latest_record.lifecycle_status,
        scoring_model_version=latest_record.scoring_model_version,
        criteria_breakdown=criteria_dict,
        gate_results=gate_dict,
        deductions=deductions_list,
        evidence_references=evidence_list,
        verified_at=latest_record.verified_at,
    )
