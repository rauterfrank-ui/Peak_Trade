"""Contract tests for pit_okx_pt1h_panel_ohlcv_dataset_v1."""

from __future__ import annotations

import pytest

from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    InstrumentPanelSeriesV1,
    PanelBarV1,
    PanelValidationErrorCode,
    build_panel_dataset_manifest_v1,
    compute_panel_digest,
    validate_panel_series_v1,
)


def _bar(
    instrument_id: str,
    hour: int,
    *,
    open_: str = "100",
    high: str = "101",
    low: str = "99",
    close: str = "100.5",
    volume: str = "1000",
) -> PanelBarV1:
    return PanelBarV1(
        instrument_id=instrument_id,
        timestamp_utc=f"2026-06-01T{hour:02d}:00:00Z",
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_final=True,
    )


def _series(inst: str, hours: range) -> InstrumentPanelSeriesV1:
    bars = tuple(_bar(inst, hour) for hour in hours)
    return InstrumentPanelSeriesV1(
        instrument_id=inst,
        native_instrument_id=f"{inst.split(':')[2]}-USDT-SWAP",
        bars=bars,
        series_digest="0" * 64,
    )


class TestPanelValidation:
    def test_valid_multi_instrument_panel_passes(self) -> None:
        hours = range(0, 6)
        series = [
            _series(f"okx:linear_perpetual:{base}:USDT:USDT:perp", hours)
            for base in ("ETH", "SOL", "ADA", "DOT", "LINK")
        ]
        result = validate_panel_series_v1(series, min_instruments=5)
        assert result.valid
        assert result.duplicate_check == "PASS"
        assert result.gap_check == "PASS"
        assert result.out_of_order_check == "PASS"

    def test_duplicate_timestamp_fails(self) -> None:
        inst = "okx:linear_perpetual:ETH:USDT:USDT:perp"
        bars = (_bar(inst, 1), _bar(inst, 1))
        series = [
            InstrumentPanelSeriesV1(
                instrument_id=inst,
                native_instrument_id="ETH-USDT-SWAP",
                bars=bars,
                series_digest="0" * 64,
            )
        ]
        result = validate_panel_series_v1(series, min_instruments=1)
        assert not result.valid
        assert PanelValidationErrorCode.DUPLICATE_TIMESTAMP.value in result.error_codes

    def test_bitcoin_instrument_fails(self) -> None:
        series = [_series("okx:linear_perpetual:BTC:USDT:USDT:perp", range(3))]
        result = validate_panel_series_v1(series, min_instruments=1)
        assert PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value in result.error_codes

    def test_gap_detection_fails(self) -> None:
        inst = "okx:linear_perpetual:ETH:USDT:USDT:perp"
        bars = (_bar(inst, 1), _bar(inst, 3))
        series = [
            InstrumentPanelSeriesV1(
                instrument_id=inst,
                native_instrument_id="ETH-USDT-SWAP",
                bars=bars,
                series_digest="0" * 64,
            )
        ]
        result = validate_panel_series_v1(series, min_instruments=1)
        assert PanelValidationErrorCode.GAP_DETECTED.value in result.error_codes

    def test_manifest_digest_is_deterministic(self) -> None:
        hours = range(0, 3)
        series = [
            _series(f"okx:linear_perpetual:{base}:USDT:USDT:perp", hours)
            for base in ("ETH", "SOL", "ADA", "DOT", "LINK")
        ]
        manifest = build_panel_dataset_manifest_v1(
            series_list=series,
            lifecycle_registry_ref="pit_futures_lifecycle_registry_v1:test:sha256:" + ("a" * 64),
            lifecycle_registry_digest="a" * 64,
            period_start_utc="2026-06-01T00:00:00Z",
            period_end_utc="2026-06-01T02:00:00Z",
            config_digest="b" * 64,
            source_provenance_digest="c" * 64,
        )
        assert manifest.bar_granularity == BAR_GRANULARITY
        assert compute_panel_digest(series) == manifest.normalized_panel_digest
