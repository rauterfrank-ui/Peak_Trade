"""Bilateral CURRENT productive MV2+DP natural ENTER regressions (post-V32)."""

from __future__ import annotations

from pathlib import Path

from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    CANONICAL_BULL_BEAR_SYMMETRY_INVARIANT_V1,
    CURRENT_CANONICAL_DECISION_SSOT_LAYER_COUNT_V1,
    CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1,
    LAYER_COUNT_MATCH_STATUS_V1,
    NAKED_LAYERED_CORE_L1_L10_COUNT_V1,
    assert_complete_decision_ssot_layer_trace_v1,
    assert_natural_enter_long_cycle_v1,
    assert_natural_enter_short_cycle_v1,
    assert_natural_short_arm_cycle_v1,
    run_layered_long_arm_then_enter_for_pre_external_v1,
    run_natural_enter_long_sequence_for_bound_v1,
    run_natural_enter_short_sequence_for_bound_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _INSTRUMENT,
    _bound,
    _produced_g17_producer,
)
from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_state import SideState


def test_double_play_decision_ssot_layer_model_and_bilateral_complete_traces_v1() -> None:
    """Decision-SSOT = 8 layers; L1–L10 mechanical count is separate (explained)."""
    assert CURRENT_CANONICAL_DECISION_SSOT_LAYER_COUNT_V1 == 8
    assert CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1[0] == "C1_OBSERVATION_ACCEPTANCE"
    assert CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1[-1] == "ENTRY_EXIT_POLICY"
    assert NAKED_LAYERED_CORE_L1_L10_COUNT_V1 == 10
    assert LAYER_COUNT_MATCH_STATUS_V1 == "DIFFERENT_BUT_EXPLAINED"

    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    _o1, _u, long_enter, _c, _m = run_natural_enter_long_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    long_trace = assert_complete_decision_ssot_layer_trace_v1(
        long_enter, expected_selected_side="LONG"
    )
    _o2, _d, short_arm, short_enter, _ac, _ec, _sm = run_natural_enter_short_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    short_arm_trace = assert_complete_decision_ssot_layer_trace_v1(
        short_arm, expected_selected_side="SHORT"
    )
    short_enter_trace = assert_complete_decision_ssot_layer_trace_v1(
        short_enter, expected_selected_side="SHORT"
    )
    assert (
        long_trace
        == short_arm_trace
        == short_enter_trace
        == (CURRENT_CANONICAL_DECISION_SSOT_LAYER_ORDER_V1)
    )
    # Timing difference is canonical (arm cycle ≠ enter cycle for Short).
    assert str(short_arm.cycle_id) != str(short_enter.cycle_id)
    assert str(short_arm.decision_outcome) != "enter_short"
    assert str(short_enter.decision_outcome) == "enter_short"


def test_current_mv2_dp_natural_long_entry_v1() -> None:
    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    _origin, upscope_candidate, enter_cycle, _closes, mark_px = (
        run_natural_enter_long_sequence_for_bound_v1(
            bound=bound,
            g17_typed_vol_producer=g17,
        )
    )
    assert_natural_enter_long_cycle_v1(enter_cycle)
    assert upscope_candidate.decision_outcome not in {"enter_long", "enter_short"}
    intermediate = enter_cycle.replay.intermediate
    assert intermediate.composition_result.composition_status is CompositionStatus.LONG_SELECTED
    assert intermediate.bull_assessment is not None
    assert intermediate.bull_assessment.status is DirectionalAssessmentStatus.CONFIRMED
    assert float(mark_px) == 1635.0
    assert "first-class opposing layers" in CANONICAL_BULL_BEAR_SYMMETRY_INVARIANT_V1


def test_current_mv2_dp_natural_short_entry_after_arm_transition_v1() -> None:
    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    (
        _origin,
        downscope_candidate,
        arm_cycle,
        enter_cycle,
        _arm_closes,
        _enter_closes,
        _mark,
    ) = run_natural_enter_short_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    assert downscope_candidate.decision_outcome not in {"enter_long", "enter_short"}
    assert_natural_short_arm_cycle_v1(arm_cycle)
    assert str(arm_cycle.decision_outcome) != "enter_short"
    assert_natural_enter_short_cycle_v1(enter_cycle)
    # Timing difference is canonical: arm cycle ≠ enter cycle.
    assert str(getattr(arm_cycle, "cycle_id", "")) != str(getattr(enter_cycle, "cycle_id", ""))
    intermediate = enter_cycle.replay.intermediate
    assert intermediate.composition_result.composition_status is CompositionStatus.SHORT_SELECTED
    assert intermediate.bear_assessment is not None
    assert intermediate.bear_assessment.status is DirectionalAssessmentStatus.CONFIRMED


