"""Scholarship Change History API Routes.

Exposes paginated field-level change history and audit queries.
"""
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.db.models import ScholarshipChangeHistory
from app.models.schemas import (
    ScholarshipChangeHistorySchema,
    ScholarshipChangeListResponse,
)

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.get("/recent", response_model=ScholarshipChangeListResponse)
def list_recent_changes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    field_name: Optional[str] = Query(None, description="Filter by changed field name"),
    classification: Optional[str] = Query(None, description="Filter by change classification"),
    scholarship_id: Optional[int] = Query(None, description="Filter by scholarship ID"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated field-level change audit trail across all scholarships."""
    query = db.query(ScholarshipChangeHistory)

    if scholarship_id:
        query = query.filter(ScholarshipChangeHistory.scholarship_id == scholarship_id)
    if field_name:
        query = query.filter(ScholarshipChangeHistory.field_name == field_name)
    if classification:
        query = query.filter(ScholarshipChangeHistory.change_classification == classification)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    records = (
        query.order_by(ScholarshipChangeHistory.detection_timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [ScholarshipChangeHistorySchema.model_validate(r) for r in records]

    return ScholarshipChangeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
