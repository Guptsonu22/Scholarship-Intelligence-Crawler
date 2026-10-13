import pytest
from app.services.extraction.field_extractor import FieldExtractor

DETAILED_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Post Matric Scholarship for SC Students - National Scholarship Portal</title>
</head>
<body>
    <header>
        <div class="gov-title">Ministry of Social Justice and Empowerment</div>
    </header>
    <main>
        <h1>Post Matric Scholarship for SC Students</h1>
        <div class="overview">
            <p>Offered by the Ministry of Social Justice and Empowerment for scheduled caste scholars across India.</p>
        </div>
        <section class="eligibility">
            <h2>Eligibility Criteria</h2>
            <p>Open for girl students and boy students pursuing Undergraduate / Bachelor's degrees.</p>
            <p>Annual family income should not exceed ₹2,50,000 per annum.</p>
            <p>Candidate must belong to SC category.</p>
        </section>
        <section class="benefits">
            <h2>Financial Assistance</h2>
            <p>Scholarship amount is ₹50,000 per annum including maintenance allowance.</p>
        </section>
        <section class="dates">
            <h2>Important Dates</h2>
            <p>Last date to apply is 31st October 2026.</p>
        </section>
        <section class="docs">
            <h2>Required Documents</h2>
            <ul>
                <li>Aadhaar Card</li>
                <li>Income Certificate</li>
                <li>Caste Certificate</li>
                <li>Marksheet of qualifying examination</li>
            </ul>
        </section>
        <div class="cta">
            <a href="https://scholarships.gov.in/apply-now" class="btn">Apply Now</a>
        </div>
    </main>
</body>
</html>
"""


def test_field_extractor_extracts_all_fields():
    data = FieldExtractor.extract(DETAILED_HTML_FIXTURE, "https://scholarships.gov.in/schemes/post-matric-sc")

    assert data.name == "Post Matric Scholarship for SC Students"
    assert data.provider == "Ministry of Social Justice and Empowerment"
    assert data.amount_benefit is not None
    assert "50,000" in data.amount_benefit
    assert data.closing_date == "2026-10-31"
    assert data.course_level == "Undergraduate / Bachelor's"
    assert "2,50,000" in data.income_criteria
    assert "SC" in data.category_requirements
    assert "Aadhaar Card" in data.documents_required
    assert data.application_url == "https://scholarships.gov.in/apply-now"

    # Verify field-level evidence attachments
    field_names = [e.field_name for e in data.evidence_list]
    assert "name" in field_names
    assert "provider" in field_names
    assert "amount_benefit" in field_names
    assert "closing_date" in field_names
    assert "income_criteria" in field_names
    assert "application_url" in field_names

    # Check evidence text snippet
    amount_ev = next(e for e in data.evidence_list if e.field_name == "amount_benefit")
    assert "50,000" in amount_ev.evidence_text


def test_field_extractor_missing_fields_remain_none():
    minimal_html = """
    <html>
    <body>
        <h1>Tata Trusts Medical Education Grant</h1>
        <p>Supported by Tata Trusts for medical scholars.</p>
    </body>
    </html>
    """
    data = FieldExtractor.extract(minimal_html, "https://tatatrusts.org/medical")
    assert data.name == "Tata Trusts Medical Education Grant"
    assert data.provider == "Tata Trusts"
    # Unmentioned fields must remain None, never hallucinated!
    assert data.closing_date is None
    assert data.amount_benefit is None
    assert data.income_criteria is None
    assert data.application_url is None
