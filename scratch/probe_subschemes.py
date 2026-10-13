import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

sub_urls = [
    "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme",
    "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions",
    "https://www.aicte-india.org/schemes/students-development-schemes/Saksham/General-Instructions",
    "https://www.aicte-india.org/schemes/students-development-schemes/Swanath/General-Instructions",
    "https://www.aicte-india.org/schemes/students-development-schemes/ADF-Scheme",
    "https://aicte.gov.in/schemes/students-development-schemes/aicte-yashasvi-scholarship-scheme",
    "https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants",
]

for url in sub_urls:
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        print(f"[{r.status_code}] len: {len(r.text)} -> {url}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            h1 = soup.find(["h1", "h2"])
            h1_text = h1.get_text(strip=True) if h1 else "No H1"
            print(f"       Heading: {h1_text[:60]}")
    except Exception as e:
        print(f"Error on {url}: {e}")
