from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import CrawlRun, CandidateURL, CrawlAttempt
from app.models.schemas import (
    CrawlRunSchema,
    CandidateDetailSchema,
    CandidateSchema,
    CrawlAttemptSchema,
    CrawlRunRequest,
    CrawlRunResponse,
)
from app.services.crawling.crawler_service import CrawlerService

router = APIRouter(prefix="/crawl", tags=["Crawl"])


@router.get("/runs", response_model=List[CrawlRunSchema])
def list_crawl_runs(
    limit: int = Query(20, ge=1, le=100, description="Max recent runs to return"),
    db: Session = Depends(get_db),
):
    """Retrieve audit history of recent discovery and crawl runs."""
    return db.query(CrawlRun).order_by(CrawlRun.id.desc()).limit(limit).all()


@router.get("/candidates/{candidate_id}", response_model=CandidateDetailSchema)
def get_candidate_details(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """Inspect candidate URL details and its complete crawl attempt history."""
    candidate = db.query(CandidateURL).filter(CandidateURL.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate URL #{candidate_id} not found",
        )

    attempts = (
        db.query(CrawlAttempt)
        .filter(CrawlAttempt.candidate_id == candidate_id)
        .order_by(CrawlAttempt.id.desc())
        .all()
    )

    return CandidateDetailSchema(
        candidate=CandidateSchema.model_validate(candidate),
        attempts=[CrawlAttemptSchema.model_validate(att) for att in attempts],
    )


@router.post("/run", response_model=CrawlRunResponse, status_code=status.HTTP_200_OK)
def trigger_crawl_run(
    payload: CrawlRunRequest = CrawlRunRequest(),
    db: Session = Depends(get_db),
):
    """Triggers a controlled crawl run across queued or selected scholarship candidates."""
    service = CrawlerService()
    crawl_run = service.run_crawl_session(
        db=db,
        candidate_ids=payload.candidate_ids,
        max_pages=payload.max_pages,
        delay_seconds=payload.delay_seconds,
    )

    return CrawlRunResponse(
        run_id=crawl_run.id,
        status=crawl_run.status,
        message="Crawl run completed",
        pages_attempted=crawl_run.pages_crawled + crawl_run.pages_failed,
        pages_succeeded=crawl_run.pages_crawled,
        pages_failed=crawl_run.pages_failed,
    )
