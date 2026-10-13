"""Verification Engine.

Orchestrates deterministic evidence evaluation, mandatory verification gates,
explainable scoring, lifecycle assessment, and persistent audit trail recording.
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from urllib.parse import urlparse

from app.db.models import Scholarship, FieldEvidence, VerificationRecord, CrawlAttempt
from app.services.verification.source_classifier import SourceClassifier
from app.services.verification.evidence_evaluator import EvidenceEvaluator, UMBRELLA_TITLES
from app.services.verification.scoring_model import DeterministicScoringModel
from app.services.verification.gates import VerificationGates, GateEvaluationResult


class VerificationEngine:
    """Core verification service for evaluating authenticity and confidence."""

    @classmethod
    def verify_scholarship(
        cls,
        scholarship_id: int,
        db: Session,
        reference_date: Optional[str] = None,  # Format: YYYY-MM-DD
        evaluation_timestamp: Optional[datetime] = None,
    ) -> VerificationRecord:
        """Runs complete deterministic verification on a scholarship record."""
        now = evaluation_timestamp or datetime.now(timezone.utc)
        today_str = reference_date or now.strftime("%Y-%m-%d")

        scholarship = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
        if not scholarship:
            raise ValueError(f"Scholarship ID {scholarship_id} not found.")

        # 1. Classify Source
        source_class = SourceClassifier.classify(scholarship.official_source_url)
        is_aggregator = source_class.category == "AGGREGATOR"
        is_official_source = source_class.is_official

        # 2. Evaluate Field Evidence Records
        field_ratings: Dict[str, str] = {}
        evidence_refs: List[Dict[str, Any]] = []

        for ev in scholarship.evidence_records:
            rating, explanation = EvidenceEvaluator.evaluate_field(
                field_name=ev.field_name,
                extracted_value=ev.extracted_value,
                evidence_snippet=ev.evidence_text,
                html_selector=ev.html_selector,
                retrieval_timestamp=ev.retrieval_timestamp,
                reference_time=now,
            )
            ev.quality_rating = rating
            field_ratings[ev.field_name] = rating
            evidence_refs.append({
                "evidence_id": ev.id,
                "field_name": ev.field_name,
                "extracted_value": ev.extracted_value,
                "quality_rating": rating,
                "explanation": explanation,
                "source_url": ev.source_url,
                "snippet": (ev.evidence_text[:160] + "...") if len(ev.evidence_text or "") > 160 else ev.evidence_text,
            })

        # 3. Check for Umbrella / Multi-scheme Titles
        name_lower = (scholarship.name or "").strip().lower()
        is_umbrella = (
            any(u in name_lower for u in UMBRELLA_TITLES)
            or scholarship.page_type == "SCHOLARSHIP_LISTING"
        )

        # 4. Check Contradictions
        has_contradictions = False
        contradiction_reasons: List[str] = []

        if scholarship.opening_date and scholarship.closing_date:
            try:
                if scholarship.opening_date > scholarship.closing_date:
                    has_contradictions = True
                    contradiction_reasons.append(
                        f"Opening date ({scholarship.opening_date}) is after closing date ({scholarship.closing_date})."
                    )
            except Exception:
                pass

        if is_umbrella and len(scholarship.evidence_records) > 0:
            # Umbrella page presenting multiple schemes
            has_contradictions = True
            contradiction_reasons.append(
                f"Page title '{scholarship.name}' represents multiple distinct schemes conflated into a single record."
            )

        # 5. Check Application URL
        has_app_url = bool(scholarship.application_url and scholarship.application_url.strip())
        is_app_url_official = False
        app_url_not_applicable = False

        if has_app_url:
            app_class = SourceClassifier.classify(scholarship.application_url)
            # Official if same domain, gov domain, or official provider
            source_domain = urlparse(scholarship.official_source_url).netloc.lower()
            app_domain = urlparse(scholarship.application_url).netloc.lower()
            if app_class.is_official or app_domain == source_domain or app_domain.endswith("gov.in") or app_domain.endswith("nic.in"):
                is_app_url_official = True
            else:
                is_app_url_official = False
        else:
            # If no application URL, check if acceptable (e.g. not published yet or offline)
            app_url_not_applicable = True

        # 6. Check Deadline and Lifecycle
        has_closing_date = bool(scholarship.closing_date and scholarship.closing_date.strip())
        is_deadline_expired = False
        is_deadline_contextual = field_ratings.get("closing_date") == "SUPPORTED"

        if has_closing_date:
            try:
                if scholarship.closing_date < today_str:
                    is_deadline_expired = True
                    lifecycle_status = "EXPIRED"
                else:
                    # Check if expiring soon (within 14 days)
                    from datetime import date
                    d_close = datetime.strptime(scholarship.closing_date[:10], "%Y-%m-%d").date()
                    d_today = datetime.strptime(today_str, "%Y-%m-%d").date()
                    days_remaining = (d_close - d_today).days
                    if days_remaining <= 14:
                        lifecycle_status = "EXPIRING_SOON"
                    else:
                        lifecycle_status = "ACTIVE"
            except Exception:
                lifecycle_status = "PENDING_VERIFICATION"
        else:
            lifecycle_status = "ACTIVE"  # Open/rolling

        # 7. Check Crawl Freshness
        crawl_attempt = (
            db.query(CrawlAttempt)
            .filter(CrawlAttempt.id == scholarship.crawl_attempt_id)
            .first()
        ) if scholarship.crawl_attempt_id else None

        crawl_status = crawl_attempt.http_status if crawl_attempt else 200
        days_since_fetch = None
        fetch_time = scholarship.last_fetched_timestamp or (crawl_attempt.created_at if crawl_attempt else None)
        if fetch_time:
            if fetch_time.tzinfo is None:
                fetch_time = fetch_time.replace(tzinfo=timezone.utc)
            days_since_fetch = max(0, (now - fetch_time).days)

        # 8. Run All Mandatory Gates
        gate_results: Dict[str, Dict[str, Any]] = {}
        gates_list: List[GateEvaluationResult] = []

        g_official = VerificationGates.official_source_gate(
            source_url=scholarship.official_source_url,
            category=source_class.category,
            is_official=is_official_source,
            is_aggregator=is_aggregator,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_official)

        g_identity = VerificationGates.scholarship_identity_gate(
            name=scholarship.name,
            is_umbrella_or_listing=is_umbrella,
            page_type=scholarship.page_type,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_identity)

        g_evidence = VerificationGates.field_evidence_gate(
            field_ratings=field_ratings,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_evidence)

        g_contra = VerificationGates.contradiction_gate(
            has_contradictions=has_contradictions,
            contradiction_reasons=contradiction_reasons,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_contra)

        g_freshness = VerificationGates.freshness_gate(
            crawl_http_status=crawl_status,
            days_since_fetch=days_since_fetch,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_freshness)

        g_app = VerificationGates.application_link_gate(
            application_url=scholarship.application_url,
            is_official_portal=is_app_url_official,
            is_not_applicable=app_url_not_applicable,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_app)

        g_lifecycle = VerificationGates.lifecycle_gate(
            closing_date_str=scholarship.closing_date,
            reference_date=today_str,
            evidence_refs=evidence_refs,
            now=now,
        )
        gates_list.append(g_lifecycle)

        all_gates_pass = True
        failed_gate_explanations: List[str] = []
        for g in gates_list:
            gate_results[g.gate_name] = g.to_dict()
            if g.status == "FAIL":
                all_gates_pass = False
                failed_gate_explanations.append(f"{g.gate_name}: {g.explanation}")

        # 9. Compute Deterministic Score
        score_outcome = DeterministicScoringModel.evaluate(
            source_category=source_class.category,
            is_official_source=is_official_source,
            is_aggregator=is_aggregator,
            name=scholarship.name,
            provider=scholarship.provider,
            is_umbrella_or_listing=is_umbrella,
            field_evidence_summary=field_ratings,
            has_application_url=has_app_url,
            is_app_url_official=is_app_url_official,
            app_url_not_applicable=app_url_not_applicable,
            has_closing_date=has_closing_date,
            is_deadline_contextual=is_deadline_contextual,
            is_deadline_expired=is_deadline_expired,
            days_since_fetch=days_since_fetch,
            crawl_http_status=crawl_status,
            has_contradictions=has_contradictions,
            contradiction_details=contradiction_reasons,
        )

        computed_score = score_outcome.total_score

        # 10. Enforce STRICT Golden Rule for VERIFIED
        # Score >= 95.0 AND all gates pass (status is PASS or NOT_APPLICABLE)
        all_deductions = list(score_outcome.deductions_summary)
        if failed_gate_explanations:
            for f_exp in failed_gate_explanations:
                all_deductions.append(f"Failed gate: {f_exp}")

        if computed_score >= 95.0 and all_gates_pass and not is_aggregator:
            verification_status = "VERIFIED"
        else:
            verification_status = "REVIEW_REQUIRED"

        # Update Scholarship
        scholarship.verification_status = verification_status
        scholarship.confidence_score = computed_score
        scholarship.lifecycle_status = lifecycle_status

        # Set older verification records as not latest
        db.query(VerificationRecord).filter(
            VerificationRecord.scholarship_id == scholarship.id
        ).update({"is_latest": False})

        # Create persistent verification record
        crit_dict = {
            k: {
                "criterion_name": v.criterion_name,
                "points_awarded": v.points_awarded,
                "max_points": v.max_points,
                "explanation": v.explanation,
                "deductions": v.deductions,
            }
            for k, v in score_outcome.criteria.items()
        }

        record = VerificationRecord(
            scholarship_id=scholarship.id,
            confidence_score=computed_score,
            verification_status=verification_status,
            lifecycle_status=lifecycle_status,
            scoring_model_version=DeterministicScoringModel.MODEL_VERSION,
            scoring_breakdown=json.dumps(crit_dict),
            gate_results=json.dumps(gate_results),
            deductions_reasons=json.dumps(all_deductions),
            evidence_references=json.dumps(evidence_refs),
            is_latest=True,
            verified_at=now,
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        db.refresh(scholarship)

        return record

    @classmethod
    def verify_all(
        cls,
        db: Session,
        reference_date: Optional[str] = None,
    ) -> List[VerificationRecord]:
        """Runs verification on all extracted scholarship records in the database."""
        scholarships = db.query(Scholarship).all()
        results: List[VerificationRecord] = []
        for s in scholarships:
            rec = cls.verify_scholarship(s.id, db, reference_date=reference_date)
            results.append(rec)
        return results

    @classmethod
    def get_summary(cls, db: Session) -> Dict[str, Any]:
        """Returns actual database statistics and average confidence."""
        total = db.query(Scholarship).count()
        verified_count = db.query(Scholarship).filter(Scholarship.verification_status == "VERIFIED").count()
        review_required_count = db.query(Scholarship).filter(Scholarship.verification_status == "REVIEW_REQUIRED").count()
        unverified_count = db.query(Scholarship).filter(Scholarship.verification_status == "UNVERIFIED").count()
        expired_count = db.query(Scholarship).filter(Scholarship.lifecycle_status == "EXPIRED").count()
        active_count = db.query(Scholarship).filter(Scholarship.lifecycle_status.in_(["ACTIVE", "EXPIRING_SOON"])).count()

        # Compute average confidence from latest verification records
        latest_records = db.query(VerificationRecord).filter(VerificationRecord.is_latest == True).all()
        if latest_records:
            avg_score = round(sum(r.confidence_score for r in latest_records) / len(latest_records), 2)
            last_run = max(r.verified_at for r in latest_records).isoformat()
        else:
            avg_score = 0.0
            last_run = None

        return {
            "total_scholarships": total,
            "verified_count": verified_count,
            "review_required_count": review_required_count,
            "unverified_count": unverified_count,
            "expired_count": expired_count,
            "active_count": active_count,
            "average_confidence": avg_score,
            "last_verification_run": last_run,
        }
