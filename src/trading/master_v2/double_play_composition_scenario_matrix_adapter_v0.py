# src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py
"""
Scenario replay adapter: routes Double Play composition through the canonical
``double_play_composition_matrix_v1`` owner while preserving the legacy
``DoublePlayCompositionDecision`` envelope for scenario replay consumers.

No runtime authority, no semantic extension — wiring-only parity slice.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from trading.master_v2.double_play_composition import (
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionDecision,
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionStatus,
    CompositionDirectionState,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.double_play_suitability import SuitabilityProjectionDecision
from trading.master_v2.double_play_survival import SurvivalEnvelopeDecision
from trading.master_v2.survival_suitability_scenario_binding_adapter_v0 import (
    ScenarioSurvivalSuitabilityOverridesV0,
    apply_canonical_survival_suitability_pre_matrix_gates_v0,
    evaluate_scenario_survival_suitability_v0,
)

DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_LAYER_VERSION = "v0"
DOUBLE_PLAY_COMPOSITION_SCENARIO_MATRIX_ADAPTER_OWNER = (
    "trading.master_v2.double_play_composition_scenario_matrix_adapter_v0"
)
CANONICAL_DOUBLE_PLAY_COMPOSITION_OWNER = "trading.master_v2.double_play_composition_matrix_v1"

_DEFAULT_POLICY = DoublePlayCompositionPolicyV1(
    validity_epochs=3,
    both_candidate_outcome=BothCandidateOutcome.OBSERVE,
    both_invalid_outcome=BothInvalidOutcome.BLOCKED,
    policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
)


def _apply_legacy_pre_matrix_gates(
    inp: DoublePlayCompositionInput,
) -> Optional[DoublePlayCompositionDecision]:
    tr = inp.transition
    side_st = inp.resulting_side_state
    surv = inp.survival
    suit = inp.suitability
    proj = suit.projection
    req = inp.requested_side
    rat = inp.capital_slot_ratchet_decision
    rel = inp.capital_slot_release_decision

    if (
        tr.live_authorization_granted
        or suit.live_authorization
        or proj.live_authorization
        or surv.live_authorization
        or (rat is not None and rat.live_authorization)
        or (rel is not None and rel.live_authorization)
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.LIVE_NOT_AUTHORIZED,),
            reason="Live authorization must not be asserted on sub-decisions; fail closed.",
            live_authorization=False,
        )

    if side_st == SideState.KILL_ALL:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.KILL_ALL,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_KILL_ALL,),
            reason="State is KILL_ALL; no new activation.",
            live_authorization=False,
        )

    if side_st == SideState.CHOP_GUARD_BLOCK:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.CHOP_GUARD,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_CHOP_GUARD,),
            reason="Chop guard blocks new activation.",
            live_authorization=False,
        )

    # Survival/suitability authority is canonical-only (Surface E); legacy envelope not used here.

    if (
        req in (RequestedSide.LONG_BULL, RequestedSide.SHORT_BEAR)
        and side_st == SideState.NEUTRAL_OBSERVE
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_NOT_ACTIVE_OR_ARMED,),
            reason="Directional request while state is neutral observe; not active/armed.",
            live_authorization=False,
        )

    if req == RequestedSide.NEUTRAL_OBSERVE and side_st == SideState.NEUTRAL_OBSERVE:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.OBSERVE_ONLY,
            block_reasons=(),
            reason="Neutral observe path; model-level observe only.",
            live_authorization=False,
        )

    return None


def _apply_legacy_capital_slot_overlay(
    inp: DoublePlayCompositionInput,
    *,
    matrix_status: CompositionStatus,
) -> DoublePlayCompositionDecision:
    req = inp.requested_side
    rat = inp.capital_slot_ratchet_decision
    rel = inp.capital_slot_release_decision

    if rel is not None and rel.released:
        if req in (RequestedSide.LONG_BULL, RequestedSide.SHORT_BEAR):
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.CAPITAL_SLOT_RELEASED,),
                reason=(
                    "Capital slot released (inactivity or opportunity cost); "
                    "no directional model eligibility."
                ),
                live_authorization=False,
            )
        if req == RequestedSide.NEUTRAL_OBSERVE:
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.OBSERVE_ONLY,
                block_reasons=(),
                reason="Capital slot released; neutral observe only (model-level).",
                live_authorization=False,
            )

    if rat is not None and rat.block_reasons:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.CAPITAL_SLOT_RATCHET_BLOCKED,),
            reason="Capital slot ratchet pre-authorization blocked.",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.CHOP_GUARD_BLOCK:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.CHOP_GUARD,
            block_reasons=(DoublePlayCompositionBlockReason.STATE_CHOP_GUARD,),
            reason="Canonical matrix chop guard blocks new activation.",
            live_authorization=False,
        )

    if matrix_status in (CompositionStatus.OBSERVE, CompositionStatus.NO_ACTION):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.OBSERVE_ONLY,
            block_reasons=(),
            reason="Canonical matrix observe-only coordination.",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.BLOCKED:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Canonical matrix blocked coordination.",
            live_authorization=False,
        )

    if matrix_status in (CompositionStatus.LONG_SELECTED, CompositionStatus.SHORT_SELECTED):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
            block_reasons=(),
            reason="All pure gates pass; model-only eligibility (not trading permission).",
            live_authorization=False,
        )

    if matrix_status is CompositionStatus.REVERSAL_PREPARATION:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
            block_reasons=(),
            reason="Reversal preparation; model-only eligibility (not trading permission).",
            live_authorization=False,
        )

    return DoublePlayCompositionDecision(
        status=DoublePlayCompositionStatus.BLOCKED,
        block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
        reason=f"Unhandled canonical matrix status: {matrix_status.value}",
        live_authorization=False,
    )


def build_scenario_matrix_composition_input_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    side_st: SideState,
    survival: SurvivalEnvelopeDecision | None = None,
    suitability: SuitabilityProjectionDecision | None = None,
    survival_suitability_overrides: ScenarioSurvivalSuitabilityOverridesV0 | None = None,
) -> DoublePlayCompositionInputV1:
    del survival, suitability  # legacy compatibility params; canonical owners are authority
    evaluation = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=side_st,
        overrides=survival_suitability_overrides,
    )
    raw = DoublePlayCompositionInputV1(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        bull_directional_assessment=evaluation.bull_assessment,
        bear_directional_assessment=evaluation.bear_assessment,
        bull_survival_result=evaluation.bull_survival,
        bear_survival_result=evaluation.bear_survival,
        bull_suitability_result=evaluation.bull_suitability,
        bear_suitability_result=evaluation.bear_suitability,
        previous_direction_state=_previous_direction_state(side_st),
        position_management_context=_position_management_context(side_st),
        last_evaluated_trading_epoch=trading_epoch - 1,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    )
    return replace(raw, input_digest=compute_composition_input_digest(raw))


def _position_management_context(side_st: SideState) -> PositionManagementContext:
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return PositionManagementContext.LONG_POSITION
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return PositionManagementContext.SHORT_POSITION
    return PositionManagementContext.FLAT


def _previous_direction_state(side_st: SideState) -> CompositionDirectionState:
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED, SideState.LONG_BLOCKED):
        return CompositionDirectionState.LONG
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED, SideState.SHORT_BLOCKED):
        return CompositionDirectionState.SHORT
    return CompositionDirectionState.NEUTRAL


def evaluate_scenario_matrix_composition_v0(
    matrix_input: DoublePlayCompositionInputV1,
    *,
    policy: DoublePlayCompositionPolicyV1 | None = None,
) -> DoublePlayCompositionResultV1:
    return evaluate_double_play_composition_matrix_v1(
        matrix_input,
        policy or _DEFAULT_POLICY,
    )


def compose_double_play_scenario_via_canonical_matrix_v0(
    inp: DoublePlayCompositionInput,
    *,
    instrument_id: str,
    trading_epoch: int,
    context_reference: str,
    policy: DoublePlayCompositionPolicyV1 | None = None,
) -> DoublePlayCompositionDecision:
    canonical_eval = evaluate_scenario_survival_suitability_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        side_st=inp.resulting_side_state,
    )
    pre = apply_canonical_survival_suitability_pre_matrix_gates_v0(inp, canonical_eval)
    if pre is not None:
        return pre

    pre = _apply_legacy_pre_matrix_gates(inp)
    if pre is not None:
        return pre

    matrix_input = build_scenario_matrix_composition_input_v0(
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        context_reference=context_reference,
        side_st=inp.resulting_side_state,
        survival=inp.survival,
        suitability=inp.suitability,
    )
    matrix_result = evaluate_scenario_matrix_composition_v0(matrix_input, policy=policy)
    return _apply_legacy_capital_slot_overlay(
        inp,
        matrix_status=matrix_result.composition_status,
    )


def legacy_and_matrix_composition_parity_aligned_v0(
    legacy: DoublePlayCompositionDecision,
    matrix_result: DoublePlayCompositionResultV1,
) -> bool:
    status_map = {
        CompositionStatus.LONG_SELECTED: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
        CompositionStatus.SHORT_SELECTED: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
        CompositionStatus.CHOP_GUARD_BLOCK: DoublePlayCompositionStatus.CHOP_GUARD,
        CompositionStatus.OBSERVE: DoublePlayCompositionStatus.OBSERVE_ONLY,
        CompositionStatus.NO_ACTION: DoublePlayCompositionStatus.OBSERVE_ONLY,
        CompositionStatus.BLOCKED: DoublePlayCompositionStatus.BLOCKED,
        CompositionStatus.REVERSAL_PREPARATION: DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
    }
    expected = status_map.get(matrix_result.composition_status)
    if expected is None:
        return False
    return legacy.status is expected
