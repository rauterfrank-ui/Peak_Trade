"""INIT_ROOT_01: Cold-S7 layered init uses finalized close grid (not static CMC pair)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    bootstrap_s8_lane_via_s7_compose_v1,
    build_s8_occupied_lane_pairs_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1 import (
    productive_cycle_bind_seam_v1 as seam_mod,
)
from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_bind_seam_v1 import (
    _layered_core_initialization_observations_v1,
    ensure_productive_layered_core_episode_store_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
    strong_uptrend_closes_v1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    observation_mark_payloads_for_bound_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _lane_g17,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    ORIGIN_SHA,
    _bound_lane_1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationClassification,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.double_play_old_effective_host_contract_v1 import (
    layered_core_cmc_mark_observation_init_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import DEFAULT_VENUE


def test_wp3_flag_on_init_observations_use_full_close_grid_not_static_cmc() -> None:
    assert layered_core_cmc_mark_observation_init_v1() is True
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id="INST",
        venue_instrument_id="INST-VENUE",
    )
    closes = (100.0, 101.0, 102.5)
    ts = 1_700_000_120.0
    obs = _layered_core_initialization_observations_v1(
        instrument_key=key,
        finalized_closes=closes,
        last_finalized_event_ts_unix=ts,
    )
    assert len(obs) == 3
    assert [o.mark_price for o in obs] == list(closes)
    assert obs[-1].venue_event_time == ts
    assert obs[0].venue_event_time == ts - 120.0


def test_init_observations_distinct_on_uptrend_grid() -> None:
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id="INST",
        venue_instrument_id="INST-VENUE",
    )
    closes = tuple(float(x) for x in strong_uptrend_closes_v1()[:5])
    ts = governed_productive_c1_event_ts_unix_v1()
    obs = _layered_core_initialization_observations_v1(
        instrument_key=key,
        finalized_closes=closes,
        last_finalized_event_ts_unix=float(ts),
    )
    state = initial_observation_acceptance_state_v1(bound_instrument_key=key)
    classifications = []
    for candidate in obs:
        result = evaluate_distinct_market_observation_v1(state, candidate)
        classifications.append(result.classification)
        state = result.state_after
    assert ObservationClassification.DISTINCT in classifications
    assert classifications.count(ObservationClassification.DUPLICATE) >= 0


def test_cold_s7_compose_bootstrap_no_initialization_incomplete_with_wp3_flag(
    tmp_path: Path,
) -> None:
    assert layered_core_cmc_mark_observation_init_v1() is True
    bound = _bound_lane_1()
    path = strong_uptrend_closes_v1()
    last_ts = governed_productive_c1_event_ts_unix_v1(offset_seconds=180.0)
    closes = tuple(float(x) for x in path[:20])
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=closes,
        last_event_ts_unix=last_ts,
    )
    mark_payload, index_payload = observation_mark_payloads_for_bound_v1(
        bound=bound,
        mark_px=float(closes[-1]),
    )
    lane = tmp_path / "cold_s7"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane, bound=bound)
    g17 = _lane_g17(pairs)
    bootstrap_s8_lane_via_s7_compose_v1(
        composed_pairs=pairs,
        origin_main_sha=ORIGIN_SHA,
        g17_producers=g17,
        candles_payload=candles,
        mark_price_payload=mark_payload,
        venue_native_id=str(bound.venue_native_id),
        index_tickers_payload=index_payload,
    )
    store = Path(pairs["LANE_1"][0].lane_state_root)
    restore_episode_from_store_v1(store, expected_instrument_id=str(bound.instrument_id))


def test_ensure_productive_uses_close_grid_when_wp3_flag_on(tmp_path: Path) -> None:
    assert layered_core_cmc_mark_observation_init_v1() is True
    captured: list[tuple[float, ...]] = []

    def _spy(*, instrument_key, finalized_closes, last_finalized_event_ts_unix):  # type: ignore[no-untyped-def]
        captured.append(tuple(float(c) for c in finalized_closes))
        return seam_mod._layered_core_initialization_observations_v1(
            instrument_key=instrument_key,
            finalized_closes=finalized_closes,
            last_finalized_event_ts_unix=last_finalized_event_ts_unix,
        )

    orig = seam_mod._layered_core_initialization_observations_v1
    seam_mod._layered_core_initialization_observations_v1 = _spy  # type: ignore[assignment]
    try:
        from src.ops.p5_10_productive_activation_and_binding_v1.productive_cycle_layered_core_bind_wiring_v1 import (
            incoming_cursor_has_existing_scope_carrier_v1,
        )
        from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

        bound = _bound_lane_1()
        closes = (1.0, 1.1)
        if not incoming_cursor_has_existing_scope_carrier_v1({"existing_scope": object()}):
            pytest.skip("scope carrier helper unavailable")
        failures = ensure_productive_layered_core_episode_store_v1(
            store_root=tmp_path,
            bound_instrument=bound,
            mark_price_m_t=1.2,
            finalized_closes=closes,
            last_finalized_event_ts_unix=1_700_000_000.0,
            outgoing_cursor={"existing_scope": object()},
        )
        assert captured == [closes]
        assert not any("INITIALIZATION_INCOMPLETE" in f for f in failures)
    finally:
        seam_mod._layered_core_initialization_observations_v1 = orig  # type: ignore[assignment]
