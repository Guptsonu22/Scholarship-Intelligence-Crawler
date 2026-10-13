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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateURL", back_populates="crawl_attempts")
    crawl_run = relationship("CrawlRun", back_populates="crawl_attempts")
