import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

backend_path = os.path.abspath("backend")
app_path = os.path.join(backend_path, "app")
sys.path.insert(0, backend_path)
sys.path.insert(0, app_path)

from app.db.database import SessionLocal
from app.db.models import Scholarship, FieldEvidence, VerificationRecord

db = SessionLocal()
records = db.query(Scholarship).order_by(Scholarship.id.asc()).all()
print(f"Total scholarships in database: {len(records)}\n")

for s in records:
    print(f"#{s.id:02d} [{s.source_category}] Status: {s.verification_status:<15} Score: {s.confidence_score}% Lifecycle: {s.lifecycle_status}")
    print(f"     Title:    {s.name}")
    print(f"     Provider: {s.provider}")
    print(f"     URL:      {s.official_source_url}")
    print(f"     Evidence: {len(s.evidence_records)} items")
    print("-" * 75)

print("\nSummary by Verification Status:")
for status in ["VERIFIED", "REVIEW_REQUIRED"]:
    count = sum(1 for s in records if s.verification_status == status)
    print(f"  {status}: {count}")

print("\nSummary by Category:")
cats = {}
for s in records:
    cats[s.source_category] = cats.get(s.source_category, 0) + 1
for cat, count in cats.items():
    print(f"  {cat}: {count}")

db.close()
