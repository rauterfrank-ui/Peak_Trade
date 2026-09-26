"""Evidence bundle for F1/M9 Owner threshold value ratification (600s)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

EVIDENCE_SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_scoped_owner_threshold_value_ratification_evidence/v1"
)


class F1M9ThresholdRatificationPhaseStateV1(str, Enum):
    RATIFICATION_DENIED = "RATIFICATION_DENIED"
    RATIFICATION_COMPLETED = "RATIFICATION_COMPLETED"


@dataclass(frozen=True, slots=True)
class F1M9ThresholdValueRatificationStateEvidenceV1:
    phase_state: F1M9ThresholdRatificationPhaseStateV1
    reason_codes: tuple[str, ...]
    threshold_value_authorized: bool
    threshold_numeric_max_age_seconds: float | None
    owner_threshold_record_digest: str | None
    threshold_ledger_entry_digest: str | None
    configuration_digest_after_threshold: str | None
    scoped_owner_threshold_value_authorized: bool
    threshold_value_ratified: bool
    productive_activation_authorized: bool
    execution_evidence_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_digest_after_threshold": self.configuration_digest_after_threshold,
            "execution_evidence_digest": self.execution_evidence_digest,
            "owner_threshold_record_digest": self.owner_threshold_record_digest,
            "phase_state": self.phase_state.value,
            "productive_activation_authorized": self.productive_activation_authorized,
            "reason_codes": list(self.reason_codes),
            "scoped_owner_threshold_value_authorized": self.scoped_owner_threshold_value_authorized,
            "threshold_ledger_entry_digest": self.threshold_ledger_entry_digest,
            "threshold_numeric_max_age_seconds": self.threshold_numeric_max_age_seconds,
            "threshold_value_authorized": self.threshold_value_authorized,
            "threshold_value_ratified": self.threshold_value_ratified,
        }


def build_threshold_ratification_state_evidence_v1(
    *,
    phase_state: F1M9ThresholdRatificationPhaseStateV1,
    reason_codes: tuple[str, ...],
    threshold_value_authorized: bool,
    threshold_numeric_max_age_seconds: float | None,
    owner_threshold_record_digest: str | None,
    threshold_ledger_entry_digest: str | None,
    configuration_digest_after_threshold: str | None,
    scoped_owner_threshold_value_authorized: bool,
    threshold_value_ratified: bool,
    productive_activation_authorized: bool,
) -> F1M9ThresholdValueRatificationStateEvidenceV1:
    body = {
        "phase_state": phase_state.value,
        "reason_codes": list(reason_codes),
        "threshold_value_authorized": threshold_value_authorized,
        "threshold_numeric_max_age_seconds": threshold_numeric_max_age_seconds,
        "owner_threshold_record_digest": owner_threshold_record_digest,
        "threshold_ledger_entry_digest": threshold_ledger_entry_digest,
        "configuration_digest_after_threshold": configuration_digest_after_threshold,
        "scoped_owner_threshold_value_authorized": scoped_owner_threshold_value_authorized,
        "threshold_value_ratified": threshold_value_ratified,
        "productive_activation_authorized": productive_activation_authorized,
    }
    digest = compute_content_sha256(body)
    return F1M9ThresholdValueRatificationStateEvidenceV1(
        phase_state=phase_state,
        reason_codes=reason_codes,
        threshold_value_authorized=threshold_value_authorized,
        threshold_numeric_max_age_seconds=threshold_numeric_max_age_seconds,
        owner_threshold_record_digest=owner_threshold_record_digest,
        threshold_ledger_entry_digest=threshold_ledger_entry_digest,
        configuration_digest_after_threshold=configuration_digest_after_threshold,
        scoped_owner_threshold_value_authorized=scoped_owner_threshold_value_authorized,
        threshold_value_ratified=threshold_value_ratified,
        productive_activation_authorized=productive_activation_authorized,
        execution_evidence_digest=digest,
    )


__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "F1M9ThresholdRatificationPhaseStateV1",
    "F1M9ThresholdValueRatificationStateEvidenceV1",
    "build_threshold_ratification_state_evidence_v1",
]
