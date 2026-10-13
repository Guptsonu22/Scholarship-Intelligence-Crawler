from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import Base, engine, SessionLocal
from app.db.models import (
    SystemInfo,
    SeedSource,
    SourceClassification,
    CandidateURL,
    CrawlRun,
    CrawlAttempt,
    Scholarship,
    FieldEvidence,
    ExtractionRun,
    VerificationRecord,
)

DEFAULT_SEEDS = [
    # 1. Central Government
    {
        "name": "National Scholarship Portal (NSP)",
        "base_url": "https://scholarships.gov.in/",
        "category": "CENTRAL_GOVERNMENT",
        "description": "Central government unified portal for major national scholarship schemes (Ministry of Minority Affairs, Social Justice, Tribal Affairs, etc.).",
        "scrape_depth": 2,
    },
    {
        "name": "UGC Scholarships and Fellowships",
        "base_url": "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx",
        "category": "CENTRAL_GOVERNMENT",
        "description": "University Grants Commission official listings of central fellowships, research grants, and student scholarships.",
        "scrape_depth": 2,
    },
    {
        "name": "AICTE Student Development Schemes",
        "base_url": "https://www.aicte-india.org/schemes/students-development-schemes",
        "category": "CENTRAL_GOVERNMENT",
        "description": "All India Council for Technical Education schemes (Pragati, Saksham, Swanath).",
        "scrape_depth": 2,
    },
    # 2. State Government
    {
        "name": "Karnataka State Scholarship Portal (SSP)",
        "base_url": "https://ssp.postmatric.karnataka.gov.in/",
        "category": "STATE_GOVERNMENT",
        "description": "Official post-matric and pre-matric state scholarship portal of Government of Karnataka.",
        "scrape_depth": 2,
    },
    {
        "name": "MahaDBT Maharashtra",
        "base_url": "https://mahadbt.maharashtra.gov.in/",
        "category": "STATE_GOVERNMENT",
        "description": "Government of Maharashtra direct benefit transfer and state scholarship portal.",
        "scrape_depth": 2,
    },
    {
        "name": "UP Scholarship Portal",
        "base_url": "https://scholarship.up.gov.in/",
        "category": "STATE_GOVERNMENT",
        "description": "Government of Uttar Pradesh online scholarship and fee reimbursement system.",
        "scrape_depth": 2,
    },
    # 3. Universities & Premier Institutions
    {
        "name": "IISc Bangalore Financial Support",
        "base_url": "https://iisc.ac.in/admissions/financial-support/",
        "category": "UNIVERSITY",
        "description": "Indian Institute of Science official student fellowships and financial assistance.",
        "scrape_depth": 2,
    },
    {
        "name": "IIT Bombay Scholarships",
        "base_url": "https://www.iitb.ac.in/newsite/academics/scholarship.html",
        "category": "UNIVERSITY",
        "description": "Indian Institute of Technology Bombay institute merit-cum-means and donor scholarships.",
        "scrape_depth": 2,
    },
    # 4. Corporate CSR
    {
        "name": "Reliance Foundation Scholarships",
        "base_url": "https://www.reliancefoundation.org/our-work/education/scholarships",
        "category": "CORPORATE_CSR",
        "description": "Reliance Foundation undergraduate and postgraduate scholarship initiatives.",
        "scrape_depth": 2,
    },
    {
        "name": "Tata Trusts Individual Grants",
        "base_url": "https://www.tatatrusts.org/our-work/education/individual-grants-programme",
        "category": "CORPORATE_CSR",
        "description": "Tata Trusts financial assistance and education support programmes.",
        "scrape_depth": 2,
    },
    {
        "name": "ONGC Foundation Education Support",
        "base_url": "https://ongcfoundation.org/",
        "category": "CORPORATE_CSR",
        "description": "Oil and Natural Gas Corporation CSR education grants and scholarship schemes.",
        "scrape_depth": 2,
    },
    # 5. Philanthropic Trusts & Foundations
    {
        "name": "K.C. Mahindra Education Trust",
        "base_url": "https://www.kcmet.org/what-we-do-scholarships.aspx",
        "category": "TRUST_FOUNDATION",
        "description": "K.C. Mahindra scholarships for post-graduate studies abroad and domestic diploma/degree awards.",
        "scrape_depth": 2,
    },
    {
        "name": "Narotam Sekhsaria Foundation",
        "base_url": "https://pg.nsfoundation.co.in/",
        "category": "TRUST_FOUNDATION",
        "description": "Interest-free loan scholarships for postgraduate studies in India and abroad.",
        "scrape_depth": 2,
    },
    {
        "name": "Sitaram Jindal Foundation",
        "base_url": "https://www.sitaramjindalfoundation.org/scholarships.php",
        "category": "TRUST_FOUNDATION",
        "description": "Sitaram Jindal Foundation educational merit-cum-means scholarships.",
        "scrape_depth": 2,
    },
    # 6. Aggregator (Discovery feed only - requires primary source)
    {
        "name": "Buddy4Study Featured Portal",
        "base_url": "https://www.buddy4study.com/scholarships",
        "category": "AGGREGATOR",
        "description": "Scholarship listing feed used for candidate discovery; flagged as aggregator requiring primary source.",
        "scrape_depth": 1,
    },
]


def init_db() -> None:
    """Initialize database tables, apply safe migrations, and seed default sources."""
    # Create all newly declared tables
    Base.metadata.create_all(bind=engine)

    # Safe column migration check for SQLite
    try:
        with engine.connect() as conn:
            # crawl_attempts
            res = conn.execute(text("PRAGMA table_info(crawl_attempts)"))
            cols = [row[1] for row in res.fetchall()]
            if cols and "raw_html" not in cols:
                conn.execute(text("ALTER TABLE crawl_attempts ADD COLUMN raw_html TEXT"))

            # scholarships
            res = conn.execute(text("PRAGMA table_info(scholarships)"))
            cols = [row[1] for row in res.fetchall()]
            if cols and "verification_status" not in cols:
                conn.execute(text("ALTER TABLE scholarships ADD COLUMN verification_status VARCHAR(50) DEFAULT 'UNVERIFIED'"))
            if cols and "confidence_score" not in cols:
                conn.execute(text("ALTER TABLE scholarships ADD COLUMN confidence_score FLOAT"))

            # field_evidence
            res = conn.execute(text("PRAGMA table_info(field_evidence)"))
            cols = [row[1] for row in res.fetchall()]
            if cols and "quality_rating" not in cols:
                conn.execute(text("ALTER TABLE field_evidence ADD COLUMN quality_rating VARCHAR(50) DEFAULT 'SUPPORTED'"))

            conn.commit()
    except Exception:
        pass

    # Populate default seed sources if not present
    db: Session = SessionLocal()
    try:
        existing_count = db.query(SeedSource).count()
        if existing_count == 0:
            for seed in DEFAULT_SEEDS:
                record = SeedSource(**seed)
                db.add(record)
            db.commit()
    finally:
        db.close()
