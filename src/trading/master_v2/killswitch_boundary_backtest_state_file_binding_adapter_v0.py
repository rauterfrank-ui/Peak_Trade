# src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
KillSwitch boundary semantics via the Surface K offline replay adapter.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from trading.master_v2.double_play_entry_exit_policy_v0 import (
    PositionState,
    ReconciliationState,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KILLSWITCH_FENCING_OWNER,
    KillSwitchBoundaryMode,
    KillSwitchBoundaryOfflineReplayBindingResultV0,
    KillSwitchBoundaryOfflineReplayContextV0,
    bind_killswitch_boundary_offline_replay_evidence_v0,
    killswitch_boundary_binding_non_authority_boundary_ok_v0,
)

KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0"
)
KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "killswitch_boundary_backtest_state_file_v0"
)

_VALID_BOUNDARY_MODES = frozenset(mode.value for mode in KillSwitchBoundaryMode)


@dataclass(frozen=True)
class KillSwitchBacktestStateFileRecordV0:
    """Parsed KillSwitch backtest state-file payload."""

    killswitch_boundary_mode: str
    fencing_digest_ref: str
    state_file_digest_ref: str
    prior_killswitch_active: bool = False
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class KillSwitchBoundaryBacktestStateFileEvidenceV0:
    killswitch_boundary_backtest_state_file_bound: bool
    killswitch_boundary_mode: str
    no_new_positions: bool
    no_position_increase: bool
    cancel_pending_required: bool
    reduce_to_flat_required: bool
    emergency_flatten_required: bool
    reconciliation_required: bool
    fencing_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: KillSwitchBoundaryOfflineReplayBindingResultV0
    surface_k_adapter_owner_ref: str
    killswitch_fencing_owner_ref: str


def _canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    stripped = {k: v for k, v in payload.items() if k != "state_file_digest_ref"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_backtest_state_file_digest_v0(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_backtest_state_file_digest_from_payload_v0(payload: Mapping[str, Any]) -> str:
    return compute_backtest_state_file_digest_v0(_canonical_payload_bytes(payload))


def _parse_boundary_mode(raw: object) -> KillSwitchBoundaryMode:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("killswitch_boundary_mode_missing")
    normalized = raw.strip().lower()
    if normalized not in _VALID_BOUNDARY_MODES:
        raise ValueError(f"killswitch_boundary_mode_invalid:{normalized}")
    return KillSwitchBoundaryMode(normalized)


def parse_killswitch_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> KillSwitchBacktestStateFileRecordV0:
    """Parse backtest KillSwitch state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("killswitch_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("killswitch_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("killswitch_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("killswitch_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("killswitch_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("killswitch_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if schema_version and schema_version != KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION:
        raise ValueError("killswitch_backtest_state_file_schema_version_mismatch")

    mode = _parse_boundary_mode(decoded.get("killswitch_boundary_mode"))
    fencing_digest_ref = str(decoded.get("fencing_digest_ref", "")).strip()
    if not fencing_digest_ref:
        raise ValueError("fencing_digest_ref_missing")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("killswitch_backtest_state_file_digest_mismatch")

    prior_active = bool(decoded.get("prior_killswitch_active", False))
    return KillSwitchBacktestStateFileRecordV0(
        killswitch_boundary_mode=mode.value,
        fencing_digest_ref=fencing_digest_ref,
        state_file_digest_ref=state_file_digest_ref,
        prior_killswitch_active=prior_active,
        raw_payload=dict(decoded),
    )


def verify_killswitch_backtest_state_file_digest_v0(
    record: KillSwitchBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("killswitch_backtest_state_file_digest_mismatch")


def _derive_reconciliation_required(
    boundary: KillSwitchBoundaryOfflineReplayBindingResultV0,
) -> bool:
    return boundary.boundary.reconciliation_precedence_blocks_new_exposure or any(
        code in boundary.boundary.reason_codes
        for code in ("reconciliation_required", "position_reconciliation_required")
    )


def _derive_no_new_positions(mode: KillSwitchBoundaryMode, *, active: bool) -> bool:
    return active and mode in (
        KillSwitchBoundaryMode.BLOCK_NEW,
        KillSwitchBoundaryMode.NO_NEW_POSITIONS,
        KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
    )


def bind_killswitch_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: KillSwitchBacktestStateFileRecordV0,
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILED,
    position_state: PositionState | None = None,
) -> KillSwitchBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file KillSwitch mode through the Surface K offline adapter."""
    pos_state = position_state if position_state is not None else PositionState.FLAT_RECONCILED
    mode = KillSwitchBoundaryMode(state_file.killswitch_boundary_mode)
    active = mode is not KillSwitchBoundaryMode.NORMAL
    offline_binding = bind_killswitch_boundary_offline_replay_evidence_v0(
        evidence,
        context=KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=mode,
            killswitch_active=active,
            prior_killswitch_active=state_file.prior_killswitch_active,
            reconciliation_state=reconciliation_state,
            position_state=pos_state,
        ),
    )
    if not killswitch_boundary_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("killswitch_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    return KillSwitchBoundaryBacktestStateFileEvidenceV0(
        killswitch_boundary_backtest_state_file_bound=True,
        killswitch_boundary_mode=mode.value,
        no_new_positions=_derive_no_new_positions(mode, active=active),
        no_position_increase=boundary.no_position_increase,
        cancel_pending_required=boundary.cancel_pending_boundary_only,
        reduce_to_flat_required=boundary.reduce_to_flat_boundary_only,
        emergency_flatten_required=boundary.emergency_flatten_boundary_only,
        reconciliation_required=_derive_reconciliation_required(offline_binding),
        fencing_digest_ref=state_file.fencing_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_k_adapter_owner_ref=KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
        killswitch_fencing_owner_ref=KILLSWITCH_FENCING_OWNER,
    )


def evaluate_backtest_state_file_boundary_only_v0(
    state_file: KillSwitchBacktestStateFileRecordV0,
) -> KillSwitchBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-killswitch-state-file-stub",
        replay_id="backtest-killswitch-state-file-stub",
        instrument_id="backtest-stub",
        trading_epoch=0,
        composition_result_id="stub",
        entry_exit_policy_ref="stub",
        selected_side="none",
        decision_outcome="observe",
        reason_codes=("stub",),
        decision_precedence_trace=("stub",),
        config_digest="stub",
        implementation_digest="stub",
    )
    return bind_killswitch_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_killswitch_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: KillSwitchBoundaryBacktestStateFileEvidenceV0,
    has_existing_position: bool = False,
) -> int:
    """Fail-closed backtest exposure representation — no runtime orders."""
    if position_signal == 0:
        return 0
    mode = KillSwitchBoundaryMode(evidence.killswitch_boundary_mode)
    if mode is KillSwitchBoundaryMode.BLOCK_NEW:
        return 0
    if mode is KillSwitchBoundaryMode.NO_NEW_POSITIONS:
        return position_signal if has_existing_position else 0
    if evidence.no_position_increase and position_signal != 0:
        return 0
    if evidence.emergency_flatten_required and position_signal != 0:
        return 0
    if evidence.reconciliation_required and position_signal != 0:
        return 0
    if evidence.no_new_positions and position_signal != 0:
        return 0
    return position_signal


def backtest_state_file_binding_non_authority_ok_v0(
    evidence: KillSwitchBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.killswitch_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    return killswitch_boundary_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_killswitch_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> KillSwitchBacktestStateFileRecordV0:
    record = parse_killswitch_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_killswitch_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
