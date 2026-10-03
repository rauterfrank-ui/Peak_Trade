"""Regression: LIVE-29P join uses Layer-C adverse exit distance (not fixed 80)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    resolve_current_productive_live_29p_adverse_exit_distance_v1,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)


def test_layer_c_distance_differs_from_canonical_fixed_80_on_productive_enter_replay() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    assert cycle_b.replay is not None
    distance, reasons = resolve_current_productive_live_29p_adverse_exit_distance_v1(cycle_b.replay)
    assert reasons == ()
    assert distance is not None
    assert float(distance) != float(CANONICAL_ADVERSE_EXIT_DISTANCE)
    assert float(distance) > 0.0


def test_low_mark_canonical_80_fail_closed_layer_c_derives_valid_stop() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    assert cycle_b.replay is not None
    replay = cycle_b.replay
    mc = replay.intermediate.market_context
    low_mark = replace(mc, mark_price=0.18)
    low_replay = replace(
        replay,
        intermediate=replace(replay.intermediate, market_context=low_mark),
    )
    assert (
        derive_protective_stop_price_from_adverse_exit_v0(
            selected_side="long",
            reference_price=Decimal("0.18"),
            adverse_exit_distance=Decimal(str(CANONICAL_ADVERSE_EXIT_DISTANCE)),
        )
        is None
    )
    distance, reasons = resolve_current_productive_live_29p_adverse_exit_distance_v1(low_replay)
    assert reasons == ()
    assert distance is not None
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side="long",
        reference_price=Decimal("0.18"),
        adverse_exit_distance=Decimal(str(distance)),
    )
    assert stop is not None
    assert stop > Decimal("0")
    assert stop < Decimal("0.18")


def test_missing_market_context_fail_closed() -> None:
    distance, reasons = resolve_current_productive_live_29p_adverse_exit_distance_v1(None)
    assert distance is None
    assert "replay_intermediate_missing" in reasons
