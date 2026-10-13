import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()

c.execute("SELECT id, url, anchor_text FROM candidate_urls WHERE url LIKE '%archive%' OR url LIKE '%closed%' OR url LIKE '%circular%' OR url LIKE '%notice%' OR anchor_text LIKE '%last date%' OR anchor_text LIKE '%2023%' OR anchor_text LIKE '%2024%' LIMIT 20")
rows = c.fetchall()
print(f"Candidates with archival/deadline markers: {len(rows)}")
for r in rows:
    print(f"  Cand #{r[0]}: {r[1]} | anchor='{r[2]}'")

conn.close()
