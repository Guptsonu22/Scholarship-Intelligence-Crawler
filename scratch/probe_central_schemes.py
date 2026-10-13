import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    ("AICTE PMSSS JK", "https://www.aicte-india.org/bureaus/jk"),
    ("AICTE PMSSS Overview", "https://www.aicte-india.org/bureaus/jk/overview"),
    ("AICTE Pragati Batch Guidelines", "https://www.aicte-india.org/schemes/students-development-schemes/batch-2019-2020-pragati"),
    ("AICTE Saksham Batch Guidelines", "https://www.aicte-india.org/schemes/students-development-schemes/batch-2019-2020-saksham"),
    ("AICTE Fellowship Portal", "https://yukti.mic.gov.in/aicte-fellowship"),
    ("National Apprenticeship NATS", "https://nats.education.gov.in/"),
    ("Department of Higher Education", "https://www.education.gov.in/scholarships-education-loan-0"),
]

for name, url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len={len(r.text)} -> {name}: {url}")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
