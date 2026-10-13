import requests
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

r = requests.get('https://harchhatravratti.highereduhry.ac.in/', headers={'User-Agent': 'EDXSO-Scholarship-Crawler/1.0'}, timeout=10, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
for a in soup.find_all('a', href=True):
    href = a['href']
    t = a.get_text(strip=True)
    if 'scheme' in href.lower() or 'scholarship' in href.lower() or 'detail' in href.lower() or 'guideline' in href.lower():
        print(t, "-->", href)
