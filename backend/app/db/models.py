from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class SystemInfo(Base):
    """System information and state tracking table."""
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SeedSource(Base):
    """Configured entrypoint portals and websites for candidate discovery."""
    __tablename__ = "seed_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    base_url = Column(String(500), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    scrape_depth = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SourceClassification(Base):
    """Domain classification rules and cache."""
    __tablename__ = "source_classifications"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    is_official = Column(Boolean, default=False, nullable=False)
    trust_score = Column(Float, default=0.5, nullable=False)
    classification_reason = Column(Text, nullable=False)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CandidateURL(Base):
    """Discovered potential scholarship page URLs."""
    __tablename__ = "candidate_urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    normalized_url = Column(String(500), unique=True, nullable=False, index=True)
    discovery_source_url = Column(String(500), nullable=False)
    discovery_method = Column(String(50), nullable=False, default="SEED_PORTAL")
    source_category = Column(String(50), nullable=False, default="UNKNOWN", index=True)
    anchor_text = Column(String(500), nullable=True)
    page_title = Column(String(500), nullable=True)
    relevance_score = Column(Float, default=0.0, nullable=False)
    status = Column(
        String(50),
        default="DISCOVERED",
        nullable=False,
        index=True,
    )  # DISCOVERED, QUEUED, CRAWLED, FAILED, REJECTED
    is_official_source = Column(Boolean, default=False, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    crawl_attempts = relationship("CrawlAttempt", back_populates="candidate", cascade="all, delete-orphan")
    scholarships = relationship("Scholarship", back_populates="candidate")
    evidence_records = relationship("FieldEvidence", back_populates="candidate")


class CrawlRun(Base):
    """Audit log of crawl execution sessions."""
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED
    candidates_discovered = Column(Integer, default=0, nullable=False)
    pages_crawled = Column(Integer, default=0, nullable=False)
    pages_failed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    crawl_attempts = relationship("CrawlAttempt", back_populates="crawl_run")


class CrawlAttempt(Base):
    """Individual HTTP fetch result for a candidate URL."""
    __tablename__ = "crawl_attempts"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_urls.id"), nullable=True, index=True)
    crawl_run_id = Column(Integer, ForeignKey("crawl_runs.id"), nullable=True, index=True)
    fetch_url = Column(String(500), nullable=False)
    final_url = Column(String(500), nullable=True)
    http_status = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    content_length = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA-256
    response_time_ms = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False)  # SUCCESS, HTTP_ERROR, TIMEOUT, BLOCKED_SSRF, etc.
    error_reason = Column(Text, nullable=True)
    extracted_links_count = Column(Integer, default=0, nullable=False)
    raw_html = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateURL", back_populates="crawl_attempts")
    crawl_run = relationship("CrawlRun", back_populates="crawl_attempts")


