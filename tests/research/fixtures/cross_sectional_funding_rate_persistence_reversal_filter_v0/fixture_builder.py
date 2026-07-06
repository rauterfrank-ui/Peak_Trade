"""Synthetic fixtures for cross-sectional funding-rate persistence reversal filter v0 infrastructure tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1, PanelBarV1

PANEL_CALENDAR_START_UTC = datetime(2024, 5, 1, 0, 0, tzinfo=timezone.utc)
PANEL_CALENDAR_END_UTC = datetime(2024, 9, 1, 0, 0, tzinfo=timezone.utc)


def _bars(
    instrument_id: str,
    *,
    base_close: float,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[PanelBarV1, ...]:
    bars: list[PanelBarV1] = []
    cursor = start or PANEL_CALENDAR_START_UTC
    stop = end or PANEL_CALENDAR_END_UTC
    idx = 0
    while cursor < stop:
        ts = cursor.strftime("%Y-%m-%dT%H:%M:%SZ")
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
        cursor += timedelta(hours=1)
        idx += 1
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
