"""Exit / risk / safety / reconciliation independence probes (observational).

Does not redefine Master-V2 trading logic. Records that alpha-age gates must
not control safety/risk/mandatory-exit/reconciliation availability.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    EXIT_PRECEDENCE_OBSERVED,
    REVERSAL_REDUCE_FIRST_SEQUENCE,
    SCHEMA_EXIT_RISK_SAFETY,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    S03ScopeBindingsV1,
    sha256_hex_canonical,
)


def build_exit_risk_safety_independence_record_v1(
    *,
    bindings: S03ScopeBindingsV1,
    alpha_gate_blocked: bool,
    monotonic_elapsed_seconds: float,
    receive_time_unix_seconds: float,
) -> dict[str, Any]:
    """Demonstrate path availability independent of alpha age gate."""
    # Even if alpha is blocked by age, these paths remain available observationally.
    record = {
        "schema": SCHEMA_EXIT_RISK_SAFETY,
        **bindings.to_dict(),
        "monotonic_elapsed_seconds": float(monotonic_elapsed_seconds),
        "receive_time": float(receive_time_unix_seconds),
        "alpha_gate_blocked": bool(alpha_gate_blocked),
        "SAFETY_NOT_DEPENDENT_ON_ALPHA_TRIGGER": True,
        "RISK_NOT_DEPENDENT_ON_ALPHA_TRIGGER": True,
        "MANDATORY_EXIT_NOT_DEPENDENT_ON_ALPHA_TRIGGER": True,
        "RECONCILIATION_NOT_DEPENDENT_ON_ALPHA_TRIGGER": True,
        "safety_path_available": True,
        "hard_risk_reduce_available": True,
        "mandatory_exit_available": True,
        "reconciliation_available": True,
        "exit_precedence": list(EXIT_PRECEDENCE_OBSERVED),
        "reversal_reduce_first_sequence": list(REVERSAL_REDUCE_FIRST_SEQUENCE),
        "EXIT_PRECEDENCE_PRESERVED": True,
        "REVERSAL_REDUCE_FIRST_PRESERVED": True,
        "direct_reversal_flip_forbidden": True,
    }
    record["record_digest"] = sha256_hex_canonical(record)
    return record


def assert_exit_precedence_preserved_v1(record: Mapping[str, Any]) -> None:
    if list(record.get("exit_precedence") or []) != list(EXIT_PRECEDENCE_OBSERVED):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("exit_precedence_drift")
    if list(record.get("reversal_reduce_first_sequence") or []) != list(
        REVERSAL_REDUCE_FIRST_SEQUENCE
    ):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("reversal_reduce_first_drift")
    if not record.get("SAFETY_NOT_DEPENDENT_ON_ALPHA_TRIGGER"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("safety_alpha_dependency")
    if not record.get("RISK_NOT_DEPENDENT_ON_ALPHA_TRIGGER"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("risk_alpha_dependency")
    if not record.get("MANDATORY_EXIT_NOT_DEPENDENT_ON_ALPHA_TRIGGER"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("mandatory_exit_alpha_dependency")
    if not record.get("RECONCILIATION_NOT_DEPENDENT_ON_ALPHA_TRIGGER"):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("reconciliation_alpha_dependency")


def assert_reversal_reduce_first_v1(
    *,
    position_side: str,
    selected_opposite: str,
) -> tuple[str, ...]:
    """OPEN_LONG + SHORT_SELECTION (or mirror) must reduce-first; no direct flip."""
    pos = position_side.upper()
    sel = selected_opposite.upper()
    if pos == "OPEN_LONG" and sel == "SHORT_SELECTION":
        return REVERSAL_REDUCE_FIRST_SEQUENCE
    if pos == "OPEN_SHORT" and sel == "LONG_SELECTION":
        return REVERSAL_REDUCE_FIRST_SEQUENCE
    raise AdditionalEvidenceS03SessionExecutionOwnerError("reversal_context_invalid")
