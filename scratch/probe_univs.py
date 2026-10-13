import requests
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0 (+https://edxso.org/bot; academic-research)"}

univs = [
    ("IIT Madras Financial Aid", "https://www.iitm.ac.in/academics/financial-assistance"),
    ("IIT Kanpur Scholarships", "https://www.iitk.ac.in/dora/scholarships"),
    ("IIT Bombay Academics", "https://www.iitb.ac.in/en/academics/financial-support"),
    ("IIT Roorkee", "https://www.iitr.ac.in/academics/pages/Scholarships.html"),
    ("Jadavpur University", "http://www.jaduniv.edu.in/"),
    ("Delhi University", "http://du.ac.in/"),
    ("IISc Students", "https://iisc.ac.in/students-corner/"),
    ("BITS Pilani Practice School", "https://www.bits-pilani.ac.in/"),
    ("Ashoka University Financial Aid", "https://www.ashoka.edu.in/financial-aid/"),
    ("Shiv Nadar University Aid", "https://snu.edu.in/admissions/scholarships/"),
    ("Plaksha University Aid", "https://plaksha.edu.in/admissions/financial-aid"),
    ("Ahmedabad University Aid", "https://ahduni.edu.in/admissions/financial-aid/"),
]

for name, url in univs:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f"[{r.status_code}] len: {len(r.text)} -> {name} ({url})")
    except Exception as e:
        print(f"[ERR] -> {name}: {e}")
