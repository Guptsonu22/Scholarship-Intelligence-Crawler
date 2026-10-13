import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

url = "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions"
r = requests.get(url, headers=headers, timeout=12, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
text = soup.get_text(separator=" ", strip=True)

print("len text:", len(text))
print("has_scholarship_term:", bool(re.search(r"scholarship|fellowship|financial aid|yojana|stipend", text, re.I)))
print("has_criteria:", bool(re.search(r"eligibility|criteria|qualification|income|documents|selection", text, re.I)))
print("has_award_or_date:", bool(re.search(r"amount|award|stipend|benefit|deadline|last date|closing date|valid till", text, re.I)))

from app.services.extraction.page_assessor import PageAssessor
ptype, reason = PageAssessor.assess_page(r.text, url)
print("Text preview:", text[:1500].encode('ascii', errors='replace').decode())
