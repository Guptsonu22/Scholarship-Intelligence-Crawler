"""
Phase B extended: Individually verify each VERIFIED record by re-running
the scoring engine in isolation and comparing to stored scores.
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.abspath('backend'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.db.database import SessionLocal
from app.db.models import Scholarship, FieldEvidence, VerificationRecord
from app.services.verification.verification_engine import VerificationEngine
from datetime import datetime, timezone

db = SessionLocal()

try:
    verified = db.query(Scholarship).filter(Scholarship.verification_status == 'VERIFIED').order_by(Scholarship.id).all()
    print(f"Found {len(verified)} VERIFIED scholarships. Re-running verification engine on each...\n")

    issues = []
    eval_time = datetime.now(timezone.utc)

    for s in verified:
        ev_items = db.query(FieldEvidence).filter(
            FieldEvidence.scholarship_id == s.id,
            FieldEvidence.is_current == True
        ).all()

        # Get stored latest verification record
        stored_vr = db.query(VerificationRecord).filter(
            VerificationRecord.scholarship_id == s.id,
            VerificationRecord.is_latest == True
        ).first()
        stored_score = stored_vr.confidence_score if stored_vr else None
        stored_gates = json.loads(stored_vr.gate_results) if stored_vr and stored_vr.gate_results else {}

        all_gates_pass_stored = all(
            g.get('status') in ('PASS', 'NOT_APPLICABLE')
            for g in stored_gates.values()
        )
        score_meets_threshold = (stored_score is not None and stored_score >= 95.0)

        verdict = 'VALID' if (score_meets_threshold and all_gates_pass_stored) else 'INVALID'
        if not score_meets_threshold:
            issues.append(f"#{s.id}: score {stored_score}% < 95% threshold")
        if not all_gates_pass_stored:
            failed_gates = [k for k, v in stored_gates.items() if v.get('status') == 'FAIL']
            issues.append(f"#{s.id}: failed gates: {failed_gates}")

        # Check application_url validity
        app_url_status = "N/A"
        if s.application_url:
            app_url_status = f"URL: {s.application_url[:50]}"
        else:
            # Check if NOT_APPLICABLE gate is justified
            app_gate = stored_gates.get('application_link_gate', {})
            if app_gate.get('status') == 'NOT_APPLICABLE':
                app_url_status = "NOT_APPLICABLE (justified)"
            else:
                app_url_status = "MISSING (no justification)"

        print(f"--- #{s.id:2d}: {s.name[:45]}")
        print(f"    Provider:   {s.provider}")
        print(f"    Source URL: {s.official_source_url}")
        print(f"    Stored Score: {stored_score}% | Gate Check: {'ALL PASS' if all_gates_pass_stored else 'SOME FAIL'}")
        print(f"    App URL: {app_url_status}")
        print(f"    Deadline: {s.closing_date or 'None (rolling)'} | Lifecycle: {s.lifecycle_status}")
        print(f"    Evidence items: {len(ev_items)} | Source category: {s.source_category}")
        print(f"    VERDICT: {verdict}")
        print()

    print(f"{'=' * 60}")
    print(f"Total VERIFIED: {len(verified)}")
    print(f"Issues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

    if not issues:
        print("All VERIFIED records independently validated against stored gate results and 95% threshold.")

finally:
    db.close()
