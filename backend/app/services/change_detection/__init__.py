"""Change Detection Service Package.

Responsible for tracking scholarship lifecycle updates across crawl cycles:
- Field-level diff calculation
- Historical value preservation without overwriting audit trails
- Detection of deadline extensions, status transitions (ACTIVE, EXPIRED, STALE), and amount updates
"""
