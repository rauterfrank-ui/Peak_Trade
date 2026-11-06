"""Synthetic deterministic fixtures for cross-sectional relative-strength v0 tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
)

_INSTRUMENTS = (
    "okx:linear_perpetual:ETH-USDT",
    "okx:linear_perpetual:SOL-USDT",
    "okx:linear_perpetual:AVAX-USDT",
    "okx:linear_perpetual:LINK-USDT",
    "okx:linear_perpetual:DOT-USDT",
)


def _hourly_timestamps(*, count: int, end: str) -> tuple[str, ...]:
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return tuple(
        (end_dt - timedelta(hours=count - 1 - offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for offset in range(count)
    )


def _closes_for_instrument(
    instrument_index: int,
    *,
    bar_count: int,
    end: str = "2024-06-01T01:00:00Z",
) -> tuple[float, ...]:
    """Deterministic monotonic closes with instrument-specific drift."""
    base = 100.0 + instrument_index * 10.0
    drift = 0.002 * (instrument_index + 1)
    return tuple(base * (1.0 + drift) ** i for i in range(bar_count))


def build_synthetic_panel_series_v0(
    *,
    bar_count: int = 30,
    end: str = "2024-06-01T01:00:00Z",
    instruments: tuple[str, ...] = _INSTRUMENTS,
) -> tuple[InstrumentPanelSeriesV1, ...]:
    timestamps = _hourly_timestamps(count=bar_count, end=end)
    series_list: list[InstrumentPanelSeriesV1] = []
    for idx, instrument_id in enumerate(instruments):
        closes = _closes_for_instrument(idx, bar_count=bar_count, end=end)
        bars = tuple(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=f"{closes[i]:.8f}",
                high=f"{closes[i] * 1.01:.8f}",
                low=f"{closes[i] * 0.99:.8f}",
                close=f"{closes[i]:.8f}",
                volume="1000",
                is_final=True,
            )
            for i, ts in enumerate(timestamps)
        )
        series = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=instrument_id.split(":")[-1],
            bars=bars,
            series_digest="",
        )
        digest = compute_series_digest(series)
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=series.instrument_id,
                native_instrument_id=series.native_instrument_id,
                bars=series.bars,
                series_digest=digest,
            )
        )
    return tuple(series_list)


def build_incomplete_panel_series_v0(
    *,
    bar_count: int = 30,
) -> tuple[InstrumentPanelSeriesV1, ...]:
    """Panel with one instrument having fewer bars (staleness/incomplete)."""
    full = build_synthetic_panel_series_v0(bar_count=bar_count)
    short_inst = full[0]
    short_bars = short_inst.bars[: bar_count - 3]
    short_series = InstrumentPanelSeriesV1(
        instrument_id=short_inst.instrument_id,
        native_instrument_id=short_inst.native_instrument_id,
        bars=short_bars,
        series_digest=compute_series_digest(
            InstrumentPanelSeriesV1(
                instrument_id=short_inst.instrument_id,
                native_instrument_id=short_inst.native_instrument_id,
                bars=short_bars,
                series_digest="",
            )
        ),
    )
    return (short_series,) + full[1:]


def build_bitcoin_contaminated_panel_v0(
    *,
    bar_count: int = 30,
) -> tuple[InstrumentPanelSeriesV1, ...]:
    instruments = _INSTRUMENTS[:4] + ("okx:linear_perpetual:BTC-USDT",)
    return build_synthetic_panel_series_v0(bar_count=bar_count, instruments=instruments)