class Scholarship(Base):
    """Structured scholarship opportunity extracted with evidence."""
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True)
    stable_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True)
    provider = Column(String(255), nullable=True, index=True)
    official_source_url = Column(String(500), nullable=False, index=True)
    application_url = Column(String(500), nullable=True)
    source_category = Column(String(50), nullable=False, default="UNKNOWN", index=True)
    is_official_source = Column(Boolean, default=False, nullable=False)

    amount_benefit = Column(String(255), nullable=True)
    amount_details = Column(Text, nullable=True)
    eligibility_summary = Column(Text, nullable=True)
    academic_requirements = Column(Text, nullable=True)
    course_level = Column(String(255), nullable=True)
    income_criteria = Column(String(255), nullable=True)
    age_criteria = Column(String(255), nullable=True)
    gender_criteria = Column(String(100), nullable=True)
    category_requirements = Column(String(255), nullable=True)
    domicile_state = Column(String(100), nullable=True)
    institution_requirements = Column(String(255), nullable=True)

    opening_date = Column(String(50), nullable=True)
    closing_date = Column(String(50), nullable=True)
    documents_required = Column(Text, nullable=True)
    selection_process = Column(Text, nullable=True)
    renewal_requirements = Column(Text, nullable=True)

    lifecycle_status = Column(
        String(50),
        default="PENDING_VERIFICATION",
        nullable=False,
        index=True,
    )  # ACTIVE, EXPIRED, UPCOMING, PENDING_VERIFICATION
    page_type = Column(
        String(50),
        default="SCHOLARSHIP_DETAIL",
        nullable=False,
    )  # SCHOLARSHIP_DETAIL, SCHOLARSHIP_LISTING, GENERIC_PAGE, APPLICATION_PORTAL, INSUFFICIENT_EVIDENCE
    extraction_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_fetched_timestamp = Column(DateTime, nullable=True)
    content_hash = Column(String(64), nullable=True)
    extraction_method = Column(String(50), default="DETERMINISTIC_DOM", nullable=False)
    validation_warnings = Column(Text, nullable=True)  # JSON-encoded array of warnings

    verification_status = Column(
        String(50),
        default="UNVERIFIED",
        nullable=False,
        index=True,
    )  # UNVERIFIED, VERIFIED, REVIEW_REQUIRED, NO_LONGER_VERIFIABLE
    confidence_score = Column(Float, nullable=True)

    candidate_id = Column(Integer, ForeignKey("candidate_urls.id"), nullable=True, index=True)
    crawl_attempt_id = Column(Integer, ForeignKey("crawl_attempts.id"), nullable=True, index=True)

    candidate = relationship("CandidateURL", back_populates="scholarships")
    evidence_records = relationship(
        "FieldEvidence",
        back_populates="scholarship",
        cascade="all, delete-orphan",
    )
    verification_records = relationship(
        "VerificationRecord",
        back_populates="scholarship",
        cascade="all, delete-orphan",
        order_by="desc(VerificationRecord.verified_at)",
    )


class FieldEvidence(Base):
    """Field-level verifiable textual evidence extracted from source pages."""
    __tablename__ = "field_evidence"

    id = Column(Integer, primary_key=True, index=True)
    scholarship_id = Column(Integer, ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_urls.id"), nullable=True, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    extracted_value = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=False)
    evidence_text = Column(Text, nullable=False)
    page_title = Column(String(500), nullable=True)
    retrieval_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    content_hash = Column(String(64), nullable=True)
    extraction_method = Column(String(50), default="DETERMINISTIC_DOM", nullable=False)
    html_selector = Column(String(255), nullable=True)
    validation_status = Column(String(50), default="VALID", nullable=False)  # VALID, SUSPICIOUS, UNVERIFIED
    quality_rating = Column(
        String(50),
        default="SUPPORTED",
        nullable=False,
    )  # SUPPORTED, WEAK_EVIDENCE, NOT_FOUND, CONFLICTING, STALE

    scholarship = relationship("Scholarship", back_populates="evidence_records")
    candidate = relationship("CandidateURL", back_populates="evidence_records")


class VerificationRecord(Base):
    """Audit record and detailed outcome of deterministic verification runs."""
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    scholarship_id = Column(Integer, ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 100.0
    verification_status = Column(String(50), nullable=False, index=True)  # VERIFIED, REVIEW_REQUIRED, NO_LONGER_VERIFIABLE
    lifecycle_status = Column(String(50), nullable=False, index=True)  # ACTIVE, EXPIRING_SOON, EXPIRED, PENDING_VERIFICATION, NO_LONGER_VERIFIABLE
    scoring_model_version = Column(String(50), default="v1.0-deterministic", nullable=False)

    scoring_breakdown = Column(Text, nullable=False)  # JSON {criterion: {points: float, max_points: float, explanation: str}}
    gate_results = Column(Text, nullable=False)  # JSON {gate_name: {status: PASS/FAIL/NOT_APPLICABLE, explanation: str, evidence_refs: list, evaluated_at: str}}
    deductions_reasons = Column(Text, nullable=False)  # JSON list of str
    evidence_references = Column(Text, nullable=True)  # JSON list of dicts {field: str, status: str, snippet: str}
    is_latest = Column(Boolean, default=True, nullable=False, index=True)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    scholarship = relationship("Scholarship", back_populates="verification_records")



class ExtractionRun(Base):
    """Audit log of structured scholarship extraction sessions."""
    __tablename__ = "extraction_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED
    candidates_scanned = Column(Integer, default=0, nullable=False)
    scholarships_extracted = Column(Integer, default=0, nullable=False)
    insufficient_evidence_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