def test_current_mv2_dp_long_and_short_not_simultaneous_on_natural_entries() -> None:
    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    _o1, _u, long_enter, _c, _m = run_natural_enter_long_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    _o2, _d, _arm, short_enter, _ac, _ec, _sm = run_natural_enter_short_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    long_side = long_enter.outgoing_cursor.side_state
    short_side = short_enter.outgoing_cursor.side_state
    long_active = long_side in {
        SideState.LONG_ACTIVE,
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
    }
    short_active = short_side in {
        SideState.SHORT_ACTIVE,
        SideState.SHORT_ARMED,
        SideState.SHORT_ARMED_NEUTRAL_START,
        SideState.SHORT_ARMED_SWITCH_TERMINAL,
    }
    # Separate fixtures: each trajectory arms one side only.
    assert long_active is True
    assert short_active is True
    assert long_side != short_side


def test_layered_long_arm_persist_then_enter_long(tmp_path: Path) -> None:
    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    arm_cycle, enter_cycle, _closes, _mark, _ts = (
        run_layered_long_arm_then_enter_for_pre_external_v1(
            bound=bound,
            g17_typed_vol_producer=g17,
            lane_state_root=tmp_path / "lanes",
        )
    )
    assert str(arm_cycle.decision_outcome) != "enter_long"
    assert_natural_enter_long_cycle_v1(enter_cycle)


def test_layered_short_arm_persist_restore_then_enter_short(tmp_path: Path) -> None:
    """Short layered topology: oneshot arm → persist → compose enter under store."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        persist_current_productive_sidestate_confirmation_cursor_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        _lane_pair_v1,
    )
    from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
        ensure_productive_layered_core_episode_store_v1,
    )
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        _compose_layered_lane_cycle_v1,
        natural_enter_short_after_arm_closes_v1,
        run_downscope_candidate_progress_cycles_v1,
        run_natural_short_arm_cycle_v1,
    )

    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)
    _origin, downscope_candidate, path = run_downscope_candidate_progress_cycles_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    arm_cycle, arm_closes, arm_mark = run_natural_short_arm_cycle_v1(
        downscope_candidate_cycle=downscope_candidate,
        bound=bound,
        g17_typed_vol_producer=g17,
        downtrend=path,
    )
    assert_natural_short_arm_cycle_v1(arm_cycle)

    pair = _lane_pair_v1(lane_state_root=tmp_path / "lanes", bound=bound)
    store_root = Path(pair[0].lane_state_root)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        arm_cycle.outgoing_cursor,
        store_root=store_root,
    )
    enter_closes = natural_enter_short_after_arm_closes_v1(arm_closes)
    enter_mark = float(enter_closes[-1])
    enter_ts = 1_700_000_100.0
    ensure_productive_layered_core_episode_store_v1(
        store_root=store_root,
        bound_instrument=bound,
        mark_price_m_t=enter_mark,
        finalized_closes=enter_closes,
        last_finalized_event_ts_unix=enter_ts,
        outgoing_cursor=arm_cycle.outgoing_cursor,
    )
    enter_cycle = _compose_layered_lane_cycle_v1(
        pair=pair,
        g17_typed_vol_producer=g17,
        closes=enter_closes,
        mark_px=enter_mark,
        event_ts_unix=enter_ts,
        cycle_id_prefix="layered-short-enter",
    )
    assert_natural_enter_short_cycle_v1(enter_cycle)


def test_bilateral_natural_enter_crs_binds_only_at_enter_live_29p_join_v1() -> None:
    """Same CRS owner/bind for Long and Short: pre-join None → join LIVE_ACCOUNT_BOUND PASS."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        DECISION_ENTER,
        STATUS_PASS,
        join_current_productive_enter_live_29p_before_venue_plan_v1,
    )
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        _balance_payload,
        _injected,
    )
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )

    g17 = _produced_g17_producer(instrument_id=_INSTRUMENT)
    bound = _bound(instrument_id=_INSTRUMENT)

    def _assert_join_crs(enter_cycle: object) -> None:
        replay = getattr(enter_cycle, "replay", None)
        assert replay is not None
        assert replay.intermediate.capital_risk_sizing_decision is None
        assert replay.intermediate.canonical_order_intent is None
        join = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=replay,
            bound_instrument=bound,
            injected=_injected(payload=_balance_payload()),
            decision_epoch="2026-09-16T00:00:00Z",
        )
        assert join.decision_class == DECISION_ENTER
        assert join.status == STATUS_PASS
        assert join.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
        rebound = join.replay
        assert rebound is not None
        sizing = rebound.intermediate.capital_risk_sizing_decision
        assert sizing is not None
        assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
        assert rebound.intermediate.canonical_order_intent is not None

    _o1, _u, long_enter, _c, _m = run_natural_enter_long_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    assert_natural_enter_long_cycle_v1(long_enter)
    _assert_join_crs(long_enter)

    _o2, _d, _arm, short_enter, _ac, _ec, _sm = run_natural_enter_short_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17,
    )
    assert_natural_enter_short_cycle_v1(short_enter)
    _assert_join_crs(short_enter)
