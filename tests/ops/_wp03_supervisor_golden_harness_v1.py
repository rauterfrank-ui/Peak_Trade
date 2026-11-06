"""Shared offline harness for CURRENT-WP-03 supervisor golden convergence tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    persist_current_productive_sidestate_confirmation_cursor_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.trace_v1 import (
    StandingSupervisorTraceV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.wp02_insertion_v1 import (
    Wp02InsertionContextV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.unified_recovery_orchestration_v1 import (
    execute_unified_recovery_orchestration_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    StandingSupervisorRunResultV1,
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_productive_c1_event_ts_unix_v1,
    run_natural_enter_long_sequence_for_bound_v1,
    run_natural_enter_short_sequence_for_bound_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _bound_lane_1,
    _continuous_auth,
    _cursor_floor_or_zero,
    _lane_g17,
    _observation_from_closes,
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _FakeClock,
)
from src.ops.current_wp02_default_productive_universe_handoff_v1.wp02_hook_v1 import (
    Wp02HookBindingV1,
    build_default_wp02_hook_v1,
)
from tests.ops._wp02_universe_fixture_v1 import (
    wp02_eth_only_mark_price_payload_v1,
    wp02_eth_only_universe_source_payload_v1,
)
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    OBSERVED_UNIX,
    _held_writer,
)
from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
    OWNER_GO_BASELINE_SHA,
    REPO,
    _f1_m9_evaluator_factory,
    _public_rest_empty,
    _seed_public_marks,
    _supervisor_config,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest

BASE_TS = 1_757_631_540_000


def _supervisor_config_wp03(tmp_path: Path) -> StandingSupervisorConfigV1:
    cfg = _supervisor_config(tmp_path)
    return replace(cfg, wp02_productive_default_enabled=False)


def _wp02_hook_v1(tmp_path: Path):
    writer = _held_writer(tmp_path / "wp02_topology")
    binding = Wp02HookBindingV1(
        wp02_state_root=tmp_path / "wp02_state",
        topology_state_root_base=tmp_path / "wp02_topology",
        repository_sha=OWNER_GO_BASELINE_SHA,
        universe_source_payload=wp02_eth_only_universe_source_payload_v1(),
        universe_mark_price_payload=wp02_eth_only_mark_price_payload_v1(),
        source_event_time="2026-09-26T00:00:00Z",
        lane_assignment_writer=writer,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    return build_default_wp02_hook_v1(binding)


def _run_supervisor_with_observations_v1(
    tmp_path: Path,
    *,
    observations: list[Any],
    max_cycles: int,
    bootstrap_closes: list[float] | None = None,
    prepared_lane: tuple[Any, Any, dict[str, Any]] | None = None,
) -> StandingSupervisorRunResultV1:
    _seed_public_marks(tmp_path / "public_store")
    if prepared_lane is not None:
        bound, g17, pairs = prepared_lane
    else:
        bound = _bound_lane_1()
        lane_root = tmp_path / "lane_state"
        pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
        g17 = _lane_g17(pairs)
        path = bootstrap_closes if bootstrap_closes is not None else strong_uptrend_closes_v1()
        t_boot = governed_productive_c1_event_ts_unix_v1(offset_seconds=60.0)
        obs_boot = _observation_from_closes(closes=path[:14], event_ts=t_boot - 60.0)
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=OWNER_GO_BASELINE_SHA,
            g17_producers=g17,
            candles_payload=obs_boot.candles_payload,
            mark_price_payload=obs_boot.mark_price_payload,
            venue_native_id=str(bound.venue_native_id),
            index_tickers_payload=obs_boot.index_tickers_payload,
        )
    native_id = str(bound.venue_native_id)
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    auth = _continuous_auth(native_id=native_id, max_cycles=max_cycles)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=max_cycles,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001 if max_cycles > 1 else auth.wait_interval_seconds,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    return run_n1_standing_pre_external_supervisor_v1(
        config=_supervisor_config_wp03(tmp_path),
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(observations),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        wp02_hook=_wp02_hook_v1(tmp_path),
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )


def _run_persistent_enter_after_wp02_v1(
    tmp_path: Path,
    *,
    bound: Any,
    pairs: dict[str, Any],
    g17: dict[str, Any],
    observations: list[Any],
    max_cycles: int,
) -> StandingSupervisorRunResultV1:
    """Recovery + public supply + WP-02, then the same continuous path the supervisor uses."""
    cfg = _supervisor_config_wp03(tmp_path)
    _seed_public_marks(cfg.public_store_root)
    recovery = execute_unified_recovery_orchestration_v1(
        public_store_root=cfg.public_store_root,
        private_store_root=cfg.private_store_root,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        venue_native_id=cfg.venue_native_id,
    )
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
        run_public_runtime_ws_normalization_cycle_v1,
    )

    run_public_runtime_ws_normalization_cycle_v1(
        store_root=cfg.public_store_root,
        venue_native_id=cfg.venue_native_id,
        canonical_instrument_id=cfg.canonical_instrument_id,
        ws_messages=[],
        rest_fetch_json=_public_rest_empty,
    )
    wp02_sink: dict[str, Any] = {}
    _wp02_hook_v1(tmp_path)(
        Wp02InsertionContextV1(
            public_store_root=cfg.public_store_root,
            venue_native_id=cfg.venue_native_id,
            canonical_instrument_id=cfg.canonical_instrument_id,
            economic_md_mark_count=MINIMUM_FINALIZED_PT1M_MARKS,
            tick_index=0,
            wp02_result_sink=wp02_sink,
        )
    )
    floor = _cursor_floor_or_zero(Path(pairs["LANE_1"][0].lane_state_root))
    auth = _continuous_auth(native_id=str(bound.venue_native_id), max_cycles=max_cycles)
    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=auth.continuous_owner_go,
        native_id=auth.native_id,
        bar=auth.bar,
        expected_cursor_floor=float(floor),
        max_cycles_per_run=max_cycles,
        max_run_duration_seconds=auth.max_run_duration_seconds,
        wait_interval_seconds=0.001,
        max_wait_for_next_c1_seconds=30.0,
        stall_seconds=auth.stall_seconds,
    )
    clock = _FakeClock()
    policy_result = run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
        authorization=auth,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        lane_state_root=cfg.lane_state_root,
        bound=bound,
        g17_producers=g17,
        observation_source=ScriptedContinuousObservationSourceV1(observations),
        evidence_root=cfg.evidence_root,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        lock_root=cfg.lock_root,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    orch = policy_result.orchestrator_result
    chain_result = wp02_sink.get("chain_result")
    trace = StandingSupervisorTraceV1(
        run_id="wp03-golden-session",
        bound_instrument_id=str(bound.instrument_id),
        venue_native_id=str(bound.venue_native_id),
        recovery_completed=recovery.ok,
        recovery_steps=list(recovery.steps_completed),
        public_supply_refreshed=True,
        public_marks_count=MINIMUM_FINALIZED_PT1M_MARKS,
        pretrade_truth_refreshed=True,
        wp02_hook_invoked=True,
        wp02_cap21_refresh_invoked=bool(getattr(chain_result, "cap21_refresh_invoked", False)),
        wp02_hard_facts_handoff_invoked=bool(
            getattr(chain_result, "hard_facts_handoff_invoked", False)
        ),
        wp02_membership_persisted=bool(getattr(chain_result, "membership_persisted", False)),
        continuous_admission_granted=True,
        accepted_c1_count=int(orch.accepted_c1_count),
        governed_cycle_count=int(orch.cycles_completed),
        terminal_disposition=str(orch.disposition),
        post_count=int(orch.post_count),
        extra={
            "wp02": wp02_sink,
            "observation_scope": "scoped_readonly_inject",
        },
    )
    if chain_result is not None:
        trace.extra["wp02_ranking_snapshot_id"] = str(
            (getattr(chain_result, "ranking_snapshot", None) or {}).get("ranking_snapshot_id") or ""
        )
    return StandingSupervisorRunResultV1(
        ok=recovery.ok and orch.post_count == 0,
        run_id=trace.run_id,
        trace=trace,
        recovery=recovery,
        policy_result=policy_result,
        owner_go_consumed=(
            cfg.evidence_root / "bounded_continuous_run_owner_go_consume_v1.json"
        ).is_file(),
        authority_invariants_ok=True,
    )


def run_natural_long_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    bound = _bound_lane_1()
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17 = _lane_g17(pairs)
    g17_single = g17["LANE_1"]
    _o, _u, enter_cycle, enter_closes, _mark = run_natural_enter_long_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17_single,
    )
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        enter_cycle.outgoing_cursor,
        store_root=cursor_root,
    )
    floor = _cursor_floor_or_zero(cursor_root)
    enter_ts = max(governed_productive_c1_event_ts_unix_v1(offset_seconds=300.0), floor + 60.0)
    result = _run_persistent_enter_after_wp02_v1(
        tmp_path,
        bound=bound,
        pairs=pairs,
        g17=g17,
        observations=[
            _observation_from_closes(closes=enter_closes, event_ts=enter_ts, bound=bound)
        ],
        max_cycles=1,
    )
    result.trace.extra["natural_enter_decision"] = str(enter_cycle.decision_outcome)
    return result


def run_natural_short_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    bound = _bound_lane_1()
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    g17_single = _lane_g17(pairs)["LANE_1"]
    (
        _o1,
        _d,
        _arm,
        enter_cycle,
        _ac,
        enter_closes,
        _sm,
    ) = run_natural_enter_short_sequence_for_bound_v1(
        bound=bound,
        g17_typed_vol_producer=g17_single,
    )
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    persist_current_productive_sidestate_confirmation_cursor_v1(
        enter_cycle.outgoing_cursor,
        store_root=cursor_root,
    )
    floor = _cursor_floor_or_zero(cursor_root)
    enter_ts = max(governed_productive_c1_event_ts_unix_v1(offset_seconds=300.0), floor + 60.0)
    result = _run_persistent_enter_after_wp02_v1(
        tmp_path,
        bound=bound,
        pairs=pairs,
        g17=_lane_g17(pairs),
        observations=[
            _observation_from_closes(closes=enter_closes, event_ts=enter_ts, bound=bound)
        ],
        max_cycles=1,
    )
    result.trace.extra["natural_enter_decision"] = str(enter_cycle.decision_outcome)
    return result


def run_hold_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    flat = [100.0] * 20
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=[_observation_from_closes(closes=flat, event_ts=t0)],
        max_cycles=1,
        bootstrap_closes=strong_uptrend_closes_v1()[:14],
    )


def run_two_epoch_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    path = strong_uptrend_closes_v1()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=[
            _observation_from_closes(closes=path[:16], event_ts=t0),
            None,
            _observation_from_closes(closes=path[:18], event_ts=t1),
        ],
        max_cycles=2,
    )
