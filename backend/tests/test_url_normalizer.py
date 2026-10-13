import pytest
from app.services.discovery.url_normalizer import normalize_url, score_scholarship_relevance


def test_normalize_url_strips_fragments():
    url = "https://scholarships.gov.in/public/schemeGuidelines#section2"
    normalized = normalize_url(url)
    assert normalized == "https://scholarships.gov.in/public/schemeGuidelines"


def test_normalize_url_resolves_relative_links():
    base = "https://scholarships.gov.in/portal/home"
    relative = "../schemes/central-sector.html"
    normalized = normalize_url(relative, base_url=base)
    assert normalized == "https://scholarships.gov.in/schemes/central-sector.html"


def test_normalize_url_removes_tracking_params():
    url = "https://tatatrusts.org/education?utm_source=google&utm_medium=cpc&ref=twitter&id=42"
    normalized = normalize_url(url)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "ref" not in normalized
    assert "id=42" in normalized


def test_normalize_url_rejects_non_http_schemes():
    assert normalize_url("javascript:void(0)") is None
    assert normalize_url("mailto:help@scholarships.gov.in") is None
    assert normalize_url("tel:+911234567890") is None
    assert normalize_url("file:///etc/passwd") is None


def test_normalize_url_rejects_binary_extensions():
    assert normalize_url("https://scholarships.gov.in/guidelines.pdf") is None
    assert normalize_url("https://scholarships.gov.in/brochure.docx") is None
    assert normalize_url("https://scholarships.gov.in/image.jpg") is None


def test_relevance_scoring_scholarship_keywords():
    url = "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx"
    score, is_rel = score_scholarship_relevance(url, anchor_text="National Fellowship Scheme")
    assert score >= 0.35
    assert is_rel is True


def test_relevance_scoring_disqualifies_generic_nav_links():
    url = "https://scholarships.gov.in/terms"
    score, is_rel = score_scholarship_relevance(url, anchor_text="Terms of Use")
    assert score == 0.0
    assert is_rel is False
