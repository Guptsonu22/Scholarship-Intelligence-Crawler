import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import hashlib
from datetime import datetime, timezone
from app.services.crawling.http_client import EthicalHttpClient
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

test_targets = [
    {
        "category": "CENTRAL_GOVERNMENT",
        "name": "AICTE PG Scholarship Scheme",
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme",
        "record_id": 2,
    },
    {
        "category": "STATE_GOVERNMENT",
        "name": "West Bengal OASIS Portal",
        "url": "https://oasis.gov.in/",
        "record_id": 8,
    },
    {
        "category": "UNIVERSITY",
        "name": "IIT Kanpur Scholarships",
        "url": "https://www.iitk.ac.in/dora/scholarships-and-awards",
        "record_id": 9,
    },
    {
        "category": "TRUST_FOUNDATION",
        "name": "Sitaram Jindal Foundation",
        "url": "https://www.sitaramjindalfoundation.org/scholarships.php",
        "record_id": 13,
    },
    {
        "category": "CENTRAL_GOVERNMENT",
        "name": "CSIR JRF Scheme",
        "url": "https://csirhrdg.res.in/Home/Index/1/Default/1749/58",
        "record_id": 17,
    }
]

print("=== LIVE SOURCE AUDIT (PHASE 7) ===")
print("Executing live probes using EthicalHttpClient with SSRF Guard, User-Agent, and Timeout controls...\n")

client = EthicalHttpClient(timeout=15)

for target in test_targets:
    url = target["url"]
    name = target["name"]
    cat = target["category"]
    rec_id = target["record_id"]
    now_str = datetime.now(timezone.utc).isoformat()
    
    print(f"--- Probing [{cat}] Record #{rec_id}: {name} ---")
    print(f"Target URL: {url}")
    print(f"Probe Timestamp: {now_str}")
    
    try:
        # Note: respect_robots is True by default in EthicalHttpClient
        res = client.fetch(url, respect_robots=True, max_redirects=5)
        print(f"Fetch Status: {res.status}")
        print(f"HTTP Status: {res.http_status}")
        print(f"Final URL: {res.final_url}")
        print(f"Content Length: {res.content_length} bytes")
        print(f"Content Hash (SHA-256): {res.content_hash}")
        print(f"Response Time: {res.response_time_ms} ms")
        
        if res.status == "SUCCESS" and res.html:
            p_type, p_reason = PageAssessor.assess_page(res.html, res.final_url or url)
            print(f"Live Page Assessment: {p_type} (Reason: {p_reason})")
            
            extracted = FieldExtractor.extract(res.html, res.final_url or url)
            print(f"Live Extracted Title: '{extracted.name}'")
            print(f"Live Extracted Provider: '{extracted.provider}'")
            print(f"Live Extracted Amount: '{extracted.amount_benefit}'")
            print(f"Live Extracted App URL: '{extracted.application_url}'")
            print(f"Live Evidence count: {len(extracted.evidence_list)} items")
            for ev_item in extracted.evidence_list:
                print(f"  -> {ev_item.field_name}: '{ev_item.extracted_value[:35]}' [{ev_item.html_selector}]")
            print("Audit Status: LIVE FETCH AND EXTRACTION CONFIRMED")
        else:
            print(f"Error Reason: {res.error_reason}")
            print(f"Audit Status: LIVE FETCH STATUS: {res.status}")
            
    except Exception as e:
        print(f"Live Fetch Exception: {type(e).__name__}: {str(e)}")
        print("Audit Status: LIVE FETCH UNREACHABLE")
        
    print()
