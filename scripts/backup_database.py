"""Safe database backup before any audit operations."""
import sys
import shutil
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

src = os.path.abspath('data/scholarships.db')
backup_dir = os.path.abspath('data/backups')
os.makedirs(backup_dir, exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
dest = os.path.join(backup_dir, f'scholarships_backup_{timestamp}.db')

shutil.copy2(src, dest)

# Verify backup
src_size = os.path.getsize(src)
dest_size = os.path.getsize(dest)

print(f"SOURCE: {src} ({src_size} bytes)")
print(f"BACKUP: {dest} ({dest_size} bytes)")
print(f"MATCH: {src_size == dest_size}")
print(f"READABLE: {os.path.isfile(dest)}")

if src_size == dest_size:
    print("BACKUP SUCCESSFUL")
else:
    print("BACKUP FAILED - size mismatch")
    sys.exit(1)
