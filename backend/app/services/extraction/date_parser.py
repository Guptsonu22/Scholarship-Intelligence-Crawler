import re
from datetime import datetime
from typing import Optional, Tuple

MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Regex for common Indian date patterns
DATE_REGEXES = [
    # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    re.compile(r"\b([0-3]?[0-9])[\/\-\.]([0-1]?[0-9])[\/\-\.](202[0-9]|203[0-9])\b"),
    # YYYY-MM-DD
    re.compile(r"\b(202[0-9]|203[0-9])[\/\-\.]([0-1]?[0-9])[\/\-\.]([0-3]?[0-9])\b"),
    # 31st October 2026 or 31 October 2026
    re.compile(r"\b([0-3]?[0-9])(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[,\s]+(202[0-9]|203[0-9])\b", re.I),
    # October 31, 2026
    re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+([0-3]?[0-9])(?:st|nd|rd|th)?[,\s]+(202[0-9]|203[0-9])\b", re.I),
]

DEADLINE_CONTEXT_PATTERNS = [
    re.compile(r"(?:last\s+date|closing\s+date|deadline|application\s+deadline|valid\s+till|till|upto|up\s+to|end\s+date)\s*(?:is|:|-)?\s*([^\.\n\<\>]+)", re.I),
]


class DateParser:
    """Extracts and validates structured date representations from free-form text."""

    @classmethod
    def parse_deadline(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Searches text for deadline dates in priority context.

        Returns:
            (formatted_iso_date, verbatim_context_snippet)
        """
        if not text:
            return None, None

        # 1. Search near explicit deadline keywords
        for pattern in DEADLINE_CONTEXT_PATTERNS:
            match = pattern.search(text)
            if match:
                snippet = match.group(0).strip()
                date_str = cls.extract_first_date(snippet)
                if date_str:
                    return date_str, snippet[:200]

        return None, None

    @classmethod
    def extract_first_date(cls, text: str) -> Optional[str]:
        """Finds the first valid date in text and formats it as YYYY-MM-DD."""
        if not text:
            return None

        # Pattern 1: DD/MM/YYYY
        m = DATE_REGEXES[0].search(text)
        if m:
            d, m_val, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime(y, m_val, d)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Pattern 2: YYYY-MM-DD
        m = DATE_REGEXES[1].search(text)
        if m:
            y, m_val, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                dt = datetime(y, m_val, d)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Pattern 3: DD Month YYYY
        m = DATE_REGEXES[2].search(text)
        if m:
            d = int(m.group(1))
            m_str = m.group(2).lower()
            y = int(m.group(3))
            m_val = MONTH_NAMES.get(m_str)
            if m_val:
                try:
                    dt = datetime(y, m_val, d)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        # Pattern 4: Month DD, YYYY
        m = DATE_REGEXES[3].search(text)
        if m:
            m_str = m.group(1).lower()
            d = int(m.group(2))
            y = int(m.group(3))
            m_val = MONTH_NAMES.get(m_str)
            if m_val:
                try:
                    dt = datetime(y, m_val, d)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        return None
