"""Regression: declarative baseline EOI/EOP pairing (shared productive evaluator).

No development evaluation execution. Treatment strategy-emitted path untouched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backtest.engine import (
    _compute_directional_gross_pnl_v0,
    _compute_roundtrip_fee_slippage_components_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.constants_v1 import (
    FEE_BPS_PER_SIDE,
    SLIPPAGE_BPS_PER_SIDE,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.panel_wiring_v1 import (
    ArmEventSeriesV1,
)
from src.research.volatility_compression_breakout_v1_development_evaluation_v1.productive_exit_pnl_evaluator_v1 import (
    build_effective_cost_config_from_binding_v1,
    simulate_arm_roundtrips_v1,
)
from src.research.volatility_compression_breakout_v1_strategy_v1 import (
    EXIT_PARAMS_DECLARATIVE_V1,
    SIGNAL_LAG_BARS_V1,
)

REPO = Path(__file__).resolve().parents[2]


def _cost_binding() -> dict:
    return {
        "binding_version": "v1",
        "implicit_zero_cost_forbidden": True,
        "fee_model_binding": {
            "fee_bps_per_side": FEE_BPS_PER_SIDE,
            "fee_model_version": "backtest_fee_taker_symmetric_v0",
        },
        "slippage_model_binding": {
            "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
            "slippage_model_version": "backtest_slippage_symmetric_v0",
        },
        "spread_model_binding": {
            "conservative_half_spread_bps": 5.0,
            "spread_model_version": "research_conservative_bps_v1",
        },
    }


def _late_entry_geometry(*, side: str) -> tuple[InstrumentPanelSeriesV1, ArmEventSeriesV1, int]:
    """AGLD-like geometry from forensic fixture: TIME_EXIT unreachable → EOI pairs."""
    import pandas as pd

    max_bars = int(EXIT_PARAMS_DECLARATIVE_V1["time_exit_max_bars"])
    lag = int(SIGNAL_LAG_BARS_V1)
    warmup = 160
    post_fill = 9
    entry_i = warmup
    fill_i = entry_i + lag
    n = fill_i + 1 + post_fill
    assert fill_i + max_bars >= n

    bars: list[PanelBarV1] = []
    start = pd.Timestamp("2023-01-01T00:00:00Z")
    for i in range(n):
        base = 0.58
        # Exact forensic AGLD flat/calm geometry (identical closes → identical regime rank).
        px = base - 0.0001 * max(0, i - fill_i)
        ts = (start + pd.Timedelta(hours=i)).isoformat().replace("+00:00", "Z")
        bars.append(
            PanelBarV1(
                instrument_id="INST_EOS",
                timestamp_utc=ts,
                open=f"{px:.6f}",
                high=f"{px + 0.001:.6f}",
                low=f"{px - 0.001:.6f}",
                close=f"{px:.6f}",
                volume="1",
                is_final=True,
            )
        )
    series = InstrumentPanelSeriesV1(
        instrument_id="INST_EOS",
        native_instrument_id="INST_EOS",
        bars=tuple(bars),
        series_digest="eos_geometry_v1",
    )
    mask = tuple(i == entry_i for i in range(n))
    sides = tuple(side if i == entry_i else "NONE" for i in range(n))
    arm = ArmEventSeriesV1(
        arm_id="BASELINE",
        instrument_id="INST_EOS",
        timestamps_utc=tuple(b.timestamp_utc for b in series.bars),
        entry_sides=sides,
        entry_event_mask=mask,
    )
    return series, arm, entry_i


def _calm_series(
    *,
    instrument_id: str,
    n: int,
    start: float = 100.0,
    drift: float = 0.0,
) -> InstrumentPanelSeriesV1:
    import pandas as pd

    bars: list[PanelBarV1] = []
    px = start
    t0 = pd.Timestamp("2023-01-01T00:00:00Z")
    for i in range(n):
        o = px
        c = px + drift
        h = max(o, c) + 0.01
        lo = min(o, c) - 0.01
        ts = (t0 + pd.Timedelta(hours=i)).isoformat().replace("+00:00", "Z")
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=f"{o:.6f}",
                high=f"{h:.6f}",
                low=f"{lo:.6f}",
                close=f"{c:.6f}",
                volume="1",
                is_final=True,
            )
        )
        px = c
    return InstrumentPanelSeriesV1(
        instrument_id=instrument_id,
        native_instrument_id=instrument_id,
        bars=tuple(bars),
        series_digest=f"eos_{instrument_id}",
    )


def test_open_long_at_panel_end_pairs_via_eoi() -> None:
    series, arm, entry_i = _late_entry_geometry(side="LONG")
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    trades = simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)
    assert len(trades) == 1
    tr = trades[0]
    assert tr.side == "long"
    assert tr.exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert tr.exit_index == len(series.bars) - 1
    assert tr.entry_index == entry_i + int(SIGNAL_LAG_BARS_V1)
    assert tr.exit_time == series.bars[-1].timestamp_utc


def test_open_short_at_panel_end_pairs_via_eoi() -> None:
    series, arm, entry_i = _late_entry_geometry(side="SHORT")
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    trades = simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)
    assert len(trades) == 1
    tr = trades[0]
    assert tr.side == "short"
    assert tr.exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert tr.exit_index == len(series.bars) - 1
    assert tr.entry_index == entry_i + int(SIGNAL_LAG_BARS_V1)


def test_multi_instrument_end_of_series_pairing() -> None:
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    series_a, arm_a, _ = _late_entry_geometry(side="LONG")
    series_b, arm_b, _ = _late_entry_geometry(side="SHORT")
    # Distinct instrument ids.
    series_b = InstrumentPanelSeriesV1(
        instrument_id="INST_EOS_B",
        native_instrument_id="INST_EOS_B",
        bars=tuple(
            PanelBarV1(
                instrument_id="INST_EOS_B",
                timestamp_utc=b.timestamp_utc,
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
                is_final=b.is_final,
            )
            for b in series_b.bars
        ),
        series_digest="eos_b",
    )
    arm_b = ArmEventSeriesV1(
        arm_id="BASELINE",
        instrument_id="INST_EOS_B",
        timestamps_utc=arm_b.timestamps_utc,
        entry_sides=arm_b.entry_sides,
        entry_event_mask=arm_b.entry_event_mask,
    )
    trades_a = simulate_arm_roundtrips_v1(panel_series=(series_a,), arm=arm_a, effective_cost=cost)
    trades_b = simulate_arm_roundtrips_v1(panel_series=(series_b,), arm=arm_b, effective_cost=cost)
    assert len(trades_a) == 1 and len(trades_b) == 1
    assert trades_a[0].exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert trades_b[0].exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert trades_a[0].instrument_id == "INST_EOS"
    assert trades_b[0].instrument_id == "INST_EOS_B"


def test_no_double_exits_and_deterministic_fees_slippage_timestamps() -> None:
    series, arm, _ = _late_entry_geometry(side="LONG")
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    t1 = simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)
    t2 = simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)
    assert len(t1) == 1 and len(t2) == 1
    a, b = t1[0], t2[0]
    assert a.exit_index == b.exit_index
    assert a.exit_time == b.exit_time
    assert a.exit_reason == b.exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"
    assert a.entry_fee == pytest.approx(b.entry_fee)
    assert a.exit_fee == pytest.approx(b.exit_fee)
    assert a.entry_slippage == pytest.approx(b.entry_slippage)
    assert a.exit_slippage == pytest.approx(b.exit_slippage)
    assert a.pnl == pytest.approx(b.pnl)
    # Single roundtrip → exactly one exit realization via canonical primitives.
    gross = _compute_directional_gross_pnl_v0(
        size=a.size, entry_price=a.entry_price, exit_price=a.exit_price, side="long"
    )
    fees = _compute_roundtrip_fee_slippage_components_v0(
        size=a.size,
        entry_price=a.entry_price,
        exit_price=a.exit_price,
        effective_cost=cost,
    )
    assert a.gross_pnl == pytest.approx(gross)
    assert a.entry_fee == pytest.approx(fees[0])
    assert a.exit_fee == pytest.approx(fees[1])
    assert a.entry_slippage == pytest.approx(fees[2])
    assert a.exit_slippage == pytest.approx(fees[3])


def test_eop_wins_only_when_ranked_after_eoi_on_shared_last_bar() -> None:
    """On last instrument=panel bar, EOI precedes EOP (canonical ascending wins-first)."""
    series, arm, _ = _late_entry_geometry(side="LONG")
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    n = len(series.bars)
    mask = [False] * n
    mask[-1] = True  # panel-last coincides with instrument-last
    trades = simulate_arm_roundtrips_v1(
        panel_series=(series,),
        arm=arm,
        effective_cost=cost,
        is_panel_last_bar_mask=mask,
    )
    assert len(trades) == 1
    assert trades[0].exit_reason == "END_OF_INSTRUMENT_LIQUIDATION"


def test_same_bar_fill_on_final_bar_still_unpairable() -> None:
    series = _calm_series(instrument_id="INST_X", n=180)
    n = len(series.bars)
    # Entry on last bar → fill would need next bar; no fill bar.
    arm = ArmEventSeriesV1(
        arm_id="B",
        instrument_id="INST_X",
        timestamps_utc=tuple(b.timestamp_utc for b in series.bars),
        entry_sides=tuple("LONG" if i == n - 1 else "NONE" for i in range(n)),
        entry_event_mask=tuple(i == n - 1 for i in range(n)),
    )
    cost = build_effective_cost_config_from_binding_v1(_cost_binding())
    with pytest.raises(ValueError, match="UNPAIRABLE_ENTRY_NO_FILL_BAR"):
        simulate_arm_roundtrips_v1(panel_series=(series,), arm=arm, effective_cost=cost)
