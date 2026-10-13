import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0"}
url = "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship-Scheme"
r = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")
text = soup.get_text(separator=" ", strip=True)

for h in soup.find_all(["h1", "h2", "h3", "h4"]):
    print(f"Heading <{h.name}>:", h.get_text(strip=True).encode('ascii', errors='replace').decode())

print("\nKeywords search:")
for kw in ["amount", "stipend", "12,400", "gate", "gpat", "eligibility", "scholarship", "month"]:
    print(f"Contains '{kw}':", kw in text.lower())
