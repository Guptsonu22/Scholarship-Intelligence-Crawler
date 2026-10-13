"""Tests for Phase 6: Real Scholarship Coverage & Official-Source Verification."""
import pytest
from bs4 import BeautifulSoup
from app.services.verification.source_classifier import SourceClassifier
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.verification.scoring_model import DeterministicScoringModel
from app.services.verification.gates import VerificationGates
from app.services.verification.verification_engine import VerificationEngine


def test_source_classification_across_all_four_categories():
    """Verify that SourceClassifier correctly categorizes official sources across 4 sectors."""
    # 1. Central Government
    res_central = SourceClassifier.classify("https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme")
    assert res_central.category == "CENTRAL_GOVERNMENT"
    assert res_central.is_official is True
    assert res_central.trust_score >= 0.95

    res_dst = SourceClassifier.classify("https://online-inspire.gov.in/")
    assert res_central.category == "CENTRAL_GOVERNMENT"
    assert res_dst.is_official is True

    # 2. State Government
    res_oasis = SourceClassifier.classify("https://oasis.gov.in/")
    assert res_oasis.category == "STATE_GOVERNMENT"
    assert res_oasis.is_official is True
    assert res_oasis.trust_score >= 0.95

    res_haryana = SourceClassifier.classify("https://harchhatravratti.highereduhry.ac.in/")
    assert res_haryana.category == "STATE_GOVERNMENT"
    assert res_haryana.is_official is True

    # 3. University / Premier Institution
    res_iitk = SourceClassifier.classify("https://www.iitk.ac.in/dora/scholarships")
    assert res_iitk.category == "UNIVERSITY"
    assert res_iitk.is_official is True
    assert res_iitk.trust_score >= 0.90

    res_apu = SourceClassifier.classify("https://azimpremjiuniversity.edu.in/undergraduate/financial-aid")
    assert res_apu.category == "UNIVERSITY"
    assert res_apu.is_official is True

    # 4. Corporate CSR / Philanthropic Trust
    res_tata = SourceClassifier.classify("https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants")
    assert res_tata.category == "CORPORATE_CSR"
    assert res_tata.is_official is True

    res_birla = SourceClassifier.classify("https://www.adityabirlascholars.net/")
    assert res_birla.category == "CORPORATE_CSR"
    assert res_birla.is_official is True

    res_sekhsaria = SourceClassifier.classify("https://pg.nsfoundation.co.in/")
    assert res_sekhsaria.category == "TRUST_FOUNDATION"
    assert res_sekhsaria.is_official is True


def test_page_assessor_distinguishes_detail_from_directory():
    """Verify that specific scheme detail pages are assessed as SCHOLARSHIP_DETAIL."""
    detail_html = """
    <html>
      <head><title>AICTE PG Scholarship Scheme</title></head>
      <body>
        <h1>Post Graduate Scholarship Scheme</h1>
        <p>AICTE provides financial assistance of Rs 12,400 per month to full-time GATE/GPAT qualified students admitted to M.Tech programs.</p>
        <h2>Eligibility Criteria</h2>
        <p>Must have a valid GATE or GPAT score at the time of admission. Annual family income must meet the prescribed criteria.</p>
        <p>Last date for student verification by institute is 31/12/2026.</p>
      </body>
    </html>
    """
    page_type, reason = PageAssessor.assess_page(detail_html, "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme")
    assert page_type == "SCHOLARSHIP_DETAIL"

    # Multi-scheme directory listing page
    listing_html = """
    <html>
      <head><title>All Scholarship Schemes</title></head>
      <body>
        <h1>Scheme Directory</h1>
        <table>
          <tr><td>Scheme 1: Pre-Matric SC</td><td><a href="/scheme1">View</a></td></tr>
          <tr><td>Scheme 2: Post-Matric SC</td><td><a href="/scheme2">View</a></td></tr>
          <tr><td>Scheme 3: Merit Award</td><td><a href="/scheme3">View</a></td></tr>
          <tr><td>Scheme 4: Higher Education</td><td><a href="/scheme4">View</a></td></tr>
          <tr><td>Scheme 5: Technical Fellowship</td><td><a href="/scheme5">View</a></td></tr>
          <tr><td>Scheme 6: Girls Stipend</td><td><a href="/scheme6">View</a></td></tr>
          <tr><td>Scheme 7: Minority Grant</td><td><a href="/scheme7">View</a></td></tr>
          <tr><td>Scheme 8: Disability Grant</td><td><a href="/scheme8">View</a></td></tr>
        </table>
      </body>
    </html>
    """
    listing_type, listing_reason = PageAssessor.assess_page(listing_html, "https://example.gov.in/schemes")
    assert listing_type == "SCHOLARSHIP_LISTING"


