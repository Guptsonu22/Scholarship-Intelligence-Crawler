"""Scholarship Lifecycle and Stale Data Manager.

Evaluates lifecycle progression (ACTIVE, EXPIRING_SOON, EXPIRED, NO_LONGER_VERIFIABLE),
detects stale data thresholds, and records transition audit entries.
"""
from datetime import datetime, timezone, date
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models import Scholarship, ScholarshipChangeHistory

EXPIRING_SOON_DAYS_THRESHOLD = 14
STALE_DAYS_THRESHOLD = 90


class LifecycleManager:
    """Manages scholarship lifecycle transitions and staleness checks."""

    @classmethod
    def evaluate_lifecycle(
        cls,
        scholarship: Scholarship,
        reference_date: Optional[str] = None,  # YYYY-MM-DD
        now: Optional[datetime] = None,
        crawl_http_status: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Tuple[str, Optional[str]]:
        """Calculates lifecycle state and records transition in change history if changed."""
        eval_now = now or datetime.now(timezone.utc)
        today_str = reference_date or eval_now.strftime("%Y-%m-%d")

        old_status = scholarship.lifecycle_status
        new_status = old_status
        reason = None

        # 1. Handle permanent removal / non-accessible primary source
        if crawl_http_status == 404:
            new_status = "NO_LONGER_VERIFIABLE"
            reason = "Official source page returned HTTP 404 Not Found."
        elif scholarship.closing_date:
            try:
                # Normal YYYY-MM-DD comparison
                if scholarship.closing_date < today_str:
                    new_status = "EXPIRED"
                    reason = f"Application deadline '{scholarship.closing_date}' expired as of '{today_str}'."
                else:
                    d_close = datetime.strptime(scholarship.closing_date[:10], "%Y-%m-%d").date()
                    d_today = datetime.strptime(today_str, "%Y-%m-%d").date()
                    days_remaining = (d_close - d_today).days
                    if days_remaining <= EXPIRING_SOON_DAYS_THRESHOLD:
                        new_status = "EXPIRING_SOON"
                        reason = f"Application window closes in {days_remaining} days ({scholarship.closing_date})."
                    else:
                        new_status = "ACTIVE"
                        reason = f"Opportunity is active with closing date {scholarship.closing_date}."
            except Exception:
                new_status = old_status
        else:
            # Ongoing / rolling admissions
            new_status = "ACTIVE"
            reason = "Open-ended or rolling submission window."

        # If lifecycle status changed and db session provided, record in change history
        if new_status != old_status and db:
            change_record = ScholarshipChangeHistory(
                scholarship_id=scholarship.id,
                field_name="lifecycle_status",
                previous_value=old_status,
                new_value=new_status,
                detection_timestamp=eval_now,
                source_url=scholarship.official_source_url,
                change_classification="LIFECYCLE_TRANSITION",
                requires_reverification=True,
                is_reviewed=False,
            )
            db.add(change_record)
            scholarship.lifecycle_status = new_status
            db.commit()

        return new_status, reason

    @classmethod
    def is_stale(
        cls,
        scholarship: Scholarship,
        stale_threshold_days: int = STALE_DAYS_THRESHOLD,
        now: Optional[datetime] = None,
    ) -> bool:
        """Determines if a scholarship's evidence exceeds the freshness policy."""
        eval_now = now or datetime.now(timezone.utc)
        fetch_time = scholarship.last_fetched_timestamp or scholarship.extraction_timestamp
        if not fetch_time:
            return True
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=timezone.utc)
        return (eval_now - fetch_time).days > stale_threshold_days
