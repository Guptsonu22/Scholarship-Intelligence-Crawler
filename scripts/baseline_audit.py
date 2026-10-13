import sqlite3

conn = sqlite3.connect('file:data/scholarships.db?mode=ro', uri=True)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM scholarships')
print('Scholarships:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM scholarships WHERE verification_status='VERIFIED'")
print('Verified:', c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM scholarships WHERE verification_status='REVIEW_REQUIRED'")
print('Review Required:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM field_evidence WHERE is_current=1')
print('Current Evidence:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM field_evidence')
print('Total Evidence:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM verification_records')
print('Verification Records:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM candidate_urls')
print('Candidate URLs:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM scholarship_change_history')
print('Change History:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM crawl_runs')
print('Crawl Runs:', c.fetchone()[0])

conn.close()
