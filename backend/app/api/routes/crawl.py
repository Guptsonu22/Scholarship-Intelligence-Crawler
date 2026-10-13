from typing import List, Optional
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
    SchedulerStatusResponse,
)
from app.services.crawling.scheduler import scheduler

router = APIRouter(prefix="/crawl", tags=["Crawl"])


@router.get("/status", response_model=SchedulerStatusResponse)
def get_crawl_status():
    """Retrieve current crawl execution and scheduler status."""
    return scheduler.get_status()


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
    res = scheduler.run_pipeline(
        db=db,
        max_candidates=payload.max_pages,
        candidate_ids=payload.candidate_ids,
        manual=True,
    )

    if res.get("status") == "OVERLAPPING_REJECTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=res["message"],
        )

    run_id = res.get("run_id", 0)
    pages_crawled = res.get("pages_crawled", 0)
    failed_fetches = res.get("failed_fetches", 0)
    changes_detected = res.get("changes_detected", 0)
    pages_unchanged = res.get("pages_unchanged", 0)

    return CrawlRunResponse(
        run_id=run_id,
        status=res.get("status", "COMPLETED"),
        message=f"Crawl run #{run_id} completed: {pages_crawled} crawled, {pages_unchanged} unchanged, {changes_detected} changes detected, {failed_fetches} failed.",
        pages_attempted=pages_crawled + failed_fetches,
        pages_succeeded=pages_crawled,
        pages_failed=failed_fetches,
    )

