import pytest
from app.services.verification.source_classifier import SourceClassifier


def test_classify_central_government_portal():
    result = SourceClassifier.classify("https://scholarships.gov.in/public/schemeGuidelines")
    assert result.category == "CENTRAL_GOVERNMENT"
    assert result.is_official is True
    assert result.trust_score >= 0.95
    assert "Government of India" in result.reason


def test_classify_state_government_portal():
    result = SourceClassifier.classify("https://ssp.postmatric.karnataka.gov.in/index.aspx")
    assert result.category == "STATE_GOVERNMENT"
    assert result.is_official is True
    assert "karnataka.gov.in" in result.reason


def test_classify_university():
    result = SourceClassifier.classify("https://iisc.ac.in/admissions/financial-support/")
    assert result.category == "UNIVERSITY"
    assert result.is_official is True
    assert ".ac.in" in result.reason


def test_classify_corporate_csr():
    result = SourceClassifier.classify("https://www.reliancefoundation.org/scholarships")
    assert result.category == "CORPORATE_CSR"
    assert result.is_official is True
    assert "reliancefoundation.org" in result.reason


def test_classify_trust_foundation():
    result = SourceClassifier.classify("https://www.kcmet.org/what-we-do-scholarships.aspx")
    assert result.category == "TRUST_FOUNDATION"
    assert result.is_official is True
    assert "kcmet.org" in result.reason


def test_classify_aggregator():
    result = SourceClassifier.classify("https://www.buddy4study.com/scholarships")
    assert result.category == "AGGREGATOR"
    assert result.is_official is False
    assert "buddy4study.com" in result.reason


def test_classify_unknown_domain():
    result = SourceClassifier.classify("https://random-scholarship-blog.xyz/post-1")
    assert result.category == "UNKNOWN"
    assert result.is_official is False
    assert result.trust_score < 0.5
