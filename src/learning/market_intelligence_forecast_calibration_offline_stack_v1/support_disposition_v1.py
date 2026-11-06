"""Evidence support / abstention disposition for MI forecasts (no fabricated confidence)."""

from __future__ import annotations

from typing import Final

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

SUPPORT_SUFFICIENT_EVIDENCE: Final[str] = "SUFFICIENT_EVIDENCE"
SUPPORT_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"
SUPPORT_NOT_EVALUABLE: Final[str] = "NOT_EVALUABLE"

ALLOWED_SUPPORT_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    {
        SUPPORT_SUFFICIENT_EVIDENCE,
        SUPPORT_INSUFFICIENT_EVIDENCE,
        SUPPORT_NOT_EVALUABLE,
    }
)

EVALUABILITY_SUFFICIENT: Final[str] = SUPPORT_SUFFICIENT_EVIDENCE
EVALUABILITY_INSUFFICIENT: Final[str] = SUPPORT_INSUFFICIENT_EVIDENCE
EVALUABILITY_NOT_EVALUABLE: Final[str] = SUPPORT_NOT_EVALUABLE


def require_support_disposition(value: object, field: str) -> str:
    token = str(value or "").strip()
    if token not in ALLOWED_SUPPORT_DISPOSITIONS:
        raise DdoValidationError(f"INVALID_SUPPORT_DISPOSITION:{field}")
    return token
