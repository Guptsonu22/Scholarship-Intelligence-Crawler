import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.db.models import Scholarship, FieldEvidence
from app.models.schemas import (
    ScholarshipSchema,
    ScholarshipDetailSchema,
    ScholarshipListResponse,
    FieldEvidenceSchema,
)

router = APIRouter(prefix="/scholarships", tags=["Scholarships"])


@router.get("", response_model=ScholarshipListResponse)
def list_scholarships(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by source category"),
    status: Optional[str] = Query(None, description="Filter by lifecycle status"),
    search: Optional[str] = Query(None, description="Search keyword in name or provider"),
    db: Session = Depends(get_db),
):
    """List structured scholarship records with pagination and filtering."""
    query = db.query(Scholarship)

    if category:
        query = query.filter(Scholarship.source_category == category)
    if status:
        query = query.filter(Scholarship.lifecycle_status == status)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Scholarship.name.ilike(search_pattern),
                Scholarship.provider.ilike(search_pattern),
            )
        )

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    records = (
        query.order_by(Scholarship.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for s in records:
        s_schema = ScholarshipSchema.model_validate(s)
        s_schema.evidence_count = len(s.evidence_records)
        items.append(s_schema)

    return ScholarshipListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{scholarship_id}", response_model=ScholarshipDetailSchema)
def get_scholarship_detail(
    scholarship_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full details of an extracted scholarship opportunity along with its field evidence."""
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholarship #{scholarship_id} not found",
        )

    s_schema = ScholarshipSchema.model_validate(scholarship)
    s_schema.evidence_count = len(scholarship.evidence_records)

    evidence_items = [
        FieldEvidenceSchema.model_validate(ev)
        for ev in scholarship.evidence_records
    ]

    return ScholarshipDetailSchema(
        scholarship=s_schema,
        evidence_records=evidence_items,
    )


@router.get("/{scholarship_id}/evidence", response_model=List[FieldEvidenceSchema])
def get_scholarship_field_evidence(
    scholarship_id: int,
    field_name: Optional[str] = Query(None, description="Optional filter by specific field name"),
    db: Session = Depends(get_db),
):
    """Inspect field-level evidence records for a scholarship opportunity."""
    scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not scholarship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scholarship #{scholarship_id} not found",
        )

    query = db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == scholarship_id)
    if field_name:
        query = query.filter(FieldEvidence.field_name == field_name)

    return query.order_by(FieldEvidence.id.asc()).all()
