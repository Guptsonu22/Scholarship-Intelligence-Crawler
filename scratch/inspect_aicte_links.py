import requests
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

r = requests.get('https://www.aicte-india.org/schemes/students-development-schemes', headers={'User-Agent': 'EDXSO-Scholarship-Crawler/1.0'}, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text(strip=True)
    if any(k in href.lower() for k in ['scheme', 'student', 'pragati', 'saksham', 'swanath', 'adf', 'pg', 'fellowship']):
        print(f"{text} -> {href}")
