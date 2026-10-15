"""Fail-closed CURRENT proof eligibility (R1-B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.ops.ghv_forensic_source_provenance_v1.provenance_contract_v1 import (
    SourceDirtyStatus,
    SourceValidationMode,
)


@dataclass(frozen=True)
class ProofEligibilityResultV1:
    proof_eligibility: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "PROOF_ELIGIBILITY": self.proof_eligibility,
            "PROOF_ELIGIBILITY_REASONS": list(self.reasons),
        }


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def evaluate_proof_eligibility_v1(
    *,
    declared_current_sha: str | None,
    actual_source_sha: str | None,
    ghv_source_sha: str | None,
    test_execution_sha: str | None,
    source_dirty_status: SourceDirtyStatus,
    source_validation_mode: SourceValidationMode,
    current_graph_verified: bool | None,
    snapshot_binding_verified: bool | None,
    source_validation_pass_reported: bool | None,
    source_validation_pass_composed_field: bool | None,
    crosswalk_execution_success: bool | None,
    ghv_evidence_attached: bool | None,
    evidence_repository_sha: str | None,
    workspace_read_declared_pin: bool = False,
) -> ProofEligibilityResultV1:
    reasons: list[str] = []

    if not declared_current_sha:
        reasons.append("MISSING_PROVENANCE")
    if not actual_source_sha:
        reasons.append("MISSING_PROVENANCE")
    if not ghv_source_sha:
        reasons.append("MISSING_PROVENANCE")

    if declared_current_sha and actual_source_sha and declared_current_sha != actual_source_sha:
        reasons.append("SOURCE_SHA_MISMATCH")

    if source_dirty_status == SourceDirtyStatus.DIRTY:
        reasons.append("DIRTY_SOURCE_UNVERIFIED")
    elif source_dirty_status == SourceDirtyStatus.UNKNOWN:
        reasons.append("SOURCE_TREE_UNVERIFIED")

    if source_validation_mode == SourceValidationMode.NAVIGATION_ONLY:
        reasons.append("NAVIGATION_ONLY")

    if source_validation_mode == SourceValidationMode.UNKNOWN:
        reasons.append("STRICT_VALIDATION_MISSING")

    if source_validation_mode == SourceValidationMode.STRICT_CURRENT:
        if source_validation_pass_reported is not True:
            reasons.append("STRICT_VALIDATION_MISSING")
        if crosswalk_execution_success is not True:
            reasons.append("STRICT_VALIDATION_MISSING")

    if current_graph_verified is not True:
        if source_validation_pass_composed_field is True or source_validation_pass_reported is True:
            reasons.append("SOURCE_VALIDATION_PASS_SEMANTICS")
        if current_graph_verified is False:
            if "SOURCE_VALIDATION_PASS_SEMANTICS" not in reasons:
                reasons.append("SOURCE_VALIDATION_PASS_SEMANTICS")

    if snapshot_binding_verified is not True:
        reasons.append("SNAPSHOT_BINDING_UNVERIFIED")

    if evidence_repository_sha and actual_source_sha:
        if evidence_repository_sha != actual_source_sha:
            reasons.append("GHV_SOURCE_MISMATCH")
    if ghv_source_sha and actual_source_sha and ghv_source_sha != actual_source_sha:
        reasons.append("GHV_SOURCE_MISMATCH")

    if (
        source_validation_pass_composed_field is not None
        and source_validation_pass_reported is not None
        and source_validation_pass_composed_field != source_validation_pass_reported
    ):
        reasons.append("CONTRADICTORY_PROVENANCE")

    if not test_execution_sha:
        reasons.append("TEST_EXECUTION_SOURCE_UNKNOWN")
    elif declared_current_sha and test_execution_sha != declared_current_sha:
        reasons.append("TEST_EXECUTION_SOURCE_UNKNOWN")

    if workspace_read_declared_pin:
        reasons.append("SOURCE_TREE_UNVERIFIED")

    if (
        source_validation_mode == SourceValidationMode.STRICT_CURRENT
        and current_graph_verified is False
    ):
        if "NAVIGATION_ONLY" not in reasons:
            pass  # covered by snapshot / semantics reasons

    unique = tuple(dict.fromkeys(reasons))
    eligible = len(unique) == 0
    return ProofEligibilityResultV1(proof_eligibility=eligible, reasons=unique)
