import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.database import get_db
from app.db.models import SeedSource, CandidateURL, CrawlRun
from app.models.schemas import (
    SeedSourceSchema,
    CandidateSchema,
    CandidateListResponse,
    DiscoveryRunRequest,
    DiscoveryRunResponse,
)
from app.services.discovery.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["Discovery"])


@router.get("/sources", response_model=List[SeedSourceSchema])
def list_seed_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled state"),
    db: Session = Depends(get_db),
):
    """Retrieve all configured authentic scholarship seed sources."""
    query = db.query(SeedSource)
    if category:
        query = query.filter(SeedSource.category == category)
    if is_enabled is not None:
        query = query.filter(SeedSource.is_enabled == is_enabled)
    return query.all()


@router.post("/run", response_model=DiscoveryRunResponse, status_code=status.HTTP_200_OK)
def trigger_discovery_run(
    payload: DiscoveryRunRequest = DiscoveryRunRequest(),
    db: Session = Depends(get_db),
):
    """Triggers a controlled discovery run across configured seed sources."""
    service = DiscoveryService()
    crawl_run = service.run_discovery_session(
        db=db,
        source_ids=payload.source_ids,
        max_seeds=payload.max_seeds,
        respect_robots=payload.respect_robots,
    )

    return DiscoveryRunResponse(
        run_id=crawl_run.id,
        status=crawl_run.status,
        message="Discovery session completed successfully",
        seeds_processed=crawl_run.pages_crawled + crawl_run.pages_failed,
        candidates_discovered=crawl_run.candidates_discovered,
        new_candidates_added=crawl_run.candidates_discovered,
    )


@router.get("/candidates", response_model=CandidateListResponse)
def list_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (DISCOVERED, CRAWLED, FAILED, etc.)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_official: Optional[bool] = Query(None, description="Filter by official source"),
    search: Optional[str] = Query(None, description="Search keyword in URL or anchor text"),
    db: Session = Depends(get_db),
):
    """List discovered scholarship candidate URLs with pagination and filtering."""
    query = db.query(CandidateURL)

    if status:
        query = query.filter(CandidateURL.status == status)
    if category:
        query = query.filter(CandidateURL.source_category == category)
    if is_official is not None:
        query = query.filter(CandidateURL.is_official_source == is_official)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CandidateURL.url.ilike(search_pattern),
                CandidateURL.anchor_text.ilike(search_pattern),
            )
        )

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    items = (
        query.order_by(CandidateURL.relevance_score.desc(), CandidateURL.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CandidateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
