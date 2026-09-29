"""Persistent Natural-ENTER convergence (S8 fixed lane + S6 + S7). No POST. No network."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
    DISPOSITION_MAX_CYCLES,
    DISPOSITION_MAX_DURATION,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    RUNTIME_OWNER_GO as S6_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    InjectedContinuousObservationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PersistentNaturalEnterConvergenceError,
    adjudicate_existing_owner_go_reuse_read_only_v1,
    assert_post_path_unreachable_from_runner_source_v1,
    assert_productive_execution_forbidden_v1,
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
    preflight_current_productive_persistent_natural_enter_v1,
    read_sidestate_continuity_snapshot_v1,
    run_offline_persistent_natural_enter_convergence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    observation_mark_payloads_for_bound_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
    run_natural_enter_long_sequence_for_bound_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _bound,
    _lane_g17,
    _market_kwargs,
    _pair,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    _cursor_floor_or_zero,
)
from tests.ops.test_full_core_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    _build_fresh_chain,
    _materialize_productivity_root,
)
from tests.ops.test_single_selected_future_runtime_binding_v1 import REPO_SHA
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _FakeClock,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    ORIGIN_SHA,
    _occupancy_absent,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_CONVERGENCE_V1.md"
)
NATIVE_ID = "0G-USDT-SWAP"


def _bound_lane_1() -> BoundInstrumentV1:
    base = _bound(lane_id="LANE_1")
    return base.__class__(
        instrument_id="inst-0g-usdt-swap",
        venue_native_id=NATIVE_ID,
        ranking_snapshot_id=base.ranking_snapshot_id,
        ranking_integrity_digest=base.ranking_integrity_digest,
        universe_snapshot_id=base.universe_snapshot_id,
        selection_id=base.selection_id,
        selection_integrity_digest=base.selection_integrity_digest,
        selection_state=base.selection_state,
    )


def _continuous_auth(
    *, native_id: str, max_cycles: int = 4
) -> CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    return CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=S6_RUNTIME_OWNER_GO,
        native_id=native_id,
        bar="1m",
        expected_cursor_floor=0.0,
        max_cycles_per_run=max_cycles,
        max_run_duration_seconds=180.0,
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=60.0,
    )


def _observation_from_closes(
    *, closes: tuple[float, ...], event_ts: float, bound: BoundInstrumentV1 | None = None
) -> InjectedContinuousObservationV1:
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=closes,
        last_event_ts_unix=event_ts,
    )
    b = bound or _bound_lane_1()
    mark_px = float(closes[-1]) + 1.0
    index_px = mark_px * 0.995
    mark_payload, index_payload = observation_mark_payloads_for_bound_v1(
        bound=b, mark_px=mark_px, index_px=index_px
    )
    return InjectedContinuousObservationV1(
        candles_payload=candles,
        occupancy_payloads=_occupancy_absent(),
        mark_price_payload=mark_payload,
        index_tickers_payload=index_payload,
    )


def test_module_pins_and_post_unreachable() -> None:
    assert CONTINUOUS_RUN_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert_productive_execution_forbidden_v1()
    assert assert_post_path_unreachable_from_runner_source_v1() is True
    assert SPEC_PATH.is_file()


def test_owner_go_reuse_read_only_unconsumed_store(tmp_path: Path) -> None:
    adj = adjudicate_existing_owner_go_reuse_read_only_v1(post_durable_store_root=tmp_path)
    assert adj.status == "VALID_UNTIL_CONSUMED"
    assert adj.post_owner_go_consumed is False
    assert adj.post_consumer_reachable_from_runner is False


def test_fixed_lane_and_cursor_store_roots_match(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    assert cursor_root.is_absolute() or str(cursor_root).endswith("LANE_1")


def test_preflight_cap24_handoff_without_reinvoke(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build", repository_sha=REPO_SHA)
    prod = _materialize_productivity_root(tmp_path, chain)
    native_id = str(chain["venue_native_id"])
    lane_root = tmp_path / "lane_state"
    pre = preflight_current_productive_persistent_natural_enter_v1(
        productivity_root=prod,
        lane_state_root=lane_root,
        repository_sha=REPO_SHA,
        binding_epoch=chain["binding_epoch"],
        authorization_native_id=native_id,
    )
    assert pre.ok is True
    assert pre.cap24_reselection_performed is False
    assert Path(pre.cursor_store_root).resolve() == Path(pre.lane_state_root).resolve()


def test_preflight_native_id_mismatch_fail_closed(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build", repository_sha=REPO_SHA)
    prod = _materialize_productivity_root(tmp_path, chain)
    pre = preflight_current_productive_persistent_natural_enter_v1(
        productivity_root=prod,
        lane_state_root=tmp_path / "lane",
        repository_sha=REPO_SHA,
        binding_epoch=chain["binding_epoch"],
        authorization_native_id="WRONG-NATIVE",
    )
    assert pre.ok is False
    assert pre.reason_code == "AUTHORIZATION_NATIVE_ID_MISMATCH"


def test_n1_bootstrap_uses_injected_c1_closes_not_stale_market_kwargs(tmp_path: Path) -> None:
    """Regression: JoinError seam_fail_closed:NakedLayeredCoreDurableStateError on bootstrap."""
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        invoke_occupied_lane_governed_cycle_n1_consumer_v1,
    )

    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=180.0)
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=strong_uptrend_closes_v1(count=12),
        last_event_ts_unix=last_ts,
    )
    bound = pairs["LANE_1"][1]
    kwargs = _market_kwargs(cycle_id_prefix="bootstrap-closes-regression", last_ts=last_ts)
    mark_px = 1.0
    index_px = 0.995
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_provenance_from_governed_synthetic_close_mark_and_index_v1,
    )

    kwargs["mark_px"] = mark_px
    kwargs["index_px"] = index_px
    kwargs["finalized_closes"] = (1.0, 2.0, 3.0)
    kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
    kwargs["candles_payload"] = candles
    kwargs["canonical_price_provenance"] = build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id),
            mark_px=mark_px,
            index_px=index_px,
        )
    results = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
    assert results["LANE_1"].governed_cycle_result.post_count == 0
    assert (Path(pairs["LANE_1"][0].lane_state_root) / CURSOR_FILENAME).is_file()


def test_s6_s7_single_cycle_then_cursor_floor_advances_for_second_run(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    t2 = t1 + 60.0
    obs_boot = _observation_from_closes(closes=path[:18], event_ts=t0 - 60.0)
    obs_one = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:20], event_ts=t0)]
    )
    clock = _FakeClock()
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    result = run_offline_persistent_natural_enter_convergence_v1(
        authorization=_continuous_auth(native_id=native_id, max_cycles=1),
        origin_main_sha=ORIGIN_SHA,
        lane_state_root=lane_root,
        bound=bound,
        g17_producers=g17,
        observation_source=obs_one,
        bootstrap_observation=obs_boot,
        evidence_root=tmp_path / "evidence_a",
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.post_count == 0
    assert result.cycles_completed == 1
    floor_after = _cursor_floor_or_zero(cursor_root)
    assert floor_after > 0.0
    snap = read_sidestate_continuity_snapshot_v1(cursor_root)
    assert snap["trading_epoch"] is not None
    auth2 = _continuous_auth(native_id=native_id, max_cycles=1)
    auth2 = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth2.continuous_owner_go,
        native_id=auth2.native_id,
        bar=auth2.bar,
        expected_cursor_floor=float(floor_after),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth2.max_run_duration_seconds,
        wait_interval_seconds=auth2.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth2.max_wait_for_next_c1_seconds,
        stall_seconds=auth2.stall_seconds,
    )
    obs_two = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:24], event_ts=t1)]
    )
    result2 = run_offline_persistent_natural_enter_convergence_v1(
        authorization=auth2,
        origin_main_sha=ORIGIN_SHA,
        lane_state_root=lane_root,
        bound=bound,
        g17_producers=g17,
        observation_source=obs_two,
        evidence_root=tmp_path / "evidence_b",
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result2.cycles_completed == 1
    assert _cursor_floor_or_zero(cursor_root) >= float(t0)


def test_max_cycles_bound_enforced(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    obs_boot = _observation_from_closes(closes=path[:14], event_ts=t0 - 60.0)
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=ORIGIN_SHA,
        g17_producers=g17,
        candles_payload=obs_boot.candles_payload,
        mark_price_payload=obs_boot.mark_price_payload,
        venue_native_id=native_id,
        index_tickers_payload=obs_boot.index_tickers_payload,
    )
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    obs = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:16], event_ts=t0)]
    )
    clock = _FakeClock()
    auth = _continuous_auth(native_id=native_id, max_cycles=1)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=1,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_offline_persistent_natural_enter_convergence_v1(
        authorization=auth,
        origin_main_sha=ORIGIN_SHA,
        lane_state_root=lane_root,
        bound=bound,
        g17_producers=g17,
        observation_source=obs,
        evidence_root=tmp_path / "evidence2",
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.disposition == DISPOSITION_MAX_CYCLES
    assert result.cycles_completed == 1


def test_max_duration_bound_enforced(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    obs = ScriptedContinuousObservationSourceV1(
        [_observation_from_closes(closes=path[:16], event_ts=t0), None]
    )
    clock = _FakeClock()
    clock.now = 0.0
    auth = _continuous_auth(native_id=native_id, max_cycles=4)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=auth.expected_cursor_floor,
        max_cycles_per_run=4,
        max_run_duration_seconds=0.01,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )

    def _time() -> float:
        clock.now += 0.02
        return clock.now

    result = run_offline_persistent_natural_enter_convergence_v1(
        authorization=auth,
        origin_main_sha=ORIGIN_SHA,
        lane_state_root=lane_root,
        bound=bound,
        g17_producers=g17,
        observation_source=obs,
        evidence_root=tmp_path / "evidence3",
        time_fn=_time,
        sleep_fn=lambda _s: None,
    )
    assert result.disposition == DISPOSITION_MAX_DURATION


def test_cap24_writer_not_reinvoked_per_s6_cycle(tmp_path: Path) -> None:
    chain = _build_fresh_chain(tmp_path / "build", repository_sha=REPO_SHA)
    native_id = str(chain["venue_native_id"])
    bound = _bound_lane_1()
    bound = bound.__class__(
        instrument_id=chain["instrument_id"],
        venue_native_id=chain["venue_native_id"],
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
        universe_snapshot_id=bound.universe_snapshot_id,
        selection_id=bound.selection_id,
        selection_integrity_digest=bound.selection_integrity_digest,
        selection_state=bound.selection_state,
    )
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    obs = ScriptedContinuousObservationSourceV1(
        [
            _observation_from_closes(closes=path[:18], event_ts=t0, bound=bound),
            None,
            _observation_from_closes(closes=path[:20], event_ts=t1, bound=bound),
            None,
        ]
    )
    obs_boot = _observation_from_closes(closes=path[:14], event_ts=t0 - 60.0, bound=bound)
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=ORIGIN_SHA,
        g17_producers=g17,
        candles_payload=obs_boot.candles_payload,
        mark_price_payload=obs_boot.mark_price_payload,
        venue_native_id=native_id,
        index_tickers_payload=obs_boot.index_tickers_payload,
    )
    with patch(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_cap24_selection_state_canonical_writer_v1."
        "execute_current_productive_cap24_selection_state_canonical_write_v1",
        side_effect=AssertionError("CAP24_WRITER_REINVOKED"),
    ):
        run_offline_persistent_natural_enter_convergence_v1(
            authorization=_continuous_auth(native_id=native_id, max_cycles=2),
            origin_main_sha=ORIGIN_SHA,
            lane_state_root=lane_root,
            bound=bound,
            g17_producers=g17,
            observation_source=obs,
            evidence_root=tmp_path / "evidence4",
            time_fn=_FakeClock().time,
            sleep_fn=lambda _s: None,
        )


def test_pre_external_terminal_on_natural_enter_long(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    native_id = str(bound.venue_native_id)
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17_single = _lane_g17(pairs)["LANE_1"]
    _o, _u, enter_cycle, enter_closes, _mark = run_natural_enter_long_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17_single,
    )
    assert enter_cycle.outgoing_cursor is not None
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        persist_current_productive_sidestate_confirmation_cursor_v1,
    )

    persist_current_productive_sidestate_confirmation_cursor_v1(
        enter_cycle.outgoing_cursor,
        store_root=cursor_root,
    )
    floor = _cursor_floor_or_zero(cursor_root)
    enter_ts = max(governed_productive_c1_event_ts_unix_v1(offset_seconds=300.0), floor + 60.0)
    obs = ScriptedContinuousObservationSourceV1(
        [
            _observation_from_closes(
                closes=enter_closes,
                event_ts=enter_ts,
            )
        ]
    )
    auth = _continuous_auth(native_id=native_id, max_cycles=2)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=2,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=auth.max_wait_for_next_c1_seconds,
        stall_seconds=auth.stall_seconds,
    )
    result = run_offline_persistent_natural_enter_convergence_v1(
        authorization=auth,
        origin_main_sha=ORIGIN_SHA,
        lane_state_root=lane_root,
        bound=bound,
        g17_producers={"LANE_1": g17_single},
        observation_source=obs,
        evidence_root=tmp_path / "evidence5",
        time_fn=_FakeClock().time,
        sleep_fn=lambda _s: None,
    )
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.post_count == 0


def test_cursor_store_mismatch_fail_closed(tmp_path: Path) -> None:
    bound = _bound_lane_1()
    with pytest.raises(PersistentNaturalEnterConvergenceError, match="CURSOR_STORE_ROOT_DRIFT"):
        runner = __import__(
            "src.ops.full_core_live_path_composition_root_v1."
            "current_productive_persistent_natural_enter_convergence_v1",
            fromlist=["make_n1_occupied_lane_s5_runner_v1"],
        ).make_n1_occupied_lane_s5_runner_v1(
            composed_pairs=build_s8_occupied_lane_pairs_v1(
                lane_state_root=tmp_path / "lane",
                bound=bound,
            ),
            g17_producers=_lane_g17({"LANE_1": _pair(tmp_path, "LANE_1")}),
            cycle_id_prefix_base="mismatch",
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
            CurrentProductiveGovernedCycleAuthorizationV1,
            EG_OWNER_GO,
            GET_OWNER_GO,
            OCCUPANCY_OWNER_GO,
            RUNTIME_OWNER_GO,
            T2_RUNTIME_OWNER_GO,
        )

        runner(
            authorization=CurrentProductiveGovernedCycleAuthorizationV1(
                cycle_owner_go=RUNTIME_OWNER_GO,
                get_owner_go=GET_OWNER_GO,
                eg_owner_go=EG_OWNER_GO,
                occupancy_owner_go=OCCUPANCY_OWNER_GO,
                t2_owner_go=T2_RUNTIME_OWNER_GO,
                native_id=str(bound.venue_native_id),
                bar="1m",
                expected_cursor_floor=0.0,
            ),
            origin_main_sha=ORIGIN_SHA,
            cursor_store_root=tmp_path / "wrong_root",
            lock_root=tmp_path / "lock",
            evidence_root=tmp_path / "ev",
            candles_payload={"code": "0", "data": []},
        )
