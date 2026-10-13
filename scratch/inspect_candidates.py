from app.db.database import SessionLocal
from app.db.models import CandidateURL
from collections import Counter

def check_candidates():
    db = SessionLocal()
    try:
        total = db.query(CandidateURL).count()
        status_counts = Counter(c.status for c in db.query(CandidateURL).all())
        category_counts = Counter(c.source_category for c in db.query(CandidateURL).all())
        
        print(f"Total Candidate URLs: {total}")
        print("Statuses:", dict(status_counts))
        print("Categories:", dict(category_counts))
        
        print("\nSample DISCOVERED Candidates:")
        discovered = db.query(CandidateURL).filter(CandidateURL.status == "DISCOVERED").limit(15).all()
        for c in discovered:
            print(f"#{c.id} [{c.source_category}] {c.normalized_url} (Score: {c.relevance_score}, Anchor: {c.anchor_text[:40] if c.anchor_text else 'None'})")
    finally:
        db.close()

if __name__ == "__main__":
    check_candidates()
