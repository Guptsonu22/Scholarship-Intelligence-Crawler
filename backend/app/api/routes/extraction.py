from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import ExtractionRun
from app.models.schemas import (
    ExtractionRunRequest,
    ExtractionRunResponse,
    ExtractionRunSchema,
)
from app.services.extraction.extraction_service import ExtractionService

router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.post("/run", response_model=ExtractionRunResponse, status_code=status.HTTP_200_OK)
def trigger_extraction_run(
    payload: ExtractionRunRequest = ExtractionRunRequest(),
    db: Session = Depends(get_db),
):
    """Triggers deterministic field extraction across crawled or candidate pages."""
    service = ExtractionService()
    run = service.run_extraction_session(
        db=db,
        candidate_ids=payload.candidate_ids,
        max_candidates=payload.max_candidates,
    )

    return ExtractionRunResponse(
        run_id=run.id,
        status=run.status,
        message="Extraction session completed",
        candidates_scanned=run.candidates_scanned,
        scholarships_extracted=run.scholarships_extracted,
        insufficient_evidence_count=run.insufficient_evidence_count,
        failed_count=run.failed_count,
    )


@router.get("/runs", response_model=List[ExtractionRunSchema])
def list_extraction_runs(
    limit: int = Query(20, ge=1, le=100, description="Max recent runs to return"),
    db: Session = Depends(get_db),
):
    """List recent extraction run sessions and their execution metrics."""
    return db.query(ExtractionRun).order_by(ExtractionRun.id.desc()).limit(limit).all()
