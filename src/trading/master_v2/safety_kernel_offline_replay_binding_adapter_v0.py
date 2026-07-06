# src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py
"""
Offline replay adapter: binds Integrated / Scenario replay to canonical
Safety-Kernel boundary semantics without duplicating live kernel logic.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Tuple

from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
    KILL_SWITCH_OWNER_REF,
    KILL_SWITCH_POLICY_DIGEST,
    KILL_SWITCH_STATE_MACHINE_DIGEST,
)
from src.meta.learning_loop.runtime_eligibility_v1 import (
    AUTHORITY_LEVEL as RUNTIME_ELIGIBILITY_AUTHORITY_LEVEL,
    CONTRACT_NAME as RUNTIME_ELIGIBILITY_CONTRACT_NAME,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    finalize_offline_replay_decision_evidence_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)

SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_LAYER_VERSION = "v0"
SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
)
RUNTIME_ELIGIBILITY_OWNER = "src.meta.learning_loop.runtime_eligibility_v1"
KILLSWITCH_FENCING_OWNER = (
    "src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1"
)

SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
SAFETY_BOUNDARY_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"
SCHEDULER_EFFECT_NONE = "NONE"

_ENTER_OUTCOMES = frozenset(
    {
        DecisionOutcome.ENTER_LONG.value,
        DecisionOutcome.ENTER_SHORT.value,
    }
)


@dataclass(frozen=True)
class SafetyKernelOfflineReplayContextV0:
    """Offline-only safety-kernel boundary inputs — no runtime state files."""

    safety_mode: SafetyMode = SafetyMode.NORMAL
    safety_exit_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILED
    position_state: PositionState = PositionState.FLAT_RECONCILED
    trading_gate: TradingGate = TradingGate.ENTRY_ALLOWED
    killswitch_blocked: bool = False
    safety_decision_allowed: bool = True


@dataclass(frozen=True)
class SafetyKernelOfflineReplayBoundaryV0:
    safety_boundary_bound: bool
    runtime_authority_effect: str
    order_effect: str
    credential_effect: str
    scheduler_effect: str
    kill_switch_boundary_represented: bool
    reconciliation_requirement_represented: bool
    unknown_outcome_semantics_represented: bool
    no_submission_before_permission: bool
    no_permission_issued: bool
    hard_block_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    runtime_eligibility_owner_ref: str
    killswitch_owner_ref: str
    killswitch_contract_digest: str
    killswitch_policy_digest: str
    killswitch_state_machine_digest: str
    runtime_eligibility_contract_name: str
    runtime_eligibility_authority_level: str
    input_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class SafetyKernelOfflineReplayBindingResultV0:
    evidence: CanonicalTradingDecisionEvidenceV1
    boundary: SafetyKernelOfflineReplayBoundaryV0
    binding_applied: bool
    safety_boundary_ref: str
    safety_boundary_effect: str


def _compute_input_digest(ctx: SafetyKernelOfflineReplayContextV0) -> str:
    payload = {
        "killswitch_blocked": ctx.killswitch_blocked,
        "position_state": ctx.position_state.value,
        "reconciliation_state": ctx.reconciliation_state.value,
        "safety_decision_allowed": ctx.safety_decision_allowed,
        "safety_exit_signal": {
            "reason_code": ctx.safety_exit_signal.reason_code or "",
            "triggered": ctx.safety_exit_signal.triggered,
        },
        "safety_mode": ctx.safety_mode.value,
        "trading_gate": ctx.trading_gate.value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize_boundary_canonical(boundary: SafetyKernelOfflineReplayBoundaryV0) -> str:
    payload = {
        "credential_effect": boundary.credential_effect,
        "hard_block_reasons": list(boundary.hard_block_reasons),
        "kill_switch_boundary_represented": boundary.kill_switch_boundary_represented,
        "killswitch_contract_digest": boundary.killswitch_contract_digest,
        "killswitch_owner_ref": boundary.killswitch_owner_ref,
        "killswitch_policy_digest": boundary.killswitch_policy_digest,
        "killswitch_state_machine_digest": boundary.killswitch_state_machine_digest,
        "no_permission_issued": boundary.no_permission_issued,
        "no_submission_before_permission": boundary.no_submission_before_permission,
        "order_effect": boundary.order_effect,
        "reason_codes": list(boundary.reason_codes),
        "reconciliation_requirement_represented": boundary.reconciliation_requirement_represented,
        "runtime_authority_effect": boundary.runtime_authority_effect,
        "runtime_eligibility_authority_level": boundary.runtime_eligibility_authority_level,
        "runtime_eligibility_contract_name": boundary.runtime_eligibility_contract_name,
        "runtime_eligibility_owner_ref": boundary.runtime_eligibility_owner_ref,
        "safety_boundary_bound": boundary.safety_boundary_bound,
        "scheduler_effect": boundary.scheduler_effect,
        "unknown_outcome_semantics_represented": boundary.unknown_outcome_semantics_represented,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_safety_boundary_ref_v0(boundary: SafetyKernelOfflineReplayBoundaryV0) -> str:
    return boundary.semantic_digest


def evaluate_offline_safety_kernel_boundary_v0(
    ctx: SafetyKernelOfflineReplayContextV0,
    *,
    decision_outcome: str = "",
) -> SafetyKernelOfflineReplayBoundaryV0:
    """Derive offline safety-kernel boundary evidence from replay context."""
    hard_blocks: list[str] = []
    reason_codes: list[str] = []

    kill_switch_represented = True
    reconciliation_represented = True
    unknown_outcome_represented = True

    if ctx.killswitch_blocked or not ctx.safety_decision_allowed:
        hard_blocks.append("killswitch_boundary_blocks_new_entry")
        reason_codes.append("killswitch_blocked")
    if ctx.safety_mode is not SafetyMode.NORMAL:
        hard_blocks.append("safety_mode_not_normal")
        reason_codes.append(f"safety_mode_{ctx.safety_mode.value}")
    if ctx.safety_exit_signal.triggered:
        hard_blocks.append("safety_exit_signal_active")
        reason_codes.append(ctx.safety_exit_signal.reason_code or "safety_exit")

    if ctx.reconciliation_state is not ReconciliationState.RECONCILED:
        hard_blocks.append("reconciliation_required_blocks_new_exposure")
        reason_codes.append("reconciliation_required")

    if ctx.position_state is PositionState.SUBMISSION_UNKNOWN:
        hard_blocks.append("unknown_outcome_no_auto_resubmit")
        reason_codes.append("submission_unknown")
    if ctx.position_state is PositionState.RECONCILIATION_REQUIRED:
        hard_blocks.append("position_reconciliation_required")
        reason_codes.append("position_reconciliation_required")

    if ctx.trading_gate is TradingGate.BLOCKED:
        hard_blocks.append("trading_gate_blocked")
        reason_codes.append("trading_gate_blocked")

    if decision_outcome in _ENTER_OUTCOMES and hard_blocks:
        reason_codes.append("entry_blocked_by_safety_kernel_boundary")

    input_digest = _compute_input_digest(ctx)
    boundary = SafetyKernelOfflineReplayBoundaryV0(
        safety_boundary_bound=True,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        credential_effect=CREDENTIAL_EFFECT_NONE,
        scheduler_effect=SCHEDULER_EFFECT_NONE,
        kill_switch_boundary_represented=kill_switch_represented,
        reconciliation_requirement_represented=reconciliation_represented,
        unknown_outcome_semantics_represented=unknown_outcome_represented,
        no_submission_before_permission=True,
        no_permission_issued=True,
        hard_block_reasons=tuple(dict.fromkeys(hard_blocks)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        runtime_eligibility_owner_ref=RUNTIME_ELIGIBILITY_OWNER,
        killswitch_owner_ref=KILL_SWITCH_OWNER_REF,
        killswitch_contract_digest=KILL_SWITCH_CONTRACT_DIGEST,
        killswitch_policy_digest=KILL_SWITCH_POLICY_DIGEST,
        killswitch_state_machine_digest=KILL_SWITCH_STATE_MACHINE_DIGEST,
        runtime_eligibility_contract_name=RUNTIME_ELIGIBILITY_CONTRACT_NAME,
        runtime_eligibility_authority_level=RUNTIME_ELIGIBILITY_AUTHORITY_LEVEL,
        input_digest=input_digest,
        semantic_digest="",
    )
    semantic_digest = hashlib.sha256(
        _serialize_boundary_canonical(boundary).encode("utf-8")
    ).hexdigest()
    return replace(boundary, semantic_digest=semantic_digest)


def bind_safety_kernel_offline_replay_evidence_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    context: SafetyKernelOfflineReplayContextV0,
) -> SafetyKernelOfflineReplayBindingResultV0:
    """Attach offline safety-kernel boundary evidence to decision evidence."""
    boundary = evaluate_offline_safety_kernel_boundary_v0(
        context,
        decision_outcome=evidence.decision_outcome,
    )
    safety_boundary_ref = compute_safety_boundary_ref_v0(boundary)
    merged_reason_codes = tuple(dict.fromkeys((*evidence.reason_codes, *boundary.reason_codes)))
    bound_evidence = replace(
        evidence,
        reason_codes=merged_reason_codes,
        safety_boundary_ref=safety_boundary_ref,
        safety_boundary_effect=SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )
    finalized = finalize_offline_replay_decision_evidence_v1(bound_evidence)
    return SafetyKernelOfflineReplayBindingResultV0(
        evidence=finalized,
        boundary=boundary,
        binding_applied=True,
        safety_boundary_ref=safety_boundary_ref,
        safety_boundary_effect=SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    )


def evaluate_scenario_safety_kernel_v0(
    evidence: CanonicalTradingDecisionEvidenceV1,
    *,
    context: SafetyKernelOfflineReplayContextV0,
) -> SafetyKernelOfflineReplayBindingResultV0:
    return bind_safety_kernel_offline_replay_evidence_v0(evidence, context=context)


def safety_kernel_binding_non_authority_boundary_ok_v0(
    binding: SafetyKernelOfflineReplayBindingResultV0,
) -> bool:
    boundary = binding.boundary
    ev = binding.evidence
    if not boundary.safety_boundary_bound:
        return False
    if boundary.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if boundary.order_effect != ORDER_EFFECT_NONE:
        return False
    if boundary.credential_effect != CREDENTIAL_EFFECT_NONE:
        return False
    if boundary.scheduler_effect != SCHEDULER_EFFECT_NONE:
        return False
    if not boundary.no_permission_issued:
        return False
    if not boundary.no_submission_before_permission:
        return False
    if not boundary.kill_switch_boundary_represented:
        return False
    if not boundary.reconciliation_requirement_represented:
        return False
    if not boundary.unknown_outcome_semantics_represented:
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
        and binding.safety_boundary_effect != SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE
    ):
        return False
    return True


def system_economic_evidence_admissible_v0(
    binding: SafetyKernelOfflineReplayBindingResultV0,
) -> bool:
    return False
