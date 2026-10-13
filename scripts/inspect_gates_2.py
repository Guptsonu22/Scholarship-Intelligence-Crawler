import sys
import sqlite3
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()
c.execute('SELECT scholarship_id, gate_results FROM verification_records WHERE scholarship_id=2 ORDER BY id DESC LIMIT 1')
row = c.fetchone()
print(f"Scholarship ID {row[0]}:")
gates = json.loads(row[1])
for k, v in gates.items():
    print(f"  {k}: {v}")
conn.close()
