# src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to the canonical
``double_play_entry_exit_policy_v0`` owner without duplicating policy logic.

Wiring-only parity slice — no runtime authority, no trading semantic extension.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.double_play_composition_matrix_v1 import DoublePlayCompositionResultV1
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_VERSION,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import SideState

DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
DOUBLE_PLAY_ENTRY_EXIT_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0"
)
CANONICAL_ENTRY_EXIT_POLICY_OWNER = "trading.master_v2.double_play_entry_exit_policy_v0"

_DEFAULT_POLICY = DoublePlayEntryExitPolicyV0()


def side_state_to_entry_exit_direction(side: SideState) -> EntryExitDirectionState:
    """Mirror integrated offline replay direction mapping (reuse contract)."""
    table = {
        SideState.NEUTRAL_OBSERVE: EntryExitDirectionState.NEUTRAL,
        SideState.LONG_ARMED: EntryExitDirectionState.LONG_ARMED,
        SideState.LONG_ACTIVE: EntryExitDirectionState.LONG_ACTIVE,
        SideState.LONG_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SHORT_ARMED: EntryExitDirectionState.SHORT_ARMED,
        SideState.SHORT_ACTIVE: EntryExitDirectionState.SHORT_ACTIVE,
        SideState.SHORT_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.SHORT_ARMED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.LONG_ARMED,
        SideState.CHOP_GUARD_BLOCK: EntryExitDirectionState.NEUTRAL,
        SideState.KILL_ALL: EntryExitDirectionState.NEUTRAL,
    }
    return table.get(side, EntryExitDirectionState.NEUTRAL)


@dataclass(frozen=True)
class ScenarioEntryExitPolicyContextV0:
    """Explicit offline scenario policy context — never inferred from confidence."""

    position_state: PositionState = PositionState.FLAT_RECONCILED
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILED
    trading_gate: TradingGate = TradingGate.ENTRY_ALLOWED
    safety_mode: SafetyMode = SafetyMode.NORMAL
    existing_position_side: ExistingPositionSide = ExistingPositionSide.NONE
    venue_flat: bool = True
    cooldown_pass: bool = True
    scope_adverse_exit_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    profit_protection_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    time_exit_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    strategy_invalidation_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    hard_risk_reduction_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    safety_exit_signal: PolicySignalV0 = PolicySignalV0(triggered=False)
    safety_decision_allowed: bool = True


def default_scenario_entry_exit_policy_context_v0(
    *,
    safety_decision_allowed: bool = True,
) -> ScenarioEntryExitPolicyContextV0:
    return ScenarioEntryExitPolicyContextV0(safety_decision_allowed=safety_decision_allowed)


def build_scenario_entry_exit_policy_input_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    composition_result: DoublePlayCompositionResultV1,
    side_state: SideState,
    policy_context: ScenarioEntryExitPolicyContextV0 | None = None,
) -> DoublePlayEntryExitPolicyInputV0:
    ctx = policy_context or default_scenario_entry_exit_policy_context_v0()
    safety_mode = ctx.safety_mode
    if not ctx.safety_decision_allowed:
        safety_mode = SafetyMode.BLOCKED

    raw = DoublePlayEntryExitPolicyInputV0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=composition_result,
        direction_state=side_state_to_entry_exit_direction(side_state),
        position_state=ctx.position_state,
        reconciliation_state=ctx.reconciliation_state,
        trading_gate=ctx.trading_gate,
        safety_mode=safety_mode,
        data_integrity_state=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        clock_trust_valid=True,
        cooldown_pass=ctx.cooldown_pass,
        existing_position_side=ctx.existing_position_side,
        venue_flat=ctx.venue_flat,
        scope_adverse_exit_signal=ctx.scope_adverse_exit_signal,
        profit_protection_signal=ctx.profit_protection_signal,
        time_exit_signal=ctx.time_exit_signal,
        strategy_invalidation_signal=ctx.strategy_invalidation_signal,
        hard_risk_reduction_signal=ctx.hard_risk_reduction_signal,
        safety_exit_signal=ctx.safety_exit_signal,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=ENTRY_EXIT_POLICY_VERSION,
    )
    return replace(raw, input_digest=compute_entry_exit_policy_input_digest(raw))


def evaluate_scenario_entry_exit_policy_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    composition_result: DoublePlayCompositionResultV1,
    side_state: SideState,
    policy_context: ScenarioEntryExitPolicyContextV0 | None = None,
    policy: DoublePlayEntryExitPolicyV0 | None = None,
) -> EntryExitPolicyDecisionV0:
    inp = build_scenario_entry_exit_policy_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=composition_result,
        side_state=side_state,
        policy_context=policy_context,
    )
    return evaluate_double_play_entry_exit_policy_v0(inp, policy or _DEFAULT_POLICY)


def entry_exit_decision_non_authority_boundary_ok_v0(
    decision: EntryExitPolicyDecisionV0,
) -> bool:
    return (
        not decision.execution_eligible
        and not decision.adapter_compatible
        and decision.quantity_status == "NOT_BOUND"
        and decision.authority_effect == "NONE"
        and decision.runtime_effect == "NONE"
    )


def scenario_entry_exit_side_states_v0(
    *,
    prior_side_state: SideState,
    side_state: SideState,
) -> Tuple[str, str]:
    return prior_side_state.value, side_state.value
