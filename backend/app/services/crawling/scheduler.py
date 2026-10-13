"""Crawl Scheduler and Lifecycle Update Runner.

Provides controlled recurring background crawling, overlap prevention,
candidate prioritization (official and stale first), and graceful shutdown.
"""
import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import (
    CandidateURL,
    Scholarship,
    CrawlRun,
    CrawlAttempt,
)
from app.services.crawling.crawler_service import CrawlerService
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.lifecycle.change_detector import ChangeDetector
from app.services.lifecycle.lifecycle_manager import LifecycleManager
from app.services.verification.verification_engine import VerificationEngine
from app.services.extraction.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


class CrawlScheduler:
    """Singleton scheduler managing recurring update cycles and preventing overlaps."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CrawlScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, interval_seconds: int = 3600, default_max_candidates: int = 5):
        if self._initialized:
            return
        self.interval_seconds = interval_seconds
        self.default_max_candidates = default_max_candidates
        self.is_active = False
        self.is_running_job = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.last_run_time: Optional[datetime] = None
        self.last_run_status: Optional[str] = None
        self.last_run_summary: Optional[Dict[str, Any]] = None
        self.next_run_time: Optional[datetime] = None

        self._initialized = True

    def start(self) -> Dict[str, Any]:
        """Starts the recurring scheduler background daemon."""
        with self._lock:
            if self.is_active:
                return {
                    "status": "ALREADY_ACTIVE",
                    "message": "Scheduler is already active.",
                    "interval_seconds": self.interval_seconds,
                    "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
                }

            self.is_active = True
            self._stop_event.clear()
            self.next_run_time = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)

            self._thread = threading.Thread(
                target=self._worker_loop,
                name="CrawlSchedulerWorker",
                daemon=True,
            )
            self._thread.start()
            logger.info(f"CrawlScheduler started with interval {self.interval_seconds}s.")
            return {
                "status": "STARTED",
                "message": f"Scheduler started. Recurring crawl interval: {self.interval_seconds}s.",
                "next_run_time": self.next_run_time.isoformat(),
            }

    def stop(self) -> Dict[str, Any]:
        """Gracefully stops the scheduler."""
        with self._lock:
            if not self.is_active:
                return {"status": "ALREADY_STOPPED", "message": "Scheduler is not currently running."}

            self.is_active = False
            self._stop_event.set()
            self.next_run_time = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("CrawlScheduler stopped.")
        return {"status": "STOPPED", "message": "Scheduler has been gracefully stopped."}

    def get_status(self) -> Dict[str, Any]:
        """Returns the current scheduler execution status and last run metrics."""
        return {
            "is_active": self.is_active,
            "is_running_job": self.is_running_job,
            "interval_seconds": self.interval_seconds,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_run_status": self.last_run_status,
            "last_run_summary": self.last_run_summary,
            "next_run_time": self.next_run_time.isoformat() if (self.is_active and self.next_run_time) else None,
        }

    def _worker_loop(self):
        """Background worker loop sleeping for interval and triggering update runs."""
        while not self._stop_event.is_set():
            # Wait for interval or stop event
            if self._stop_event.wait(timeout=self.interval_seconds):
                break

            if not self.is_active:
                break

            # Execute scheduled run
            logger.info("Scheduled crawl cycle triggered by worker loop.")
            db = SessionLocal()
            try:
                self.run_pipeline(
                    db=db,
                    max_candidates=self.default_max_candidates,
                    manual=False,
                )
            except Exception as e:
                logger.error(f"Error during scheduled crawl run: {e}", exc_info=True)
            finally:
                db.close()

            if self.is_active:
                self.next_run_time = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)

    def run_pipeline(
        self,
        db: Session,
        max_candidates: int = 5,
        candidate_ids: Optional[List[int]] = None,
        manual: bool = True,
    ) -> Dict[str, Any]:
        """Core unified crawl and change detection execution pipeline.
        
        Strictly prevents overlapping crawl jobs.
        """
        # Overlap prevention check
        with self._lock:
            if self.is_running_job:
                return {
                    "status": "OVERLAPPING_REJECTED",
                    "message": "A crawl and change-detection session is already running. Please wait for completion.",
                }
            self.is_running_job = True

        start_time = datetime.now(timezone.utc)
        crawl_service = CrawlerService()
        crawler_run_record = CrawlRun(
            status="RUNNING",
            started_at=start_time,
        )
        db.add(crawler_run_record)
        db.commit()
        db.refresh(crawler_run_record)

        candidates_processed = 0
        pages_crawled = 0
        pages_unchanged = 0
        changes_detected = 0
        new_scholarships = 0
        reverifications_run = 0
        failed_fetches = 0
        error_details = []

        try:
            # 1. Candidate Prioritization
            target_candidates = self._prioritize_candidates(
                db=db,
                candidate_ids=candidate_ids,
                max_candidates=max_candidates,
            )

            for cand in target_candidates:
                candidates_processed += 1
                try:
                    # 2. Fetch candidate using existing ethical crawler
                    attempt: CrawlAttempt = crawl_service.crawl_candidate(
                        db=db,
                        candidate=cand,
                        crawl_run_id=crawler_run_record.id,
                        respect_robots=True,
                    )

                    if attempt.status != "SUCCESS" or not attempt.raw_html:
                        failed_fetches += 1
                        error_details.append(f"{cand.normalized_url}: {attempt.status} ({attempt.error_reason})")
                        continue

                    pages_crawled += 1

                    # 3. Check if candidate corresponds to an existing Scholarship
                    existing_scholarship = (
                        db.query(Scholarship)
                        .filter(
                            (Scholarship.official_source_url == cand.normalized_url)
                            | (Scholarship.candidate_id == cand.id)
                        )
                        .first()
                    )

                    if existing_scholarship:
                        # 4. Check Content Hash
                        if (
                            existing_scholarship.content_hash
                            and existing_scholarship.content_hash == attempt.content_hash
                        ):
                            # UNCHANGED CONTENT: Avoid duplicate extraction noise!
                            pages_unchanged += 1
                            existing_scholarship.last_fetched_timestamp = start_time

                            # Re-check lifecycle (e.g. deadline expired with real passage of time)
                            new_lc, lc_reason = LifecycleManager.evaluate_lifecycle(
                                scholarship=existing_scholarship,
                                now=start_time,
                                crawl_http_status=attempt.http_status,
                                db=db,
                            )
                            db.commit()
                            continue

                        # Content hash changed: Re-assess and detect changes!
                        p_type, _ = PageAssessor.assess_page(attempt.raw_html, cand.normalized_url)
                        if p_type == "SCHOLARSHIP_DETAIL":
                            extracted = FieldExtractor.extract(attempt.raw_html, cand.normalized_url)
                            
                            # Run field-level change detection
                            recorded_changes = ChangeDetector.detect_and_apply_changes(
                                db=db,
                                scholarship=existing_scholarship,
                                extracted_data=extracted,
                                new_content_hash=attempt.content_hash,
                                crawl_run_id=crawler_run_record.id,
                                evaluation_timestamp=start_time,
                            )

                            if recorded_changes:
                                changes_detected += len(recorded_changes)
                                # Check if re-verification is required
                                needs_reverify = any(ch.requires_reverification for ch in recorded_changes)
                                if needs_reverify:
                                    VerificationEngine.verify_scholarship(
                                        scholarship_id=existing_scholarship.id,
                                        db=db,
                                        evaluation_timestamp=start_time,
                                    )
                                    reverifications_run += 1
                    else:
                        # 5. New Candidate: Extract new scholarship
                        extraction_svc = ExtractionService()
                        new_sch, p_type = extraction_svc.process_candidate(
                            db=db,
                            candidate=cand,
                            html=attempt.raw_html,
                            content_hash=attempt.content_hash,
                            crawl_attempt_id=attempt.id,
                        )
                        if new_sch:
                            new_scholarships += 1
                            # Run verification on newly discovered scholarship
                            VerificationEngine.verify_scholarship(
                                scholarship_id=new_sch.id,
                                db=db,
                                evaluation_timestamp=start_time,
                            )
                            reverifications_run += 1

                except Exception as cand_exc:
                    failed_fetches += 1
                    err_msg = f"Error processing candidate #{cand.id}: {cand_exc}"
                    logger.error(err_msg, exc_info=True)
                    error_details.append(err_msg)

            crawler_run_record.status = "COMPLETED"
            crawler_run_record.completed_at = datetime.now(timezone.utc)
            crawler_run_record.pages_crawled = pages_crawled
            crawler_run_record.pages_failed = failed_fetches
            db.commit()

            summary = {
                "run_id": crawler_run_record.id,
                "status": "COMPLETED",
                "manual": manual,
                "candidates_processed": candidates_processed,
                "pages_crawled": pages_crawled,
                "pages_unchanged": pages_unchanged,
                "changes_detected": changes_detected,
                "new_scholarships": new_scholarships,
                "reverifications_run": reverifications_run,
                "failed_fetches": failed_fetches,
                "errors": error_details,
                "started_at": start_time.isoformat(),
                "completed_at": crawler_run_record.completed_at.isoformat(),
            }

            self.last_run_time = start_time
            self.last_run_status = "COMPLETED"
            self.last_run_summary = summary
            return summary

        except Exception as run_exc:
            crawler_run_record.status = "FAILED"
            crawler_run_record.error_message = str(run_exc)
            crawler_run_record.completed_at = datetime.now(timezone.utc)
            db.commit()
            self.last_run_status = "FAILED"
            logger.error(f"Crawl session #{crawler_run_record.id} failed: {run_exc}", exc_info=True)
            return {
                "run_id": crawler_run_record.id,
                "status": "FAILED",
                "error": str(run_exc),
            }
        finally:
            with self._lock:
                self.is_running_job = False

    def _prioritize_candidates(
        self,
        db: Session,
        candidate_ids: Optional[List[int]],
        max_candidates: int,
    ) -> List[CandidateURL]:
        """Selects candidates giving priority to existing scholarships due for refresh, then official seeds."""
        if candidate_ids:
            return db.query(CandidateURL).filter(CandidateURL.id.in_(candidate_ids)).all()

        selected: List[CandidateURL] = []
        selected_ids = set()

        # 1. Existing scholarships due for re-crawl / refresh (official primary sources first)
        existing_schs = (
            db.query(Scholarship)
            .filter(Scholarship.candidate_id.isnot(None))
            .order_by(Scholarship.last_fetched_timestamp.asc().nullsfirst())
            .all()
        )
        for s in existing_schs:
            if s.candidate and s.candidate.id not in selected_ids:
                selected.append(s.candidate)
                selected_ids.add(s.candidate.id)
                if len(selected) >= max_candidates:
                    return selected

        # 2. Uncrawled official candidates
        official_candidates = (
            db.query(CandidateURL)
            .filter(
                CandidateURL.status.in_(["DISCOVERED", "QUEUED"]),
                CandidateURL.is_official_source == True,
            )
            .order_by(CandidateURL.relevance_score.desc())
            .limit(max_candidates - len(selected))
            .all()
        )
        for cand in official_candidates:
            if cand.id not in selected_ids:
                selected.append(cand)
                selected_ids.add(cand.id)
                if len(selected) >= max_candidates:
                    return selected

        # 3. Remaining discovered candidates
        remaining_candidates = (
            db.query(CandidateURL)
            .filter(CandidateURL.status.in_(["DISCOVERED", "QUEUED"]))
            .order_by(CandidateURL.relevance_score.desc())
            .limit(max_candidates - len(selected))
            .all()
        )
        for cand in remaining_candidates:
            if cand.id not in selected_ids:
                selected.append(cand)
                selected_ids.add(cand.id)
                if len(selected) >= max_candidates:
                    break

        return selected


# Global scheduler instance
scheduler = CrawlScheduler()
