"""Field-Level Change Detection Engine.

Compares new extracted observations with previously stored values,
filters extraction noise and formatting variance, preserves full evidence history,
and records structured change audit entries.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.db.models import (
    Scholarship,
    FieldEvidence,
    ScholarshipChangeHistory,
    CrawlRun,
)

logger = logging.getLogger(__name__)

# Critical fields that mandate re-verification evaluation upon change
CRITICAL_REVERIFICATION_FIELDS = {
    "closing_date",
    "opening_date",
    "provider",
    "amount_benefit",
    "eligibility_summary",
    "application_url",
    "name",
    "course_level",
    "income_criteria",
}

# Classification mapping for changed fields
FIELD_CLASSIFICATION_MAP = {
    "closing_date": "CRITICAL_DEADLINE",
    "opening_date": "CRITICAL_DEADLINE",
    "amount_benefit": "BENEFIT_UPDATE",
    "amount_details": "BENEFIT_UPDATE",
    "eligibility_summary": "ELIGIBILITY_REVISION",
    "academic_requirements": "ELIGIBILITY_REVISION",
    "income_criteria": "ELIGIBILITY_REVISION",
    "age_criteria": "ELIGIBILITY_REVISION",
    "gender_criteria": "ELIGIBILITY_REVISION",
    "category_requirements": "ELIGIBILITY_REVISION",
    "domicile_state": "ELIGIBILITY_REVISION",
    "institution_requirements": "ELIGIBILITY_REVISION",
    "application_url": "URL_CHANGE",
    "name": "IDENTITY_UPDATE",
    "provider": "IDENTITY_UPDATE",
    "course_level": "ELIGIBILITY_REVISION",
}


def normalize_value(val: Optional[str]) -> str:
    """Normalizes whitespace and formatting to distinguish real changes from extraction noise."""
    if val is None:
        return ""
    # Collapse multiple whitespaces, tabs, and newlines
    cleaned = re.sub(r"\s+", " ", str(val).strip())
    return cleaned


class ChangeDetector:
    """Detects genuine field-level changes and records immutable audit history."""

    @classmethod
    def detect_and_apply_changes(
        cls,
        db: Session,
        scholarship: Scholarship,
        extracted_data: Any,  # ExtractedScholarshipData
        new_content_hash: Optional[str] = None,
        crawl_run_id: Optional[int] = None,
        evaluation_timestamp: Optional[datetime] = None,
    ) -> List[ScholarshipChangeHistory]:
        """Compares newly extracted fields with existing scholarship attributes.
        
        Applies changes safely, attaches new field evidence without erasing history,
        and creates ScholarshipChangeHistory records.
        """
        now = evaluation_timestamp or datetime.now(timezone.utc)
        recorded_changes: List[ScholarshipChangeHistory] = []

        # Fields to compare: (scholarship_attr, extracted_attr)
        fields_to_check = [
            ("name", extracted_data.name),
            ("provider", extracted_data.provider),
            ("amount_benefit", extracted_data.amount_benefit),
            ("amount_details", getattr(extracted_data, "amount_details", None)),
            ("eligibility_summary", extracted_data.eligibility_summary),
            ("academic_requirements", getattr(extracted_data, "academic_requirements", None)),
            ("course_level", extracted_data.course_level),
            ("income_criteria", extracted_data.income_criteria),
            ("age_criteria", getattr(extracted_data, "age_criteria", None)),
            ("gender_criteria", extracted_data.gender_criteria),
            ("category_requirements", extracted_data.category_requirements),
            ("domicile_state", getattr(extracted_data, "domicile_state", None)),
            ("institution_requirements", getattr(extracted_data, "institution_requirements", None)),
            ("opening_date", getattr(extracted_data, "opening_date", None)),
            ("closing_date", extracted_data.closing_date),
            ("application_url", extracted_data.application_url),
            ("documents_required", getattr(extracted_data, "documents_required", None)),
            ("selection_process", getattr(extracted_data, "selection_process", None)),
            ("renewal_requirements", getattr(extracted_data, "renewal_requirements", None)),
        ]

        # Map new evidence items by field_name
        new_evidence_by_field: Dict[str, Any] = {}
        if hasattr(extracted_data, "evidence_list"):
            for item in extracted_data.evidence_list:
                new_evidence_by_field[item.field_name] = item

        # Query existing current evidence
        existing_evidence_by_field: Dict[str, FieldEvidence] = {}
        curr_evs = (
            db.query(FieldEvidence)
            .filter(
                FieldEvidence.scholarship_id == scholarship.id,
                FieldEvidence.is_current == True,
            )
            .all()
        )
        for ev in curr_evs:
            existing_evidence_by_field[ev.field_name] = ev

        for field_name, new_val_raw in fields_to_check:
            old_val_raw = getattr(scholarship, field_name)

            old_norm = normalize_value(old_val_raw)
            new_norm = normalize_value(new_val_raw)

            # Rule 4: Extraction noise filter
            # If new observation is missing/empty, DO NOT treat it as a deletion of prior known data!
            if not new_norm and old_norm:
                logger.info(
                    f"Candidate extraction for '{field_name}' yielded empty value. "
                    f"Retaining previous value '{old_val_raw}'."
                )
                continue

            # If both are empty or normalized strings match, no change occurred
            if old_norm == new_norm:
                continue

            # A GENUINE CHANGE OCCURRED!
            classification = FIELD_CLASSIFICATION_MAP.get(field_name, "METADATA_UPDATE")
            requires_reverification = field_name in CRITICAL_REVERIFICATION_FIELDS

            # Find previous evidence record
            prev_ev = existing_evidence_by_field.get(field_name)
            prev_ev_id = prev_ev.id if prev_ev else None

            # Create new FieldEvidence record if evidence exists
            new_ev_id = None
            ev_item = new_evidence_by_field.get(field_name)

            # Mark previous evidence as superseded
            if prev_ev:
                prev_ev.is_current = False

            if ev_item:
                new_ev = FieldEvidence(
                    scholarship_id=scholarship.id,
                    candidate_id=scholarship.candidate_id,
                    field_name=field_name,
                    extracted_value=ev_item.extracted_value,
                    source_url=scholarship.official_source_url,
                    evidence_text=ev_item.evidence_text,
                    page_title=getattr(extracted_data, "page_title", None),
                    retrieval_timestamp=now,
                    content_hash=new_content_hash,
                    extraction_method="DETERMINISTIC_DOM",
                    html_selector=ev_item.html_selector,
                    validation_status="VALID",
                    quality_rating="SUPPORTED",
                    is_current=True,
                )
                db.add(new_ev)
                db.flush()  # Allocate ID
                new_ev_id = new_ev.id

            # Update Scholarship field value
            setattr(scholarship, field_name, new_val_raw)

            # Create immutable change history record
            change_record = ScholarshipChangeHistory(
                scholarship_id=scholarship.id,
                field_name=field_name,
                previous_value=old_val_raw,
                new_value=new_val_raw,
                detection_timestamp=now,
                previous_evidence_id=prev_ev_id,
                new_evidence_id=new_ev_id,
                source_url=scholarship.official_source_url,
                crawl_run_id=crawl_run_id,
                change_classification=classification,
                requires_reverification=requires_reverification,
                is_reviewed=False,
            )
            db.add(change_record)
            recorded_changes.append(change_record)

        # Update metadata timestamps on scholarship
        if new_content_hash:
            scholarship.content_hash = new_content_hash
        scholarship.last_fetched_timestamp = now

        db.commit()
        return recorded_changes
