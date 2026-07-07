# src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
Safety Kernel semantics via the Surface J offline replay adapter.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
)
from src.meta.learning_loop.runtime_eligibility_v1 import (
    CONTRACT_NAME as RUNTIME_ELIGIBILITY_CONTRACT_NAME,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    SafetyKernelOfflineReplayBindingResultV0,
    SafetyKernelOfflineReplayContextV0,
    bind_safety_kernel_offline_replay_evidence_v0,
    safety_kernel_binding_non_authority_boundary_ok_v0,
)

SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0"
)
SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "safety_kernel_boundary_backtest_state_file_v0"
)

_VALID_SAFETY_MODES = frozenset(mode.value for mode in SafetyMode)
_VALID_RECONCILIATION_STATES = frozenset(state.value for state in ReconciliationState)
_VALID_POSITION_STATES = frozenset(state.value for state in PositionState)
_VALID_TRADING_GATES = frozenset(gate.value for gate in TradingGate)


@dataclass(frozen=True)
class SafetyKernelBacktestStateFileRecordV0:
    """Parsed Safety Kernel backtest state-file payload."""

    safety_mode: str
    safety_exit_signal_triggered: bool
    safety_exit_signal_reason_code: str
    reconciliation_state: str
    position_state: str
    trading_gate: str
    killswitch_blocked: bool
    safety_decision_allowed: bool
    safety_kernel_owner_digest_ref: str
    killswitch_fencing_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class SafetyKernelBoundaryBacktestStateFileEvidenceV0:
    safety_kernel_boundary_backtest_state_file_bound: bool
    safety_policy_decision_represented: bool
    safety_block_reasons_represented: bool
    no_order_without_safety_pass_represented: bool
    safety_boundary_ref: str
    safety_boundary_effect: str
    hard_block_reasons: tuple[str, ...]
    adapter_compatible: bool
    safety_kernel_owner_digest_ref: str
    killswitch_fencing_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: SafetyKernelOfflineReplayBindingResultV0
    surface_j_adapter_owner_ref: str


