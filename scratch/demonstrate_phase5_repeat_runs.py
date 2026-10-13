import json
import logging
import time
from datetime import datetime
from sqlalchemy import select, func
from app.db.database import SessionLocal
from app.db.models import (
    Scholarship,
    CandidateURL,
    FieldEvidence,
    VerificationRecord,
    ScholarshipChangeHistory,
    CrawlRun,
)
from app.services.crawling.scheduler import scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase5_demonstration")

def get_db_metrics():
    db = SessionLocal()
    try:
        scholarships_count = db.query(func.count(Scholarship.id)).scalar() or 0
        candidates_count = db.query(func.count(CandidateURL.id)).scalar() or 0
        crawled_candidates_count = db.query(func.count(CandidateURL.id)).filter(
            CandidateURL.status.in_(["FETCHED", "PARSED", "EXTRACTED"])
        ).scalar() or 0
        evidence_count = db.query(func.count(FieldEvidence.id)).scalar() or 0
        verification_count = db.query(func.count(VerificationRecord.id)).scalar() or 0
        changes_count = db.query(func.count(ScholarshipChangeHistory.id)).scalar() or 0
        crawl_runs_count = db.query(func.count(CrawlRun.id)).scalar() or 0

        active_scholarships = []
        for s in db.query(Scholarship).all():
            active_scholarships.append({
                "id": s.id,
                "name": s.name,
                "provider": s.provider,
                "status": s.verification_status,
                "confidence_score": s.confidence_score,
                "closing_date": str(s.closing_date) if s.closing_date else None,
                "source_url": s.official_source_url,
            })

        return {
            "scholarships_count": scholarships_count,
            "candidates_count": candidates_count,
            "crawled_candidates_count": crawled_candidates_count,
            "evidence_count": evidence_count,
            "verification_count": verification_count,
            "changes_count": changes_count,
            "crawl_runs_count": crawl_runs_count,
            "scholarships": active_scholarships,
        }
    finally:
        db.close()

def main():
    print("=" * 75)
    print("PHASE 5 REPEAT-RUN LIVE DEMONSTRATION & CHANGE AUDIT")
    print("=" * 75)
    
    # 1. Baseline metrics before any runs
    initial_metrics = get_db_metrics()
    print("\n--- BASELINE METRICS (BEFORE RUN 1) ---")
    print(json.dumps(initial_metrics, indent=2))
    
    # 2. Execute Run 1 (max_candidates=1 to prioritize existing scholarship source)
    print("\n>>> EXECUTING REPEAT CYCLE 1 (max_candidates=1)...")
    db1 = SessionLocal()
    try:
        run_1_result = scheduler.run_pipeline(db=db1, max_candidates=1)
    finally:
        db1.close()
    print("Run 1 Result:")
    print(json.dumps(run_1_result, indent=2))
    
    metrics_after_run_1 = get_db_metrics()
    print("\n--- METRICS AFTER RUN 1 ---")
    print(json.dumps(metrics_after_run_1, indent=2))
    
    # Wait polite pause
    print("\nWaiting polite interval before Cycle 2...")
    time.sleep(2)
    
    # 3. Execute Run 2 (revisit same source)
    print("\n>>> EXECUTING REPEAT CYCLE 2 (max_candidates=1)...")
    db2 = SessionLocal()
    try:
        run_2_result = scheduler.run_pipeline(db=db2, max_candidates=1)
    finally:
        db2.close()
    print("Run 2 Result:")
    print(json.dumps(run_2_result, indent=2))
    
    metrics_after_run_2 = get_db_metrics()
    print("\n--- METRICS AFTER RUN 2 ---")
    print(json.dumps(metrics_after_run_2, indent=2))
    
    print("\n" + "=" * 75)
    print("DEMONSTRATION SUMMARY")
    print("=" * 75)
    print(f"Run 1 processed: {run_1_result['candidates_processed']}, crawled: {run_1_result['pages_crawled']}, unchanged: {run_1_result['pages_unchanged']}, changes: {run_1_result['changes_detected']}")
    print(f"Run 2 processed: {run_2_result['candidates_processed']}, crawled: {run_2_result['pages_crawled']}, unchanged: {run_2_result['pages_unchanged']}, changes: {run_2_result['changes_detected']}")
    print(f"Initial Scholarships: {initial_metrics['scholarships_count']} -> Post Run 2: {metrics_after_run_2['scholarships_count']}")
    print(f"Initial Change Audit Entries: {initial_metrics['changes_count']} -> Post Run 2: {metrics_after_run_2['changes_count']}")
    print("=" * 75)

if __name__ == "__main__":
    main()
