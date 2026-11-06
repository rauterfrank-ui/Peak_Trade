"""Bind existing Pure-Stack producers — never invent Decision semantics."""

from __future__ import annotations

from typing import Optional, Tuple

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotConfig,
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
    CapitalSlotState,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionDecision,
    DoublePlayCompositionInput,
    RequestedSide,
    compose_double_play_decision,
)
from trading.master_v2.double_play_futures_input import (
    FuturesInputReadinessDecision,
    FuturesInputSnapshot,
    evaluate_futures_input_snapshot,
)
from trading.master_v2.double_play_state import (
    SideState,
    TransitionDecision,
)  # SideState for compose input
from trading.master_v2.double_play_suitability import (
    SuitabilityProjectionDecision,
    SuitabilityProjectionInput,
    project_strategy_suitability,
)
from trading.master_v2.double_play_survival import (
    DoublePlaySurvivalEnvelope,
    SurvivalEnvelopeDecision,
    evaluate_survival_envelope,
)

from src.ops.productive_pure_stack_display_decision_host_binding_v1.input_builders_v1 import (
    CanonicalInputAuthorityAbsentError,
    assert_no_unauthorized_fallback_flags_v1,
    reject_resultv1_mapping_attempt_v1,
)


def produce_futures_input_readiness_v1(
    snapshot: FuturesInputSnapshot,
) -> FuturesInputReadinessDecision:
    assert_no_unauthorized_fallback_flags_v1()
    reject_resultv1_mapping_attempt_v1(snapshot)
    return evaluate_futures_input_snapshot(snapshot)


def produce_survival_envelope_decision_v1(
    envelope: DoublePlaySurvivalEnvelope,
) -> SurvivalEnvelopeDecision:
    assert_no_unauthorized_fallback_flags_v1()
    reject_resultv1_mapping_attempt_v1(envelope)
    return evaluate_survival_envelope(envelope)


def produce_suitability_projection_decision_v1(
    inp: SuitabilityProjectionInput,
) -> SuitabilityProjectionDecision:
    assert_no_unauthorized_fallback_flags_v1()
    reject_resultv1_mapping_attempt_v1(inp)
    return project_strategy_suitability(inp)


def produce_capital_slot_ratchet_v1(
    config: CapitalSlotConfig,
    state: CapitalSlotState,
) -> CapitalSlotRatchetDecision:
    assert_no_unauthorized_fallback_flags_v1()
    return evaluate_capital_slot_ratchet(config, state)


def produce_capital_slot_release_v1(
    config: CapitalSlotConfig,
    state: CapitalSlotState,
) -> CapitalSlotReleaseDecision:
    assert_no_unauthorized_fallback_flags_v1()
    return evaluate_capital_slot_release(config, state)


def produce_composition_decision_v1(
    *,
    transition: TransitionDecision,
    resulting_side_state: SideState,
    survival: SurvivalEnvelopeDecision,
    suitability: SuitabilityProjectionDecision,
    requested_side: RequestedSide,
    capital_slot_ratchet: Optional[CapitalSlotRatchetDecision],
    capital_slot_release: Optional[CapitalSlotReleaseDecision],
) -> DoublePlayCompositionDecision:
    """Compose only when all required Pure-Stack Decisions are already present."""
    assert_no_unauthorized_fallback_flags_v1()
    if any(
        value is None
        for value in (transition, survival, suitability, resulting_side_state, requested_side)
    ):
        raise CanonicalInputAuthorityAbsentError(
            "DoublePlayCompositionInput",
            "partial_composition_forbidden",
        )
    inp = DoublePlayCompositionInput(
        transition=transition,
        resulting_side_state=resulting_side_state,
        survival=survival,
        suitability=suitability,
        requested_side=requested_side,
        capital_slot_ratchet_decision=capital_slot_ratchet,
        capital_slot_release_decision=capital_slot_release,
    )
    return compose_double_play_decision(inp)


def assert_transition_identity_v1(
    *,
    from_transition_state: TransitionDecision,
    from_bundle_or_intermediate: TransitionDecision,
) -> bool:
    """Identity proof: same object or exact field equality (no evidence rebuild)."""
    if from_transition_state is from_bundle_or_intermediate:
        return True
    return (
        from_transition_state.allowed == from_bundle_or_intermediate.allowed
        and from_transition_state.reason_code == from_bundle_or_intermediate.reason_code
        and from_transition_state.live_authorization_granted
        == from_bundle_or_intermediate.live_authorization_granted
    )