def _canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    stripped = {k: v for k, v in payload.items() if k != "state_file_digest_ref"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_backtest_state_file_digest_v0(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_backtest_state_file_digest_from_payload_v0(payload: Mapping[str, Any]) -> str:
    return compute_backtest_state_file_digest_v0(_canonical_payload_bytes(payload))


def _parse_enum_value(
    raw: object,
    *,
    field_name: str,
    valid: frozenset[str],
    default: str | None = None,
) -> str:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if default is not None:
            return default
        raise ValueError(f"{field_name}_missing")
    if not isinstance(raw, str):
        raise ValueError(f"{field_name}_invalid")
    normalized = raw.strip().lower()
    if normalized not in valid:
        raise ValueError(f"{field_name}_invalid:{normalized}")
    return normalized


def parse_safety_kernel_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> SafetyKernelBacktestStateFileRecordV0:
    """Parse backtest Safety Kernel state file. Fail-closed on invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("safety_kernel_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("safety_kernel_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("safety_kernel_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("safety_kernel_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("safety_kernel_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("safety_kernel_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("safety_kernel_backtest_state_file_schema_version_mismatch")

    safety_mode = _parse_enum_value(
        decoded.get("safety_mode"),
        field_name="safety_mode",
        valid=_VALID_SAFETY_MODES,
        default=SafetyMode.NORMAL.value,
    )
    reconciliation_state = _parse_enum_value(
        decoded.get("reconciliation_state"),
        field_name="reconciliation_state",
        valid=_VALID_RECONCILIATION_STATES,
        default=ReconciliationState.RECONCILED.value,
    )
    position_state = _parse_enum_value(
        decoded.get("position_state"),
        field_name="position_state",
        valid=_VALID_POSITION_STATES,
        default=PositionState.FLAT_RECONCILED.value,
    )
    trading_gate = _parse_enum_value(
        decoded.get("trading_gate"),
        field_name="trading_gate",
        valid=_VALID_TRADING_GATES,
        default=TradingGate.ENTRY_ALLOWED.value,
    )

    owner_ref = str(decoded.get("safety_kernel_owner_digest_ref", "")).strip()
    if not owner_ref:
        raise ValueError("safety_kernel_owner_digest_ref_missing")
    if owner_ref != RUNTIME_ELIGIBILITY_CONTRACT_NAME:
        raise ValueError("safety_kernel_owner_digest_ref_mismatch")

    fencing_ref = str(decoded.get("killswitch_fencing_digest_ref", "")).strip()
    if not fencing_ref:
        raise ValueError("killswitch_fencing_digest_ref_missing")
    if fencing_ref != KILL_SWITCH_CONTRACT_DIGEST:
        raise ValueError("killswitch_fencing_digest_ref_mismatch")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("safety_kernel_backtest_state_file_digest_mismatch")

    return SafetyKernelBacktestStateFileRecordV0(
        safety_mode=safety_mode,
        safety_exit_signal_triggered=bool(decoded.get("safety_exit_signal_triggered", False)),
        safety_exit_signal_reason_code=str(
            decoded.get("safety_exit_signal_reason_code", "")
        ).strip(),
        reconciliation_state=reconciliation_state,
        position_state=position_state,
        trading_gate=trading_gate,
        killswitch_blocked=bool(decoded.get("killswitch_blocked", False)),
        safety_decision_allowed=bool(decoded.get("safety_decision_allowed", True)),
        safety_kernel_owner_digest_ref=owner_ref,
        killswitch_fencing_digest_ref=fencing_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_safety_kernel_backtest_state_file_digest_v0(
    record: SafetyKernelBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("safety_kernel_backtest_state_file_digest_mismatch")


def _context_from_state_file(
    state_file: SafetyKernelBacktestStateFileRecordV0,
) -> SafetyKernelOfflineReplayContextV0:
    return SafetyKernelOfflineReplayContextV0(
        safety_mode=SafetyMode(state_file.safety_mode),
        safety_exit_signal=PolicySignalV0(
            triggered=state_file.safety_exit_signal_triggered,
            reason_code=state_file.safety_exit_signal_reason_code or None,
        ),
        reconciliation_state=ReconciliationState(state_file.reconciliation_state),
        position_state=PositionState(state_file.position_state),
        trading_gate=TradingGate(state_file.trading_gate),
        killswitch_blocked=state_file.killswitch_blocked,
        safety_decision_allowed=state_file.safety_decision_allowed,
    )


def bind_safety_kernel_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: SafetyKernelBacktestStateFileRecordV0,
) -> SafetyKernelBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file Safety Kernel through the Surface J offline adapter."""
    offline_binding = bind_safety_kernel_offline_replay_evidence_v0(
        evidence,
        context=_context_from_state_file(state_file),
    )
    if not safety_kernel_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("safety_kernel_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    hard_block_reasons = boundary.hard_block_reasons
    safety_policy_decision_represented = bool(offline_binding.safety_boundary_ref)
    safety_block_reasons_represented = True
    no_order_without_safety_pass_represented = boundary.no_submission_before_permission
    return SafetyKernelBoundaryBacktestStateFileEvidenceV0(
        safety_kernel_boundary_backtest_state_file_bound=True,
        safety_policy_decision_represented=safety_policy_decision_represented,
        safety_block_reasons_represented=safety_block_reasons_represented,
        no_order_without_safety_pass_represented=no_order_without_safety_pass_represented,
        safety_boundary_ref=offline_binding.safety_boundary_ref,
        safety_boundary_effect=offline_binding.safety_boundary_effect,
        hard_block_reasons=hard_block_reasons,
        adapter_compatible=False,
        safety_kernel_owner_digest_ref=state_file.safety_kernel_owner_digest_ref,
        killswitch_fencing_digest_ref=state_file.killswitch_fencing_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_j_adapter_owner_ref=SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
    state_file: SafetyKernelBacktestStateFileRecordV0,
    *,
    decision_outcome: str = "enter_long",
) -> SafetyKernelBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-safety-kernel-state-file-stub",
        replay_id="backtest-safety-kernel-state-file-stub",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        composition_result_id="stub",
        entry_exit_policy_ref="stub",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("stub",),
        decision_precedence_trace=("stub",),
        config_digest="stub",
        implementation_digest="stub",
    )
    return bind_safety_kernel_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_safety_kernel_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: SafetyKernelBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Fail-closed backtest exposure representation — no runtime orders."""
    if position_signal == 0:
        return 0
    if not evidence.safety_kernel_boundary_backtest_state_file_bound:
        return 0
    if evidence.adapter_compatible:
        return 0
    if evidence.safety_boundary_effect != SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE:
        return 0
    if evidence.hard_block_reasons:
        return 0
    if not evidence.no_order_without_safety_pass_represented:
        return 0
    return position_signal


def backtest_safety_kernel_state_file_binding_non_authority_ok_v0(
    evidence: SafetyKernelBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.safety_kernel_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    if evidence.adapter_compatible:
        return False
    return safety_kernel_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_safety_kernel_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> SafetyKernelBacktestStateFileRecordV0:
    record = parse_safety_kernel_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_safety_kernel_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
