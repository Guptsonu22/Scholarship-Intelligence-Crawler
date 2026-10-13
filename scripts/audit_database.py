import sys
import sqlite3
import json
from collections import defaultdict
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM scholarships")
total_schol = c.fetchone()[0]

c.execute("SELECT verification_status, COUNT(*) FROM scholarships GROUP BY verification_status")
by_verification = dict(c.fetchall())

c.execute("SELECT lifecycle_status, COUNT(*) FROM scholarships GROUP BY lifecycle_status")
by_lifecycle = dict(c.fetchall())

c.execute("SELECT COUNT(*) FROM field_evidence")
total_evidence = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM verification_records")
total_verifications = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM scholarship_change_history")
change_count = c.fetchone()[0]

c.execute("SELECT official_source_url FROM scholarships")
urls = [r[0] for r in c.fetchall()]
domains = set()
for u in urls:
    if u:
        parsed = urlparse(u)
        domains.add(parsed.netloc)

c.execute("SELECT source_category, COUNT(*) FROM scholarships GROUP BY source_category")
by_category = dict(c.fetchall())

print(f"TOTAL SCHOLARSHIPS: {total_schol}")
print(f"BY VERIFICATION STATUS: {by_verification}")
print(f"BY LIFECYCLE: {by_lifecycle}")
print(f"BY SOURCE CATEGORY: {by_category}")
print(f"TOTAL FIELD EVIDENCE: {total_evidence}")
print(f"TOTAL VERIFICATION RECORDS: {total_verifications}")
print(f"TOTAL CHANGE HISTORY ROWS: {change_count}")
print(f"DISTINCT PRIMARY-SOURCE DOMAINS ({len(domains)}): {sorted(list(domains))}")

c.execute("SELECT id, name, provider, official_source_url, verification_status, confidence_score, lifecycle_status, closing_date FROM scholarships ORDER BY id")
rows = c.fetchall()
print("\n--- ALL SCHOLARSHIP RECORDS (21) ---")
for r in rows:
    print(f"#{r[0]:2d} | {r[1][:38]:<38} | {r[2][:20]:<20} | Ver={r[4]:<15} | Score={r[5]}% | Life={r[6]:<10} | DL={r[7]}")

print("\n--- DETAILED AUDIT OF ALL 10 VERIFIED RECORDS ---")
c.execute("SELECT s.id, s.name, s.provider, s.official_source_url, s.application_url, s.amount_benefit, s.closing_date, s.confidence_score, s.verification_status, s.lifecycle_status, vr.gate_results, vr.scoring_breakdown, vr.deductions_reasons FROM scholarships s LEFT JOIN verification_records vr ON s.id = vr.scholarship_id AND vr.is_latest = 1 WHERE s.verification_status='VERIFIED' ORDER BY s.id")
verified_rows = c.fetchall()

for v in verified_rows:
    s_id, name, prov, src_url, app_url, amt, dl, score, ver_st, life_st, gate_json, score_json, ded_json = v
    gates = json.loads(gate_json) if gate_json else {}
    breakdown = json.loads(score_json) if score_json else {}
    
    # Check evidence attached
    c.execute("SELECT field_name, excerpt_or_text, quality_rating FROM (SELECT field_name, evidence_text as excerpt_or_text, quality_rating FROM field_evidence WHERE scholarship_id=?)", (s_id,))
    ev_items = c.fetchall()
    
    all_pass = all(gate.get('passed', False) for gate in gates.values())
    
    print(f"\nID: #{s_id:2d} | Title: {name}")
    print(f"  Provider: {prov}")
    print(f"  Source URL: {src_url}")
    print(f"  App URL: {app_url}")
    print(f"  Amount: {amt} | Deadline: {dl}")
    print(f"  Score: {score}% | Status: {ver_st} | Lifecycle: {life_st}")
    print(f"  Mandatory Gates ({len(gates)} gates, All pass: {all_pass}):")
    for gname, gval in gates.items():
        print(f"    - {gname}: passed={gval.get('passed')} (reason: {gval.get('reason')})")
    print(f"  Evidence count: {len(ev_items)} attached")
    fields_with_ev = [e[0] for e in ev_items]
    print(f"  Evidence fields: {', '.join(fields_with_ev)}")

print("\n--- DUPLICATE / SUSPICIOUS SIMILARITY CHECK ---")
c.execute("SELECT name, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(name)) HAVING COUNT(*) > 1")
dup_names = c.fetchall()
print(f"Duplicate names: {dup_names}")

c.execute("SELECT official_source_url, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(official_source_url)) HAVING COUNT(*) > 1")
dup_urls = c.fetchall()
print(f"Duplicate official source URLs: {dup_urls}")

print("\n--- CHANGE HISTORY ENTRIES ---")
c.execute("SELECT id, scholarship_id, field_name, previous_value, new_value, change_classification, detection_timestamp FROM scholarship_change_history ORDER BY id")
change_rows = c.fetchall()
print(f"Total Change Records: {len(change_rows)}")
for ch in change_rows:
    print(f"  Change #{ch[0]} on Schol #{ch[1]}: field='{ch[2]}', class='{ch[5]}'")
    print(f"    Old: {ch[3]}")
    print(f"    New: {ch[4]}")
    print(f"    At: {ch[6]}")

conn.close()
