import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    # Central Gov
    ("CSIR HRDG JRF", "https://csirhrdg.res.in/Home/Index/1/Default/1749/58"),
    ("CSIR HRDG Schemes Overview", "https://csirhrdg.res.in/Home/Index/1/InPage/52/24/37"),
    ("UGC Junior Research Fellowship", "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx"),
    ("MoTA National Fellowship", "https://overseas.tribal.gov.in/"),
    ("Indian Council of Medical Research (ICMR) JRF", "https://main.icmr.nic.in/content/fellowships-0"),
    # State Gov
    ("Kerala DCE Post Matric", "http://www.dcescholarship.kerala.gov.in/dce/he_ma.php?page=scholarships"),
    ("Haryana Higher Education Scheme", "https://highereduhry.ac.in/Scholarship.aspx"),
    ("Rajasthan Uttar Matric", "https://sjms.rajasthan.gov.in/"),
    ("Himachal Pradesh ePass", "https://hpepass.cgg.gov.in/"),
    # Universities
    ("IIT Delhi Scholarships", "https://home.iitd.ac.in/scholarships.php"),
    ("IIT Bombay Financial Assistance", "https://www.iitb.ac.in/newsite/academics/scholarship.html"),
    ("IISc Bangalore Fellowships", "https://iisc.ac.in/admissions/financial-support/"),
    ("IIT Roorkee Student Aid", "https://iitr.ac.in/Academics/Financial%20Assistance.html"),
    # Corporate CSR & Trusts
    ("Kotak Shiksha Nidhi", "https://kotakeducation.org/kotak-shiksha-nidhi/"),
    ("Reliance Foundation PG", "https://www.reliancefoundation.org/our-work/education/scholarships"),
    ("Infosys Foundation Education", "https://www.infosys.com/infosys-foundation/initiatives/education.html"),
]

for name, url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"[{r.status_code}] len={len(r.text)} -> {name}: {url}")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
