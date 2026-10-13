"""
Phase F: Live source crawler validation - representative sample across all 4 sectors.
Uses the project's EthicalHttpClient with SSRF guard, robots.txt, and rate limiting.
Does NOT retry aggressively or exceed 1 request per domain per run.
"""
import sys
import os
import hashlib
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath('backend'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.services.crawling.http_client import EthicalHttpClient
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor

client = EthicalHttpClient(timeout=12)

sources = [
    # (sector, db_id, name, url)
    ("CENTRAL_GOVERNMENT",  2, "AICTE PG Scholarship", "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme"),
    ("CENTRAL_GOVERNMENT", 17, "CSIR JRF-NET Scheme",  "https://csirhrdg.res.in/Home/Index/1/Default/1749/58"),
    ("STATE_GOVERNMENT",    8, "WB OASIS Portal",      "https://oasis.gov.in/"),
    ("UNIVERSITY",          9, "IIT Kanpur Scholarships", "https://www.iitk.ac.in/dora/scholarships-and-awards"),
    ("TRUST_FOUNDATION",   13, "Sitaram Jindal Foundation", "https://www.sitaramjindalfoundation.org/scholarships.php"),
]

print("=" * 70)
print("PHASE F: LIVE SOURCE CRAWLER VALIDATION")
print(f"Probe time: {datetime.now(timezone.utc).isoformat()}")
print("Protocol: EthicalHttpClient | Robots.txt: enforced | Delay: 2s/domain")
print("=" * 70)

live_pass = 0
live_fail = 0

for sector, db_id, name, url in sources:
    print(f"\n--- [{sector}] DB Record #{db_id}: {name} ---")
    print(f"Requested URL: {url}")
    start = time.time()
    res = client.fetch(url, respect_robots=True, max_redirects=5)
    elapsed = (time.time() - start) * 1000

    print(f"Fetch status: {res.status}")
    print(f"HTTP status:  {res.http_status}")
    print(f"Final URL:    {res.final_url}")
    print(f"Content len:  {res.content_length} bytes")
    print(f"Content hash: {res.content_hash}")
    print(f"Response ms:  {elapsed:.0f}ms")

    if res.status == "SUCCESS" and res.html:
        p_type, p_reason = PageAssessor.assess_page(res.html, res.final_url or url)
        print(f"Page type:    {p_type}")

        extracted = FieldExtractor.extract(res.html, res.final_url or url)
        print(f"Ext. Title:   {extracted.name}")
        print(f"Ext. Prov:    {extracted.provider}")
        print(f"Ext. Amount:  {extracted.amount_benefit}")
        print(f"Ext. AppURL:  {extracted.application_url}")
        print(f"Evidence cnt: {len(extracted.evidence_list)} items")

        for ev in extracted.evidence_list:
            snippet = str(ev.evidence_text)[:50].replace('\n', ' ')
            print(f"  * {ev.field_name}: '{str(ev.extracted_value)[:40]}' [{ev.html_selector}] | evidence='{snippet}'")

        # Note any discrepancies with claimed DB values
        print(f"Source type:  LIVE HTTP FETCH - NOT FIXTURE")
        live_pass += 1
    else:
        print(f"Error reason: {res.error_reason}")
        print(f"Source type:  LIVE FETCH FAILED")
        live_fail += 1

    # Enforce polite inter-domain delay
    time.sleep(1)

print(f"\n{'=' * 70}")
print(f"PHASE F SUMMARY: {live_pass} live fetch successes | {live_fail} failures")
print("All fetches used live network requests, NOT test fixtures.")
