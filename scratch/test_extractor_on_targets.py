import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor
from app.services.verification.source_classifier import SourceClassifier

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

urls = [
    ("AICTE PG Scholarship", "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme"),
    ("AICTE Pragati", "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions"),
    ("AICTE Saksham", "https://www.aicte-india.org/schemes/students-development-schemes/Saksham/General-Instructions"),
    ("AICTE Swanath", "https://www.aicte-india.org/schemes/students-development-schemes/Swanath/General-Instructions"),
    ("AICTE ADF", "https://www.aicte-india.org/schemes/students-development-schemes/ADF-Scheme"),
    ("AICTE Yashasvi", "https://aicte.gov.in/schemes/students-development-schemes/aicte-yashasvi-scholarship-scheme"),
    ("Tata Trusts Education", "https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants"),
    ("Narotam Sekhsaria PG", "https://pg.nsfoundation.co.in/"),
    ("Sitaram Jindal Foundation", "https://www.sitaramjindalfoundation.org/scholarships.php"),
    ("Aditya Birla Scholarships", "https://www.adityabirlascholars.net/"),
    ("IIT Madras Financial Aid", "https://www.iitm.ac.in/academics/financial-assistance"),
    ("IIT Kanpur Scholarships", "https://www.iitk.ac.in/dora/scholarships"),
    ("Azim Premji University Aid", "https://azimpremjiuniversity.edu.in/undergraduate/financial-aid"),
    ("West Bengal Oasis", "https://oasis.gov.in/"),
    ("Haryana Har-Chhatravratti", "https://harchhatravratti.highereduhry.ac.in/"),
]

print("=== TESTING CURRENT PAGE ASSESSOR & FIELD EXTRACTOR ===")
for name, url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        ptype, reason = PageAssessor.assess_page(r.text, url)
        classification = SourceClassifier.classify(url)
        extracted = FieldExtractor.extract(r.text, url) if ptype == "SCHOLARSHIP_DETAIL" else None
        
        print(f"\n[{name}] -> {ptype} ({reason})")
        print(f"  Classification: {classification.category} (official={classification.is_official}, trust={classification.trust_score})")
        if extracted:
            print(f"  Extracted Name: {extracted.name}")
            print(f"  Provider: {extracted.provider}")
            print(f"  Amount/Benefit: {extracted.amount_benefit}")
            print(f"  Closing Date: {extracted.closing_date}")
            print(f"  Course Level: {extracted.course_level}")
            print(f"  Eligibility: {extracted.eligibility_summary[:80] if extracted.eligibility_summary else None}")
            print(f"  Evidence count: {len(extracted.evidence_list)}")
    except Exception as e:
        print(f"ERR {name}: {e}")
