import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0"}
url = "https://www.iitm.ac.in/academics/financial-assistance"
r = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")

for h in soup.find_all(["h1", "h2", "h3", "h4"]):
    h_text = h.get_text(strip=True)
    if h_text and len(h_text) > 3:
        print(f"Heading <{h.name}>:", h_text.encode('ascii', errors='replace').decode()[:80])

text = soup.get_text(separator=" ", strip=True)
print("\nKeywords:")
for kw in ["merit", "means", "mcm", "free studentship", "eligibility", "income", "tuition", "fee waiver", "sc/st"]:
    print(f"Contains '{kw}':", kw in text.lower())
