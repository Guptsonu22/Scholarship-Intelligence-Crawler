"""Mandatory Verification Gates.

Explicit, independently testable verification gates that must all pass
before any scholarship record can receive the VERIFIED designation.
Even if a record has a high score (e.g. >= 95%), any failed gate forces REVIEW_REQUIRED.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class GateEvaluationResult:
    """Outcome of a single verification gate."""
    gate_name: str
    status: str  # PASS, FAIL, NOT_APPLICABLE
    explanation: str
    evidence_refs: List[Dict[str, Any]]
    evaluated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VerificationGates:
    """Collection of deterministic mandatory verification gates."""

    @staticmethod
    def official_source_gate(
        source_url: str,
        category: str,
        is_official: bool,
        is_aggregator: bool,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if is_aggregator:
            return GateEvaluationResult(
                gate_name="official_source_gate",
                status="FAIL",
                explanation=f"Source URL '{source_url}' is classified as an aggregator (discovery feed), not an authoritative primary source.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        if not is_official:
            return GateEvaluationResult(
                gate_name="official_source_gate",
                status="FAIL",
                explanation=f"Source URL '{source_url}' could not be established as an official government, university, or verified CSR domain.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="official_source_gate",
            status="PASS",
            explanation=f"Authoritative official primary source verified under category '{category}'.",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def scholarship_identity_gate(
        name: Optional[str],
        is_umbrella_or_listing: bool,
        page_type: str = "SCHOLARSHIP_DETAIL",
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if not name or len(name.strip()) < 4:
            return GateEvaluationResult(
                gate_name="scholarship_identity_gate",
                status="FAIL",
                explanation="Scholarship opportunity name is missing or too brief to identify a specific grant.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        if is_umbrella_or_listing or page_type == "SCHOLARSHIP_LISTING":
            return GateEvaluationResult(
                gate_name="scholarship_identity_gate",
                status="FAIL",
                explanation=f"Title '{name}' represents an umbrella directory/multi-scheme portal rather than an individual, distinct scholarship opportunity.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="scholarship_identity_gate",
            status="PASS",
            explanation=f"Distinct individual scholarship identity established: '{name}'.",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def field_evidence_gate(
        field_ratings: Dict[str, str],  # field_name -> rating
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        # Name must be supported
        if field_ratings.get("name") != "SUPPORTED":
            return GateEvaluationResult(
                gate_name="field_evidence_gate",
                status="FAIL",
                explanation=f"Name field lacks direct supported evidence (current rating: {field_ratings.get('name', 'NOT_FOUND')}).",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        # Provider must be supported
        if field_ratings.get("provider") != "SUPPORTED":
            return GateEvaluationResult(
                gate_name="field_evidence_gate",
                status="FAIL",
                explanation=f"Provider field lacks direct supported evidence (current rating: {field_ratings.get('provider', 'NOT_FOUND')}).",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        # Must have at least one supported core eligibility or benefit field
        has_supported_core = any(
            field_ratings.get(k) == "SUPPORTED"
            for k in ["eligibility_summary", "academic_requirements", "amount_benefit", "course_level", "category_requirements"]
        )

        if not has_supported_core:
            return GateEvaluationResult(
                gate_name="field_evidence_gate",
                status="FAIL",
                explanation="No critical eligibility or benefit field is directly supported by verified textual evidence.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="field_evidence_gate",
            status="PASS",
            explanation="All critical identity and core eligibility/benefit fields are directly supported by source evidence.",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def contradiction_gate(
        has_contradictions: bool,
        contradiction_reasons: Optional[List[str]] = None,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if has_contradictions:
            reasons_str = "; ".join(contradiction_reasons or ["Unresolved contradictions found"])
            return GateEvaluationResult(
                gate_name="contradiction_gate",
                status="FAIL",
                explanation=f"Unresolved critical contradictions detected: {reasons_str}",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="contradiction_gate",
            status="PASS",
            explanation="No conflicting dates, benefit amounts, or multi-scheme details detected.",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def freshness_gate(
        crawl_http_status: Optional[int],
        days_since_fetch: Optional[int],
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if crawl_http_status != 200:
            return GateEvaluationResult(
                gate_name="freshness_gate",
                status="FAIL",
                explanation=f"Source fetch was unsuccessful (HTTP status: {crawl_http_status}).",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        if days_since_fetch is not None and days_since_fetch > 90:
            return GateEvaluationResult(
                gate_name="freshness_gate",
                status="FAIL",
                explanation=f"Evidence is stale: last successful fetch was {days_since_fetch} days ago (>90 days limit).",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="freshness_gate",
            status="PASS",
            explanation=f"Source page successfully fetched and evidence is fresh ({days_since_fetch or 0} days old).",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def application_link_gate(
        application_url: Optional[str],
        is_official_portal: bool,
        is_not_applicable: bool = False,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if is_not_applicable or not application_url:
            return GateEvaluationResult(
                gate_name="application_link_gate",
                status="NOT_APPLICABLE",
                explanation="Application portal URL is not currently applicable (application window not opened, offline submission, or direct institutional notice).",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        if not is_official_portal:
            return GateEvaluationResult(
                gate_name="application_link_gate",
                status="FAIL",
                explanation=f"Application URL '{application_url}' points to an unofficial or unrecognized third-party domain.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        return GateEvaluationResult(
            gate_name="application_link_gate",
            status="PASS",
            explanation=f"Application portal URL '{application_url}' verified on official provider/national apex infrastructure.",
            evidence_refs=refs,
            evaluated_at=eval_time,
        )

    @staticmethod
    def lifecycle_gate(
        closing_date_str: Optional[str],
        reference_date: Optional[str] = None,  # YYYY-MM-DD
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        now: Optional[datetime] = None,
    ) -> GateEvaluationResult:
        eval_time = (now or datetime.now(timezone.utc)).isoformat()
        refs = evidence_refs or []

        if not closing_date_str:
            # Ongoing / rolling admissions
            return GateEvaluationResult(
                gate_name="lifecycle_gate",
                status="PASS",
                explanation="No explicit closing date published; opportunity treated as rolling/open-ended with ongoing validity.",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )

        today_str = reference_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Compare dates if closing_date matches YYYY-MM-DD format
        try:
            if closing_date_str < today_str:
                return GateEvaluationResult(
                    gate_name="lifecycle_gate",
                    status="FAIL",
                    explanation=f"Reported closing date '{closing_date_str}' has expired as of evaluation date '{today_str}'.",
                    evidence_refs=refs,
                    evaluated_at=eval_time,
                )
            else:
                return GateEvaluationResult(
                    gate_name="lifecycle_gate",
                    status="PASS",
                    explanation=f"Reported closing date '{closing_date_str}' is active and valid (future deadline relative to '{today_str}').",
                    evidence_refs=refs,
                    evaluated_at=eval_time,
                )
        except Exception as e:
            return GateEvaluationResult(
                gate_name="lifecycle_gate",
                status="FAIL",
                explanation=f"Could not reliably evaluate closing date '{closing_date_str}': {e}",
                evidence_refs=refs,
                evaluated_at=eval_time,
            )
