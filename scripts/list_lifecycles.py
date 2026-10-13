import sys
import sqlite3
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()

c.execute("SELECT id, name, provider, official_source_url, closing_date, lifecycle_status, verification_status, confidence_score FROM scholarships ORDER BY id")
rows = c.fetchall()

print(f"{'ID':<3} | {'Status':<16} | {'Lifecycle':<10} | {'Score':<6} | {'Closing Date':<12} | {'Name'}")
print("-" * 100)
for r in rows:
    print(f"{r[0]:<3} | {r[6]:<16} | {r[5]:<10} | {r[7]}% | {str(r[4]):<12} | {r[1][:50]}")

conn.close()
