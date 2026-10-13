import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "source",
    "fbclid",
    "gclid",
    "sessionid",
    "_ga",
}

# Binary file extensions to exclude from candidate discovery
EXCLUDED_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".exe",
    ".docx",
    ".xlsx",
    ".pptx",
    ".mp4",
    ".mp3",
)

PRIMARY_KEYWORDS = {
    "scholarship": 0.40,
    "fellowship": 0.35,
    "financial aid": 0.30,
    "stipend": 0.30,
    "yojana": 0.25,
    "medhabruti": 0.35,
    "vidyasaarathi": 0.35,
    "post-matric": 0.30,
    "post matric": 0.30,
    "pre-matric": 0.30,
    "pre matric": 0.30,
    "grant": 0.20,
}

SECONDARY_KEYWORDS = {
    "eligibility": 0.15,
    "apply": 0.10,
    "guidelines": 0.10,
    "scheme": 0.10,
    "award": 0.10,
    "merit": 0.10,
    "financial support": 0.20,
    "student support": 0.15,
    "education": 0.05,
}

DISQUALIFYING_ANCHORS = {
    "about us",
    "contact us",
    "privacy policy",
    "terms of use",
    "disclaimer",
    "login",
    "sign in",
    "register",
    "sitemap",
    "home",
}


def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
    """Normalizes a URL by resolving relative links, removing fragments, stripping tracking parameters,

    and standardizing slashes and casing.
    """
    if not url or not isinstance(url, str):
        return None

    cleaned = url.strip()

    # Skip non-http schemes
    if cleaned.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return None

    # Resolve relative URL if base_url provided
    if base_url:
        cleaned = urljoin(base_url, cleaned)

    try:
        parsed = urlparse(cleaned)
    except Exception:
        return None

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return None

    hostname = parsed.hostname
    if not hostname:
        return None

    hostname = hostname.lower()

    # Port handling
    port = f":{parsed.port}" if parsed.port and parsed.port not in (80, 443) else ""
    netloc = f"{hostname}{port}"

    # Path normalization: collapse multiple slashes, strip trailing slash unless root
    path = parsed.path
    path = re.sub(r"/+", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    if not path:
        path = "/"

    # Check for excluded file extensions
    path_lower = path.lower()
    if any(path_lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return None

    # Filter out tracking query parameters while preserving legitimate queries
    filtered_queries = []
    if parsed.query:
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        for k, v in query_pairs:
            if k.lower() not in TRACKING_PARAMS:
                filtered_queries.append((k, v))

    # Sort queries for deterministic comparison
    filtered_queries.sort(key=lambda x: x[0])
    query_str = urlencode(filtered_queries)

    # Reconstruct normalized URL without fragment
    normalized = urlunparse((scheme, netloc, path, "", query_str, ""))
    return normalized


def score_scholarship_relevance(
    url: str,
    anchor_text: Optional[str] = None,
    page_title: Optional[str] = None,
) -> Tuple[float, bool]:
    """Computes a heuristic relevance score [0.0 - 1.0] indicating likelihood that the link leads to a scholarship.

    Returns:
        (score, is_relevant)
    """
    anchor_clean = (anchor_text or "").strip().lower()
    if anchor_clean in DISQUALIFYING_ANCHORS:
        return 0.0, False

    text_to_search = f"{url.lower()} {anchor_clean} {(page_title or '').lower()}"

    score = 0.0

    for kw, weight in PRIMARY_KEYWORDS.items():
        if kw in text_to_search:
            score += weight

    for kw, weight in SECONDARY_KEYWORDS.items():
        if kw in text_to_search:
            score += weight

    # Normalize score between 0.0 and 1.0
    final_score = min(1.0, round(score, 2))
    is_relevant = final_score >= 0.20

    return final_score, is_relevant
