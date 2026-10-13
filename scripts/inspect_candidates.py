import sqlite3

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()
c.execute("SELECT id, url, normalized_url, status, relevance_score, is_official_source FROM candidate_urls")
rows = c.fetchall()
print(f"Total candidate URLs: {len(rows)}")
for r in rows[:15]:
    print(f"Cand #{r[0]}: {r[1][:60]} | status={r[3]} | rel={r[4]}")
conn.close()
