"""
Phase E: Live API endpoint testing against running backend.
Tests every enumerated route with actual response validation.
"""
import sys
import json
import requests
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
results = []

def test(method, path, desc, validate_fn=None, body=None, expected_codes=(200,)):
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=8)
        elif method == "POST":
            r = requests.post(url, json=body or {}, timeout=8)
        else:
            r = requests.request(method, url, json=body, timeout=8)
        status = "PASS" if r.status_code in expected_codes else "FAIL"
        detail = ""
        if status == "PASS" and validate_fn:
            try:
                vresult = validate_fn(r)
                if vresult is not True:
                    status = "WARN"
                    detail = str(vresult)
            except Exception as ve:
                status = "WARN"
                detail = f"Validation error: {ve}"
        code = r.status_code
    except requests.ConnectionError:
        status, code, detail = "FAIL", 0, "Connection refused"
    except requests.Timeout:
        status, code, detail = "FAIL", 0, "Timeout"
    except Exception as e:
        status, code, detail = "FAIL", 0, str(e)

    results.append((method, path, code, status, desc, detail))
    print(f"[{status}] {method} {path:<45} -> {code} | {desc}{' | ' + detail if detail else ''}")
    return status, code

print(f"=== Phase E: Live API Endpoint Testing ({datetime.now(timezone.utc).isoformat()}) ===\n")

# Health
test("GET", "/api/health", "Health check",
     lambda r: r.json().get("status") == "ok" and r.json().get("database") == "connected")

# OpenAPI
test("GET", "/openapi.json", "OpenAPI schema exists",
     lambda r: "paths" in r.json())
test("GET", "/docs", "Swagger UI renders", lambda r: "swagger" in r.text.lower())
test("GET", "/redoc", "ReDoc UI renders", lambda r: len(r.text) > 1000)

# Discovery
test("GET", "/api/discovery/sources", "List seed sources",
     lambda r: isinstance(r.json(), list) and len(r.json()) > 0)
test("GET", "/api/discovery/candidates?page=1&page_size=5", "List candidates paginated",
     lambda r: "items" in r.json() and r.json().get("total", 0) > 0)
test("POST", "/api/discovery/run", "Trigger discovery run (safe: limited)",
     lambda r: "status" in r.json(), body={"source_id": None, "max_candidates": 0},
     expected_codes=(200, 201, 400, 422))

# Crawl
test("GET", "/api/crawl/runs?limit=5", "List crawl runs",
     lambda r: isinstance(r.json(), list))
test("GET", "/api/crawl/status", "Crawl status",
     lambda r: r.status_code in (200, 404))

# Scheduler
test("GET", "/api/scheduler/status", "Scheduler status",
     lambda r: "is_active" in r.json())

# Scholarships listing
test("GET", "/api/scholarships?page=1&page_size=25", "Scholarships list returns 21",
     lambda r: r.json().get("total") == 21)
test("GET", "/api/scholarships?page=1&page_size=5&category=CENTRAL_GOVERNMENT", "Filter by category",
     lambda r: r.json().get("total", 0) > 0)

# Per-scholarship detail, evidence, verification, changes
for sid in [2, 8, 17]:
    test("GET", f"/api/scholarships/{sid}", f"Scholarship #{sid} detail",
         lambda r, _sid=sid: r.json().get("id") == _sid or "scholarship" in r.json())
    test("GET", f"/api/scholarships/{sid}/evidence", f"Scholarship #{sid} evidence",
         lambda r: isinstance(r.json(), list) or ("items" in r.json()))
    test("GET", f"/api/scholarships/{sid}/verification", f"Scholarship #{sid} verification",
         lambda r: "confidence_score" in r.json() or "scholarship_id" in r.json())
    test("GET", f"/api/scholarships/{sid}/changes", f"Scholarship #{sid} changes",
         lambda r: isinstance(r.json(), list) or "items" in r.json())

# Non-existent scholarship
test("GET", "/api/scholarships/9999", "Non-existent scholarship -> 404",
     expected_codes=(404,))

# Verification
test("GET", "/api/verification/summary", "Verification summary",
     lambda r: r.json().get("total_scholarships") == 21 and r.json().get("verified_count") == 10)
test("GET", "/api/verification/history/2", "Verification history scholarship #2",
     lambda r: isinstance(r.json(), list) or "scholarship_id" in r.json())
test("GET", "/api/verification/detail/2", "Verification detail scholarship #2",
     lambda r: r.status_code in (200, 404))

# Changes
test("GET", "/api/changes/recent?limit=10", "Recent changes list",
     lambda r: isinstance(r.json(), list) or "items" in r.json() or "changes" in r.json())

# Extraction runs
test("GET", "/api/extraction/runs?limit=5", "Extraction runs",
     lambda r: isinstance(r.json(), list) or "items" in r.json())

print("\n--- SUMMARY ---")
passed = sum(1 for r in results if r[3] == "PASS")
warned = sum(1 for r in results if r[3] == "WARN")
failed = sum(1 for r in results if r[3] == "FAIL")
total = len(results)
print(f"Total endpoints tested: {total}")
print(f"PASS: {passed} | WARN: {warned} | FAIL: {failed}")

if failed:
    print("\nFailed endpoints:")
    for r in results:
        if r[3] == "FAIL":
            print(f"  {r[0]} {r[1]} -> {r[2]} | {r[5]}")
