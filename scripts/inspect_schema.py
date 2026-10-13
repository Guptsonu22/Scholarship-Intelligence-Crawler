import sqlite3

conn = sqlite3.connect('data/scholarships.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('Tables:', tables)
for t in tables:
    c.execute(f"PRAGMA table_info({t[0]})")
    cols = [(col[1], col[2]) for col in c.fetchall()]
    print(f"\n--- {t[0]} ---")
    for col in cols:
        print(f"  {col[0]} ({col[1]})")
