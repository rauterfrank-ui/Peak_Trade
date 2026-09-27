"""Chart update contract tests for Landscape V3."""

from __future__ import annotations

from src.webui.market_dashboard_landscape_v3.candle_chart_v1 import LandscapeV3ChartStateV1


def test_open_candle_revision_without_recreate() -> None:
    chart = LandscapeV3ChartStateV1("ETH-USDT-SWAP")
    chart.bootstrap_from_finalized_rows(
        [{"interval_start_ms": 1_000_000, "mark_px": "100", "confirm": "1"}]
    )
    ev1 = chart.apply_live_mark({"interval_start_ms": 1_060_000, "mark_px": "101", "confirm": "0"})
    assert ev1[-1]["chart_event"] == "open_candle"
    ev2 = chart.apply_live_mark({"interval_start_ms": 1_060_000, "mark_px": "102", "confirm": "0"})
    assert ev2[-1]["chart_event"] == "revise_open_candle"
    assert len(chart.candles) == 2


def test_finalize_and_append_without_duplicate_ts() -> None:
    chart = LandscapeV3ChartStateV1("ETH-USDT-SWAP")
    chart.bootstrap_from_finalized_rows([])
    chart.apply_live_mark({"interval_start_ms": 1_060_000, "mark_px": "101", "confirm": "0"})
    chart.apply_live_mark({"interval_start_ms": 1_060_000, "mark_px": "101.5", "confirm": "1"})
    chart.apply_live_mark({"interval_start_ms": 1_120_000, "mark_px": "102", "confirm": "0"})
    ts_set = [c.interval_start_ms for c in chart.candles]
    assert len(ts_set) == len(set(ts_set))


def test_instrument_reset_clears_state() -> None:
    chart = LandscapeV3ChartStateV1("ETH-USDT-SWAP")
    chart.bootstrap_from_finalized_rows(
        [{"interval_start_ms": 1_000_000, "mark_px": "1", "confirm": "1"}]
    )
    chart.reset_for_instrument("BTC-USDT-SWAP")
    assert chart.venue_native_id == "BTC-USDT-SWAP"
    assert chart.candles == []
