"""Regime→SideState projection for future layered CZ-4 bind (contract/validator only).

Authority: LayeredCoreAuthoritySealV1 regime_pre/regime_post is the sole trading-decision
regime source for this projection. SideState is a downstream lifecycle surface (O-R2).

Orientation alignment for regime_post uses the same BULL=LONG / BEAR=SHORT rule as L9
(``naked_mv2_dp_explicit_layered_core_v1.l9_counter_move_v1._regime_to_direction``).
Switch pending rows mirror productive ``transition_state`` long/short active reversal
entries (``double_play_state.transition_state`` DOWNSCOPE_CONFIRMED while ACTIVE).

Does not wire into integrated replay or CZ-4. Does not authorize cutover.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import ActiveSide, SideState, derive_active_side
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    scope_direction_from_side_state_v1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1

CONTRACT_OWNER = "ops.p5_7_regime_sidestate_projection_mapping_contract_v1.contract_v1"


class RegimeSideStateProjectionPhaseV1(str, Enum):
    INITIAL_SEED = "initial_seed"
    MECHANICAL_STEP = "mechanical_step"


class RegimeSideStateProjectionFailureCodeV1(str, Enum):
    REGIME_PRE_POST_INVALID = "regime_pre_post_invalid"
    SEAL_SWITCH_FLAG_INCONSISTENT = "seal_switch_flag_inconsistent"
    OCCUPANCY_CONTRADICTS_PRIOR_SIDESTATE = "occupancy_contradicts_prior_sidestate"
    OCCUPANCY_CONTRADICTS_VENUE_FLAT = "occupancy_contradicts_venue_flat"
    ACTIVE_FROM_REGIME_ALONE_FORBIDDEN = "active_from_regime_alone_forbidden"
    IMPLICIT_BULL_TO_LONG_ACTIVE = "implicit_bull_to_long_active_forbidden"
    IMPLICIT_BEAR_TO_SHORT_ACTIVE = "implicit_bear_to_short_active_forbidden"
    SWITCH_FROM_INCOMPATIBLE_PRIOR = "switch_from_incompatible_prior_sidestate"
    SIDESTATE_TO_REGIME_BACKFLOW_FORBIDDEN = "sidestate_to_regime_backflow_forbidden"
    PROJECTION_DOMAIN_UNRESOLVED = "projection_domain_unresolved"


@dataclass(frozen=True)
class RegimeSideStateProjectionInputV1:
    regime_pre: NakedRegimeV1
    regime_post: NakedRegimeV1
    switch_condition_met: bool
    prior_side_state: SideState
    phase: RegimeSideStateProjectionPhaseV1
    venue_flat: bool
    existing_position_side: ExistingPositionSide


@dataclass(frozen=True)
class RegimeSideStateProjectionResultV1:
    ok: bool
    projected_side_state: SideState | None
    failure_codes: Tuple[str, ...]


def regime_to_scope_direction_v1(regime: NakedRegimeV1) -> ScopeDirectionState:
    """Same orientation rule as L9 counter-move (BULL→LONG, BEAR→SHORT)."""
    if regime is NakedRegimeV1.BULL:
        return ScopeDirectionState.LONG
    return ScopeDirectionState.SHORT


def _armed_neutral_start_for_regime_v1(regime: NakedRegimeV1) -> SideState:
    if regime is NakedRegimeV1.BULL:
        return SideState.LONG_ARMED_NEUTRAL_START
    return SideState.SHORT_ARMED_NEUTRAL_START


def _fail(*codes: RegimeSideStateProjectionFailureCodeV1) -> RegimeSideStateProjectionResultV1:
    return RegimeSideStateProjectionResultV1(
        ok=False,
        projected_side_state=None,
        failure_codes=tuple(dict.fromkeys(c.value for c in codes)),
    )


def _ok(projected: SideState) -> RegimeSideStateProjectionResultV1:
    return RegimeSideStateProjectionResultV1(
        ok=True,
        projected_side_state=projected,
        failure_codes=(),
    )


def _validate_occupancy_consistency_v1(
    inp: RegimeSideStateProjectionInputV1,
) -> Tuple[str, ...]:
    failures: list[RegimeSideStateProjectionFailureCodeV1] = []
    pos = inp.existing_position_side
    if inp.venue_flat and pos is not ExistingPositionSide.NONE:
        failures.append(RegimeSideStateProjectionFailureCodeV1.OCCUPANCY_CONTRADICTS_VENUE_FLAT)
    if not inp.venue_flat and pos is ExistingPositionSide.NONE:
        failures.append(RegimeSideStateProjectionFailureCodeV1.OCCUPANCY_CONTRADICTS_VENUE_FLAT)

    active = derive_active_side(inp.prior_side_state)
    if pos is ExistingPositionSide.LONG and active is not ActiveSide.LONG:
        if inp.prior_side_state not in (
            SideState.NEUTRAL_OBSERVE,
            SideState.LONG_ARMED,
            SideState.LONG_ARMED_NEUTRAL_START,
            SideState.LONG_ARMED_SWITCH_TERMINAL,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
        ):
            failures.append(
                RegimeSideStateProjectionFailureCodeV1.OCCUPANCY_CONTRADICTS_PRIOR_SIDESTATE
            )
    if pos is ExistingPositionSide.SHORT and active is not ActiveSide.SHORT:
        if inp.prior_side_state not in (
            SideState.NEUTRAL_OBSERVE,
            SideState.SHORT_ARMED,
            SideState.SHORT_ARMED_NEUTRAL_START,
            SideState.SHORT_ARMED_SWITCH_TERMINAL,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
        ):
            failures.append(
                RegimeSideStateProjectionFailureCodeV1.OCCUPANCY_CONTRADICTS_PRIOR_SIDESTATE
            )
    return tuple(dict.fromkeys(c.value for c in failures))


def _validate_seal_regime_consistency_v1(
    inp: RegimeSideStateProjectionInputV1,
) -> Tuple[str, ...]:
    switched = inp.regime_pre is not inp.regime_post
    if inp.switch_condition_met != switched:
        return (RegimeSideStateProjectionFailureCodeV1.SEAL_SWITCH_FLAG_INCONSISTENT.value,)
    return ()


def _forbid_active_from_regime_only_v1(
    *,
    prior: SideState,
    projected: SideState,
    inp: RegimeSideStateProjectionInputV1,
) -> Tuple[str, ...]:
    failures: list[RegimeSideStateProjectionFailureCodeV1] = []
    if projected in (SideState.LONG_ACTIVE, SideState.SHORT_ACTIVE):
        if (
            prior == projected
            and inp.regime_pre is inp.regime_post
            and not inp.switch_condition_met
        ):
            return ()
        if inp.venue_flat or inp.existing_position_side is ExistingPositionSide.NONE:
            failures.append(
                RegimeSideStateProjectionFailureCodeV1.ACTIVE_FROM_REGIME_ALONE_FORBIDDEN
            )
        if projected is SideState.LONG_ACTIVE and inp.regime_post is NakedRegimeV1.BULL:
            if prior not in (
                SideState.LONG_ACTIVE,
                SideState.SWITCH_SHORT_TO_LONG_PENDING,
                SideState.LONG_BLOCKED,
            ):
                failures.append(RegimeSideStateProjectionFailureCodeV1.IMPLICIT_BULL_TO_LONG_ACTIVE)
        if projected is SideState.SHORT_ACTIVE and inp.regime_post is NakedRegimeV1.BEAR:
            if prior not in (
                SideState.SHORT_ACTIVE,
                SideState.SWITCH_LONG_TO_SHORT_PENDING,
                SideState.SHORT_BLOCKED,
            ):
                failures.append(
                    RegimeSideStateProjectionFailureCodeV1.IMPLICIT_BEAR_TO_SHORT_ACTIVE
                )
    return tuple(dict.fromkeys(c.value for c in failures))


def project_regime_to_sidestate_v1(
    inp: RegimeSideStateProjectionInputV1,
) -> RegimeSideStateProjectionResultV1:
    """Project seal regime_pre/post onto operational SideState (downstream only)."""
    if inp.regime_pre not in (NakedRegimeV1.BULL, NakedRegimeV1.BEAR):
        return _fail(RegimeSideStateProjectionFailureCodeV1.REGIME_PRE_POST_INVALID)
    if inp.regime_post not in (NakedRegimeV1.BULL, NakedRegimeV1.BEAR):
        return _fail(RegimeSideStateProjectionFailureCodeV1.REGIME_PRE_POST_INVALID)

    for code in _validate_seal_regime_consistency_v1(inp):
        return RegimeSideStateProjectionResultV1(
            ok=False, projected_side_state=None, failure_codes=(code,)
        )

    occ_failures = _validate_occupancy_consistency_v1(inp)
    if occ_failures:
        return RegimeSideStateProjectionResultV1(
            ok=False, projected_side_state=None, failure_codes=occ_failures
        )

    if inp.prior_side_state in (SideState.KILL_ALL, SideState.CHOP_GUARD_BLOCK):
        return _fail(RegimeSideStateProjectionFailureCodeV1.PROJECTION_DOMAIN_UNRESOLVED)

    switched = inp.switch_condition_met and inp.regime_pre is not inp.regime_post

    if not switched:
        if inp.phase is RegimeSideStateProjectionPhaseV1.INITIAL_SEED:
            if inp.prior_side_state is SideState.NEUTRAL_OBSERVE and inp.venue_flat:
                projected = _armed_neutral_start_for_regime_v1(inp.regime_post)
                active_fail = _forbid_active_from_regime_only_v1(
                    prior=inp.prior_side_state, projected=projected, inp=inp
                )
                if active_fail:
                    return RegimeSideStateProjectionResultV1(
                        ok=False, projected_side_state=None, failure_codes=active_fail
                    )
                return _ok(projected)
        return _ok(inp.prior_side_state)

    pre_dir = regime_to_scope_direction_v1(inp.regime_pre)
    post_dir = regime_to_scope_direction_v1(inp.regime_post)
    prior_dir = scope_direction_from_side_state_v1(
        inp.prior_side_state,
        fallback=ScopeDirectionState.LONG
        if pre_dir is ScopeDirectionState.LONG
        else ScopeDirectionState.SHORT,
    )

    active = derive_active_side(inp.prior_side_state)

    if active is ActiveSide.LONG and post_dir is ScopeDirectionState.SHORT:
        projected = SideState.SWITCH_LONG_TO_SHORT_PENDING
    elif active is ActiveSide.SHORT and post_dir is ScopeDirectionState.LONG:
        projected = SideState.SWITCH_SHORT_TO_LONG_PENDING
    elif inp.venue_flat and active is ActiveSide.NEUTRAL:
        projected = _armed_neutral_start_for_regime_v1(inp.regime_post)
    elif active is ActiveSide.NEUTRAL and prior_dir is pre_dir:
        projected = _armed_neutral_start_for_regime_v1(inp.regime_post)
    else:
        return _fail(RegimeSideStateProjectionFailureCodeV1.SWITCH_FROM_INCOMPATIBLE_PRIOR)

    active_fail = _forbid_active_from_regime_only_v1(
        prior=inp.prior_side_state, projected=projected, inp=inp
    )
    if active_fail:
        return RegimeSideStateProjectionResultV1(
            ok=False, projected_side_state=None, failure_codes=active_fail
        )
    return _ok(projected)


def validate_no_sidestate_to_regime_backflow_v1(
    *,
    side_state: SideState,
    inferred_regime: NakedRegimeV1 | None,
) -> RegimeSideStateProjectionResultV1:
    """SideState must never be interpreted as authoritative core regime."""
    if inferred_regime is not None:
        return _fail(RegimeSideStateProjectionFailureCodeV1.SIDESTATE_TO_REGIME_BACKFLOW_FORBIDDEN)
    _ = side_state
    return RegimeSideStateProjectionResultV1(
        ok=True,
        projected_side_state=None,
        failure_codes=(),
    )


def all_naked_regime_domain_v1() -> Tuple[NakedRegimeV1, ...]:
    return (NakedRegimeV1.BULL, NakedRegimeV1.BEAR)


def all_sidestate_domain_v1() -> Tuple[SideState, ...]:
    return tuple(SideState)


__all__ = [
    "CONTRACT_OWNER",
    "RegimeSideStateProjectionFailureCodeV1",
    "RegimeSideStateProjectionInputV1",
    "RegimeSideStateProjectionPhaseV1",
    "RegimeSideStateProjectionResultV1",
    "all_naked_regime_domain_v1",
    "all_sidestate_domain_v1",
    "project_regime_to_sidestate_v1",
    "regime_to_scope_direction_v1",
    "validate_no_sidestate_to_regime_backflow_v1",
]
