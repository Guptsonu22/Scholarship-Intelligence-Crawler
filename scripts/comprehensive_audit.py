import sys
import sqlite3
import json
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM scholarships")
total_schol = c.fetchone()[0]

c.execute("SELECT verification_status, COUNT(*) FROM scholarships GROUP BY verification_status")
by_ver = dict(c.fetchall())

c.execute("SELECT lifecycle_status, COUNT(*) FROM scholarships GROUP BY lifecycle_status")
by_life = dict(c.fetchall())

c.execute("SELECT COUNT(*) FROM field_evidence")
total_ev = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM verification_records")
total_vr = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM scholarship_change_history")
total_ch = c.fetchone()[0]

print("=== REPRODUCIBLE DATABASE METRICS ===")
print(f"Total distinct scholarship records: {total_schol}")
print(f"By verification status: {by_ver}")
print(f"By lifecycle status: {by_life}")
print(f"Field evidence count: {total_ev}")
print(f"Verification audit count: {total_vr}")
print(f"Change history count: {total_ch}")

# Domains and types
c.execute("SELECT official_source_url, source_category FROM scholarships")
rows = c.fetchall()
domains = set()
categories = set()
for r in rows:
    if r[0]:
        domains.add(urlparse(r[0]).netloc)
    if r[1]:
        categories.add(r[1])

print(f"Distinct primary-source domains ({len(domains)}): {sorted(list(domains))}")
print(f"Distinct source categories ({len(categories)}): {sorted(list(categories))}")

# Check duplicate names / URLs / providers
c.execute("SELECT name, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(name)) HAVING COUNT(*) > 1")
dup_names = c.fetchall()
print(f"Duplicate names: {dup_names}")

c.execute("SELECT official_source_url, COUNT(*) FROM scholarships GROUP BY LOWER(TRIM(official_source_url)) HAVING COUNT(*) > 1")
dup_urls = c.fetchall()
print(f"Duplicate official URLs: {dup_urls}")

# Check critical fields evidence coverage
# Critical fields: name, provider, amount_benefit, eligibility_summary
c.execute("""
SELECT s.id, s.name,
       COUNT(CASE WHEN fe.field_name = 'name' THEN 1 END) as has_name,
       COUNT(CASE WHEN fe.field_name = 'provider' THEN 1 END) as has_prov,
       COUNT(CASE WHEN fe.field_name = 'amount_benefit' THEN 1 END) as has_amt,
       COUNT(CASE WHEN fe.field_name = 'eligibility_summary' THEN 1 END) as has_elig
FROM scholarships s
LEFT JOIN field_evidence fe ON s.id = fe.scholarship_id AND fe.is_current = 1
GROUP BY s.id
""")
crit_coverage = c.fetchall()
missing_crit = [r for r in crit_coverage if not (r[2] and r[3] and r[4] and r[5])]
print(f"Records with missing critical field evidence: {len(missing_crit)}")

print("\n=== INDIVIDUAL AUDIT OF ALL 10 CLAIMED VERIFIED RECORDS ===")
c.execute("""
SELECT s.id, s.name, s.provider, s.official_source_url, s.application_url, 
       s.amount_benefit, s.closing_date, s.confidence_score, s.verification_status,
       s.lifecycle_status, vr.gate_results, vr.scoring_breakdown, vr.deductions_reasons
FROM scholarships s
JOIN verification_records vr ON s.id = vr.scholarship_id AND vr.is_latest = 1
WHERE s.verification_status = 'VERIFIED'
ORDER BY s.id
""")
verified_records = c.fetchall()

for idx, vr in enumerate(verified_records, 1):
    sid, name, prov, src, app, amt, dl, score, vstat, lstat, gjson, sbreak, djson = vr
    gates = json.loads(gjson) if gjson else {}
    breakdown = json.loads(sbreak) if sbreak else {}
    deductions = json.loads(djson) if djson else []
    
    # Gate check
    all_gates_pass = len(gates) == 7 and all(g.get("status") == "PASS" for g in gates.values())
    
    # Evidence items
    c.execute("SELECT field_name, extracted_value, html_selector, quality_rating, evidence_text FROM field_evidence WHERE scholarship_id=? AND is_current=1", (sid,))
    evs = c.fetchall()
    
    print(f"\n--- [VERIFIED Record {idx}/10] Scholarship #{sid} ---")
    print(f"  Title: {name}")
    print(f"  Provider: {prov}")
    print(f"  Official Source URL: {src}")
    print(f"  Application URL: {app}")
    print(f"  Amount/Benefit: {amt}")
    print(f"  Deadline: {dl}")
    print(f"  Confidence Score: {score}% (Required >=95%: {'PASS' if score >= 95.0 else 'FAIL'})")
    print(f"  Lifecycle: {lstat}")
    print(f"  All 7 Gates Pass: {all_gates_pass}")
    for gname, ginfo in gates.items():
        print(f"    * {gname}: {ginfo.get('status')} - {ginfo.get('explanation')[:70]}...")
    print(f"  Evidence Items Attached: {len(evs)}")
    for ev in evs:
        print(f"    - {ev[0]}: val='{str(ev[1])[:40]}' | rating={ev[3]} | sel='{ev[2]}'")
    if deductions:
        print(f"  Deductions: {deductions}")

conn.close()
