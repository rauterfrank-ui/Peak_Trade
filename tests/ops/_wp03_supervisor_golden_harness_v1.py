"""Shared offline harness for CURRENT-WP-03 supervisor golden convergence tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    ScriptedContinuousObservationSourceV1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorConfigV1,
    StandingSupervisorRunResultV1,
    run_n1_standing_pre_external_supervisor_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_productive_c1_event_ts_unix_v1,
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
    _supervisor_config,
)
from tests.ops._host_private_rest_fixture_v1 import host_private_rest_fixture_v1 as _fixture_rest

BASE_TS = 1_757_631_540_000


def _run_with_fixed_offline_acquisition_clock_v1(**kwargs):
    """Synthetic decisions at a fixed start; acquisition/evaluation clocks advance.

    The original financial path must preserve distinct decision/capture times.
    These injected payloads remain synthetic, without any venue contact.
    """
    from unittest.mock import patch
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_persistent_natural_enter_convergence_v1 as runner,
    )

    instant = datetime.now(timezone.utc)

    class OfflineDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz is not None else instant.replace(tzinfo=None)

    with patch.object(runner, "datetime", OfflineDateTime):
        return run_n1_standing_pre_external_supervisor_v1(**kwargs)


def _supervisor_config_wp03(tmp_path: Path, bound) -> StandingSupervisorConfigV1:
    cfg = _supervisor_config(tmp_path)
    return replace(
        cfg,
        wp02_productive_default_enabled=False,
        venue_native_id=bound.venue_native_id,
        canonical_instrument_id=bound.instrument_id,
    )


def _wp02_hook_v1(tmp_path: Path, native_id: str):
    writer = _held_writer(tmp_path / "wp02_topology")
    universe = wp02_eth_only_universe_source_payload_v1()
    base = native_id.split("-")[0]
    universe["data"][0].update(instId=native_id, baseCcy=base, ctValCcy=base, uly=f"{base}-USDT")
    marks = wp02_eth_only_mark_price_payload_v1()
    marks["data"][0]["instId"] = native_id
    binding = Wp02HookBindingV1(
        wp02_state_root=tmp_path / "wp02_state",
        topology_state_root_base=tmp_path / "wp02_topology",
        repository_sha=OWNER_GO_BASELINE_SHA,
        universe_source_payload=universe,
        universe_mark_price_payload=marks,
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
    pretrade_transport=None,
    cap24_productivity_root=None,
) -> StandingSupervisorRunResultV1:
    if prepared_lane is not None:
        bound, g17, pairs = prepared_lane
    else:
        bound = _bound_lane_1()
        lane_root = tmp_path / "lane_state"
        pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
        g17 = _lane_g17(pairs)
        path = (
            bootstrap_closes
            if bootstrap_closes is not None
            else strong_uptrend_closes_v1(count=128)
        )
        t_boot = governed_productive_c1_event_ts_unix_v1(offset_seconds=60.0)
        obs_boot = _observation_from_closes(closes=path[:104], event_ts=t_boot - 60.0)
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
    # Explicit synthetic finalized public history for this fixture's instrument.
    from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
        append_fact_v1,
        default_store_paths_v1,
    )
    from src.ops.economic_md_input_producer_v1.constants_v1 import (
        MINIMUM_FINALIZED_PT1M_MARKS,
        PT1M_STEP_MS,
    )

    paths = default_store_paths_v1(tmp_path / "public_store")
    for index in range(MINIMUM_FINALIZED_PT1M_MARKS):
        append_fact_v1(
            paths,
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + index * PT1M_STEP_MS,
                "mark_px": str(100 + index),
                "confirm": "1",
                "captured_at": "2026-09-26T00:00:00Z",
                "instrument": {"venue_native_id": native_id},
            },
        )
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
    config = _supervisor_config_wp03(tmp_path, bound) if cap24_productivity_root is None else None
    private_fetch = _fixture_rest
    if cap24_productivity_root is not None:
        from tests.ops._host_private_rest_fixture_v1 import initialize_synthetic_host_budget_v1
        from tests.ops.test_portfolio_budget_host_v1 import _fetch
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
            REUSED_BINDING_ACCOUNT_SCOPE,
        )

        config = StandingSupervisorConfigV1(
            public_store_root=tmp_path / "public_store",
            private_store_root=tmp_path / "private_store",
            lane_state_root=tmp_path / "lane_state",
            evidence_root=tmp_path / "evidence",
            lock_root=tmp_path / "lock",
            venue_native_id=bound.venue_native_id,
            canonical_instrument_id=bound.instrument_id,
            expected_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
            cap24_productivity_root=cap24_productivity_root,
            wp02_productive_default_enabled=False,
        )
        initialize_synthetic_host_budget_v1(
            config.private_store_root, bound, account=REUSED_BINDING_ACCOUNT_SCOPE
        )
        private_fetch = _fetch(uid=REUSED_BINDING_ACCOUNT_SCOPE)
    return _run_with_fixed_offline_acquisition_clock_v1(
        config=config,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=auth,
        observation_source=ScriptedContinuousObservationSourceV1(observations),
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=private_fetch,
        pretrade_transport=pretrade_transport,
        wp02_hook=_wp02_hook_v1(tmp_path, native_id),
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
    """Use the actual supervisor and its original private/budget host lifecycle."""
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=observations,
        max_cycles=max_cycles,
        prepared_lane=(bound, g17, pairs),
    )


def _run_layered_entry_supervisor_v1(tmp_path: Path, *, short: bool, with_pretrade: bool = True):
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
        prepare_layered_short_armed_seed_for_pre_external_invoke_v1,
    )
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        _bound as account_bound,
        _productive_transport,
    )
    from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
        write_cap21_productivity_root_for_inst_v1,
    )
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        observation_mark_payloads_for_bound_v1,
    )

    bound = account_bound()
    lane_root = tmp_path / "lane_state"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_root, bound=bound)
    prepare = (
        prepare_layered_short_armed_seed_for_pre_external_invoke_v1
        if short
        else prepare_layered_long_armed_seed_for_pre_external_invoke_v1
    )
    arm, closes, mark, event_ts, g17 = prepare(
        bound=bound, g17_typed_vol_producer=None, lane_state_root=lane_root
    )
    assert arm.decision_outcome not in {"enter_long", "enter_short"}
    observation = _observation_from_closes(closes=closes, event_ts=event_ts, bound=bound)
    mark_payload, index_payload = observation_mark_payloads_for_bound_v1(
        bound=bound, mark_px=mark, index_px=mark * 0.995
    )
    # Explicit offline source clocks. The old untimed OKX-shaped payload no
    # longer qualifies as a current mark merely by arriving at the runner.
    captured = datetime.now(timezone.utc)
    mark_payload["data"][0]["ts"] = str(int(captured.timestamp() * 1000))
    observation = replace(
        observation,
        mark_price_payload=mark_payload,
        index_tickers_payload=index_payload,
        mark_acquired_at_utc=captured.isoformat(),
    )
    # These are explicit original-owner test ports. Their productive-class
    # fixture labels do not attest actual venue contact or natural data.
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=[observation],
        max_cycles=1,
        prepared_lane=(bound, {"LANE_1": g17}, pairs),
        pretrade_transport=_productive_transport() if with_pretrade else None,
        cap24_productivity_root=write_cap21_productivity_root_for_inst_v1(
            tmp_path, venue_native_id=bound.venue_native_id
        ),
    )


def run_natural_long_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    return _run_layered_entry_supervisor_v1(tmp_path, short=False)


def run_natural_short_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    return _run_layered_entry_supervisor_v1(tmp_path, short=True)


def run_hold_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    flat = [100.0] * 128
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=[_observation_from_closes(closes=flat, event_ts=t0)],
        max_cycles=1,
        bootstrap_closes=strong_uptrend_closes_v1(count=128)[:104],
    )


def run_two_epoch_supervisor_v1(tmp_path: Path) -> StandingSupervisorRunResultV1:
    path = strong_uptrend_closes_v1(count=128)
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    t1 = t0 + 60.0
    return _run_supervisor_with_observations_v1(
        tmp_path,
        observations=[
            _observation_from_closes(closes=path[:106], event_ts=t0),
            None,
            _observation_from_closes(closes=path[:108], event_ts=t1),
        ],
        max_cycles=2,
    )
