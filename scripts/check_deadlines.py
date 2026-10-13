import sys
import sqlite3
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()

c.execute("SELECT id, name, closing_date, lifecycle_status, official_source_url FROM scholarships WHERE closing_date IS NOT NULL")
rows = c.fetchall()
print(f"Scholarships with explicit closing_date: {len(rows)}")
for r in rows:
    print(f"  #{r[0]}: {r[1]} | closing_date={r[2]} | lifecycle={r[3]} | url={r[4]}")

conn.close()
