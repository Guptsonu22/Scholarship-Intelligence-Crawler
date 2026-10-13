import os
import sys
import json
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend and backend/app are in sys.path
backend_path = os.path.abspath("backend")
app_path = os.path.join(backend_path, "app")
sys.path.insert(0, backend_path)
sys.path.insert(0, app_path)

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.db.models import CandidateURL, CrawlRun, CrawlAttempt, Scholarship, FieldEvidence, VerificationRecord
from app.services.crawling.crawler_service import CrawlerService
from app.services.extraction.extraction_service import ExtractionService
from app.services.extraction.page_assessor import PageAssessor
from app.services.verification.verification_engine import VerificationEngine
from app.services.verification.source_classifier import SourceClassifier

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Ensure seeds and schema
init_db()

TARGET_SCHOLARSHIPS = [
    # --- 1. Central Government ---
    {
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Post Graduate (PG) Scholarship Scheme",
    },
    {
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Pragati Scholarship Scheme for Girls",
    },
    {
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/Saksham/General-Instructions",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Saksham Scholarship Scheme for Differently-Abled Students",
    },
    {
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/Swanath/General-Instructions",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Swanath Scholarship Scheme for Orphans and Wards of Martyrs",
    },
    {
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/ADF-Scheme",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Doctoral Fellowship (ADF) Scheme",
    },
    {
        "url": "https://aicte.gov.in/schemes/students-development-schemes/aicte-yashasvi-scholarship-scheme",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Yashasvi Scholarship Scheme for Core Technical Branches",
    },
    {
        "url": "https://www.aicte-india.org/bureaus/jk",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "AICTE Prime Minister's Special Scholarship Scheme (PMSSS) for J&K and Ladakh",
    },
    {
        "url": "https://csirhrdg.res.in/Home/Index/1/Default/1749/58",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "CSIR Junior Research Fellowship (JRF-NET) and SRF Scheme",
    },
    {
        "url": "https://csirhrdg.res.in/Home/Index/1/InPage/52/24/37",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "CSIR Partial Financial Assistance Scheme for Young Scientists",
    },
    {
        "url": "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "UGC Post-Graduate Indira Gandhi Scholarship for Single Girl Child",
    },
    {
        "url": "https://overseas.tribal.gov.in/",
        "category": "CENTRAL_GOVERNMENT",
        "anchor": "National Overseas Scholarship for Scheduled Tribe (ST) Students",
    },

    # --- 2. State Government ---
    {
        "url": "https://oasis.gov.in/",
        "category": "STATE_GOVERNMENT",
        "anchor": "West Bengal OASIS Pre-Matric and Post-Matric Scholarship Scheme",
    },
    {
        "url": "https://sje.rajasthan.gov.in/Default.aspx?PageID=346",
        "category": "STATE_GOVERNMENT",
        "anchor": "Rajasthan Social Justice Post-Matric Scholarship Scheme for SC/ST/SBC/OBC",
    },

    # --- 3. Universities & Premier Institutions ---
    {
        "url": "https://www.iitk.ac.in/dora/scholarships",
        "category": "UNIVERSITY",
        "anchor": "IIT Kanpur Merit-cum-Means (MCM) and Donor Scholarships",
    },
    {
        "url": "https://azimpremjiuniversity.edu.in/undergraduate/financial-aid",
        "category": "UNIVERSITY",
        "anchor": "Azim Premji University Need-Based Financial Aid and Scholarship",
    },
    {
        "url": "https://www.iitbbs.ac.in/scholarship.php",
        "category": "UNIVERSITY",
        "anchor": "IIT Bhubaneswar Merit-cum-Means (MCM) Scholarship and Tuition Fee Remission",
    },
    {
        "url": "https://www.bitsadmission.com/",
        "category": "UNIVERSITY",
        "anchor": "BITS Pilani Institute Merit and Merit-cum-Means Scholarships",
    },

    # --- 4. Corporate CSR & Philanthropic Trusts ---
    {
        "url": "https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants",
        "category": "CORPORATE_CSR",
        "anchor": "JN Tata Endowment for the Higher Education of Indians",
    },
    {
        "url": "https://pg.nsfoundation.co.in/",
        "category": "TRUST_FOUNDATION",
        "anchor": "Narotam Sekhsaria Foundation Postgraduate Scholarship Programme",
    },
    {
        "url": "https://www.sitaramjindalfoundation.org/scholarships.php",
        "category": "TRUST_FOUNDATION",
        "anchor": "Sitaram Jindal Foundation Scholarship Scheme for Degree and Professional Courses",
    },
    {
        "url": "https://www.adityabirlascholars.net/",
        "category": "CORPORATE_CSR",
        "anchor": "Aditya Birla Group Scholarships for Engineering and Management",
    },
    {
        "url": "https://ongcfoundation.org/",
        "category": "CORPORATE_CSR",
        "anchor": "ONGC Foundation Scholarship Scheme for Meritorious Students",
    },
    {
        "url": "https://kotakeducation.org/",
        "category": "CORPORATE_CSR",
        "anchor": "Kotak Kanya Scholarship Scheme for Higher Education",
    },
    {
        "url": "https://www.persistentfoundation.org/",
        "category": "CORPORATE_CSR",
        "anchor": "Persistent Foundation Kiran Girls Scholarship Scheme",
    },
]

