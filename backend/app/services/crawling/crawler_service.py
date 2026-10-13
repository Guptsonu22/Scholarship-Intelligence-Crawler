import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import CandidateURL, CrawlRun, CrawlAttempt
from app.services.crawling.http_client import EthicalHttpClient, CrawlResult
from app.services.discovery.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


class CrawlerService:
    """Manages crawl execution across queued scholarship candidates."""

    def __init__(self, http_client: Optional[EthicalHttpClient] = None):
        self.http_client = http_client or EthicalHttpClient()
        self.discovery_service = DiscoveryService(http_client=self.http_client)

    def crawl_candidate(
        self,
        db: Session,
        candidate: CandidateURL,
        crawl_run_id: Optional[int] = None,
        respect_robots: bool = True,
    ) -> CrawlAttempt:
        """Fetches a single candidate, records CrawlAttempt, updates candidate status, and extracts secondary candidate links."""
        logger.info(f"Crawling candidate #{candidate.id}: {candidate.normalized_url}")

        result: CrawlResult = self.http_client.fetch(
            candidate.normalized_url,
            respect_robots=respect_robots,
        )

        extracted_count = 0

        # If page fetched successfully, extract secondary links
        if result.status == "SUCCESS" and result.html:
            candidate.status = "CRAWLED"
            candidate.rejection_reason = None
            try:
                links = self.discovery_service.extract_candidate_links_from_html(
                    result.html,
                    base_url=result.final_url,
                )
                for link in links:
                    if link.is_relevant or link.is_official:
                        existing = db.query(CandidateURL).filter_by(normalized_url=link.normalized_url).first()
                        if not existing:
                            secondary = CandidateURL(
                                url=link.url,
                                normalized_url=link.normalized_url,
                                discovery_source_url=candidate.normalized_url,
                                discovery_method="INTERNAL_LINK",
                                source_category=link.category,
                                anchor_text=link.anchor_text,
                                relevance_score=link.relevance_score,
                                status="DISCOVERED",
                                is_official_source=link.is_official,
                            )
                            db.add(secondary)
                            extracted_count += 1
            except Exception as exc:
                logger.warning(f"Error extracting secondary links from {candidate.normalized_url}: {exc}")
        else:
            candidate.status = "FAILED"
            candidate.rejection_reason = f"{result.status}: {result.error_reason}"

        attempt = CrawlAttempt(
            candidate_id=candidate.id,
            crawl_run_id=crawl_run_id,
            fetch_url=candidate.normalized_url,
            final_url=result.final_url,
            http_status=result.http_status,
            content_type=result.content_type,
            content_length=result.content_length,
            content_hash=result.content_hash,
            response_time_ms=result.response_time_ms,
            status=result.status,
            error_reason=result.error_reason,
            extracted_links_count=extracted_count,
            raw_html=result.html if result.status == "SUCCESS" else None,
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    def run_crawl_session(
        self,
        db: Session,
        candidate_ids: Optional[List[int]] = None,
        max_pages: int = 5,
        delay_seconds: Optional[float] = None,
        respect_robots: bool = True,
    ) -> CrawlRun:
        """Executes a controlled crawl session on candidate URLs."""
        if delay_seconds:
            self.http_client.default_delay = delay_seconds

        crawl_run = CrawlRun(status="RUNNING")
        db.add(crawl_run)
        db.commit()
        db.refresh(crawl_run)

        query = db.query(CandidateURL)
        if candidate_ids:
            query = query.filter(CandidateURL.id.in_(candidate_ids))
        else:
            # Pick candidates with status DISCOVERED or QUEUED, sorted by relevance
            query = query.filter(CandidateURL.status.in_(["DISCOVERED", "QUEUED"])).order_by(
                CandidateURL.relevance_score.desc()
            )

        candidates = query.limit(max_pages).all()

        pages_crawled = 0
        pages_failed = 0
        total_discovered = 0

        try:
            for cand in candidates:
                attempt = self.crawl_candidate(
                    db=db,
                    candidate=cand,
                    crawl_run_id=crawl_run.id,
                    respect_robots=respect_robots,
                )
                if attempt.status == "SUCCESS":
                    pages_crawled += 1
                else:
                    pages_failed += 1
                total_discovered += attempt.extracted_links_count

            crawl_run.status = "COMPLETED"
            crawl_run.pages_crawled = pages_crawled
            crawl_run.pages_failed = pages_failed
            crawl_run.candidates_discovered = total_discovered
        except Exception as exc:
            crawl_run.status = "FAILED"
            crawl_run.error_message = str(exc)
            logger.error(f"Crawl run failed: {exc}", exc_info=True)
        finally:
            crawl_run.completed_at = datetime.now(timezone.utc)
            db.commit()

        return crawl_run
