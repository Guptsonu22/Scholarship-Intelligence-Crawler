import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect('file:data/scholarships.db?mode=ro', uri=True)
c = conn.cursor()

print('Total scholarships:', c.execute('SELECT COUNT(*) FROM scholarships').fetchone()[0])
print('Verified count:', c.execute('SELECT COUNT(*) FROM scholarships WHERE verification_status="VERIFIED"').fetchone()[0])
print('Review Required count:', c.execute('SELECT COUNT(*) FROM scholarships WHERE verification_status="REVIEW_REQUIRED"').fetchone()[0])
print('Active lifecycle:', c.execute('SELECT COUNT(*) FROM scholarships WHERE lifecycle_status="ACTIVE"').fetchone()[0])
print('Expired lifecycle:', c.execute('SELECT COUNT(*) FROM scholarships WHERE lifecycle_status="EXPIRED"').fetchone()[0])
print('Current evidence rows (is_current=1):', c.execute('SELECT COUNT(*) FROM field_evidence WHERE is_current=1').fetchone()[0])
print('Total evidence rows:', c.execute('SELECT COUNT(*) FROM field_evidence').fetchone()[0])
print('Latest verification records (is_latest=1):', c.execute('SELECT COUNT(*) FROM verification_records WHERE is_latest=1').fetchone()[0])
print('Total historical verification records:', c.execute('SELECT COUNT(*) FROM verification_records').fetchone()[0])
print('Discovered candidate URLs:', c.execute('SELECT COUNT(*) FROM candidate_urls').fetchone()[0])
print('Crawl runs:', c.execute('SELECT COUNT(*) FROM crawl_runs').fetchone()[0])
print('Crawl attempts:', c.execute('SELECT COUNT(*) FROM crawl_attempts').fetchone()[0])
print('Seed sources configured:', c.execute('SELECT COUNT(*) FROM seed_sources').fetchone()[0])
print('Live change history rows:', c.execute('SELECT COUNT(*) FROM scholarship_change_history').fetchone()[0])

# Sector distribution
print("\nSector distribution:")
for row in c.execute('SELECT source_category, COUNT(*) FROM scholarships GROUP BY source_category'):
    print(f"  {row[0]}: {row[1]}")

conn.close()
