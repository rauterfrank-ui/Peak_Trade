# src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
reconciliation and unknown-outcome boundary semantics via the Surface L offline
replay adapter.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from meta.learning_loop.runtime_state_reconciliation_v1 import RECONCILIATION_CONTRACT_VERSION
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0 import (
    RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    ReconciliationUnknownOutcomeOfflineReplayBindingResultV0,
    ReconciliationUnknownOutcomeOfflineReplayContextV0,
    bind_reconciliation_unknown_outcome_offline_replay_evidence_v0,
    reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0,
)

RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0"
)
RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "reconciliation_boundary_backtest_state_file_v0"
)

_VALID_RECONCILIATION_STATES = frozenset(state.value for state in ReconciliationState)
_VALID_POSITION_STATES = frozenset(state.value for state in PositionState)
_VALID_EXISTING_POSITION_SIDES = frozenset(side.value for side in ExistingPositionSide)


@dataclass(frozen=True)
class ReconciliationBacktestStateFileRecordV0:
    """Parsed reconciliation backtest state-file payload."""

    reconciliation_state: str
    position_state: str
    venue_flat: bool
    existing_position_side: str
    intent_snapshot_unresolved: bool
    order_snapshot_unresolved: bool
    fill_snapshot_unresolved: bool
    reconciliation_owner_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ReconciliationBoundaryBacktestStateFileEvidenceV0:
    reconciliation_boundary_backtest_state_file_bound: bool
    reconciliation_state: str
    position_state: str
    submission_unknown_blocks_new_exposure: bool
    reconciliation_required_maps_to_reconcile_only: bool
    unknown_outcome_never_auto_resubmits: bool
    reconciled_flat_required_before_opposite_side: bool
    unresolved_reduce_blocks_opposite_side: bool
    venue_flat_alone_insufficient: bool
    no_auto_resubmit: bool
    reconciliation_owner_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: ReconciliationUnknownOutcomeOfflineReplayBindingResultV0
    surface_l_adapter_owner_ref: str


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


def parse_reconciliation_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> ReconciliationBacktestStateFileRecordV0:
    """Parse backtest reconciliation state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("reconciliation_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("reconciliation_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("reconciliation_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("reconciliation_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("reconciliation_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("reconciliation_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != RECONCILIATION_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("reconciliation_backtest_state_file_schema_version_mismatch")

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
    existing_position_side = _parse_enum_value(
        decoded.get("existing_position_side"),
        field_name="existing_position_side",
        valid=_VALID_EXISTING_POSITION_SIDES,
        default=ExistingPositionSide.NONE.value,
    )

    owner_ref = str(decoded.get("reconciliation_owner_digest_ref", "")).strip()
    if not owner_ref:
        raise ValueError("reconciliation_owner_digest_ref_missing")
    if owner_ref != RECONCILIATION_CONTRACT_VERSION:
        raise ValueError("reconciliation_owner_digest_ref_mismatch")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("reconciliation_backtest_state_file_digest_mismatch")

    return ReconciliationBacktestStateFileRecordV0(
        reconciliation_state=reconciliation_state,
        position_state=position_state,
        venue_flat=bool(decoded.get("venue_flat", True)),
        existing_position_side=existing_position_side,
        intent_snapshot_unresolved=bool(decoded.get("intent_snapshot_unresolved", False)),
        order_snapshot_unresolved=bool(decoded.get("order_snapshot_unresolved", False)),
        fill_snapshot_unresolved=bool(decoded.get("fill_snapshot_unresolved", False)),
        reconciliation_owner_digest_ref=owner_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_reconciliation_backtest_state_file_digest_v0(
    record: ReconciliationBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("reconciliation_backtest_state_file_digest_mismatch")


def _context_from_state_file(
    state_file: ReconciliationBacktestStateFileRecordV0,
) -> ReconciliationUnknownOutcomeOfflineReplayContextV0:
    return ReconciliationUnknownOutcomeOfflineReplayContextV0(
        position_state=PositionState(state_file.position_state),
        reconciliation_state=ReconciliationState(state_file.reconciliation_state),
        venue_flat=state_file.venue_flat,
        existing_position_side=ExistingPositionSide(state_file.existing_position_side),
        intent_snapshot_unresolved=state_file.intent_snapshot_unresolved,
        order_snapshot_unresolved=state_file.order_snapshot_unresolved,
        fill_snapshot_unresolved=state_file.fill_snapshot_unresolved,
    )


def bind_reconciliation_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: ReconciliationBacktestStateFileRecordV0,
) -> ReconciliationBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file reconciliation through the Surface L offline adapter."""
    offline_binding = bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
        evidence,
        context=_context_from_state_file(state_file),
    )
    if not reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("reconciliation_backtest_state_file_non_authority_boundary_failed")

    boundary = offline_binding.boundary
    return ReconciliationBoundaryBacktestStateFileEvidenceV0(
        reconciliation_boundary_backtest_state_file_bound=True,
        reconciliation_state=state_file.reconciliation_state,
        position_state=state_file.position_state,
        submission_unknown_blocks_new_exposure=boundary.submission_unknown_blocks_new_exposure,
        reconciliation_required_maps_to_reconcile_only=(
            boundary.reconciliation_required_maps_to_reconcile_only
        ),
        unknown_outcome_never_auto_resubmits=boundary.unknown_outcome_never_auto_resubmits,
        reconciled_flat_required_before_opposite_side=(
            boundary.reconciled_flat_required_before_opposite_side
        ),
        unresolved_reduce_blocks_opposite_side=boundary.unresolved_reduce_blocks_opposite_side,
        venue_flat_alone_insufficient=boundary.venue_flat_alone_insufficient,
        no_auto_resubmit=boundary.no_auto_resubmit,
        reconciliation_owner_digest_ref=state_file.reconciliation_owner_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_l_adapter_owner_ref=RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_reconciliation_state_file_boundary_only_v0(
    state_file: ReconciliationBacktestStateFileRecordV0,
) -> ReconciliationBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-reconciliation-state-file-stub",
        replay_id="backtest-reconciliation-state-file-stub",
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
    return bind_reconciliation_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_reconciliation_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: ReconciliationBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Fail-closed backtest exposure representation — no runtime orders."""
    if position_signal == 0:
        return 0
    boundary = evidence.offline_binding.boundary
    if boundary.submission_unknown_blocks_new_exposure:
        return 0
    if boundary.reconciliation_required_maps_to_reconcile_only:
        return 0
    if boundary.unresolved_reduce_blocks_opposite_side:
        return 0
    if boundary.reconciled_flat_required_before_opposite_side:
        return 0
    if boundary.venue_flat_alone_insufficient:
        return 0
    if boundary.hard_block_reasons:
        return 0
    return position_signal


def backtest_reconciliation_state_file_binding_non_authority_ok_v0(
    evidence: ReconciliationBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.reconciliation_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    return reconciliation_unknown_outcome_binding_non_authority_boundary_ok_v0(
        evidence.offline_binding
    )


def load_reconciliation_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> ReconciliationBacktestStateFileRecordV0:
    record = parse_reconciliation_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_reconciliation_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
