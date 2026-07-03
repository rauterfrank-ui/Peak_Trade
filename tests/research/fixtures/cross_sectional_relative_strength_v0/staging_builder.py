"""Staging helpers for cross-sectional relative-strength v0 contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    compute_series_digest,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)


def write_bound_period_staging_v0(
    staging_root: Path,
    *,
    panel_series: tuple[InstrumentPanelSeriesV1, ...] | None = None,
) -> Path:
    """Write panel staging layout matching bound 2024 period fixture semantics."""
    series = panel_series or build_synthetic_panel_series_v0()
    panel_dir = staging_root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for item in series:
        for bar in item.bars:
            rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "is_final": bar.is_final,
                }
            )

    instrument_ids = [s.instrument_id for s in series]
    manifest = {
        "panel_id": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
        "dataset_version": "v1",
        "bar_granularity": "PT1H",
        "instrument_ids": instrument_ids,
        "native_instrument_ids": [s.native_instrument_id for s in series],
        "manifest_digest": "0" * 64,
    }
    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return staging_root


def write_foreign_2026_staging_v0(staging_root: Path) -> Path:
    """Write staging with foreign 2026 timestamps for rejection tests."""
    from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import PanelBarV1

    instruments = (
        "okx:linear_perpetual:ETH-USDT",
        "okx:linear_perpetual:SOL-USDT",
        "okx:linear_perpetual:AVAX-USDT",
        "okx:linear_perpetual:LINK-USDT",
        "okx:linear_perpetual:DOT-USDT",
    )
    timestamps = [f"2026-07-02T{hour:02d}:00:00Z" for hour in range(12, 15)]
    series_list: list[InstrumentPanelSeriesV1] = []
    for idx, instrument_id in enumerate(instruments):
        bars = tuple(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open="100",
                high="101",
                low="99",
                close=str(100 + idx),
                volume="1000",
                is_final=True,
            )
            for ts in timestamps
        )
        interim = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=instrument_id.split(":")[-1],
            bars=bars,
            series_digest="",
        )
        series_list.append(
            InstrumentPanelSeriesV1(
                instrument_id=interim.instrument_id,
                native_instrument_id=interim.native_instrument_id,
                bars=interim.bars,
                series_digest=compute_series_digest(interim),
            )
        )
    return write_bound_period_staging_v0(staging_root, panel_series=tuple(series_list))
