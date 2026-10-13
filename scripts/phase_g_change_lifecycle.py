"""
Phase G: Change detection and lifecycle testing.
Uses test fixtures (not live DB writes) for the change detection core logic.
Also checks the real DB state for scheduler and lifecycle record accuracy.
"""
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import sqlite3
from app.services.lifecycle.change_detector import ChangeDetector
from app.db.database import SessionLocal
from app.db.models import Scholarship, FieldEvidence
from datetime import datetime, timezone

db = SessionLocal()

print("=" * 70)
print("PHASE G: CHANGE DETECTION & LIFECYCLE TESTING")
print("=" * 70)

# --- G1: Test change detection core logic in isolation ---
print("\n[G1] ChangeDetector unit behavior tests (fixture-based, no DB writes)")

detector = ChangeDetector()

detector = ChangeDetector()

# Test via the normalize_value utility function which is the core logic
from app.services.lifecycle.change_detector import normalize_value

cases = [
    ("name", "AICTE PG Scholarship", "AICTE PG Scholarship", False, "identical string"),
    ("name", "AICTE PG Scholarship", "  AICTE PG Scholarship  ", False, "whitespace normalized"),
    ("amount_benefit", "12400 per month", "12400 per month", False, "same value"),
    ("closing_date", "2026-12-31", "2027-01-15", True,  "genuine deadline change"),
    ("eligibility_summary", "SC/ST students", "OBC and SC/ST students", True, "substantive addition"),
]

passed = 0
for field, old, new, expect_change, label in cases:
    old_norm = normalize_value(old)
    new_norm = normalize_value(new)
    is_change = old_norm != new_norm
    status = "PASS" if is_change == expect_change else "FAIL"
    print(f"  [{status}] {field}: '{old}' -> '{new}' | expected_change={expect_change} | {label}")
    if status == "PASS":
        passed += 1

print(f"  ChangeDetector unit: {passed}/{len(cases)} passed")

# --- G2: DB lifecycle state check ---
print("\n[G2] Database lifecycle state consistency")
conn = sqlite3.connect(f'file:data/scholarships.db?mode=ro', uri=True)
c = conn.cursor()

c.execute("SELECT id, name, lifecycle_status, closing_date, verification_status FROM scholarships ORDER BY id")
rows = c.fetchall()
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
issues = []

for sid, name, lstatus, dl, vstatus in rows:
    # EXPIRED + past deadline → OK
    if dl and dl < today and lstatus == "ACTIVE":
        issues.append(f"#{sid}: past deadline {dl} but lifecycle=ACTIVE")
    # VERIFIED + EXPIRED lifecycle → inconsistent
    if vstatus == "VERIFIED" and lstatus == "EXPIRED":
        issues.append(f"#{sid}: VERIFIED but lifecycle=EXPIRED (should be REVIEW_REQUIRED)")

if issues:
    for issue in issues:
        print(f"  [ISSUE] {issue}")
else:
    print("  All lifecycle states consistent with deadlines and verification statuses.")

# --- G3: Change history count ---
c.execute("SELECT COUNT(*) FROM scholarship_change_history")
total_changes = c.fetchone()[0]
print(f"\n[G3] Change history rows: {total_changes}")
print("  (0 is expected if no recrawl has been run post-initial ingestion)")

# --- G4: Crawl runs history ---
c.execute("SELECT id, status, pages_crawled, pages_failed, candidates_discovered, started_at FROM crawl_runs ORDER BY id")
crawl_runs = c.fetchall()
print(f"\n[G4] Crawl runs ({len(crawl_runs)} total):")
for r in crawl_runs:
    cid, cstatus, cp, cf, cd, ctime = r
    print(f"  Run #{cid}: status={cstatus} | crawled={cp} | failed={cf} | discovered={cd} | time={ctime}")

# --- G5: Scheduler API live check ---
import requests
r = requests.get("http://127.0.0.1:8000/api/scheduler/status", timeout=5)
sched = r.json()
print(f"\n[G5] Scheduler API: {json.dumps(sched, indent=2)}")

conn.close()
db.close()
print("\nPhase G complete.")
