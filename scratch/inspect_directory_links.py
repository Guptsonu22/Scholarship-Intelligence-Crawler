import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

def check_page_links(url, filter_keyword="scheme"):
    print(f"\n--- LINKS ON {url} ---")
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            if any(k in href.lower() or k in text.lower() for k in ["scheme", "scholarship", "fellowship", "grant", "support", "award"]):
                if href not in seen:
                    seen.add(href)
                    print(f"  [{text[:40]}] -> {href}")
    except Exception as e:
        print(f"Error on {url}: {e}")

check_page_links("https://www.aicte-india.org/schemes/students-development-schemes")
check_page_links("https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx")
check_page_links("https://www.tatatrusts.org/our-work/education/individual-grants-programme")
