import sys
import requests
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

endpoints_to_test = [
    ("Health Check", "GET", "/api/health", {}),
    ("OpenAPI Schema", "GET", "/openapi.json", {}),
    ("Swagger UI", "GET", "/docs", {}),
    ("List Seed Sources", "GET", "/api/discovery/sources", {}),
    ("List Candidates", "GET", "/api/discovery/candidates?limit=5", {}),
    ("List Crawl Runs", "GET", "/api/crawl/runs?limit=5", {}),
    ("Scheduler Status", "GET", "/api/scheduler/status", {}),
    ("Scholarships List", "GET", "/api/scholarships?limit=25", {}),
    ("Scholarship #2 Detail", "GET", "/api/scholarships/2", {}),
    ("Scholarship #2 Evidence", "GET", "/api/scholarships/2/evidence", {}),
    ("Scholarship #2 Verification", "GET", "/api/scholarships/2/verification", {}),
    ("Scholarship #2 Changes", "GET", "/api/scholarships/2/changes", {}),
    ("Verification Summary", "GET", "/api/verification/summary", {}),
    ("Recent Changes Audit", "GET", "/api/changes/recent?limit=10", {}),
    ("Extraction Runs", "GET", "/api/extraction/runs?limit=5", {}),
]

print("=== END-TO-END API ENDPOINT VERIFICATION ===")
all_pass = True

for name, method, path, params in endpoints_to_test:
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=5)
        print(f"[{method}] {path:<38} -> Status {resp.status_code} ({resp.elapsed.total_seconds()*1000:.1f}ms)")
        
        if resp.status_code not in (200, 201):
            print(f"  FAILED: Status {resp.status_code}")
            all_pass = False
        else:
            if path == "/api/health":
                print(f"  Payload: {resp.json()}")
            elif path == "/api/verification/summary":
                data = resp.json()
                print(f"  Summary Metrics: total={data.get('total_scholarships')}, verified={data.get('verified_count')}, review_required={data.get('review_required_count')}, avg_score={data.get('average_confidence_score')}%")
            elif path == "/api/scholarships?limit=25":
                data = resp.json()
                items = data.get("items", []) if isinstance(data, dict) else data
                print(f"  Returned {len(items)} scholarships")
            elif path == "/api/scheduler/status":
                print(f"  Status: {resp.json().get('status')}")
    except Exception as e:
        print(f"[{method}] {path:<38} -> ERROR: {type(e).__name__}: {str(e)}")
        all_pass = False

print("\nOVERALL API RESULT:", "ALL PASSED" if all_pass else "FAILURES DETECTED")
