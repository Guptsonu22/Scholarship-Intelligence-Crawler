import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.db.models import (
    CandidateURL,
    CrawlAttempt,
    Scholarship,
    FieldEvidence,
    ExtractionRun,
)
from app.services.crawling.http_client import EthicalHttpClient
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor, ExtractedScholarshipData
from app.services.verification.source_classifier import SourceClassifier

logger = logging.getLogger(__name__)


class ExtractionService:
    """Coordinates page assessment, deterministic field extraction, evidence linking, and database persistence."""

    def __init__(self, http_client: Optional[EthicalHttpClient] = None):
        self.http_client = http_client or EthicalHttpClient()

    def process_candidate(
        self,
        db: Session,
        candidate: CandidateURL,
        html: Optional[str] = None,
        content_hash: Optional[str] = None,
        crawl_attempt_id: Optional[int] = None,
    ) -> Tuple[Optional[Scholarship], str]:
        """Assesses page, extracts structured scholarship attributes, attaches evidence, and persists record.

        Returns:
            (scholarship_or_none, page_type)
        """
        # If HTML not supplied directly, retrieve from latest CrawlAttempt or fetch safely
        if not html:
            last_attempt = (
                db.query(CrawlAttempt)
                .filter(CrawlAttempt.candidate_id == candidate.id, CrawlAttempt.status == "SUCCESS")
                .order_by(CrawlAttempt.id.desc())
                .first()
            )
            if last_attempt and last_attempt.raw_html:
                html = last_attempt.raw_html
                content_hash = last_attempt.content_hash
                crawl_attempt_id = last_attempt.id
            else:
                # Fetch page via HTTP client
                res = self.http_client.fetch(candidate.normalized_url, respect_robots=True)
                if res.status != "SUCCESS" or not res.html:
                    return None, "FETCH_FAILED"
                html = res.html
                content_hash = res.content_hash

        # 1. Page Assessment
        page_type, reason = PageAssessor.assess_page(html, candidate.normalized_url)
        if page_type != "SCHOLARSHIP_DETAIL":
            logger.info(f"Candidate #{candidate.id} assessed as {page_type}: {reason}")
            return None, page_type

        # 2. Field Extraction
        extracted: ExtractedScholarshipData = FieldExtractor.extract(html, candidate.normalized_url)

        # 3. Validation: Must have at least a name and one verifiable attribute
        if not extracted.name:
            return None, "INSUFFICIENT_EVIDENCE"

        has_attributes = any([
            extracted.amount_benefit,
            extracted.closing_date,
            extracted.eligibility_summary,
            extracted.provider,
            extracted.course_level,
        ])
        if not has_attributes:
            return None, "INSUFFICIENT_EVIDENCE"

        # 4. Source classification
        classification = SourceClassifier.classify(candidate.normalized_url)

        # 5. Deterministic Stable ID
        unique_seed_str = f"{classification.category}:{candidate.normalized_url}:{extracted.name.lower().strip()}"
        stable_id = hashlib.sha256(unique_seed_str.encode("utf-8")).hexdigest()[:32]

        # 6. Database Upsert / Deduplication
        scholarship = db.query(Scholarship).filter_by(stable_id=stable_id).first()
        if not scholarship:
            # Check by canonical URL
            scholarship = db.query(Scholarship).filter_by(official_source_url=candidate.normalized_url).first()

        now_utc = datetime.now(timezone.utc)

        if not scholarship:
            scholarship = Scholarship(
                stable_id=stable_id,
                name=extracted.name,
                provider=extracted.provider,
                official_source_url=candidate.normalized_url,
                application_url=extracted.application_url,
                source_category=classification.category,
                is_official_source=classification.is_official,
                amount_benefit=extracted.amount_benefit,
                amount_details=extracted.amount_details,
                eligibility_summary=extracted.eligibility_summary,
                academic_requirements=extracted.academic_requirements,
                course_level=extracted.course_level,
                income_criteria=extracted.income_criteria,
                age_criteria=extracted.age_criteria,
                gender_criteria=extracted.gender_criteria,
                category_requirements=extracted.category_requirements,
                domicile_state=extracted.domicile_state,
                institution_requirements=extracted.institution_requirements,
                opening_date=extracted.opening_date,
                closing_date=extracted.closing_date,
                documents_required=extracted.documents_required,
                selection_process=extracted.selection_process,
                renewal_requirements=extracted.renewal_requirements,
                lifecycle_status="PENDING_VERIFICATION",
                page_type=page_type,
                extraction_timestamp=now_utc,
                last_fetched_timestamp=now_utc,
                content_hash=content_hash,
                extraction_method="DETERMINISTIC_DOM",
                validation_warnings=json.dumps(extracted.validation_warnings) if extracted.validation_warnings else None,
                candidate_id=candidate.id,
                crawl_attempt_id=crawl_attempt_id,
            )
            db.add(scholarship)
            db.commit()
            db.refresh(scholarship)
        else:
            # Update existing record
            scholarship.name = extracted.name
            scholarship.provider = extracted.provider or scholarship.provider
            scholarship.amount_benefit = extracted.amount_benefit or scholarship.amount_benefit
            scholarship.closing_date = extracted.closing_date or scholarship.closing_date
            scholarship.eligibility_summary = extracted.eligibility_summary or scholarship.eligibility_summary
            scholarship.course_level = extracted.course_level or scholarship.course_level
            scholarship.income_criteria = extracted.income_criteria or scholarship.income_criteria
            scholarship.gender_criteria = extracted.gender_criteria or scholarship.gender_criteria
            scholarship.category_requirements = extracted.category_requirements or scholarship.category_requirements
            scholarship.application_url = extracted.application_url or scholarship.application_url
            scholarship.content_hash = content_hash or scholarship.content_hash
            scholarship.last_fetched_timestamp = now_utc
            db.commit()

        # 7. Attach Traceable Field Evidence Records
        # Clean previous evidence for this scholarship to avoid duplicate evidence rows
        db.query(FieldEvidence).filter(FieldEvidence.scholarship_id == scholarship.id).delete()

        for item in extracted.evidence_list:
            evidence = FieldEvidence(
                scholarship_id=scholarship.id,
                candidate_id=candidate.id,
                field_name=item.field_name,
                extracted_value=item.extracted_value,
                source_url=candidate.normalized_url,
                evidence_text=item.evidence_text,
                page_title=extracted.page_title,
                retrieval_timestamp=now_utc,
                content_hash=content_hash,
                extraction_method="DETERMINISTIC_DOM",
                html_selector=item.html_selector,
                validation_status="VALID",
            )
            db.add(evidence)

        db.commit()
        db.refresh(scholarship)
        return scholarship, page_type

    def run_extraction_session(
        self,
        db: Session,
        candidate_ids: Optional[List[int]] = None,
        max_candidates: int = 10,
    ) -> ExtractionRun:
        """Executes a structured extraction session over eligible candidates."""
        run = ExtractionRun(status="RUNNING")
        db.add(run)
        db.commit()
        db.refresh(run)

        query = db.query(CandidateURL)
        if candidate_ids:
            query = query.filter(CandidateURL.id.in_(candidate_ids))
        else:
            # Prioritize candidates with status CRAWLED or high relevance score
            query = query.order_by(CandidateURL.relevance_score.desc())

        candidates = query.limit(max_candidates).all()

        scanned = 0
        extracted = 0
        insufficient = 0
        failed = 0

        try:
            for cand in candidates:
                scanned += 1
                try:
                    scholarship, outcome = self.process_candidate(db, cand)
                    if scholarship:
                        extracted += 1
                    elif outcome == "INSUFFICIENT_EVIDENCE":
                        insufficient += 1
                    else:
                        failed += 1
                except Exception as exc:
                    logger.warning(f"Error extracting candidate #{cand.id}: {exc}")
                    failed += 1

            run.status = "COMPLETED"
            run.candidates_scanned = scanned
            run.scholarships_extracted = extracted
            run.insufficient_evidence_count = insufficient
            run.failed_count = failed
        except Exception as exc:
            run.status = "FAILED"
            run.error_message = str(exc)
            logger.error(f"Extraction run failed: {exc}", exc_info=True)
        finally:
            run.completed_at = datetime.now(timezone.utc)
            db.commit()

        return run
