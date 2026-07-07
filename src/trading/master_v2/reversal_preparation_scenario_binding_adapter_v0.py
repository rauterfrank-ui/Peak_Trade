# src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to the canonical
``double_play_entry_exit_policy_v0`` reversal-preparation path without duplicating policy logic.

Wiring-only parity slice (Surface C) — no runtime authority, no trading semantic extension.
"""

from __future__ import annotations

from dataclasses import replace

from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionSelectedSide,
    CompositionStatus,
    DoublePlayCompositionResultV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitPolicyDecisionV0,
    ExitClass,
    ExistingPositionSide,
    PositionState,
)
from trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    CANONICAL_ENTRY_EXIT_POLICY_OWNER,
    ScenarioEntryExitPolicyContextV0,
    evaluate_scenario_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import SideState

REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
REVERSAL_PREPARATION_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.reversal_preparation_scenario_binding_adapter_v0"
)

REVERSAL_PREPARATION_EFFECT_BOUND_OFFLINE = "BOUND_OFFLINE"
REVERSAL_PREPARATION_EFFECT_NONE = "NONE"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"


def is_reversal_preparation_composition_v0(
    composition_result: DoublePlayCompositionResultV1,
) -> bool:
    return composition_result.composition_status is CompositionStatus.REVERSAL_PREPARATION


def derive_reversal_preparation_position_context_v0(
    composition_result: DoublePlayCompositionResultV1,
    *,
    safety_decision_allowed: bool = True,
) -> ScenarioEntryExitPolicyContextV0 | None:
    """Map REVERSAL_PREPARATION composition evidence to open-position policy context."""
    if not is_reversal_preparation_composition_v0(composition_result):
        return None
    codes = composition_result.reason_codes
    if "existing_long_position" in codes:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.LONG,
            venue_flat=False,
            safety_decision_allowed=safety_decision_allowed,
        )
    if "existing_short_position" in codes:
        return ScenarioEntryExitPolicyContextV0(
            position_state=PositionState.OPEN_FULL,
            existing_position_side=ExistingPositionSide.SHORT,
            venue_flat=False,
            safety_decision_allowed=safety_decision_allowed,
        )
    return None


def project_composition_for_reversal_preparation_entry_exit_v0(
    composition_result: DoublePlayCompositionResultV1,
) -> DoublePlayCompositionResultV1:
    """
    Consumer-bridge projection: canonical entry-exit precedence 6 expects opposite
    ``selected_side``, not ``REVERSAL_PREPARATION`` with ``selected_side=NONE``.
    """
    if not is_reversal_preparation_composition_v0(composition_result):
        return composition_result
    codes = composition_result.reason_codes
    if "existing_long_position" in codes:
        return replace(
            composition_result,
            selected_side=CompositionSelectedSide.SHORT,
        )
    if "existing_short_position" in codes:
        return replace(
            composition_result,
            selected_side=CompositionSelectedSide.LONG,
        )
    return composition_result


def evaluate_scenario_reversal_preparation_entry_exit_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    composition_result: DoublePlayCompositionResultV1,
    side_state: SideState,
    policy_context: ScenarioEntryExitPolicyContextV0,
) -> EntryExitPolicyDecisionV0:
    """Evaluate entry-exit with reversal-preparation binding when composition requires it."""
    if not policy_context.safety_decision_allowed:
        return evaluate_scenario_entry_exit_policy_v0(
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            context_reference=context_reference,
            composition_result=composition_result,
            side_state=side_state,
            policy_context=policy_context,
        )

    reversal_ctx = derive_reversal_preparation_position_context_v0(
        composition_result,
        safety_decision_allowed=policy_context.safety_decision_allowed,
    )
    if reversal_ctx is None:
        return evaluate_scenario_entry_exit_policy_v0(
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            context_reference=context_reference,
            composition_result=composition_result,
            side_state=side_state,
            policy_context=policy_context,
        )

    merged_ctx = replace(
        policy_context,
        position_state=reversal_ctx.position_state,
        existing_position_side=reversal_ctx.existing_position_side,
        venue_flat=reversal_ctx.venue_flat,
    )
    projected = project_composition_for_reversal_preparation_entry_exit_v0(composition_result)
    return evaluate_scenario_entry_exit_policy_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        composition_result=projected,
        side_state=side_state,
        policy_context=merged_ctx,
    )


def reversal_preparation_decision_is_reduce_only_preparation_v0(
    decision: EntryExitPolicyDecisionV0,
) -> bool:
    if decision.exit_class is not ExitClass.REVERSAL_PREPARATION_EXIT:
        return False
    if decision.decision_outcome in (DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT):
        return False
    if decision.position_flip_allowed:
        return False
    return decision.decision_outcome in (DecisionOutcome.REDUCE, DecisionOutcome.EXIT)


def reversal_preparation_binding_non_authority_boundary_ok_v0(
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
    if decision.decision_outcome in (DecisionOutcome.ENTER_LONG, DecisionOutcome.ENTER_SHORT):
        return False
    return True


def system_economic_evidence_admissible_v0() -> bool:
    return False


def canonical_entry_exit_owner_ref_v0() -> str:
    return CANONICAL_ENTRY_EXIT_POLICY_OWNER
