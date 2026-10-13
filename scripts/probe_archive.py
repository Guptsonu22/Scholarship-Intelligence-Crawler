import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app.services.crawling.http_client import EthicalHttpClient
from app.services.extraction.page_assessor import PageAssessor
from app.services.extraction.field_extractor import FieldExtractor

client = EthicalHttpClient(timeout=10)
url = "https://www.aicte.gov.in/bureaus/jk"
res = client.fetch(url)
print("Fetch status:", res.status)
if res.html:
    print("Length:", len(res.html))
