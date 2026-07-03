"""Synthetic fixtures for cross-sectional funding-rate delta momentum v0 binding tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1


def _bars(
    instrument_id: str,
    *,
    base_close: float,
    count: int = 30,
) -> tuple[PanelBarV1, ...]:
    bars: list[PanelBarV1] = []
    start = datetime(2024, 5, 30, 20, 0, tzinfo=timezone.utc)
    for idx in range(count):
        ts = (start + timedelta(hours=idx)).strftime("%Y-%m-%dT%H:%M:%SZ")
        close = base_close + idx * 0.01
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=str(close - 0.01),
                high=str(close + 0.02),
                low=str(close - 0.02),
                close=str(close),
                volume="1000",
                is_final=True,
            )
        )
    return tuple(bars)


def build_synthetic_ohlcv_panel_v0() -> tuple[InstrumentPanelSeriesV1, ...]:
    instruments = (
        ("okx:linear_perpetual:ETH:USDT:USDT:perp", 3000.0),
        ("okx:linear_perpetual:SOL:USDT:USDT:perp", 150.0),
        ("okx:linear_perpetual:AVAX:USDT:USDT:perp", 35.0),
        ("okx:linear_perpetual:LINK:USDT:USDT:perp", 15.0),
        ("okx:linear_perpetual:ADA:USDT:USDT:perp", 0.45),
    )
    series: list[InstrumentPanelSeriesV1] = []
    for instrument_id, base_close in instruments:
        bars = _bars(instrument_id, base_close=base_close)
        series.append(
            InstrumentPanelSeriesV1(
                instrument_id=instrument_id,
                native_instrument_id=instrument_id,
                bars=bars,
                series_digest="fixture",
            )
        )
    return tuple(series)


def build_funding_rates_for_panel_v0(
    panel: tuple[InstrumentPanelSeriesV1, ...],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for idx, series in enumerate(panel):
        rates: dict[str, str] = {}
        for bar_idx, bar in enumerate(series.bars):
            rates[bar.timestamp_utc] = str(-0.0001 + idx * 0.00005 + bar_idx * 0.000001)
        result[series.instrument_id] = rates
    return result
