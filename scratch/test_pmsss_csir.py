import requests
import urllib3
urllib3.disable_warnings()

from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.verification.source_classifier import SourceClassifier

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

urls = [
    ("AICTE PMSSS", "https://www.aicte-india.org/bureaus/jk"),
    ("CSIR HRDG JRF", "https://csirhrdg.res.in/Home/Index/1/Default/1749/58"),
    ("CSIR Financial Assistance", "https://csirhrdg.res.in/Home/Index/1/InPage/52/24/37"),
]

for name, url in urls:
    r = requests.get(url, headers=headers, timeout=10, verify=False)
    ptype, reason = PageAssessor.assess_page(r.text, url)
    print(f"\n[{name}] -> {ptype}")
    if ptype == "SCHOLARSHIP_DETAIL":
        extracted = FieldExtractor.extract(r.text, url)
        print(f"  Name: {extracted.name}")
        print(f"  Provider: {extracted.provider}")
        print(f"  Benefit: {extracted.amount_benefit}")
        print(f"  Closing: {extracted.closing_date}")
        print(f"  Course: {extracted.course_level}")
        print(f"  Evidence count: {len(extracted.evidence_list)}")
