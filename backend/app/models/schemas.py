from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall service status (ok/error)")
    app_name: str = Field(..., description="Name of the backend service")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Active runtime environment")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="UTC server timestamp")


class SystemInfoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str


class SeedSourceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    category: str
    description: Optional[str] = None
    is_enabled: bool
    scrape_depth: int
    created_at: datetime


class CandidateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    normalized_url: str
    discovery_source_url: str
    discovery_method: str
    source_category: str
    anchor_text: Optional[str] = None
    page_title: Optional[str] = None
    relevance_score: float
    status: str
    is_official_source: bool
    rejection_reason: Optional[str] = None
    discovered_at: datetime


class CandidateListResponse(BaseModel):
    items: List[CandidateSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class CrawlAttemptSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: Optional[int] = None
    crawl_run_id: Optional[int] = None
    fetch_url: str
    final_url: Optional[str] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    content_hash: Optional[str] = None
    response_time_ms: Optional[int] = None
    status: str
    error_reason: Optional[str] = None
    extracted_links_count: int
    created_at: datetime


class CandidateDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate: CandidateSchema
    attempts: List[CrawlAttemptSchema] = []


class CrawlRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    candidates_discovered: int
    pages_crawled: int
    pages_failed: int
    error_message: Optional[str] = None


class DiscoveryRunRequest(BaseModel):
    source_ids: Optional[List[int]] = Field(None, description="Optional list of seed source IDs to crawl")
    max_seeds: int = Field(5, ge=1, le=20, description="Max seed sources to process in this run")
    respect_robots: bool = Field(True, description="Whether to check and enforce robots.txt")


class DiscoveryRunResponse(BaseModel):
    run_id: int
    status: str
    message: str
    seeds_processed: int
    candidates_discovered: int
    new_candidates_added: int


class CrawlRunRequest(BaseModel):
    candidate_ids: Optional[List[int]] = Field(None, description="Optional list of candidate IDs to crawl")
    max_pages: int = Field(5, ge=1, le=50, description="Maximum candidate pages to crawl")
    delay_seconds: Optional[float] = Field(None, ge=0.5, le=10.0, description="Optional delay override between requests")


class CrawlRunResponse(BaseModel):
    run_id: int
    status: str
    message: str
    pages_attempted: int
    pages_succeeded: int
    pages_failed: int


# --- Phase 3: Extraction & Field Evidence Schemas ---

class FieldEvidenceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scholarship_id: Optional[int] = None
    candidate_id: Optional[int] = None
    field_name: str
    extracted_value: Optional[str] = None
    source_url: str
    evidence_text: str
    page_title: Optional[str] = None
    retrieval_timestamp: datetime
    content_hash: Optional[str] = None
    extraction_method: str
    html_selector: Optional[str] = None
    validation_status: str


class ScholarshipSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stable_id: str
    name: Optional[str] = None
    provider: Optional[str] = None
    official_source_url: str
    application_url: Optional[str] = None
    source_category: str
    is_official_source: bool

    amount_benefit: Optional[str] = None
    amount_details: Optional[str] = None
    eligibility_summary: Optional[str] = None
    academic_requirements: Optional[str] = None
    course_level: Optional[str] = None
    income_criteria: Optional[str] = None
    age_criteria: Optional[str] = None
    gender_criteria: Optional[str] = None
    category_requirements: Optional[str] = None
    domicile_state: Optional[str] = None
    institution_requirements: Optional[str] = None

    opening_date: Optional[str] = None
    closing_date: Optional[str] = None
    documents_required: Optional[str] = None
    selection_process: Optional[str] = None
    renewal_requirements: Optional[str] = None

    lifecycle_status: str
    page_type: str
    extraction_timestamp: datetime
    last_fetched_timestamp: Optional[datetime] = None
    content_hash: Optional[str] = None
    extraction_method: str
    validation_warnings: Optional[str] = None
    evidence_count: int = 0


class ScholarshipDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scholarship: ScholarshipSchema
    evidence_records: List[FieldEvidenceSchema] = []


class ScholarshipListResponse(BaseModel):
    items: List[ScholarshipSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExtractionRunRequest(BaseModel):
    candidate_ids: Optional[List[int]] = Field(None, description="Optional list of candidate IDs to extract from")
    max_candidates: int = Field(10, ge=1, le=50, description="Max candidate pages to process")


class ExtractionRunResponse(BaseModel):
    run_id: int
    status: str
    message: str
    candidates_scanned: int
    scholarships_extracted: int
    insufficient_evidence_count: int
    failed_count: int


class ExtractionRunSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    candidates_scanned: int
    scholarships_extracted: int
    insufficient_evidence_count: int
    failed_count: int
    error_message: Optional[str] = None
