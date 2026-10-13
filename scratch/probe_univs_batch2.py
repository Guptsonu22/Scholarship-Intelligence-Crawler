import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

candidates = [
    ("IISER Pune Fellowships", "https://www.iiserpune.ac.in/education/fellowships"),
    ("IIT Palakkad Scholarships", "https://iitpkd.ac.in/scholarships"),
    ("IIT Bhubaneswar Scholarships", "https://www.iitbbs.ac.in/scholarship.php"),
    ("BITS Pilani Admissions", "https://www.bitsadmission.com/"),
    ("IIT Kharagpur Financial Aid", "https://www.iitkgp.ac.in/financial-assistance"),
    ("Delhi University Scholarships", "http://www.du.ac.in/index.php?page=opportunities"),
    ("Punjab Scholarships", "https://punjabscholarships.gov.in/"),
    ("MP Scholarship Portal", "http://scholarshipportal.mp.nic.in/"),
    ("Bihar Post Matric", "https://pmsonline.bih.nic.in/"),
]

for name, url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len={len(r.text)} -> {name}: {url}")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
