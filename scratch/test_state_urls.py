import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

urls = [
    ("Odisha Schemes", "https://scholarship.odisha.gov.in/website/schemes"),
    ("Odisha Home", "https://scholarship.odisha.gov.in/"),
    ("Kerala DCE Home", "http://www.dcescholarship.kerala.gov.in/"),
    ("Rajasthan Schemes", "https://sje.rajasthan.gov.in/Default.aspx?PageID=346"),
    ("WB Kanyashree", "https://www.wbkanyashree.gov.in/kp_4.0/index.php"),
    ("WB SVMCM Portal", "https://svmcm.wbhed.gov.in/"),
]

for name, url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len={len(r.text)} -> {name}: {url}")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
