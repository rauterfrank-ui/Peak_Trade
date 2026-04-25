# tests/trading/master_v2/test_double_play_composition.py
from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_composition import (
    DOUBLE_PLAY_COMPOSITION_LAYER_VERSION,
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
    compose_double_play_decision,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_survival import (
    SurvivalBlockReason,
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
)
from trading.master_v2.double_play_suitability import (
    SideCompatibility,
    StrategySuitabilityProjection,
    SuitabilityClass,
    SuitabilityProjectionDecision,
)


def _surv_ok() -> SurvivalEnvelopeDecision:
    return SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.OK,
        pre_authorization_eligible=True,
        block_reasons=(),
        live_authorization=False,
    )


def _surv_blocked() -> SurvivalEnvelopeDecision:
    return SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
        block_reasons=(SurvivalBlockReason.INCOMPLETE_FINGERPRINT,),
        live_authorization=False,
    )


def _suit(
    *,
    sclass: SuitabilityClass,
    can_long: bool,
    can_short: bool,
    can_neutral: bool,
    side_c: SideCompatibility = SideCompatibility.LONG_BULL,
) -> SuitabilityProjectionDecision:
    p = StrategySuitabilityProjection(
        strategy_id="s",
        strategy_family=None,
        suitability_class=sclass,
        side_compatibility=side_c,
        eligible_for_long_bull_pool=can_long,
        eligible_for_short_bear_pool=can_short,
        eligible_for_neutral_pool=can_neutral,
        block_reasons=(),
        missing_inputs=(),
        reason="test",
    )
    return SuitabilityProjectionDecision(
        projection=p,
        can_enter_any_candidate_pool=can_long or can_short or can_neutral,
        can_enter_long_bull_pool=can_long,
        can_enter_short_bear_pool=can_short,
        can_enter_neutral_pool=can_neutral,
        live_authorization=False,
    )


def _compose(
    *,
    transition: TransitionDecision,
    state: SideState,
    surv: SurvivalEnvelopeDecision,
    suit: SuitabilityProjectionDecision,
    req: RequestedSide,
):
    return compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=transition,
            resulting_side_state=state,
            survival=surv,
            suitability=suit,
            requested_side=req,
        )
    )


def test_1_survival_block_prevents_eligibility() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_blocked(),
        suit=_suit(
            sclass=SuitabilityClass.LONG_ONLY_CANDIDATE,
            can_long=True,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.SURVIVAL_BLOCKED in d.block_reasons
    assert d.live_authorization is False


def test_2_unknown_suitability_blocks() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.UNKNOWN_SUITABILITY,
            can_long=False,
            can_short=False,
            can_neutral=False,
            side_c=SideCompatibility.UNKNOWN,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.SUITABILITY_UNKNOWN in d.block_reasons


def test_3_disabled_suitability_blocks() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.DISABLED_FOR_CANDIDATE,
            can_long=False,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.SUITABILITY_DISABLED in d.block_reasons


def test_4_long_only_cannot_approve_short_request() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.SHORT_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.LONG_ONLY_CANDIDATE,
            can_long=True,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.SHORT_BEAR,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE in d.block_reasons


def test_5_short_only_cannot_approve_long_request() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.SHORT_ONLY_CANDIDATE,
            can_long=False,
            can_short=True,
            can_neutral=False,
            side_c=SideCompatibility.SHORT_BEAR,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE in d.block_reasons


def test_6_both_sides_supports_long() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=False,
            side_c=SideCompatibility.BOTH,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_7_both_sides_supports_short() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.SHORT_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=False,
            side_c=SideCompatibility.BOTH,
        ),
        req=RequestedSide.SHORT_BEAR,
    )
    assert d.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY


def test_8_kill_all_blocks() -> None:
    d = _compose(
        transition=TransitionDecision(True, "KILL_ALL", False),
        state=SideState.KILL_ALL,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=False,
            side_c=SideCompatibility.BOTH,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.KILL_ALL
    assert DoublePlayCompositionBlockReason.STATE_KILL_ALL in d.block_reasons


def test_9_chop_guard_blocks() -> None:
    d = _compose(
        transition=TransitionDecision(True, "CHOP_GUARD", False),
        state=SideState.CHOP_GUARD_BLOCK,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.BOTH_SIDES_CANDIDATE,
            can_long=True,
            can_short=True,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.CHOP_GUARD
    assert DoublePlayCompositionBlockReason.STATE_CHOP_GUARD in d.block_reasons


def test_10_neutral_observe_is_observe_only() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.NEUTRAL_OBSERVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.NEUTRAL_RANGE_CANDIDATE,
            can_long=False,
            can_short=False,
            can_neutral=True,
            side_c=SideCompatibility.NEUTRAL_RANGE,
        ),
        req=RequestedSide.NEUTRAL_OBSERVE,
    )
    assert d.status is DoublePlayCompositionStatus.OBSERVE_ONLY


def test_11_valid_long_path_eligible_model_only() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.LONG_ONLY_CANDIDATE,
            can_long=True,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert d.block_reasons == ()


def test_12_valid_short_path_eligible_model_only() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.SHORT_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.SHORT_ONLY_CANDIDATE,
            can_long=False,
            can_short=True,
            can_neutral=False,
            side_c=SideCompatibility.SHORT_BEAR,
        ),
        req=RequestedSide.SHORT_BEAR,
    )
    assert d.status is DoublePlayCompositionStatus.ELIGIBLE_MODEL_ONLY
    assert d.block_reasons == ()


def test_13_no_live_authorization() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.LONG_ONLY_CANDIDATE,
            can_long=True,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.live_authorization is False


def test_14_no_network_imports_in_composition_module() -> None:
    p = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_composition.py"
    )
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = {"requests", "urllib3", "ccxt", "httpx", "socket", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module.split(".")[0]
            if mod in ("trading",):
                continue
            assert mod not in bad


def test_neutral_observe_blocks_directional_request() -> None:
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.NEUTRAL_OBSERVE,
        surv=_surv_ok(),
        suit=_suit(
            sclass=SuitabilityClass.LONG_ONLY_CANDIDATE,
            can_long=True,
            can_short=False,
            can_neutral=False,
        ),
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.STATE_NOT_ACTIVE_OR_ARMED in d.block_reasons


def test_layer_version() -> None:
    assert DOUBLE_PLAY_COMPOSITION_LAYER_VERSION == "v0"


def test_live_flag_on_subdecision_blocks() -> None:
    p = StrategySuitabilityProjection(
        strategy_id="s",
        strategy_family=None,
        suitability_class=SuitabilityClass.LONG_ONLY_CANDIDATE,
        side_compatibility=SideCompatibility.LONG_BULL,
        eligible_for_long_bull_pool=True,
        eligible_for_short_bear_pool=False,
        eligible_for_neutral_pool=False,
        block_reasons=(),
        missing_inputs=(),
        reason="test",
        live_authorization=True,
    )
    suit = SuitabilityProjectionDecision(
        projection=p,
        can_enter_any_candidate_pool=True,
        can_enter_long_bull_pool=True,
        can_enter_short_bear_pool=False,
        can_enter_neutral_pool=False,
        live_authorization=True,
    )
    d = _compose(
        transition=TransitionDecision(True, "X", False),
        state=SideState.LONG_ACTIVE,
        surv=_surv_ok(),
        suit=suit,
        req=RequestedSide.LONG_BULL,
    )
    assert d.status is DoublePlayCompositionStatus.BLOCKED
    assert DoublePlayCompositionBlockReason.LIVE_NOT_AUTHORIZED in d.block_reasons
