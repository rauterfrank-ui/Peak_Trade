"""S7 scope-colocated layered-core episode bootstrap (no duplicate mechanical step)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
    strong_uptrend_closes_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _bound,
    _lane_g17,
    _market_kwargs,
    _pair,
    _s7_kwargs,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    ORIGIN_SHA,
    _bound_lane_1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)


def test_sequential_cold_s7_compose_bootstrap_no_join_error(tmp_path: Path) -> None:
    """Regression: repeated cold S7 compose must not intermittently fail at episode bootstrap."""
    bound = _bound_lane_1()
    path = strong_uptrend_closes_v1()
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=180.0)
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=path[:20],
        last_event_ts_unix=last_ts,
    )
    kwargs = _market_kwargs(cycle_id_prefix="multi-cold-bootstrap", last_ts=last_ts)
    kwargs["g17_typed_vol_producers"] = None

    for i in range(10):
        lane = tmp_path / f"lane_{i}"
        pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane, bound=bound)
        kwargs["g17_typed_vol_producers"] = _lane_g17(pairs)
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=ORIGIN_SHA,
            g17_producers=kwargs["g17_typed_vol_producers"],
            candles_payload=candles,
        )
        store = Path(pairs["LANE_1"][0].lane_state_root)
        assert (store / CURSOR_FILENAME).is_file()
        restore_episode_from_store_v1(store, expected_instrument_id=str(bound.instrument_id))


def test_compose_with_misaligned_two_close_bootstrap_still_persists(tmp_path: Path) -> None:
    """Volatile last-two closes must not fail S7 compose when scope is on outgoing cursor."""
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    # Sharp last-bar move: old two-close + mechanical replay step was brittle here.
    closes = tuple(float(x) for x in (strong_uptrend_closes_v1()[:18]))
    volatile = closes[:-2] + (closes[-2] * 0.85, closes[-1] * 1.12)
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=volatile,
        last_event_ts_unix=last_ts,
    )
    market = _market_kwargs(cycle_id_prefix="volatile-two-close", last_ts=last_ts)
    market["finalized_closes"] = volatile
    market["mark_px"] = float(volatile[-1])
    s7 = _s7_kwargs(market)
    s7["g17_typed_vol_producers"] = _lane_g17(pairs)
    compose_occupied_lane_mv2_dp_durable_cycle_v1(pairs, **s7)
    store = Path(pairs["LANE_1"][0].lane_state_root)
    assert (store / CURSOR_FILENAME).is_file()


def test_compose_lane_identity_mismatch_still_fail_closed(tmp_path: Path) -> None:
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    bound = _bound(lane_id="LANE_1")
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=60.0)
    market = _market_kwargs(cycle_id_prefix="identity-fail-closed", last_ts=last_ts)
    s7 = _s7_kwargs(market)
    s7["g17_typed_vol_producers"] = _lane_g17(pairs)
    compose_occupied_lane_mv2_dp_durable_cycle_v1(pairs, **s7)
    wrong = replace(bound, instrument_id="wrong-inst")
    with pytest.raises(FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError):
        compose_occupied_lane_mv2_dp_durable_cycle_v1(
            {"LANE_1": (pairs["LANE_1"][0], wrong)},
            **s7,
        )
