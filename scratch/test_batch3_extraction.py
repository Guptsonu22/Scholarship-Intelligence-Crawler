import requests
import urllib3
urllib3.disable_warnings()

from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.verification.source_classifier import SourceClassifier

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

urls = [
    ("CSIR HRDG JRF", "https://csirhrdg.res.in/Home/Index/1/Default/1749/58"),
    ("CSIR Schemes Overview", "https://csirhrdg.res.in/Home/Index/1/InPage/52/24/37"),
    ("UGC Fellowships", "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx"),
    ("MoTA Overseas Fellowship", "https://overseas.tribal.gov.in/"),
    ("Rajasthan Uttar Matric", "https://sjms.rajasthan.gov.in/"),
    ("Himachal Pradesh ePass", "https://hpepass.cgg.gov.in/"),
    ("IIT Bhubaneswar", "https://www.iitbbs.ac.in/scholarship.php"),
]

for name, url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        ptype, reason = PageAssessor.assess_page(r.text, url)
        classification = SourceClassifier.classify(url)
        extracted = FieldExtractor.extract(r.text, url) if ptype == "SCHOLARSHIP_DETAIL" else None
        print(f"\n[{name}] -> {ptype}")
        print(f"  Category: {classification.category} (official={classification.is_official})")
        if extracted:
            print(f"  Name: {extracted.name}")
            print(f"  Provider: {extracted.provider}")
            print(f"  Benefit: {extracted.amount_benefit}")
            print(f"  Evidence count: {len(extracted.evidence_list)}")
    except Exception as e:
        print(f"ERR {name}: {e}")
