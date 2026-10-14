"""Derive capital-guard recovery exposure signals from durable atomic one-shot state.

Uses existing atomic ledger readers only. Does not apply reconciliation outcomes,
mutate atomic state, or authorize POST/capital release.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    CanaryAtomicOneShotError,
    STATE_AVAILABLE,
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_SUBMITTED_ACKNOWLEDGED,
    STATE_TERMINAL_RECONCILED,
    load_atomic_authorization_state_v1,
)

CONTRACT_ID = "FULL_CORE_RECOVERY_GUARD_EXPOSURE_SIGNALS_V1"


@dataclass(frozen=True)
class FullCoreRecoveryGuardExposureSignalsV1:
    unknown_submit_active: bool
    recovery_state_clear: bool
    durable_atomic_state: str

    def to_dict(self) -> dict[str, bool | str]:
        return {
            "unknown_submit_active": self.unknown_submit_active,
            "recovery_state_clear": self.recovery_state_clear,
            "durable_atomic_state": self.durable_atomic_state,
            "contract_id": CONTRACT_ID,
        }


def derive_full_core_recovery_guard_exposure_signals_v1(
    *,
    state_dir: Path,
    consumption_key: str,
    expected_binding_digest: str | None = None,
) -> FullCoreRecoveryGuardExposureSignalsV1:
    """Map durable atomic state to guard recovery signals (fail-closed on ledger errors)."""
    key = str(consumption_key or "").strip()
    if not key:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=True,
            recovery_state_clear=False,
            durable_atomic_state=STATE_HALTED_UNRESOLVED,
        )
    try:
        row = load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=key)
    except CanaryAtomicOneShotError:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=True,
            recovery_state_clear=False,
            durable_atomic_state=STATE_HALTED_UNRESOLVED,
        )
    if row is None:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=False,
            recovery_state_clear=True,
            durable_atomic_state=STATE_AVAILABLE,
        )
    expected = str(expected_binding_digest or "").strip()
    observed = str(row.binding_digest or "").strip()
    if expected and observed and observed != expected:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=True,
            recovery_state_clear=False,
            durable_atomic_state=STATE_HALTED_UNRESOLVED,
        )
    state = str(row.state or STATE_HALTED_UNRESOLVED).strip()
    if state == STATE_TERMINAL_RECONCILED:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=False,
            recovery_state_clear=True,
            durable_atomic_state=state,
        )
    if state in {
        STATE_SUBMIT_MAY_HAVE_OCCURRED,
        STATE_HALTED_UNRESOLVED,
    }:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=True,
            recovery_state_clear=False,
            durable_atomic_state=state,
        )
    if state in {
        STATE_RECONCILIATION_PENDING,
        STATE_SUBMITTED_ACKNOWLEDGED,
        STATE_RESERVED_PRE_POST,
    }:
        return FullCoreRecoveryGuardExposureSignalsV1(
            unknown_submit_active=False,
            recovery_state_clear=False,
            durable_atomic_state=state,
        )
    return FullCoreRecoveryGuardExposureSignalsV1(
        unknown_submit_active=True,
        recovery_state_clear=False,
        durable_atomic_state=state or STATE_HALTED_UNRESOLVED,
    )


def merge_recovery_guard_exposure_evidence_v1(
    *,
    exposure_evidence: "CanaryCapitalGuardExposureEvidenceV1",
    atomic_signals: FullCoreRecoveryGuardExposureSignalsV1,
) -> "CanaryCapitalGuardExposureEvidenceV1":
    """Combine exchange-local exposure counts with authoritative atomic recovery signals."""
    from dataclasses import replace

    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
        CanaryCapitalGuardExposureEvidenceV1,
    )

    unknown = bool(atomic_signals.unknown_submit_active or exposure_evidence.unknown_submit_active)
    recovery_clear = bool(
        atomic_signals.recovery_state_clear and exposure_evidence.recovery_state_clear
    )
    return replace(
        exposure_evidence,
        unknown_submit_active=unknown,
        recovery_state_clear=recovery_clear,
    )


def compose_capital_guard_exposure_evidence_v1(
    *,
    exposure_evidence: "CanaryCapitalGuardExposureEvidenceV1 | None",
    atomic_signals: FullCoreRecoveryGuardExposureSignalsV1,
) -> "CanaryCapitalGuardExposureEvidenceV1":
    """Build guard exposure evidence from optional exchange-local counts + atomic recovery."""
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
        CanaryCapitalGuardExposureEvidenceV1,
    )

    if exposure_evidence is None:
        return CanaryCapitalGuardExposureEvidenceV1(
            open_order_count=0,
            open_position_count=0,
            unknown_submit_active=atomic_signals.unknown_submit_active,
            recovery_state_clear=atomic_signals.recovery_state_clear,
            transport_retry_count=0,
        )
    return merge_recovery_guard_exposure_evidence_v1(
        exposure_evidence=exposure_evidence,
        atomic_signals=atomic_signals,
    )


__all__ = [
    "CONTRACT_ID",
    "FullCoreRecoveryGuardExposureSignalsV1",
    "compose_capital_guard_exposure_evidence_v1",
    "derive_full_core_recovery_guard_exposure_signals_v1",
    "merge_recovery_guard_exposure_evidence_v1",
]
