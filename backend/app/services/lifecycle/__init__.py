"""Scholarship Lifecycle and Change Detection Package.

Includes:
- Field-level change detection engine
- Whitespace and formatting noise filter
- Lifecycle status progression (ACTIVE, EXPIRING_SOON, EXPIRED, NO_LONGER_VERIFIABLE)
- Historical audit trail persistence
"""
from app.services.lifecycle.change_detector import ChangeDetector
from app.services.lifecycle.lifecycle_manager import LifecycleManager

__all__ = ["ChangeDetector", "LifecycleManager"]
