import pytest
from app.services.extraction.page_assessor import PageAssessor


def test_assess_scholarship_detail_page():
    html = """
    <html>
    <head><title>National Fellowship Scheme for Higher Education</title></head>
    <body>
        <h1>National Fellowship for Scheduled Tribe Students</h1>
        <p>Eligibility: Candidates must have taken admission in regular M.Phil/Ph.D Course.</p>
        <p>Financial Assistance: Fellowship amount is ₹31,000 per month for JRF.</p>
        <p>Application Deadline: 31st October 2026.</p>
    </body>
    </html>
    """
    page_type, reason = PageAssessor.assess_page(html, "https://scholarships.gov.in/schemes/national-fellowship")
    assert page_type == "SCHOLARSHIP_DETAIL"
    assert "opportunity details" in reason.lower()


def test_assess_application_portal_login():
    html = """
    <html>
    <head><title>Student Login - National Scholarship Portal</title></head>
    <body>
        <h2>One Time Registration (OTR) Login</h2>
        <form>
            <input type="text" name="userid" placeholder="Application ID" />
            <input type="password" name="password" placeholder="Password" />
            <input type="text" name="captcha" />
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
    page_type, reason = PageAssessor.assess_page(html, "https://scholarships.gov.in/login")
    assert page_type == "APPLICATION_PORTAL"
    assert "authentication" in reason.lower()


def test_assess_scholarship_listing_page():
    html = """
    <html>
    <head><title>Schemes on NSP</title></head>
    <body>
        <h1>List of Scholarships</h1>
        <table>
            <tr><th>Scheme</th><th>Ministry</th></tr>
            <tr><td>Pre-Matric Scholarship Scheme</td><td>Ministry of Minority Affairs</td></tr>
            <tr><td>Post-Matric Scholarship Scheme</td><td>Ministry of Minority Affairs</td></tr>
            <tr><td>Merit Cum Means Scholarship</td><td>Ministry of Minority Affairs</td></tr>
        </table>
    </body>
    </html>
    """
    page_type, reason = PageAssessor.assess_page(html, "https://scholarships.gov.in/All-Scholarships")
    assert page_type == "SCHOLARSHIP_LISTING"
    assert "directory" in reason.lower() or "multiple" in reason.lower()


def test_assess_generic_portal_homepage():
    html = """
    <html>
    <head><title>National Scholarship Portal</title></head>
    <body>
        <nav><a href="/about">About Us</a><a href="/contact">Contact</a></nav>
        <div>Welcome to the Government of India unified portal.</div>
        <footer>Copyright 2026 National Informatics Centre</footer>
    </body>
    </html>
    """
    page_type, reason = PageAssessor.assess_page(html, "https://scholarships.gov.in/home")
    assert page_type == "GENERIC_PAGE"
    assert "generic" in reason.lower()


def test_assess_insufficient_evidence():
    html = "<html><body><p>No content available.</p></body></html>"
    page_type, reason = PageAssessor.assess_page(html, "https://example.com/empty")
    assert page_type == "INSUFFICIENT_EVIDENCE"
