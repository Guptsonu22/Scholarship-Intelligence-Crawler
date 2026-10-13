import sqlite3
import json

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()
c.execute('SELECT scholarship_id, gate_results, scoring_breakdown, deductions_reasons FROM verification_records LIMIT 3')
for row in c.fetchall():
    print(f"Scholarship ID: {row[0]}")
    print(f"gate_results raw: {row[1]}")
    print(f"scoring_breakdown raw: {row[2]}")
    print(f"deductions_reasons raw: {row[3]}")
    print("-" * 40)
conn.close()
