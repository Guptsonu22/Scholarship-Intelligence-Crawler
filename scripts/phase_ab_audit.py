"""
Phase A + B comprehensive environment and database audit script.
Read-only database access throughout.
"""
import sys
import os
import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / 'data' / 'scholarships.db'

print("=" * 70)
print("PHASE A: REPOSITORY & ENVIRONMENT AUDIT")
print("=" * 70)

# Python/Node versions
venv_py = str(ROOT / 'backend' / '.venv' / 'Scripts' / 'python.exe')
res = subprocess.run([venv_py, '--version'], capture_output=True, text=True)
print(f"Venv Python: {res.stdout.strip()}")

# Directory structure
print("\n--- Top-level files ---")
for p in sorted(ROOT.iterdir()):
    if p.name not in {'.git', '__pycache__', 'node_modules'}:
        if p.is_dir():
            print(f"  DIR:  {p.name}/")
        else:
            print(f"  FILE: {p.name}  ({p.stat().st_size} bytes)")

# Check git status
res = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd=str(ROOT))
print(f"\n--- Git status (short) ---")
print(res.stdout or "(clean)")

# Check .gitignore covers secrets
gitignore_path = ROOT / '.gitignore'
gi_text = gitignore_path.read_text()
secret_patterns = ['.env', '*.db', 'node_modules', '.venv', 'dist/']
print("\n--- .gitignore secret coverage ---")
for pat in secret_patterns:
    covered = pat in gi_text
    print(f"  '{pat}': {'COVERED' if covered else 'NOT COVERED'}")

# Check .env NOT tracked
res = subprocess.run(['git', 'ls-files', '--error-unmatch', '.env'],
                     capture_output=True, cwd=str(ROOT))
print(f"  '.env' tracked by git: {res.returncode == 0} (should be False)")

# Docs existence check
print("\n--- Documentation files ---")
docs = [
    ROOT / 'README.md',
    ROOT / 'docs' / 'architecture.md',
    ROOT / 'docs' / 'technical_note.md',
    ROOT / 'docs' / 'demo_walkthrough.md',
    ROOT / '.env.example',
]
for d in docs:
    exists = d.exists()
    size = d.stat().st_size if exists else 0
    print(f"  {d.relative_to(ROOT)}: {'EXISTS' if exists else 'MISSING'} ({size} bytes)")

print("\n" + "=" * 70)
print("PHASE B: DATABASE INTEGRITY AUDIT (READ-ONLY)")
print("=" * 70)

conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
c = conn.cursor()

# Table list
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
print(f"\nTables ({len(tables)}): {tables}")

# Row counts
print("\n--- Row counts ---")
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {c.fetchone()[0]}")

# Scholarships detail
c.execute("""
    SELECT id, name, provider, official_source_url, verification_status,
           confidence_score, lifecycle_status, closing_date, source_category
    FROM scholarships ORDER BY id
""")
schols = c.fetchall()
print(f"\n--- All {len(schols)} Scholarship Records ---")
for s in schols:
    sid, name, prov, url, vstatus, score, lstatus, dl, cat = s
    print(f"  #{sid:2d} | {vstatus:<16} | {score}% | {lstatus:<10} | [{cat[:12]:<12}] | {name[:38]}")

# Duplicate checks
c.execute("SELECT name, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(name)) HAVING COUNT(*) > 1")
dup_names = c.fetchall()
c.execute("SELECT official_source_url, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(official_source_url)) HAVING COUNT(*) > 1")
dup_urls = c.fetchall()
print(f"\n--- Duplicate check ---")
print(f"  Duplicate names: {dup_names or 'NONE'}")
print(f"  Duplicate URLs:  {dup_urls or 'NONE'}")

# Evidence coverage for CRITICAL fields
c.execute("""
    SELECT s.id, s.name, s.verification_status,
           COUNT(CASE WHEN fe.field_name='name' AND fe.is_current=1 THEN 1 END) as has_name,
           COUNT(CASE WHEN fe.field_name='provider' AND fe.is_current=1 THEN 1 END) as has_prov,
           COUNT(CASE WHEN fe.field_name='amount_benefit' AND fe.is_current=1 THEN 1 END) as has_amt,
           COUNT(CASE WHEN fe.field_name='eligibility_summary' AND fe.is_current=1 THEN 1 END) as has_elig,
           COUNT(CASE WHEN fe.is_current=1 THEN 1 END) as total_ev
    FROM scholarships s
    LEFT JOIN field_evidence fe ON s.id = fe.scholarship_id
    GROUP BY s.id
    ORDER BY s.id
""")
ev_cov = c.fetchall()
print("\n--- Evidence coverage (name/provider/amount/eligibility) ---")
for row in ev_cov:
    sid, name, vstatus, hn, hp, ha, he, tot = row
    missing = []
    if not hn: missing.append('name')
    if not hp: missing.append('provider')
    if not ha: missing.append('amount')
    if not he: missing.append('eligibility')
    status = "OK" if not missing else f"MISSING: {', '.join(missing)}"
    print(f"  #{sid:2d} | {vstatus:<15} | ev={tot:2d} | {status}")

# Orphaned evidence (no parent scholarship)
c.execute("SELECT COUNT(*) FROM field_evidence fe LEFT JOIN scholarships s ON s.id = fe.scholarship_id WHERE s.id IS NULL")
orphaned_ev = c.fetchone()[0]
print(f"\n--- Foreign key integrity ---")
print(f"  Orphaned field_evidence rows: {orphaned_ev}")

c.execute("SELECT COUNT(*) FROM verification_records vr LEFT JOIN scholarships s ON s.id = vr.scholarship_id WHERE s.id IS NULL")
orphaned_vr = c.fetchone()[0]
print(f"  Orphaned verification_record rows: {orphaned_vr}")

# Change history
c.execute("SELECT COUNT(*) FROM scholarship_change_history")
ch_count = c.fetchone()[0]
print(f"\n--- Change history rows: {ch_count} ---")

# Lifecycle consistency check
print("\n--- Lifecycle vs deadline consistency ---")
c.execute("SELECT id, name, closing_date, lifecycle_status FROM scholarships WHERE closing_date IS NOT NULL")
dl_rows = c.fetchall()
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
for r in dl_rows:
    sid, name, dl, lstatus = r
    if dl and dl < today and lstatus not in ('EXPIRED', 'REVIEW_REQUIRED'):
        print(f"  INCONSISTENCY #{sid}: deadline {dl} is past but lifecycle={lstatus}")
    else:
        print(f"  #{sid}: deadline={dl}, lifecycle={lstatus} -> consistent ({today})")

conn.close()
print("\nPhase B complete. Database connection closed (read-only).")
