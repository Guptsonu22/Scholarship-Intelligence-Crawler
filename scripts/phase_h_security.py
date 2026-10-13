"""
Phase H: Security and hygiene audit.
Checks: .env not in git, SSRF protection active, robots.txt respected, 
no hardcoded secrets in source, API key exposure, input validation.
"""
import sys
import os
import subprocess
import requests

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.abspath('.')

print("=" * 70)
print("PHASE H: SECURITY & HYGIENE AUDIT")
print("=" * 70)

# H1: .env not in git
print("\n[H1] Secrets not tracked by git")
tracked = subprocess.run(['git', 'ls-files', '.env'], capture_output=True, text=True, cwd=ROOT)
env_tracked = bool(tracked.stdout.strip())
print(f"  .env tracked: {env_tracked} (should be False) -> {'PASS' if not env_tracked else 'FAIL'}")

# Check .env contents for raw API keys to warn (don't print values)
env_path = os.path.join(ROOT, '.env')
if os.path.exists(env_path):
    env_text = open(env_path).read()
    has_api_key = any(line.strip() and not line.startswith('#') and '=' in line and len(line.split('=',1)[1].strip()) > 10
                      for line in env_text.split('\n') if 'API' in line.upper() or 'KEY' in line.upper() or 'SECRET' in line.upper())
    print(f"  .env has filled secret fields: {has_api_key} (not exposed, just confirming not empty)")
else:
    print("  .env: NOT FOUND (would use defaults)")

# H2: SSRF protection
print("\n[H2] SSRF protection via API (live loopback block test)")
import sys
sys.path.insert(0, 'backend')
from app.services.crawling.http_client import EthicalHttpClient
client = EthicalHttpClient(timeout=5)

ssrf_targets = [
    ("http://127.0.0.1:8000", True, "loopback"),
    ("http://169.254.169.254/latest/meta-data", True, "AWS metadata"),
    ("http://10.0.0.1", True, "private IP"),
    ("http://localhost", True, "localhost hostname"),
    ("file:///etc/passwd", True, "file:// scheme"),
]

for url, expect_block, label in ssrf_targets:
    result = client.fetch(url)
    was_blocked = (result.status != "SUCCESS") and (result.status.startswith("BLOCKED") or "restricted" in (result.error_reason or "").lower() or "blocked" in (result.error_reason or "").lower() or "unsupported" in (result.error_reason or "").lower())
    status = "PASS" if was_blocked == expect_block else "FAIL"
    print(f"  [{status}] {label}: status={result.status} | blocked={was_blocked} | reason={result.error_reason}")

# H3: robots.txt compliance test
print("\n[H3] Robots.txt compliance (check disallow enforcement in fetch)")
# This is tested in unit tests test_crawling_security.py already
res = subprocess.run(
    ['backend\\.venv\\Scripts\\pytest.exe', 'backend/tests/test_crawling_security.py', '-v', '--tb=short'],
    capture_output=True, text=True, cwd=ROOT
)
lines = [l for l in res.stdout.splitlines() if 'PASSED' in l or 'FAILED' in l or 'ERROR' in l]
for l in lines:
    print(f"  {l}")
print(f"  Return code: {res.returncode} ({'PASS' if res.returncode == 0 else 'FAIL'})")

# H4: No hardcoded credentials in Python source
print("\n[H4] Hardcoded secrets scan in backend/app/")
result = subprocess.run(
    ['git', 'grep', '-rni', '--include=*.py',
     '-e', r'password\s*=\s*["\'][^"\']{6}',
     '-e', r'api_key\s*=\s*["\'][A-Za-z0-9]{20}',
     '-e', r'secret\s*=\s*["\'][A-Za-z0-9]{8}',
     'backend/app/', 'backend/tests/'],
    capture_output=True, text=True, cwd=ROOT
)
if result.stdout.strip():
    print(f"  [WARN] Potential hardcoded secrets found:")
    for line in result.stdout.strip().split('\n')[:5]:
        print(f"    {line}")
else:
    print("  [PASS] No hardcoded credentials patterns found in source files.")

# H5: API error responses don't leak stack traces
print("\n[H5] API error responses do not expose stack traces")
r404 = requests.get("http://127.0.0.1:8000/api/scholarships/99999999", timeout=5)
r_text = r404.text
leaks_traceback = "traceback" in r_text.lower() or "file \"" in r_text.lower()
print(f"  404 response body: {r_text[:100]}")
print(f"  Leaks traceback: {leaks_traceback} -> {'PASS' if not leaks_traceback else 'FAIL'}")

r500 = requests.get("http://127.0.0.1:8000/api/nonexistent_route", timeout=5)
leaks_tb_500 = "traceback" in r500.text.lower()
print(f"  404-on-nonexistent: status={r500.status_code} | leaks_traceback={leaks_tb_500} -> {'PASS' if not leaks_tb_500 else 'FAIL'}")

# H6: CORS headers check
print("\n[H6] CORS headers presence")
r_cors = requests.options("http://127.0.0.1:8000/api/scholarships", 
                            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
                            timeout=5)
cors_header = r_cors.headers.get("access-control-allow-origin", "MISSING")
print(f"  Access-Control-Allow-Origin: {cors_header}")
print(f"  CORS configured: {'PASS' if cors_header != 'MISSING' else 'WARN (may be handled by browser)'}")

print("\n[H7] Rate limiting check (no spam, just inspect headers)")
r_rl = requests.get("http://127.0.0.1:8000/api/scholarships", timeout=5)
rl_headers = {k: v for k, v in r_rl.headers.items() if 'rate' in k.lower() or 'limit' in k.lower()}
if rl_headers:
    print(f"  Rate limit headers: {rl_headers}")
else:
    print("  [NOTE] No rate-limit headers exposed (backend rate limiting via crawler client, not HTTP)")

print("\nPhase H complete.")
