"""RC-IMP-01 / RC-ORD-01 productive Natural Enter convergence repair contracts."""

from __future__ import annotations

from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    carry_occupied_lane_mv2_dp_decision_state_in_memory_v1,
    invoke_occupied_lane_mv2_dp_decision_state_consumer_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
    resolve_host_market_sample_venue_event_time_unix_v1,
    run_current_productive_master_v2_runtime_cycle_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    strong_uptrend_closes_v1,
)
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _lane_g17,
    _pair,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    _carry_kwargs,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _produced_g17_producer,
)


def test_resolve_host_market_sample_prefers_accepted_c1() -> None:
    assert (
        resolve_host_market_sample_venue_event_time_unix_v1(
            last_finalized_event_ts_unix=100.0,
            accepted_c1_venue_event_time_unix=200.0,
        )
        == 200.0
    )
    assert (
        resolve_host_market_sample_venue_event_time_unix_v1(
            last_finalized_event_ts_unix=100.0,
            accepted_c1_venue_event_time_unix=None,
        )
        == 100.0
    )


def test_mv2_host_c1_uses_accepted_c1_not_last_finalized_grid_anchor() -> None:
    bound = _bound()
    closes = strong_uptrend_closes_v1(count=8)
    grid_anchor = 1_700_000_000.0
    accepted_c1 = grid_anchor + 120.0
    mark = float(closes[-1])
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        provenance_for_bound_v1,
    )

    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="rc-imp-01-host-c1",
        observed_unix=accepted_c1 + 1.0,
        mark_px=mark,
        index_px=mark - 0.5,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=10.0,
        open_interest=20.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=grid_anchor,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        accepted_c1_venue_event_time_unix=accepted_c1,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound, mark_px=mark, index_px=mark - 0.5
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound
        ),
    )
    assert result.replay is not None
    assert result.outgoing_cursor is not None
    cap61 = result.outgoing_cursor.cap61_confirmation_state
    assert cap61 is not None
    ident = cap61.observation_acceptance_state.last_accepted_observation_identity
    assert ident is not None
    assert float(ident.venue_event_time) == accepted_c1
    assert float(ident.venue_event_time) != grid_anchor


def test_mv2_duplicate_does_not_advance_identity_on_accepted_c1() -> None:
    bound = _bound()
    closes = strong_uptrend_closes_v1(count=8)
    accepted_c1 = 1_700_000_200.0
    mark = float(closes[-1])
    from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
        provenance_for_bound_v1,
    )

    admission = non_productive_test_master_v2_reconciliation_admission_v1(bound=bound)
    prov = provenance_for_bound_v1(bound=bound, mark_px=mark, index_px=mark - 0.5)
    g17 = _produced_g17_producer(instrument_id=bound.instrument_id)
    kwargs = dict(
        bound_instrument=bound,
        observed_unix=accepted_c1 + 1.0,
        mark_px=mark,
        index_px=mark - 0.5,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=10.0,
        open_interest=20.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=accepted_c1 - 60.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        accepted_c1_venue_event_time_unix=accepted_c1,
        g17_typed_vol_producer=g17,
        canonical_price_provenance=prov,
        master_v2_reconciliation_admission=admission,
    )
    first = run_current_productive_master_v2_runtime_cycle_v1(cycle_id="rc-imp-dup-a", **kwargs)
    assert first.outgoing_cursor is not None
    epoch_before = (
        first.outgoing_cursor.cap61_confirmation_state.observation_acceptance_state.market_observation_epoch  # type: ignore[union-attr]
    )
    second = run_current_productive_master_v2_runtime_cycle_v1(
        cycle_id="rc-imp-dup-b",
        incoming_cursor=first.outgoing_cursor,
        accepted_c1_venue_event_time_unix=accepted_c1,
        **{k: v for k, v in kwargs.items() if k != "accepted_c1_venue_event_time_unix"},
    )
    assert second.outgoing_cursor is not None
    epoch_after = (
        second.outgoing_cursor.cap61_confirmation_state.observation_acceptance_state.market_observation_epoch  # type: ignore[union-attr]
    )
    assert epoch_after == epoch_before


def test_rc_ord_cursor_carry_advances_cap61_across_two_mv2_cycles(tmp_path: Path) -> None:
    pair = _pair(tmp_path, "LANE_1")
    prov = build_provenance_from_governed_synthetic_close_mark_and_index_v1(
        venue_native_id=str(pair[1].venue_native_id),
        mark_px=100.0,
        index_px=99.5,
    )
    g17 = {"LANE_1": _lane_g17({"LANE_1": pair})["LANE_1"]}
    base = {**_carry_kwargs(cycle_id_prefix="rc-ord-carry-1"), "g17_typed_vol_producers": g17}
    base["canonical_price_provenance"] = prov
    first_ts = 1_700_000_200.0
    second_ts = first_ts + 60.0
    first = invoke_occupied_lane_mv2_dp_decision_state_consumer_v1(
        {"LANE_1": pair},
        **base,
        accepted_c1_venue_event_time_unix=first_ts,
    )["LANE_1"]
    second = carry_occupied_lane_mv2_dp_decision_state_in_memory_v1(
        {"LANE_1": pair},
        {"LANE_1": first},
        **{**base, "cycle_id_prefix": "rc-ord-carry-2"},
        accepted_c1_venue_event_time_unix=second_ts,
    )["LANE_1"]
    assert second.incoming_cursor is not None
    assert first.cycle_result.outgoing_cursor is not None
    cap61_after = second.cycle_result.outgoing_cursor.cap61_confirmation_state
    assert cap61_after is not None
    epoch = cap61_after.observation_acceptance_state.market_observation_epoch.value
    assert epoch >= 1
