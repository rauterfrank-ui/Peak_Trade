# src/trading/master_v2/double_play_composition.py
"""
Pure composition of Double Play transition, survival envelope, and suitability decisions.

Data-only eligibility / blocked / observe status. Not trading permission.
No I/O, no execution, no registry, no live authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_survival import SurvivalEnvelopeDecision, SurvivalEnvelopeStatus
from trading.master_v2.double_play_suitability import (
    SuitabilityClass,
    SuitabilityProjectionDecision,
)

DOUBLE_PLAY_COMPOSITION_LAYER_VERSION = "v0"


class DoublePlayCompositionStatus(str, Enum):
    """Model-level composition outcome; not execution or live go."""

    ELIGIBLE_MODEL_ONLY = "eligible_model_only"
    BLOCKED = "blocked"
    OBSERVE_ONLY = "observe_only"
    KILL_ALL = "kill_all"
    CHOP_GUARD = "chop_guard"


class DoublePlayCompositionBlockReason(str, Enum):
    SURVIVAL_BLOCKED = "survival_blocked"
    SUITABILITY_UNKNOWN = "suitability_unknown"
    SUITABILITY_DISABLED = "suitability_disabled"
    REQUESTED_SIDE_NOT_ELIGIBLE = "requested_side_not_eligible"
    STATE_KILL_ALL = "state_kill_all"
    STATE_CHOP_GUARD = "state_chop_guard"
    STATE_NOT_ACTIVE_OR_ARMED = "state_not_active_or_armed"
    LIVE_NOT_AUTHORIZED = "live_not_authorized"
    CAPITAL_SLOT_RATCHET_BLOCKED = "capital_slot_ratchet_blocked"
    CAPITAL_SLOT_RELEASED = "capital_slot_released"


class RequestedSide(str, Enum):
    LONG_BULL = "long_bull"
    SHORT_BEAR = "short_bear"
    NEUTRAL_OBSERVE = "neutral_observe"


@dataclass(frozen=True)
class DoublePlayCompositionInput:
    """
    Bundle of pure model outputs for one composition step.

    ``resulting_side_state`` must be the first return value from
    ``transition_state`` (same step as ``transition``).

    Optional capital-slot decisions are data-only gating inputs; omit both for
    backward-compatible composition without capital-slot context.
    """

    transition: TransitionDecision
    resulting_side_state: SideState
    survival: SurvivalEnvelopeDecision
    suitability: SuitabilityProjectionDecision
    requested_side: RequestedSide
    capital_slot_ratchet_decision: Optional[CapitalSlotRatchetDecision] = None
    capital_slot_release_decision: Optional[CapitalSlotReleaseDecision] = None


@dataclass(frozen=True)
class DoublePlayCompositionDecision:
    status: DoublePlayCompositionStatus
    block_reasons: tuple[DoublePlayCompositionBlockReason, ...]
    reason: str
    live_authorization: bool = False


def compose_double_play_decision(
    inp: DoublePlayCompositionInput,
) -> DoublePlayCompositionDecision:
    """
    Combine transition, survival, and suitability into a single model-level status.

    Eligibility is **not** trading permission. ``live_authorization`` is always false.
    """

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

    if surv.status == SurvivalEnvelopeStatus.BLOCKED or not surv.pre_authorization_eligible:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SURVIVAL_BLOCKED,),
            reason="Survival envelope blocks composition.",
            live_authorization=False,
        )

    sc = proj.suitability_class
    if sc == SuitabilityClass.UNKNOWN_SUITABILITY:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_UNKNOWN,),
            reason="Suitability unknown; fail closed.",
            live_authorization=False,
        )

    if sc == SuitabilityClass.DISABLED_FOR_CANDIDATE:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_DISABLED,),
            reason="Suitability disabled for candidate.",
            live_authorization=False,
        )

    if req == RequestedSide.LONG_BULL and not suit.can_enter_long_bull_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested Long/Bull but suitability does not allow long/bull pool.",
            live_authorization=False,
        )

    if req == RequestedSide.SHORT_BEAR and not suit.can_enter_short_bear_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested Short/Bear but suitability does not allow short/bear pool.",
            live_authorization=False,
        )

    if req == RequestedSide.NEUTRAL_OBSERVE and not suit.can_enter_neutral_pool:
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
            reason="Requested neutral observe but suitability does not allow neutral pool.",
            live_authorization=False,
        )

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

    if rel is not None and rel.released:
        if req in (RequestedSide.LONG_BULL, RequestedSide.SHORT_BEAR):
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.CAPITAL_SLOT_RELEASED,),
                reason="Capital slot released (inactivity or opportunity cost); no directional model eligibility.",
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

    return DoublePlayCompositionDecision(
        status=DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY,
        block_reasons=(),
        reason="All pure gates pass; model-only eligibility (not trading permission).",
        live_authorization=False,
    )
