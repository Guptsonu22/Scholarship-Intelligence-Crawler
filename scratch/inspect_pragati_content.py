import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

headers = {"User-Agent": "EDXSO-Scholarship-Crawler/1.0"}
url = "https://www.aicte-india.org/schemes/students-development-schemes/Pragati/General-Instructions"
r = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(r.text, "html.parser")

# Find main content container
for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
    tag.decompose()

content = soup.find(class_=re.compile(r"content|main|article|body", re.I)) or soup.body
text = content.get_text(separator=" ", strip=True) if content else ""
print("Clean content len:", len(text))
print("Sample content:", text[:2000].encode('ascii', errors='replace').decode())

# Check headings
for h in soup.find_all(["h1", "h2", "h3", "h4"]):
    print(f"Heading <{h.name}>:", h.get_text(strip=True).encode('ascii', errors='replace').decode())