def test_field_extractor_attaches_traceable_evidence():
    """Verify that FieldExtractor extracts key fields and attaches RawEvidenceItem records."""
    html = """
    <html>
      <head><title>IIT Kanpur Scholarships</title></head>
      <body>
        <h1>IIT Kanpur Merit-cum-Means (MCM) Scholarship</h1>
        <p>Administered by Indian Institute of Technology Kanpur.</p>
        <p>Benefit: Full tuition fee waiver plus Rs. 1,000 per month pocket allowance.</p>
        <p>Eligibility Criteria: Undergraduate B.Tech students enrolled at IIT Kanpur with annual family income below Rs 5 Lakhs.</p>
        <p>Last Date to Apply: 30-11-2026.</p>
        <a href="https://www.iitk.ac.in/dora/apply">Apply Online</a>
      </body>
    </html>
    """
    extracted = FieldExtractor.extract(html, "https://www.iitk.ac.in/dora/scholarships")
    assert extracted.name is not None
    assert "IIT Kanpur" in extracted.name or "Merit-cum-Means" in extracted.name
    assert extracted.provider == "Indian Institute of Technology Kanpur"
    assert len(extracted.evidence_list) >= 4

    evidence_fields = {ev.field_name: ev for ev in extracted.evidence_list}
    assert "name" in evidence_fields
    assert "provider" in evidence_fields
    assert evidence_fields["name"].html_selector is not None
    assert evidence_fields["provider"].evidence_text != ""


def test_deterministic_scoring_reaches_95_percent_for_authentic_official_record():
    """Verify that an authentic official government scholarship with complete evidence scores >= 95%."""
    score_result = DeterministicScoringModel.evaluate(
        source_category="CENTRAL_GOVERNMENT",
        is_official_source=True,
        is_aggregator=False,
        name="AICTE PG Scholarship Scheme (GATE/GPAT)",
        provider="All India Council for Technical Education",
        is_umbrella_or_listing=False,
        field_evidence_summary={
            "name": "SUPPORTED",
            "provider": "SUPPORTED",
            "eligibility_summary": "SUPPORTED",
            "amount_benefit": "SUPPORTED",
            "closing_date": "SUPPORTED",
        },
        has_application_url=True,
        is_app_url_official=True,
        app_url_not_applicable=False,
        has_closing_date=True,
        is_deadline_contextual=True,
        is_deadline_expired=False,
        days_since_fetch=1,
        crawl_http_status=200,
        has_contradictions=False,
        contradiction_details=[],
    )

    # 25 (source) + 20 (id) + 20 (fields) + 10 (app) + 10 (deadline) + 10 (freshness) + 5 (consistency) = 100.0
    assert score_result.total_score >= 95.0
    assert len(score_result.deductions_summary) == 0


def test_failed_verification_gate_prevents_verified_status():
    """Verify that failing any verification gate strictly blocks VERIFIED status."""
    g_official = VerificationGates.official_source_gate(
        source_url="https://thirdparty-aggregator-blog.com/scholarships",
        category="AGGREGATOR",
        is_official=False,
        is_aggregator=True,
    )
    assert g_official.status == "FAIL"

    g_identity = VerificationGates.scholarship_identity_gate(
        name="All AICTE Student Development Schemes Directory",
        is_umbrella_or_listing=True,
        page_type="SCHOLARSHIP_LISTING",
    )
    assert g_identity.status == "FAIL"

    g_lifecycle = VerificationGates.lifecycle_gate(
        closing_date_str="2023-08-31",
        reference_date="2026-10-13",
    )
    assert g_lifecycle.status == "FAIL"
