import os
import sys
import json
import requests
import urllib3
urllib3.disable_warnings()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

backend_path = os.path.abspath("backend")
app_path = os.path.join(backend_path, "app")
sys.path.insert(0, backend_path)
sys.path.insert(0, app_path)

from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.verification.source_classifier import SourceClassifier
from app.services.verification.scoring_model import DeterministicScoringModel

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    ("AICTE PMSSS", "https://www.aicte-india.org/bureaus/jk"),
    ("CSIR HRDG JRF", "https://csirhrdg.res.in/Home/Index/1/Default/1749/58"),
    ("CSIR Financial Assistance", "https://csirhrdg.res.in/Home/Index/1/InPage/52/24/37"),
    ("AICTE Pragati Guidelines", "https://www.aicte-india.org/schemes/students-development-schemes/batch-2019-2020-pragati"),
    ("AICTE Saksham Guidelines", "https://www.aicte-india.org/schemes/students-development-schemes/batch-2019-2020-saksham"),
    ("NATS National Apprenticeship", "https://nats.education.gov.in/"),
    ("IIT Bhubaneswar", "https://www.iitbbs.ac.in/scholarship.php"),
]

for name, url in candidates:
    r = requests.get(url, headers=headers, timeout=10, verify=False)
    ptype, reason = PageAssessor.assess_page(r.text, url)
    print(f"\n[{name}] -> {ptype}")
    if ptype == "SCHOLARSHIP_DETAIL":
        extracted = FieldExtractor.extract(r.text, url)
        print(f"  Name: {extracted.name}")
        print(f"  Provider: {extracted.provider}")
        print(f"  Benefit: {extracted.amount_benefit}")
        print(f"  Evidence count: {len(extracted.evidence_list)}")
