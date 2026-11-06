"""Honest structural vs realized outcome completeness for GHV intelligence lineage."""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    FillSourceTypeV1,
    OutcomeRealizationKindV1,
)

STRUCTURAL_COMPLETE: Final[str] = "STRUCTURAL_COMPLETE"
STRUCTURAL_PARTIAL: Final[str] = "STRUCTURAL_PARTIAL"
STRUCTURAL_UNAVAILABLE: Final[str] = "UNAVAILABLE"

REALIZED_COMPLETE: Final[str] = "REALIZED_COMPLETE"
REALIZED_UNAVAILABLE: Final[str] = "UNAVAILABLE"


def derive_structural_outcome_completeness_v1(
    learning_evidence: Mapping[str, Any],
) -> str:
    """Structural closure from legal learning-evidence fields only."""
    if not learning_evidence:
        return STRUCTURAL_UNAVAILABLE
    decision_ref = str(learning_evidence.get("decision_event_ref") or "")
    actual_ref = str(learning_evidence.get("actual_outcome_ref") or "")
    source_state = str(learning_evidence.get("source_learning_state_record_ref") or "")
    semantic = str(learning_evidence.get("outcome_semantic_class") or "")
    if not decision_ref or not source_state or semantic in {"", "UNKNOWN", "AMBIGUOUS"}:
        return STRUCTURAL_PARTIAL
    if not actual_ref or actual_ref in {"UNKNOWN", ""}:
        return STRUCTURAL_PARTIAL
    return STRUCTURAL_COMPLETE


def derive_realized_economic_completeness_v1(
    learning_evidence: Mapping[str, Any],
) -> str:
    """Realized economics require venue fill lifecycle; never inferred from simulation."""
    provenance = learning_evidence.get("outcome_evidence_provenance") or {}
    if not isinstance(provenance, dict):
        return REALIZED_UNAVAILABLE
    fill = str(provenance.get("fill_source_type") or "")
    realization = str(provenance.get("outcome_realization_kind") or "")
    if fill in {FillSourceTypeV1.VENUE_LIVE.value, FillSourceTypeV1.VENUE_TESTNET.value} and (
        realization == OutcomeRealizationKindV1.REALIZED.value
    ):
        return REALIZED_COMPLETE
    return REALIZED_UNAVAILABLE


__all__ = [
    "REALIZED_COMPLETE",
    "REALIZED_UNAVAILABLE",
    "STRUCTURAL_COMPLETE",
    "STRUCTURAL_PARTIAL",
    "STRUCTURAL_UNAVAILABLE",
    "derive_realized_economic_completeness_v1",
    "derive_structural_outcome_completeness_v1",
]
