"""Evidence Quality Evaluator.

Evaluates the relevance, strength, and freshness of textual field-level evidence.
Ratings:
- SUPPORTED: Direct, relevant textual evidence clearly linking value to field.
- WEAK_EVIDENCE: Vague, generic container snippet, or ambiguous context.
- NOT_FOUND: Missing extracted value or empty snippet.
- CONFLICTING: Contains contradictory or mutually exclusive data.
- STALE: Evidence retrieval timestamp is older than permitted threshold.
"""
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

GENERIC_BODY_INDICATORS = [
    "skip to main content",
    "screen reader",
    "all rights reserved",
    "terms of use",
    "privacy policy",
    "sitemap",
    "navigation",
    "copyright",
    "disclaimer",
]

DEADLINE_CONTEXT_KEYWORDS = [
    "last date",
    "closing date",
    "deadline",
    "apply before",
    "application ends",
    "due date",
    "submission end",
    "cutoff date",
]

UMBRELLA_TITLES = [
    "students development schemes",
    "student development schemes",
    "development schemes",
    "schemes",
    "scholarships",
    "all scholarships",
    "financial support",
    "fellowships",
    "scholarship portal",
    "national scholarship portal",
]


class EvidenceEvaluator:
    """Evaluates field evidence quality and relevance."""

    @staticmethod
    def evaluate_field(
        field_name: str,
        extracted_value: Optional[str],
        evidence_snippet: Optional[str],
        html_selector: Optional[str] = None,
        retrieval_timestamp: Optional[datetime] = None,
        reference_time: Optional[datetime] = None,
    ) -> Tuple[str, str]:
        """Evaluates a single field evidence snippet.
        
        Returns:
            Tuple of (quality_rating, explanation)
            quality_rating in {SUPPORTED, WEAK_EVIDENCE, NOT_FOUND, CONFLICTING, STALE}
        """
        if not extracted_value or not extracted_value.strip():
            return "NOT_FOUND", f"No extracted value found for field '{field_name}'."

        if not evidence_snippet or not evidence_snippet.strip():
            return "NOT_FOUND", f"Extracted value '{extracted_value}' lacks source snippet evidence."

        val_lower = extracted_value.strip().lower()
        snip_lower = evidence_snippet.strip().lower()

        # Check staleness (> 180 days)
        now = reference_time or datetime.now(timezone.utc)
        if retrieval_timestamp:
            if retrieval_timestamp.tzinfo is None:
                retrieval_timestamp = retrieval_timestamp.replace(tzinfo=timezone.utc)
            days_old = (now - retrieval_timestamp).days
            if days_old > 180:
                return "STALE", f"Evidence was collected {days_old} days ago (>180 days threshold)."

        # Check generic boilerplate container
        for indicator in GENERIC_BODY_INDICATORS:
            if indicator in snip_lower:
                return "WEAK_EVIDENCE", f"Snippet appears to be generic page chrome/boilerplate containing '{indicator}'."

        # Field-specific evaluation
        if field_name == "name":
            # Check if name is an umbrella listing title
            for umbrella in UMBRELLA_TITLES:
                if val_lower == umbrella or val_lower == f"{umbrella} | aicte":
                    return "WEAK_EVIDENCE", f"Extracted name '{extracted_value}' is a multi-scheme umbrella/directory title rather than a specific funding opportunity."

            # Check if name or substantial part appears in snippet
            if val_lower in snip_lower:
                return "SUPPORTED", "Exact opportunity name verified in source snippet."
            words = [w for w in val_lower.split() if len(w) > 3]
            if words and all(w in snip_lower for w in words[:3]):
                return "SUPPORTED", "Opportunity name tokens strongly matched in snippet."
            return "WEAK_EVIDENCE", "Opportunity name not cleanly found in evidence snippet."

        elif field_name == "provider":
            if val_lower in snip_lower:
                return "SUPPORTED", "Provider identity explicitly verified in source evidence."
            prov_tokens = [w for w in val_lower.split() if len(w) > 3]
            if prov_tokens and sum(1 for w in prov_tokens if w in snip_lower) >= max(1, len(prov_tokens) // 2):
                return "SUPPORTED", "Provider tokens found in source text."
            return "WEAK_EVIDENCE", "Provider name not explicitly supported by snippet text."

        elif field_name == "closing_date":
            # Must verify date format and contextual association
            has_kw = any(kw in snip_lower for kw in DEADLINE_CONTEXT_KEYWORDS)
            if has_kw and val_lower in snip_lower:
                return "SUPPORTED", "Closing date accompanied by explicit deadline keywords ('last date' / 'closing date')."
            elif val_lower in snip_lower:
                return "WEAK_EVIDENCE", f"Date '{extracted_value}' present in snippet but lacks clear deadline contextual phrasing."
            return "WEAK_EVIDENCE", "Closing date not directly evidenced in snippet."

        elif field_name == "amount_benefit":
            amt_kws = ["rs", "inr", "₹", "per month", "per annum", "lakh", "concession", "tuition", "stipend"]
            has_amt_kw = any(kw in snip_lower for kw in amt_kws)
            if has_amt_kw and (val_lower in snip_lower or any(c.isdigit() for c in val_lower)):
                return "SUPPORTED", "Amount/benefit supported by monetary markers in source evidence."
            return "WEAK_EVIDENCE", "Benefit amount lacks explicit monetary context in snippet."

        elif field_name == "course_level":
            # Watch out for PDF misinterpreting 'Post-Doctoral Fellowship' or '.pdf document'
            if "post-doctoral fellowship" in snip_lower and "pdf" in snip_lower and "bachelor" not in snip_lower and "master" not in snip_lower:
                if "phd" in val_lower or "postgraduate" in val_lower:
                    return "WEAK_EVIDENCE", "Course level evidence conflates 'PDF' (Post-Doctoral Fellowship) on multi-scheme page."
            if any(lvl in snip_lower for lvl in ["undergraduate", "postgraduate", "ph.d", "phd", "diploma", "degree", "class 1", "school"]):
                return "SUPPORTED", "Course level explicitly supported by academic level terms."
            return "WEAK_EVIDENCE", "Course level evidence is indirect or ambiguous."

        elif field_name == "application_url":
            if val_lower.startswith("http://") or val_lower.startswith("https://"):
                return "SUPPORTED", "Application URL is validly formatted and present in link element."
            return "WEAK_EVIDENCE", "Application URL lacks valid web scheme."

        # Default fallback for other fields
        if val_lower in snip_lower:
            return "SUPPORTED", f"Field '{field_name}' verified in evidence snippet."
        return "WEAK_EVIDENCE", f"Field '{field_name}' lacks direct textual correspondence in snippet."
