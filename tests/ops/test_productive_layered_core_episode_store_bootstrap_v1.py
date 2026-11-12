"""S7 scope-colocated layered-core episode bootstrap (no duplicate mechanical step)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    FullAutonomyOccupiedLaneMv2DpDecisionStateAddressingJoinError,
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
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
    _observation_from_closes,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)


def test_sequential_cold_s7_compose_bootstrap_no_join_error(tmp_path: Path) -> None:
    """Regression: repeated cold S7 compose must not intermittently fail at episode bootstrap."""
    bound = _bound_lane_1()
    closes = strong_uptrend_closes_v1()
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=180.0)

    for i in range(10):
        lane = tmp_path / f"lane_{i}"
        pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane, bound=bound)
        observation = _observation_from_closes(closes=closes, event_ts=last_ts, bound=bound)
        assert observation.mark_price_payload is not None
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=ORIGIN_SHA,
            g17_producers=_lane_g17(pairs),
            candles_payload=observation.candles_payload,
            mark_price_payload=observation.mark_price_payload,
            venue_native_id=str(bound.venue_native_id),
            index_tickers_payload=observation.index_tickers_payload,
            mark_acquired_at_utc=observation.mark_acquired_at_utc,
        )
        store = Path(pairs["LANE_1"][0].lane_state_root)
        assert (store / CURSOR_FILENAME).is_file()
        restore_episode_from_store_v1(store, expected_instrument_id=str(bound.instrument_id))


def test_compose_with_misaligned_two_close_bootstrap_still_persists(tmp_path: Path) -> None:
    """Volatile last-two closes must not fail S7 compose when scope is on outgoing cursor."""
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    # Sharp last-bar move: old two-close + mechanical replay step was brittle here.
    closes = strong_uptrend_closes_v1()
    volatile = closes[:-2] + (closes[-2] * 0.85, closes[-1] * 1.12)
    native_id = str(pairs["LANE_1"][1].venue_native_id)
    market = _market_kwargs(
        cycle_id_prefix="volatile-two-close", last_ts=last_ts, venue_native_id=native_id
    )
    mark = volatile[-1]
    index = mark * 0.995
    market["finalized_closes"] = volatile
    market["mark_px"] = mark
    market["index_px"] = index
    market["bid_px"] = mark - 0.5
    market["ask_px"] = mark + 0.5
    market["canonical_price_provenance"] = (
        build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=native_id, mark_px=mark, index_px=index
        )
    )
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
