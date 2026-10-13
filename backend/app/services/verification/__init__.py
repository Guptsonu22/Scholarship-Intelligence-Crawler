"""Verification Service Package.

Deterministic evidence verification and explainable confidence scoring:
- Strict >=95.0% threshold + 7 mandatory verification gates
- Explainable point allocation (100 total points)
- Audit trail recording and safe persistence
"""
from app.services.verification.source_classifier import SourceClassifier, SourceClassificationResult
from app.services.verification.scoring_model import DeterministicScoringModel, VerificationScoreResult, CriterionScore
from app.services.verification.evidence_evaluator import EvidenceEvaluator
from app.services.verification.gates import VerificationGates, GateEvaluationResult
from app.services.verification.verification_engine import VerificationEngine

__all__ = [
    "SourceClassifier",
    "SourceClassificationResult",
    "DeterministicScoringModel",
    "VerificationScoreResult",
    "CriterionScore",
    "EvidenceEvaluator",
    "VerificationGates",
    "GateEvaluationResult",
    "VerificationEngine",
]
