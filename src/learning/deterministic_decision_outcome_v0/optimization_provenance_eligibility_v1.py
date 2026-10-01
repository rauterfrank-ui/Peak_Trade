"""Optimization provenance eligibility gate v1 — prevents silent cross-class pooling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    OutcomeSemanticClassV1,
    validate_outcome_evidence_provenance_v1,
)

GATE_ID: Final[str] = "peak_trade.learning.ddo.optimization_provenance_eligibility_v1"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"


@dataclass(frozen=True)
class OptimizationEligibilityResultV1:
    admitted: bool
    reason_code: str
    outcome_semantic_class: str
    provenance_digest: str | None
    evidence_pool_class: str | None


def evaluate_optimization_provenance_eligibility_v1(
    learning_evidence: Mapping[str, Any],
) -> OptimizationEligibilityResultV1:
    oclass = str(learning_evidence.get("outcome_semantic_class") or UNKNOWN_TOKEN)
    digest = learning_evidence.get("outcome_evidence_provenance_digest")
    pool = learning_evidence.get("evidence_pool_class")
    block = learning_evidence.get("outcome_evidence_provenance")
    if block is None:
        return OptimizationEligibilityResultV1(
            admitted=False,
            reason_code="LEARNING_EVIDENCE_MISSING_PROVENANCE",
            outcome_semantic_class=oclass,
            provenance_digest=None,
            evidence_pool_class=None,
        )
    provenance = validate_outcome_evidence_provenance_v1(block)
    oclass = str(provenance["outcome_semantic_class"])
    digest = str(provenance["provenance_digest"])
    pool = oclass
    status = str(provenance["provenance_status"])
    if status in {"UNKNOWN", "AMBIGUOUS"}:
        return OptimizationEligibilityResultV1(
            admitted=False,
            reason_code=f"PROVENANCE_STATUS_{status}",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
            evidence_pool_class=pool,
        )
    if oclass in {OutcomeSemanticClassV1.UNKNOWN.value, OutcomeSemanticClassV1.AMBIGUOUS.value}:
        return OptimizationEligibilityResultV1(
            admitted=False,
            reason_code=f"OUTCOME_SEMANTIC_CLASS_{oclass}",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
            evidence_pool_class=pool,
        )
    if pool != oclass:
        return OptimizationEligibilityResultV1(
            admitted=False,
            reason_code="EVIDENCE_POOL_CLASS_MISMATCH",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
            evidence_pool_class=pool,
        )
    return OptimizationEligibilityResultV1(
        admitted=True,
        reason_code="ADMITTED_OFFLINE_RESEARCH",
        outcome_semantic_class=oclass,
        provenance_digest=digest,
        evidence_pool_class=pool,
    )


UNKNOWN_TOKEN: Final[str] = "UNKNOWN"


def require_optimization_provenance_eligibility_v1(
    learning_evidence: Mapping[str, Any],
) -> OptimizationEligibilityResultV1:
    result = evaluate_optimization_provenance_eligibility_v1(learning_evidence)
    if not result.admitted:
        raise DdoValidationError(result.reason_code)
    return result


def assert_optimization_pool_compatible_v1(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> None:
    """Fail closed when aggregating evidence from incompatible semantic classes."""
    a = evaluate_optimization_provenance_eligibility_v1(left)
    b = evaluate_optimization_provenance_eligibility_v1(right)
    if not a.admitted or not b.admitted:
        raise DdoValidationError("OPTIMIZATION_POOL_INELIGIBLE_EVIDENCE")
    if a.evidence_pool_class != b.evidence_pool_class:
        raise DdoValidationError("OPTIMIZATION_INCOMPATIBLE_EVIDENCE_CLASSES")
