import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

target_pages = [
    ("AICTE PG Scholarship", "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme"),
    ("AICTE Pragati", "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions"),
    ("AICTE Saksham", "https://www.aicte-india.org/schemes/students-development-schemes/Saksham/General-Instructions"),
    ("AICTE Swanath", "https://www.aicte-india.org/schemes/students-development-schemes/Swanath/General-Instructions"),
    ("AICTE ADF", "https://www.aicte-india.org/schemes/students-development-schemes/ADF-Scheme"),
    ("AICTE Yashasvi", "https://aicte.gov.in/schemes/students-development-schemes/aicte-yashasvi-scholarship-scheme"),
    ("Tata Trusts Education Grants", "https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants"),
    ("Narotam Sekhsaria PG", "https://pg.nsfoundation.co.in/"),
    ("Sitaram Jindal Foundation", "https://www.sitaramjindalfoundation.org/scholarships.php"),
    ("Aditya Birla Scholarships", "https://www.adityabirlascholars.net/"),
    ("IIT Madras Financial Assistance", "https://www.iitm.ac.in/academics/financial-assistance"),
    ("IIT Kanpur Scholarships", "https://www.iitk.ac.in/dora/scholarships"),
    ("Azim Premji University Aid", "https://azimpremjiuniversity.edu.in/undergraduate/financial-aid"),
    ("West Bengal Oasis", "https://oasis.gov.in/"),
    ("Haryana Har-Chhatravratti", "https://harchhatravratti.highereduhry.ac.in/"),
]

for name, url in target_pages:
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
        text = soup.get_text(separator=" ", strip=True)
        print(f"\n==========================================")
        print(f"[{r.status_code}] {name}")
        print(f"URL: {url}")
        print(f"Title: {title}")
        print(f"Text snippet: {text[:300]}...")
    except Exception as e:
        print(f"ERR {name}: {e}")
