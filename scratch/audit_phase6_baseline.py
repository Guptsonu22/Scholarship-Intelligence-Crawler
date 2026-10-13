from app.db.database import SessionLocal
from app.db.models import Scholarship, CandidateURL, FieldEvidence, VerificationRecord, SeedSource, CrawlRun
from sqlalchemy import func

def audit():
    db = SessionLocal()
    try:
        sch_cnt = db.query(func.count(Scholarship.id)).scalar() or 0
        cand_cnt = db.query(func.count(CandidateURL.id)).scalar() or 0
        ev_cnt = db.query(func.count(FieldEvidence.id)).scalar() or 0
        ver_cnt = db.query(func.count(VerificationRecord.id)).scalar() or 0
        seed_cnt = db.query(func.count(SeedSource.id)).scalar() or 0
        runs_cnt = db.query(func.count(CrawlRun.id)).scalar() or 0

        print(f"=== PHASE 6 BASELINE DATABASE AUDIT ===")
        print(f"Total Scholarships: {sch_cnt}")
        print(f"Total Candidate URLs: {cand_cnt}")
        print(f"Total Field Evidence: {ev_cnt}")
        print(f"Total Verification Records: {ver_cnt}")
        print(f"Total Seed Sources: {seed_cnt}")
        print(f"Total Crawl Runs: {runs_cnt}")

        print("\n--- Current Scholarships ---")
        for s in db.query(Scholarship).all():
            print(f"ID #{s.id}: \"{s.name}\" | Provider: \"{s.provider}\" | Status: {s.verification_status} | Score: {s.confidence_score} | Lifecycle: {s.lifecycle_status} | Source: {s.official_source_url}")

        print("\n--- Seed Sources in DB ---")
        for ss in db.query(SeedSource).all():
            print(f"Seed #{ss.id}: {ss.name} [{ss.category}] -> {ss.base_url}")
    finally:
        db.close()

if __name__ == "__main__":
    audit()
