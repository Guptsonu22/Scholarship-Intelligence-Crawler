import logging
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.db.models import SeedSource, CandidateURL, CrawlRun
from app.services.crawling.http_client import EthicalHttpClient
from app.services.crawling.security import validate_url_safety
from app.services.discovery.url_normalizer import normalize_url, score_scholarship_relevance
from app.services.verification.source_classifier import SourceClassifier

logger = logging.getLogger(__name__)


class DiscoveredLink:
    def __init__(
        self,
        url: str,
        normalized_url: str,
        anchor_text: Optional[str],
        relevance_score: float,
        is_relevant: bool,
        category: str,
        is_official: bool,
    ):
        self.url = url
        self.normalized_url = normalized_url
        self.anchor_text = anchor_text
        self.relevance_score = relevance_score
        self.is_relevant = is_relevant
        self.category = category
        self.is_official = is_official


class DiscoveryService:
    """Discovers and queues authentic scholarship candidates from seed portals and HTML pages."""

    def __init__(self, http_client: Optional[EthicalHttpClient] = None):
        self.http_client = http_client or EthicalHttpClient()

    def extract_candidate_links_from_html(
        self,
        html: str,
        base_url: str,
    ) -> List[DiscoveredLink]:
        """Parses HTML DOM, identifies internal/external links, normalizes them, and calculates scholarship relevance."""
        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

        discovered: List[DiscoveredLink] = []
        seen_normalized = set()

        for a_tag in soup.find_all("a", href=True):
            raw_href = a_tag["href"].strip()
            anchor_text = a_tag.get_text(separator=" ", strip=True)

            normalized = normalize_url(raw_href, base_url=base_url)
            if not normalized or normalized in seen_normalized:
                continue

            # Don't discover the base page itself as a separate candidate
            if normalized == normalize_url(base_url):
                continue

            # Score relevance
            score, is_relevant = score_scholarship_relevance(
                url=normalized,
                anchor_text=anchor_text,
                page_title=page_title,
            )

            # Classify domain
            classification = SourceClassifier.classify(normalized)

            seen_normalized.add(normalized)
            discovered.append(
                DiscoveredLink(
                    url=raw_href,
                    normalized_url=normalized,
                    anchor_text=anchor_text[:500] if anchor_text else None,
                    relevance_score=score,
                    is_relevant=is_relevant,
                    category=classification.category,
                    is_official=classification.is_official,
                )
            )

        return discovered

    def run_discovery_on_seed(
        self,
        db: Session,
        seed: SeedSource,
        respect_robots: bool = True,
    ) -> Tuple[int, int]:
        """Fetches a seed portal and records discovered candidate links into the database.

        Returns:
            (total_discovered, new_added_to_db)
        """
        logger.info(f"Running discovery on seed: {seed.name} ({seed.base_url})")

        # First add seed itself as a candidate if not already present
        seed_normalized = normalize_url(seed.base_url)
        if seed_normalized:
            existing_seed = db.query(CandidateURL).filter_by(normalized_url=seed_normalized).first()
            if not existing_seed:
                classification = SourceClassifier.classify(seed_normalized)
                seed_cand = CandidateURL(
                    url=seed.base_url,
                    normalized_url=seed_normalized,
                    discovery_source_url=seed.base_url,
                    discovery_method="SEED_PORTAL",
                    source_category=seed.category or classification.category,
                    relevance_score=1.0,
                    status="QUEUED",
                    is_official_source=classification.is_official,
                )
                db.add(seed_cand)
                db.commit()

        # Fetch page HTML
        fetch_result = self.http_client.fetch(seed.base_url, respect_robots=respect_robots)
        if fetch_result.status != "SUCCESS" or not fetch_result.html:
            logger.warning(f"Could not crawl seed {seed.base_url}: {fetch_result.status} ({fetch_result.error_reason})")
            return 0, 0

        # Extract links
        links = self.extract_candidate_links_from_html(fetch_result.html, base_url=fetch_result.final_url)

        total_discovered = len(links)
        new_added = 0

        for link in links:
            # Only save links that exhibit scholarship relevance or are official portals
            if not link.is_relevant and not link.is_official:
                continue

            existing = db.query(CandidateURL).filter_by(normalized_url=link.normalized_url).first()
            if existing:
                continue

            discovery_method = "AGGREGATOR_LINK" if seed.category == "AGGREGATOR" else "INTERNAL_LINK"

            candidate = CandidateURL(
                url=link.url,
                normalized_url=link.normalized_url,
                discovery_source_url=seed.base_url,
                discovery_method=discovery_method,
                source_category=link.category,
                anchor_text=link.anchor_text,
                relevance_score=link.relevance_score,
                status="DISCOVERED",
                is_official_source=link.is_official,
            )
            db.add(candidate)
            new_added += 1

        db.commit()
        return total_discovered, new_added

    def run_discovery_session(
        self,
        db: Session,
        source_ids: Optional[List[int]] = None,
        max_seeds: int = 5,
        respect_robots: bool = True,
    ) -> CrawlRun:
        """Executes a discovery session across selected or top enabled seeds."""
        crawl_run = CrawlRun(status="RUNNING")
        db.add(crawl_run)
        db.commit()
        db.refresh(crawl_run)

        query = db.query(SeedSource).filter(SeedSource.is_enabled == True)
        if source_ids:
            query = query.filter(SeedSource.id.in_(source_ids))

        seeds = query.limit(max_seeds).all()

        total_discovered_count = 0
        pages_crawled = 0
        pages_failed = 0

        try:
            for seed in seeds:
                disc_count, added_count = self.run_discovery_on_seed(db, seed, respect_robots=respect_robots)
                if disc_count > 0:
                    pages_crawled += 1
                else:
                    pages_failed += 1
                total_discovered_count += disc_count

            crawl_run.status = "COMPLETED"
            crawl_run.candidates_discovered = total_discovered_count
            crawl_run.pages_crawled = pages_crawled
            crawl_run.pages_failed = pages_failed
        except Exception as exc:
            crawl_run.status = "FAILED"
            crawl_run.error_message = str(exc)
            logger.error(f"Discovery run failed: {exc}", exc_info=True)
        finally:
            crawl_run.completed_at = crawl_run.completed_at or CrawlRun.completed_at.default.arg(None)
            db.commit()

        return crawl_run
