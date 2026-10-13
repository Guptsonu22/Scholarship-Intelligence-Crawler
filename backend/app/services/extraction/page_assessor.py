import re
from typing import Tuple, Dict, Any
from bs4 import BeautifulSoup


class PageAssessor:
    """Classifies a page's layout and content structure into explicit page types."""

    # Keywords indicative of login / portal registration screens
    AUTH_PATTERNS = [
        re.compile(r"login|sign in|user id|password|captcha|forgot password", re.I),
        re.compile(r"one time registration|otr application|student login|institute login", re.I),
    ]

    # Keywords indicative of listing pages
    LISTING_PATTERNS = [
        re.compile(r"schemes on nsp|list of scholarships|all scholarships|view all schemes", re.I),
        re.compile(r"scholarship directory|schemes list|available scholarships", re.I),
    ]

    # Keywords indicative of generic home / informational pages
    GENERIC_PATTERNS = [
        re.compile(r"about us|contact us|privacy policy|disclaimer|terms of service|sitemap", re.I),
    ]

    @classmethod
    def assess_page(cls, html: str, url: str) -> Tuple[str, str]:
        """Assesses the page type and returns (page_type, assessment_reason).

        Page Types:
            - SCHOLARSHIP_DETAIL
            - SCHOLARSHIP_LISTING
            - APPLICATION_PORTAL
            - GENERIC_PAGE
            - INSUFFICIENT_EVIDENCE
            - FETCH_FAILED
        """
        if not html or not html.strip():
            return "FETCH_FAILED", "Empty or missing HTML content"

        soup = BeautifulSoup(html, "html.parser")
        text_content = soup.get_text(separator=" ", strip=True)

        url_lower = url.lower()

        # 1. Check for Application / Auth Portal
        if any(p in url_lower for p in ["login", "signin", "auth", "register", "otrapplication", "userlogin"]):
            inputs = soup.find_all("input")
            password_inputs = [i for i in inputs if i.get("type") == "password"]
            if password_inputs or "password" in text_content.lower() or "login" in text_content.lower():
                return "APPLICATION_PORTAL", "Page is a user authentication or registration portal, not a scholarship description."

        if len(text_content) < 100:
            return "INSUFFICIENT_EVIDENCE", "Page contains less than 100 characters of readable text"

        # 2. Check for Specific Scheme Headings (Overrides Generic Listing)
        prominent_heading = soup.find(["h1", "h2"])
        heading_text = prominent_heading.get_text(separator=" ", strip=True) if prominent_heading else ""
        has_specific_scheme_heading = bool(
            re.search(r"(?:pg\s+scholarship|pragati|saksham|swanath|yashasvi|doctoral\s+fellowship|merit-cum-means|free\s+studentship|endowment|fellowship|scholarship\s+scheme)", heading_text, re.I)
        )

        # 3. Check for Multi-Scholarship Listing Page (excluding header/nav/footer)
        clean_soup = BeautifulSoup(html, "html.parser")
        for nav_tag in clean_soup(["nav", "header", "footer", "aside"]):
            nav_tag.decompose()
        
        clean_text = clean_soup.get_text(separator=" ", strip=True)
        scheme_rows = clean_soup.find_all(["tr", "li"], string=re.compile(r"scheme|scholarship|fellowship", re.I))

        if not has_specific_scheme_heading:
            if any(p.search(clean_text) for p in cls.LISTING_PATTERNS) or len(scheme_rows) > 12:
                return "SCHOLARSHIP_LISTING", "Page contains an index, table, or directory of multiple scholarship schemes."

        # 4. Check for Generic Portal Homepage
        title = (soup.title.string or "").strip().lower() if soup.title and soup.title.string else ""
        if (
            url_lower.rstrip("/").endswith((".gov.in", ".ac.in", ".org", "scholarships.gov.in"))
            or url_lower.endswith(("/home", "/index.html", "/index.aspx", "/default.aspx"))
        ):
            # If it's a root domain or /home and lacks explicit specific scheme criteria
            if not re.search(r"eligibility|guidelines|amount|benefit|stipend|deadline", text_content, re.I):
                return "GENERIC_PAGE", "Generic portal homepage without standalone scholarship scheme details."

        # 5. Check for Scholarship Detail Evidence
        has_scholarship_term = bool(re.search(r"scholarship|fellowship|financial aid|yojana|stipend|grant|endowment", text_content, re.I))
        has_criteria = bool(re.search(r"eligibility|criteria|qualification|income|documents|selection|guidelines|instruction|manual|rules|degree|diploma|gate|gpat|ph\.?d|merit|means", text_content, re.I))
        has_award_or_date = bool(re.search(r"amount|award|stipend|benefit|deadline|last date|closing date|valid till|fee waiver|concession|rs\.?|inr|₹|per month|per annum", text_content, re.I))

        if has_scholarship_term and (has_criteria or has_award_or_date):
            return "SCHOLARSHIP_DETAIL", "Page contains specific scholarship opportunity details, criteria, or award benefits."

        # 5. Fallback: Insufficient Evidence
        return "INSUFFICIENT_EVIDENCE", "Page lacks verifiable criteria, benefits, or scholarship specifics."
