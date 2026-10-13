import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}
r = requests.get("https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx", headers=headers, timeout=12, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
for a in soup.find_all("a", href=True):
    text = a.get_text(strip=True)
    href = a["href"].strip()
    if text and len(text) > 3:
        print(f"[{text[:60]}] -> {href}")
