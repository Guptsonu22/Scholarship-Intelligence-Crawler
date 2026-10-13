import re
from typing import Optional, Tuple

# Patterns for Indian monetary amounts
CURRENCY_PATTERNS = [
    # ₹ 50,000 or ₹50,000 or Rs. 50,000 or Rs 50,000 or INR 50,000
    re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:lakhs?|crores?|k)?(?:\s*(?:per|/|-)\s*(?:annum|year|month|pm|pa|semester))?", re.I),
    # 50,000 per annum / month
    re.compile(r"([\d,]+)\s*(?:per\s+(?:annum|year|month|pm|pa)|/year|/month)", re.I),
    # 2 Lakhs or 1.5 Lakh per annum
    re.compile(r"(?:up\s+to\s+)?(?:₹|Rs\.?|INR)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?|crores?)\s*(?:per\s+(?:year|annum|month))?", re.I),
]

DESCRIPTIVE_BENEFITS = [
    re.compile(r"(?:full|100%)\s+tuition\s+fee\s+waiver", re.I),
    re.compile(r"maintenance\s+allowance\s+of\s+₹?\s*[\d,]+", re.I),
    re.compile(r"contingency\s+grant\s+(?:of\s+)?₹?\s*[\d,]+", re.I),
    re.compile(r"monthly\s+stipend\s+(?:of\s+)?₹?\s*[\d,]+", re.I),
    re.compile(r"hostel\s+subsidy|book\s+grant|free\s+education", re.I),
]


class AmountParser:
    """Parses monetary values and non-monetary benefit descriptions from text."""

    @classmethod
    def parse_benefit(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts financial or in-kind scholarship benefit from text.

        Returns:
            (normalized_benefit_string, verbatim_context_snippet)
        """
        if not text:
            return None, None

        # 1. Search near explicit amount/benefit keywords first
        benefit_context_pattern = re.compile(
            r"(?:scholarship\s+amount|award|financial\s+assistance|benefit|stipend|grant|fellowship\s+amount)\s*(?:is|:|-)?\s*([^\.\n\<\>]+)",
            re.I,
        )
        match = benefit_context_pattern.search(text)
        if match:
            snippet = match.group(0).strip()
            extracted = cls._extract_amount_from_snippet(snippet)
            if extracted:
                return extracted, snippet[:200]

        # 2. Search for explicit currency expressions
        for pat in CURRENCY_PATTERNS:
            m = pat.search(text)
            if m:
                matched_expr = m.group(0).strip()
                # Exclude purely small single-digit numbers or year-like values (e.g. 2026)
                clean_num = re.sub(r"[^\d]", "", matched_expr)
                if clean_num and clean_num not in ("2024", "2025", "2026", "2027", "2028") and len(clean_num) >= 3:
                    start = max(0, m.start() - 25)
                    end = min(len(text), m.end() + 25)
                    return matched_expr, text[start:end].strip()

        # 3. Check for descriptive non-monetary benefits (fee waiver, etc.)
        for pat in DESCRIPTIVE_BENEFITS:
            m = pat.search(text)
            if m:
                matched_expr = m.group(0).strip()
                start = max(0, m.start() - 25)
                end = min(len(text), m.end() + 25)
                return matched_expr.capitalize(), text[start:end].strip()

        return None, None

    @classmethod
    def _extract_amount_from_snippet(cls, snippet: str) -> Optional[str]:
        for pat in CURRENCY_PATTERNS:
            m = pat.search(snippet)
            if m:
                return m.group(0).strip()
        for pat in DESCRIPTIVE_BENEFITS:
            m = pat.search(snippet)
            if m:
                return m.group(0).strip().capitalize()
        return None