def main():
    db = SessionLocal()
    crawler = CrawlerService()
    extractor = ExtractionService()

    try:
        print("=== INITIATING PHASE 6 ETHICAL CRAWL & INGESTION ===")
        # Create a CrawlRun audit log
        crawl_run = CrawlRun(status="RUNNING")
        db.add(crawl_run)
        db.commit()
        db.refresh(crawl_run)

        processed = 0
        extracted_scholarships = []

        for item in TARGET_SCHOLARSHIPS:
            target_url = item["url"]
            cat = item["category"]
            anchor = item["anchor"]

            # 1. Candidate URL upsert
            cand = db.query(CandidateURL).filter_by(normalized_url=target_url).first()
            if not cand:
                cand = CandidateURL(
                    url=target_url,
                    normalized_url=target_url,
                    discovery_source_url="PHASE_6_OFFICIAL_DISCOVERY",
                    discovery_method="OFFICIAL_SEED",
                    source_category=cat,
                    anchor_text=anchor,
                    relevance_score=0.95,
                    status="QUEUED",
                    is_official_source=True,
                )
                db.add(cand)
                db.commit()
                db.refresh(cand)

            print(f"\nProcessing [{cat}] {anchor} -> {target_url}")
            
            # 2. Fetch using crawler service (ethical HTTP client)
            attempt = crawler.crawl_candidate(
                db=db,
                candidate=cand,
                crawl_run_id=crawl_run.id,
                respect_robots=False, # Official source probing with research headers
            )

            if attempt.status != "SUCCESS" or not attempt.raw_html:
                print(f"  [FETCH FAILED] Status={attempt.status}, Error={attempt.error_reason}")
                continue

            # 3. Assess and Extract structured data with evidence
            page_type, reason = PageAssessor.assess_page(attempt.raw_html, target_url)
            print(f"  [ASSESSMENT] {page_type}: {reason}")

            # If page is SCHOLARSHIP_DETAIL or has scheme content, process candidate
            scholarship, page_result = extractor.process_candidate(
                db=db,
                candidate=cand,
                html=attempt.raw_html,
                content_hash=attempt.content_hash,
                crawl_attempt_id=attempt.id,
            )

            if scholarship:
                print(f"  [EXTRACTED] #{scholarship.id}: '{scholarship.name}'")
                print(f"    Provider: '{scholarship.provider}' | Benefit: '{scholarship.amount_benefit}'")
                print(f"    Evidence count: {len(scholarship.evidence_records)}")
                
                # 4. Verify scholarship using deterministic VerificationEngine
                rec = VerificationEngine.verify_scholarship(scholarship.id, db)
                print(f"    Score: {rec.confidence_score}% | Status: {rec.verification_status} | Lifecycle: {rec.lifecycle_status}")
                extracted_scholarships.append(scholarship)
                processed += 1
            else:
                print(f"  [SKIPPED EXTRACTION] Result={page_result}")

        # Complete crawl run
        crawl_run.status = "COMPLETED"
        crawl_run.pages_crawled = processed
        db.commit()

        # Re-run verify_all to update summary
        VerificationEngine.verify_all(db)

        # Print Live Statistics
        summary = VerificationEngine.get_summary(db)
        total_schol = db.query(Scholarship).count()
        verified_count = db.query(Scholarship).filter(Scholarship.verification_status == "VERIFIED").count()
        review_count = db.query(Scholarship).filter(Scholarship.verification_status == "REVIEW_REQUIRED").count()
        evidence_count = db.query(FieldEvidence).count()

        print("\n" + "=" * 65)
        print("=== PHASE 6 CRAWL & VERIFICATION SUMMARY ===")
        print(f"Total Scholarships in Database: {total_schol}")
        print(f"VERIFIED Opportunities (>=95% + all 7 gates PASS): {verified_count}")
        print(f"REVIEW_REQUIRED / EXPIRED: {review_count}")
        print(f"Field-Level Evidence Records: {evidence_count}")
        print(f"Verification Records in Audit Trail: {db.query(VerificationRecord).count()}")
        print("\nVerification Summary Payload:")
        print(json.dumps(summary, indent=2))

    finally:
        db.close()

if __name__ == "__main__":
    main()
