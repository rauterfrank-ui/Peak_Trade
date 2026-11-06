"""Explicit F1/M9 scoped Owner Apply execution state evidence (no state aliasing)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

EVIDENCE_SCHEMA_VERSION: Final[str] = "governed_f1_m9_scoped_owner_apply_execution_evidence/v1"


class F1M9ApplyExecutionPhaseStateV1(str, Enum):
    CONFIGURATION_MATERIALIZED = "CONFIGURATION_MATERIALIZED"
    APPLY_AUTHORIZED = "APPLY_AUTHORIZED"
    APPLY_STARTED = "APPLY_STARTED"
    CONFIGURATION_RUNTIME_APPLIED = "CONFIGURATION_RUNTIME_APPLIED"
    APPLY_COMPLETED = "APPLY_COMPLETED"
    APPLY_DENIED = "APPLY_DENIED"


@dataclass(frozen=True, slots=True)
class F1M9ApplyExecutionStateEvidenceV1:
    phase_state: F1M9ApplyExecutionPhaseStateV1
    reason_codes: tuple[str, ...]
    configuration_materialized: bool
    apply_authorized: bool
    apply_started: bool
    configuration_runtime_applied: bool
    apply_completed: bool
    threshold_value_ratified: bool
    candidate_value_applied: bool
    execution_evidence_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_authorized": self.apply_authorized,
            "apply_completed": self.apply_completed,
            "apply_started": self.apply_started,
            "candidate_value_applied": self.candidate_value_applied,
            "configuration_materialized": self.configuration_materialized,
            "configuration_runtime_applied": self.configuration_runtime_applied,
            "execution_evidence_digest": self.execution_evidence_digest,
            "phase_state": self.phase_state.value,
            "reason_codes": list(self.reason_codes),
            "threshold_value_ratified": self.threshold_value_ratified,
        }


def build_apply_execution_state_evidence_v1(
    *,
    phase_state: F1M9ApplyExecutionPhaseStateV1,
    reason_codes: tuple[str, ...],
    configuration_materialized: bool,
    apply_authorized: bool,
    apply_started: bool,
    configuration_runtime_applied: bool,
    apply_completed: bool,
    threshold_value_ratified: bool,
    candidate_value_applied: bool,
    owner_apply_record_digest: str | None,
    configuration_digest: str | None,
) -> F1M9ApplyExecutionStateEvidenceV1:
    body: Mapping[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "phase_state": phase_state.value,
        "configuration_materialized": configuration_materialized,
        "apply_authorized": apply_authorized,
        "apply_started": apply_started,
        "configuration_runtime_applied": configuration_runtime_applied,
        "apply_completed": apply_completed,
        "threshold_value_ratified": threshold_value_ratified,
        "candidate_value_applied": candidate_value_applied,
        "owner_apply_record_digest": owner_apply_record_digest,
        "configuration_digest": configuration_digest,
        "reason_codes": list(reason_codes),
    }
    digest = compute_content_sha256(dict(body))
    return F1M9ApplyExecutionStateEvidenceV1(
        phase_state=phase_state,
        reason_codes=reason_codes,
        configuration_materialized=configuration_materialized,
        apply_authorized=apply_authorized,
        apply_started=apply_started,
        configuration_runtime_applied=configuration_runtime_applied,
        apply_completed=apply_completed,
        threshold_value_ratified=threshold_value_ratified,
        candidate_value_applied=candidate_value_applied,
        execution_evidence_digest=digest,
    )


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "F1M9ApplyExecutionPhaseStateV1",
    "F1M9ApplyExecutionStateEvidenceV1",
    "build_apply_execution_state_evidence_v1",
]
