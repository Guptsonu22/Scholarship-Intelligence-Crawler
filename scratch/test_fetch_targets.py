import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

test_urls = [
    ("https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme", "CENTRAL_GOVERNMENT"),
    ("https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions", "CENTRAL_GOVERNMENT"),
    ("https://www.aicte-india.org/schemes/students-development-schemes/Saksham/General-Instructions", "CENTRAL_GOVERNMENT"),
    ("https://www.aicte-india.org/schemes/students-development-schemes/Swanath/General-Instructions", "CENTRAL_GOVERNMENT"),
    ("https://www.aicte-india.org/schemes/students-development-schemes/ADF-Scheme", "CENTRAL_GOVERNMENT"),
    ("https://aicte.gov.in/schemes/students-development-schemes/aicte-yashasvi-scholarship-scheme", "CENTRAL_GOVERNMENT"),
    ("https://online-inspire.gov.in/", "CENTRAL_GOVERNMENT"),
    ("https://csirhrdg.res.in/Home/Index/1/Default/1454/58", "CENTRAL_GOVERNMENT"),
    ("https://oasis.gov.in/", "STATE_GOVERNMENT"),
    ("https://harchhatravratti.highereduhry.ac.in/", "STATE_GOVERNMENT"),
    ("https://scholarship.odisha.gov.in/website/home", "STATE_GOVERNMENT"),
    ("https://scholarships.punjab.gov.in/", "STATE_GOVERNMENT"),
    ("https://www.iitm.ac.in/academics/financial-assistance", "UNIVERSITY"),
    ("https://www.iitk.ac.in/dora/scholarships", "UNIVERSITY"),
    ("https://azimpremjiuniversity.edu.in/undergraduate/financial-aid", "UNIVERSITY"),
    ("https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants", "CORPORATE_CSR"),
    ("https://pg.nsfoundation.co.in/", "TRUST_FOUNDATION"),
    ("https://www.sitaramjindalfoundation.org/scholarships.php", "TRUST_FOUNDATION"),
    ("https://www.adityabirlascholars.net/", "CORPORATE_CSR"),
    ("https://ongcfoundation.org/", "CORPORATE_CSR"),
]

print("=== FETCHING REAL HTML FOR DETAILED ANALYSIS ===")
for url, cat in test_urls:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[{r.status_code}] len={len(r.text)} -> {url}")
    except Exception as e:
        print(f"[ERR] -> {url}: {e}")
