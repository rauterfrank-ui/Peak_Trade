# src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario replay to canonical
KillSwitch boundary semantics without duplicating live KillSwitch logic.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Tuple

from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
    KILL_SWITCH_OWNER_REF,
    KILL_SWITCH_POLICY_DIGEST,
    KILL_SWITCH_STATE_MACHINE_DIGEST,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.double_play_state import SideState

KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0"
)
KILLSWITCH_FENCING_OWNER = (
    "src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1"
)

KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
KILLSWITCH_BOUNDARY_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"

_ENTER_OUTCOMES = frozenset(
    {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
)
_INCREASE_OUTCOMES = frozenset(
    {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
)
_REDUCE_EXIT_OUTCOMES = frozenset(
    {
        DecisionOutcome.REDUCE.value,
        DecisionOutcome.EXIT.value,
    }
)


class KillSwitchBoundaryMode(str, Enum):
    """Offline KillSwitch boundary modes aligned with governance runbook semantics."""

    NORMAL = "normal"
    BLOCK_NEW = "block_new"
    NO_NEW_POSITIONS = "no_new_positions"
    NO_POSITION_INCREASE = "no_position_increase"
    CANCEL_PENDING = "cancel_pending"
    REDUCE_TO_FLAT = "reduce_to_flat"
    HARD_RISK_EXIT = "hard_risk_exit"
    EMERGENCY_FLATTEN = "emergency_flatten"


_BLOCK_NEW_MODES = frozenset(
    {
        KillSwitchBoundaryMode.BLOCK_NEW,
        KillSwitchBoundaryMode.NO_NEW_POSITIONS,
        KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
    }
)
_REDUCE_ONLY_MODES = frozenset(
    {
        KillSwitchBoundaryMode.REDUCE_TO_FLAT,
        KillSwitchBoundaryMode.HARD_RISK_EXIT,
        KillSwitchBoundaryMode.EMERGENCY_FLATTEN,
    }
)


@dataclass(frozen=True)
class KillSwitchBoundaryOfflineReplayContextV0:
    """Offline-only KillSwitch boundary inputs — no runtime state files."""

    boundary_mode: KillSwitchBoundaryMode = KillSwitchBoundaryMode.NORMAL
    killswitch_active: bool = False
    prior_killswitch_active: bool = False
    safety_mode: SafetyMode = SafetyMode.NORMAL
    side_state: SideState = SideState.NEUTRAL_OBSERVE
    trading_gate: TradingGate = TradingGate.ENTRY_ALLOWED
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILED
    position_state: PositionState = PositionState.FLAT_RECONCILED
    safety_exit_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    hard_risk_reduction_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    safety_decision_allowed: bool = True


@dataclass(frozen=True)
class KillSwitchBoundaryOfflineReplayBoundaryV0:
    killswitch_boundary_bound: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    boundary_mode: str
    block_new_entry: bool
    no_position_increase: bool
    cancel_pending_boundary_only: bool
    reduce_to_flat_boundary_only: bool
    emergency_flatten_boundary_only: bool
    no_auto_resume: bool
    reconciliation_precedence_blocks_new_exposure: bool
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    killswitch_owner_ref: str
    killswitch_contract_digest: str
    killswitch_policy_digest: str
    killswitch_state_machine_digest: str
    killswitch_fencing_owner_ref: str
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class KillSwitchBoundaryOfflineReplayBindingResultV0:
    evidence: "CanonicalTradingDecisionEvidenceV1"
    boundary: KillSwitchBoundaryOfflineReplayBoundaryV0
    binding_applied: bool
    killswitch_boundary_ref: str
    killswitch_boundary_effect: str


def derive_killswitch_boundary_mode_v0(
    *,
    safety_mode: SafetyMode,
    side_state: SideState,
    trading_gate: TradingGate,
    safety_exit_signal: PolicySignalV0,
    hard_risk_reduction_signal: PolicySignalV0,
    safety_decision_allowed: bool,
) -> KillSwitchBoundaryMode:
    """Map replay inputs to offline KillSwitch boundary mode without runtime reads."""
    if side_state is SideState.KILL_ALL or safety_mode is SafetyMode.BLOCKED:
        return KillSwitchBoundaryMode.EMERGENCY_FLATTEN
    if not safety_decision_allowed:
        return KillSwitchBoundaryMode.BLOCK_NEW
    if safety_exit_signal.triggered:
        return KillSwitchBoundaryMode.EMERGENCY_FLATTEN
    if hard_risk_reduction_signal.triggered:
        return KillSwitchBoundaryMode.HARD_RISK_EXIT
    if safety_mode is SafetyMode.EXIT_ONLY:
        return KillSwitchBoundaryMode.REDUCE_TO_FLAT
    if trading_gate is TradingGate.BLOCKED:
        return KillSwitchBoundaryMode.NO_NEW_POSITIONS
    if trading_gate is TradingGate.EXIT_ONLY:
        return KillSwitchBoundaryMode.REDUCE_TO_FLAT
    if safety_mode is SafetyMode.DEGRADED:
        return KillSwitchBoundaryMode.NO_POSITION_INCREASE
    return KillSwitchBoundaryMode.NORMAL


def _killswitch_active(mode: KillSwitchBoundaryMode) -> bool:
    return mode is not KillSwitchBoundaryMode.NORMAL


def _compute_input_digest(ctx: KillSwitchBoundaryOfflineReplayContextV0) -> str:
    payload = {
        "boundary_mode": ctx.boundary_mode.value,
        "hard_risk_reduction_signal": {
            "reason_code": ctx.hard_risk_reduction_signal.reason_code or "",
            "triggered": ctx.hard_risk_reduction_signal.triggered,
        },
        "killswitch_active": ctx.killswitch_active,
        "position_state": ctx.position_state.value,
        "prior_killswitch_active": ctx.prior_killswitch_active,
        "reconciliation_state": ctx.reconciliation_state.value,
        "safety_decision_allowed": ctx.safety_decision_allowed,
        "safety_exit_signal": {
            "reason_code": ctx.safety_exit_signal.reason_code or "",
            "triggered": ctx.safety_exit_signal.triggered,
        },
        "safety_mode": ctx.safety_mode.value,
        "side_state": ctx.side_state.value,
        "trading_gate": ctx.trading_gate.value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(
    boundary: KillSwitchBoundaryOfflineReplayBoundaryV0,
) -> str:
    payload = {
        "block_new_entry": boundary.block_new_entry,
        "boundary_mode": boundary.boundary_mode,
        "cancel_pending_boundary_only": boundary.cancel_pending_boundary_only,
        "credential_effect": boundary.credential_effect,
        "emergency_flatten_boundary_only": boundary.emergency_flatten_boundary_only,
        "hard_block_reasons": list(boundary.hard_block_reasons),
        "killswitch_boundary_bound": boundary.killswitch_boundary_bound,
        "killswitch_contract_digest": boundary.killswitch_contract_digest,
        "killswitch_fencing_owner_ref": boundary.killswitch_fencing_owner_ref,
        "killswitch_owner_ref": boundary.killswitch_owner_ref,
        "killswitch_policy_digest": boundary.killswitch_policy_digest,
        "killswitch_state_machine_digest": boundary.killswitch_state_machine_digest,
        "no_auto_resume": boundary.no_auto_resume,
        "no_position_increase": boundary.no_position_increase,
        "order_effect": boundary.order_effect,
        "reason_codes": list(boundary.reason_codes),
        "reconciliation_precedence_blocks_new_exposure": (
            boundary.reconciliation_precedence_blocks_new_exposure
        ),
        "reduce_to_flat_boundary_only": boundary.reduce_to_flat_boundary_only,
        "runtime_authority_effect": boundary.runtime_authority_effect,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_killswitch_boundary_ref_v0(
    boundary: KillSwitchBoundaryOfflineReplayBoundaryV0,
) -> str:
    return boundary.semantic_digest


def evaluate_offline_killswitch_boundary_v0(
    ctx: KillSwitchBoundaryOfflineReplayContextV0,
    *,
    decision_outcome: str = "",
) -> KillSwitchBoundaryOfflineReplayBoundaryV0:
    """Derive offline KillSwitch boundary evidence from replay context."""
    hard_blocks: list[str] = []
    reason_codes: list[str] = []

    mode = ctx.boundary_mode
    active = ctx.killswitch_active or _killswitch_active(mode)

    block_new = active and mode in _BLOCK_NEW_MODES
    no_position_increase = active and (
        mode is KillSwitchBoundaryMode.NO_POSITION_INCREASE or mode in _BLOCK_NEW_MODES
    )
    cancel_pending_only = active and mode is KillSwitchBoundaryMode.CANCEL_PENDING
    reduce_to_flat_only = active and mode in _REDUCE_ONLY_MODES
    emergency_flatten_only = active and mode is KillSwitchBoundaryMode.EMERGENCY_FLATTEN

    no_auto_resume = ctx.prior_killswitch_active and active

    reconciliation_precedence = False
    if ctx.reconciliation_state is not ReconciliationState.RECONCILED:
        reconciliation_precedence = True
        hard_blocks.append("killswitch_reconciliation_precedence_blocks_new_exposure")
        reason_codes.append("reconciliation_required")
    if ctx.position_state in (
        PositionState.SUBMISSION_UNKNOWN,
        PositionState.RECONCILIATION_REQUIRED,
    ):
        reconciliation_precedence = True
        hard_blocks.append("killswitch_reconciliation_precedence_blocks_new_exposure")
        reason_codes.append("position_reconciliation_required")

    if block_new:
        hard_blocks.append("killswitch_block_new_no_new_positions")
        reason_codes.append("killswitch_block_new")
    if no_position_increase:
        hard_blocks.append("killswitch_no_position_increase")
        reason_codes.append("killswitch_no_position_increase")
    if cancel_pending_only:
        hard_blocks.append("killswitch_cancel_pending_boundary_only")
        reason_codes.append("killswitch_cancel_pending")
    if reduce_to_flat_only:
        hard_blocks.append("killswitch_reduce_to_flat_boundary")
        reason_codes.append("killswitch_reduce_to_flat")
    if emergency_flatten_only:
        hard_blocks.append("killswitch_emergency_flatten_boundary")
        reason_codes.append("killswitch_emergency_flatten")

    if no_auto_resume:
        hard_blocks.append("killswitch_no_auto_resume")
        reason_codes.append("killswitch_no_auto_resume")

    if decision_outcome in _ENTER_OUTCOMES and (block_new or no_position_increase):
        reason_codes.append("entry_blocked_by_killswitch_boundary")
    if decision_outcome in _INCREASE_OUTCOMES and no_position_increase:
        reason_codes.append("increase_blocked_by_killswitch_boundary")
    if decision_outcome in _ENTER_OUTCOMES and reconciliation_precedence and active:
        reason_codes.append("killswitch_reconciliation_precedence_entry_blocked")

    input_digest = _compute_input_digest(ctx)
    boundary = KillSwitchBoundaryOfflineReplayBoundaryV0(
        killswitch_boundary_bound=True,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        boundary_mode=mode.value,
        block_new_entry=block_new,
        no_position_increase=no_position_increase,
        cancel_pending_boundary_only=cancel_pending_only,
        reduce_to_flat_boundary_only=reduce_to_flat_only,
        emergency_flatten_boundary_only=emergency_flatten_only,
        no_auto_resume=no_auto_resume,
        reconciliation_precedence_blocks_new_exposure=reconciliation_precedence,
        hard_block_reasons=tuple(dict.fromkeys(hard_blocks)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        killswitch_owner_ref=KILL_SWITCH_OWNER_REF,
        killswitch_contract_digest=KILL_SWITCH_CONTRACT_DIGEST,
        killswitch_policy_digest=KILL_SWITCH_POLICY_DIGEST,
        killswitch_state_machine_digest=KILL_SWITCH_STATE_MACHINE_DIGEST,
        killswitch_fencing_owner_ref=KILLSWITCH_FENCING_OWNER,
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return replace(boundary, semantic_digest=semantic_digest)


def bind_killswitch_boundary_offline_replay_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: KillSwitchBoundaryOfflineReplayContextV0,
) -> KillSwitchBoundaryOfflineReplayBindingResultV0:
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        finalize_offline_replay_decision_evidence_v1,
    )

    boundary = evaluate_offline_killswitch_boundary_v0(
        context,
        decision_outcome=evidence.decision_outcome,
    )
    killswitch_ref = compute_killswitch_boundary_ref_v0(boundary)
    merged_reason_codes = tuple(dict.fromkeys((*evidence.reason_codes, *boundary.reason_codes)))
    bound_evidence = replace(
        evidence,
        reason_codes=merged_reason_codes,
        killswitch_boundary_ref=killswitch_ref,
        killswitch_boundary_effect=KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return KillSwitchBoundaryOfflineReplayBindingResultV0(
        evidence=finalized,
        boundary=boundary,
        binding_applied=True,
        killswitch_boundary_ref=killswitch_ref,
        killswitch_boundary_effect=KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )


def evaluate_scenario_killswitch_boundary_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    context: KillSwitchBoundaryOfflineReplayContextV0,
) -> KillSwitchBoundaryOfflineReplayBindingResultV0:
    return bind_killswitch_boundary_offline_replay_evidence_v0(
        evidence,
        context=context,
    )


def killswitch_boundary_binding_non_authority_boundary_ok_v0(
    binding: KillSwitchBoundaryOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    ev = binding.evidence
    if not boundary.killswitch_boundary_bound:
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    if ev.execution_eligible or ev.adapter_compatible:
        return False
    if ev.authority_effect != "NONE":
        return False
    if ev.runtime_effect != "NONE":
        return False
    if ev.order_effect != "NONE":
        return False
    if (
        binding.binding_applied
        and binding.killswitch_boundary_effect != KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE
    ):
        return False
    return True


def system_economic_evidence_admissible_v0(
    binding: KillSwitchBoundaryOfflineReplayBindingResultV0,
) -> bool:
    return False


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
