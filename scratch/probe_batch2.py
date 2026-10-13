import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    # State Government
    ("Odisha State Scholarship", "https://scholarship.odisha.gov.in/website/home"),
    ("Bihar Post Matric", "https://pmsonline.bih.nic.in/"),
    ("Punjab State Scholarship", "https://scholarships.punjab.gov.in/"),
    ("MP State Portal", "http://scholarshipportal.mp.nic.in/Home.aspx"),
    # Central Government
    ("DST INSPIRE", "https://online-inspire.gov.in/"),
    ("CSIR HRDG Schemes", "https://csirhrdg.res.in/Home/Index/1/Default/1454/58"),
    ("AICTE QIP", "https://www.aicte-india.org/schemes/staff-development-schemes"),
    ("AICTE Institutional", "https://www.aicte-india.org/schemes/institutional-development-schemes"),
    # Corporate CSR & Trusts
    ("ONGC Foundation Merit", "https://ongcfoundation.org/"),
    ("Reliance Foundation Home", "https://www.reliancefoundation.org/"),
    ("K.C. Mahindra Home", "https://www.kcmet.org/"),
    ("Fair and Lovely Foundation", "https://www.glowandlovelycareers.in/en/scholarships"),
    ("Vidyasaarathi Portal", "https://www.vidyasaarathi.co.in/Vidyasaarathi/"),
]

for name, url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len: {len(r.text)} -> {name} ({url})")
    except Exception as e:
        print(f"[ERR] {name} -> {e}")
