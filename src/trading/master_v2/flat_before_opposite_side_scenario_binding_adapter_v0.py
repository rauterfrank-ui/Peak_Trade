# src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to the canonical
``double_play_entry_exit_policy_v0`` flat-before-opposite-side path without duplicating policy logic.

Wiring-only parity slice (Surface D) — no runtime authority, no trading semantic extension.
"""

from __future__ import annotations

from dataclasses import replace

from trading.master_v2.double_play_composition_matrix_v1 import DoublePlayCompositionResultV1
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PositionState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    ScenarioEntryExitPolicyContextV0,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    evaluate_scenario_reversal_preparation_entry_exit_v0,
)

FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.flat_before_opposite_side_scenario_binding_adapter_v0"
)

FLAT_BEFORE_OPPOSITE_SIDE_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
FLAT_BEFORE_OPPOSITE_SIDE_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"

_EXPLICIT_POSITION_OVERRIDE_STATES = frozenset(
    {
        PositionState.RECONCILIATION_REQUIRED,
        PositionState.SUBMISSION_UNKNOWN,
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
    }
)


def derive_flat_before_opposite_side_position_context_v0(
    side_state: SideState,
) -> ScenarioEntryExitPolicyContextV0 | None:
    """Map side-state pipeline evidence to open-position policy context for flat/flip gates."""
    if side_state is SideState.LONG_ACTIVE:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
        )
    if side_state is SideState.SHORT_ACTIVE:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.SHORT,
            venue_flat=False,
        )
    if side_state is SideState.SWITCH_LONG_TO_SHORT_PENDING:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
        )
    if side_state is SideState.SWITCH_SHORT_TO_LONG_PENDING:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.SHORT,
            venue_flat=False,
        )
    if side_state is SideState.LONG_BLOCKED:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.EXIT_PENDING,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
        )
    if side_state is SideState.SHORT_BLOCKED:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.EXIT_PENDING,
            existing_position_side=ExistingPositionSide.SHORT,
            venue_flat=False,
        )
    return None


def merge_flat_before_opposite_side_policy_context_v0(
    *,
    side_state: SideState,
    policy_context: ScenarioEntryExitPolicyContextV0,
) -> ScenarioEntryExitPolicyContextV0:
    """Merge side-state position evidence into scenario policy context; preserve explicit overrides."""
    if policy_context.position_state in _EXPLICIT_POSITION_OVERRIDE_STATES:
        return policy_context
    derived = derive_flat_before_opposite_side_position_context_v0(side_state)
    if derived is None:
        return policy_context
    return replace(
        policy_context,
        position_state=derived.position_state,
        existing_position_side=derived.existing_position_side,
        venue_flat=derived.venue_flat,
        reconciliation_state=policy_context.reconciliation_state,
        safety_decision_allowed=policy_context.safety_decision_allowed,
        scope_adverse_exit_signal=policy_context.scope_adverse_exit_signal,
        profit_protection_signal=policy_context.profit_protection_signal,
        time_exit_signal=policy_context.time_exit_signal,
        strategy_invalidation_signal=policy_context.strategy_invalidation_signal,
        hard_risk_reduction_signal=policy_context.hard_risk_reduction_signal,
        safety_exit_signal=policy_context.safety_exit_signal,
    )


def evaluate_scenario_flat_before_opposite_side_entry_exit_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    composition_result: DoublePlayCompositionResultV1,
    side_state: SideState,
    policy_context: ScenarioEntryExitPolicyContextV0,
) -> EntryExitPolicyDecisionV0:
    """Evaluate entry-exit with flat-before-opposite-side binding through canonical policy."""
    merged_ctx = merge_flat_before_opposite_side_policy_context_v0(
        side_state=side_state,
        policy_context=policy_context,
    )
    return evaluate_scenario_reversal_preparation_entry_exit_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=composition_result,
        side_state=side_state,
        policy_context=merged_ctx,
    )


def flat_before_opposite_side_blocks_opposite_entry_v0(
    decision: EntryExitPolicyDecisionV0,
) -> bool:
    if decision.position_flip_allowed:
        return False
    if decision.decision_outcome in (DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT):
        return False
    return True


def flat_before_opposite_side_binding_non_authority_boundary_ok_v0(
    decision: EntryExitPolicyDecisionV0,
) -> bool:
    if decision.runtime_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if decision.authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        return False
    if decision.execution_eligible:
        return False
    if decision.adapter_compatible:
        return False
    return True


def system_economic_evidence_admissible_v0() -> bool:
    return False


def canonical_entry_exit_owner_ref_v0() -> str:
    return CANONICAL_ENTRY_EXIT_POLICY_OWNER
