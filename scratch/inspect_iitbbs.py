import requests
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

r = requests.get('https://www.iitbbs.ac.in/scholarship.php', headers={'User-Agent': 'EDXSO-Scholarship-Crawler/1.0'}, timeout=10, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
    print(h.name, "->", h.get_text(strip=True))

for p in soup.find_all(['p', 'div'])[:10]:
    t = p.get_text(separator=' ', strip=True)
    if 'scholarship' in t.lower() or 'merit' in t.lower():
        print("TEXT:", t[:120])
