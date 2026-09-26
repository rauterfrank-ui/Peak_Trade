"""Evidence for F1/M9 governed productive runtime apply start (Owner GO)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

EVIDENCE_SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_evidence/v1"
)


class F1M9RuntimeApplyStartPhaseStateV1(str, Enum):
    DENIED = "RUNTIME_APPLY_START_DENIED"
    COMPLETED = "RUNTIME_APPLY_START_COMPLETED"


@dataclass(frozen=True, slots=True)
class F1M9RuntimeApplyStartStateEvidenceV1:
    phase_state: F1M9RuntimeApplyStartPhaseStateV1
    reason_codes: tuple[str, ...]
    productive_apply_occurred: bool
    runtime_apply_started: bool
    configuration_runtime_applied: bool
    owner_apply_record_digest: str | None
    owner_threshold_record_digest: str | None
    threshold_value_authorized: bool
    threshold_numeric_max_age_seconds: float | None
    threshold_enforcement_mechanical_continuation: bool
    presence_gate_transport_ready: bool
    productive_activation_authorized: bool
    execution_evidence_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_runtime_applied": self.configuration_runtime_applied,
            "execution_evidence_digest": self.execution_evidence_digest,
            "owner_apply_record_digest": self.owner_apply_record_digest,
            "owner_threshold_record_digest": self.owner_threshold_record_digest,
            "phase_state": self.phase_state.value,
            "presence_gate_transport_ready": self.presence_gate_transport_ready,
            "productive_activation_authorized": self.productive_activation_authorized,
            "productive_apply_occurred": self.productive_apply_occurred,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_started": self.runtime_apply_started,
            "threshold_enforcement_mechanical_continuation": (
                self.threshold_enforcement_mechanical_continuation
            ),
            "threshold_numeric_max_age_seconds": self.threshold_numeric_max_age_seconds,
            "threshold_value_authorized": self.threshold_value_authorized,
        }


def build_runtime_apply_start_state_evidence_v1(
    *,
    phase_state: F1M9RuntimeApplyStartPhaseStateV1,
    reason_codes: tuple[str, ...],
    productive_apply_occurred: bool,
    runtime_apply_started: bool,
    configuration_runtime_applied: bool,
    owner_apply_record_digest: str | None,
    owner_threshold_record_digest: str | None,
    threshold_value_authorized: bool,
    threshold_numeric_max_age_seconds: float | None,
    threshold_enforcement_mechanical_continuation: bool,
    presence_gate_transport_ready: bool,
    productive_activation_authorized: bool,
) -> F1M9RuntimeApplyStartStateEvidenceV1:
    body: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "phase_state": phase_state.value,
        "productive_apply_occurred": productive_apply_occurred,
        "runtime_apply_started": runtime_apply_started,
        "configuration_runtime_applied": configuration_runtime_applied,
        "owner_apply_record_digest": owner_apply_record_digest,
        "owner_threshold_record_digest": owner_threshold_record_digest,
        "threshold_value_authorized": threshold_value_authorized,
        "threshold_numeric_max_age_seconds": threshold_numeric_max_age_seconds,
        "threshold_enforcement_mechanical_continuation": (
            threshold_enforcement_mechanical_continuation
        ),
        "presence_gate_transport_ready": presence_gate_transport_ready,
        "productive_activation_authorized": productive_activation_authorized,
        "reason_codes": list(reason_codes),
    }
    digest = compute_content_sha256(body)
    return F1M9RuntimeApplyStartStateEvidenceV1(
        phase_state=phase_state,
        reason_codes=reason_codes,
        productive_apply_occurred=productive_apply_occurred,
        runtime_apply_started=runtime_apply_started,
        configuration_runtime_applied=configuration_runtime_applied,
        owner_apply_record_digest=owner_apply_record_digest,
        owner_threshold_record_digest=owner_threshold_record_digest,
        threshold_value_authorized=threshold_value_authorized,
        threshold_numeric_max_age_seconds=threshold_numeric_max_age_seconds,
        threshold_enforcement_mechanical_continuation=threshold_enforcement_mechanical_continuation,
        presence_gate_transport_ready=presence_gate_transport_ready,
        productive_activation_authorized=productive_activation_authorized,
        execution_evidence_digest=digest,
    )


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "F1M9RuntimeApplyStartPhaseStateV1",
    "F1M9RuntimeApplyStartStateEvidenceV1",
    "build_runtime_apply_start_state_evidence_v1",
]
