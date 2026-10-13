import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    # State Gov
    ("Odisha State Scholarship Portal", "https://scholarship.odisha.gov.in/website/home"),
    ("Kerala DCE Scholarships", "http://www.dcescholarship.kerala.gov.in/"),
    ("West Bengal Oasis", "https://oasis.gov.in/"),
    ("Haryana Har-Chhatravratti", "https://harchhatravratti.highereduhry.ac.in/"),
    ("MahaDBT Schemes", "https://mahadbt.maharashtra.gov.in/SchemeData/SchemeData?str=E9DDFA370C054D318D68755018693740"),
    # Central Gov
    ("CSIR HRDG", "https://csirhrdg.res.in/"),
    ("ICMR Fellowships", "https://main.icmr.nic.in/content/fellowships-0"),
    ("UGC National Fellowship", "https://www.ugc.gov.in/"),
    # University
    ("IIT Kharagpur Scholarships", "https://www.iitkgp.ac.in/"),
    ("BITS Pilani Scholarships", "https://www.bitsadmission.com/fdfees202425.aspx"),
    ("Delhi University Scholarships", "https://www.du.ac.in/index.php?page=opportunities"),
    ("IIT Gandhinagar Financial Aid", "https://iitgn.ac.in/admissions/financial_aid"),
    ("IIT Roorkee Financial Aid", "https://www.iitr.ac.in/"),
    ("IISER Pune Scholarships", "https://www.iiserpune.ac.in/education/fellowships"),
    # Corporate CSR & Trusts
    ("Kotak Education Foundation", "https://kotakeducation.org/"),
    ("Azim Premji University Aid", "https://azimpremjiuniversity.edu.in/undergraduate/financial-aid"),
    ("Infosys Foundation Education", "https://www.infosys.com/infosys-foundation/initiatives/education.html"),
    ("Persistent Foundation", "https://www.persistentfoundation.org/"),
]

for name, url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len: {len(r.text)} -> {name} ({url})")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
