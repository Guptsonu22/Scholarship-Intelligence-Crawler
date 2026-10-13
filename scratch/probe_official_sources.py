import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

urls = [
    # Central Gov
    ("AICTE Pragati", "https://www.aicte-india.org/schemes/students-development-schemes/Pragati"),
    ("AICTE Saksham", "https://www.aicte-india.org/schemes/students-development-schemes/Saksham"),
    ("AICTE Swanath", "https://www.aicte-india.org/schemes/students-development-schemes/Swanath"),
    ("AICTE PG Scholarship", "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme"),
    ("UGC Fellowships", "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx"),
    ("DST INSPIRE", "https://online-inspire.gov.in/"),
    # University
    ("IISc Financial Support", "https://iisc.ac.in/admissions/financial-support/"),
    ("IIT Bombay Scholarships", "https://www.iitb.ac.in/newsite/academics/scholarship.html"),
    ("IIT Madras Financial Aid", "https://www.iitm.ac.in/academics/financial-assistance"),
    ("IIT Delhi Scholarships", "https://home.iitd.ac.in/scholarships.php"),
    # Corporate CSR & Trust
    ("Tata Trusts Education", "https://www.tatatrusts.org/our-work/education/individual-grants-programme"),
    ("Reliance Foundation UG", "https://www.reliancefoundation.org/our-work/education/scholarships"),
    ("K.C. Mahindra Education Trust", "https://www.kcmet.org/what-we-do-scholarships.aspx"),
    ("Narotam Sekhsaria Foundation", "https://pg.nsfoundation.co.in/"),
    ("Sitaram Jindal Foundation", "https://www.sitaramjindalfoundation.org/scholarships.php"),
    ("Aditya Birla Scholarships", "https://www.adityabirlascholars.net/"),
    ("L'Oreal India FWIS", "https://www.loreal.com/en/india/articles/commitments/for-women-in-science/"),
    ("ONGC Foundation", "https://ongcfoundation.org/"),
    # State Government
    ("Karnataka SSP", "https://ssp.postmatric.karnataka.gov.in/"),
    ("MahaDBT", "https://mahadbt.maharashtra.gov.in/"),
]

headers = {
    "User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"
}

print("=== PROBING OFFICIAL SCHOLARSHIP SOURCES ===")
for name, url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[{r.status_code}] {name} ({len(r.text)} bytes) -> {url}")
        if r.status_code == 200:
            title_match = ""
            if "<title>" in r.text.lower():
                start = r.text.lower().find("<title>") + 7
                end = r.text.lower().find("</title>", start)
                title_match = r.text[start:end].strip()
            print(f"       Title: {title_match[:70]}")
    except Exception as e:
        print(f"[ERR] {name} -> {e}")
