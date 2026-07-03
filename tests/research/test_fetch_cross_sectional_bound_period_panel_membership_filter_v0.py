"""Bounded tests for full-bound-calendar panel membership filtering before validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
)
from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    _canonicalize_swap_instrument,
    _filter_bars_to_period,
    _load_instruments_snapshot,
    _load_merged_rows_for_instrument,
    group_raw_paths_by_native_instrument_v1,
    normalize_okx_candles_to_panel_bars,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    PanelValidationErrorCode,
    build_bound_panel_calendar_timestamps_v1,
    filter_panel_series_to_full_bound_calendar_coverage_v1,
    has_full_bound_panel_calendar_coverage_v1,
    validate_panel_series_v1,
)

PARTIAL_RAW_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    ".tmp_historical_20260703T181515Z"
)
BINDING_PATH = Path(
    "config/research/cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0.json"
)


def _bar(instrument_id: str, timestamp_utc: str) -> PanelBarV1:
    return PanelBarV1(
        instrument_id=instrument_id,
        timestamp_utc=timestamp_utc,
        open="1",
        high="2",
        low="0.5",
        close="1.5",
        volume="100",
        is_final=True,
    )


def _series_for_timestamps(
    instrument_id: str,
    timestamps: tuple[str, ...],
) -> InstrumentPanelSeriesV1:
    return InstrumentPanelSeriesV1(
        instrument_id=instrument_id,
        native_instrument_id=f"{instrument_id.split(':')[2]}-USDT-SWAP",
        bars=tuple(_bar(instrument_id, ts) for ts in timestamps),
        series_digest="0" * 64,
    )


def _full_calendar_series(base: str) -> InstrumentPanelSeriesV1:
    timestamps = build_bound_panel_calendar_timestamps_v1(
        PANEL_CALENDAR_START_UTC,
        PANEL_CALENDAR_END_UTC,
    )
    return _series_for_timestamps(f"okx:linear_perpetual:{base}:USDT:USDT:perp", timestamps)


def _partial_calendar_series(base: str, *, start_offset_hours: int) -> InstrumentPanelSeriesV1:
    full = build_bound_panel_calendar_timestamps_v1(
        PANEL_CALENDAR_START_UTC,
        PANEL_CALENDAR_END_UTC,
    )
    return _series_for_timestamps(
        f"okx:linear_perpetual:{base}:USDT:USDT:perp",
        full[start_offset_hours:],
    )


class TestBoundPanelCalendarTimestamps:
    def test_extended_chronological_calendar_has_2953_rows(self) -> None:
        timestamps = build_bound_panel_calendar_timestamps_v1(
            PANEL_CALENDAR_START_UTC,
            PANEL_CALENDAR_END_UTC,
        )
        assert len(timestamps) == 2953
        assert timestamps[0] == "2024-05-01T00:00:00Z"
        assert timestamps[-1] == "2024-09-01T00:00:00Z"


class TestFullBoundCalendarMembershipFilter:
    def test_partial_history_instruments_excluded(self) -> None:
        candidates = (
            _full_calendar_series("ETH"),
            _partial_calendar_series("POPCAT", start_offset_hours=2889),
        )
        result = filter_panel_series_to_full_bound_calendar_coverage_v1(
            candidates,
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        assert len(result.selected) == 1
        assert result.excluded_partial_count == 1
        assert "POPCAT" not in result.selected[0].instrument_id

    def test_null_row_instruments_excluded(self) -> None:
        empty = InstrumentPanelSeriesV1(
            instrument_id="okx:linear_perpetual:EMPTY:USDT:USDT:perp",
            native_instrument_id="EMPTY-USDT-SWAP",
            bars=(),
            series_digest="0" * 64,
        )
        result = filter_panel_series_to_full_bound_calendar_coverage_v1(
            (empty, _full_calendar_series("SOL")),
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        assert len(result.selected) == 1
        assert result.excluded_empty_count == 1

    def test_full_period_instruments_remain(self) -> None:
        candidates = tuple(
            _full_calendar_series(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK")
        )
        result = filter_panel_series_to_full_bound_calendar_coverage_v1(
            candidates,
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        assert len(result.selected) == 5
        assert result.excluded_partial_count == 0
        assert result.excluded_empty_count == 0

    def test_minimum_eligible_member_count_fail_closed(self) -> None:
        candidates = (_full_calendar_series("ETH"),)
        result = filter_panel_series_to_full_bound_calendar_coverage_v1(
            candidates,
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        assert len(result.selected) == 1
        validation = validate_panel_series_v1(result.selected, min_instruments=5)
        assert not validation.valid
        assert PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value in validation.error_codes

    def test_no_period_shortening_to_feasible_intersection(self) -> None:
        selected = filter_panel_series_to_full_bound_calendar_coverage_v1(
            (
                _full_calendar_series("ETH"),
                _partial_calendar_series("BOME", start_offset_hours=2554),
            ),
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        ).selected
        expected = build_bound_panel_calendar_timestamps_v1(
            PANEL_CALENDAR_START_UTC,
            PANEL_CALENDAR_END_UTC,
        )
        assert [bar.timestamp_utc for bar in selected[0].bars] == list(expected)
        assert selected[0].bars[0].timestamp_utc == PANEL_CALENDAR_START_UTC
        assert selected[0].bars[-1].timestamp_utc == PANEL_CALENDAR_END_UTC


class TestPanelValidationStrictness:
    def test_unfiltered_mixed_panel_reproduces_alignment_mismatch(self) -> None:
        mixed = (
            _full_calendar_series("1INCH"),
            _partial_calendar_series("POPCAT", start_offset_hours=2889),
        )
        result = validate_panel_series_v1(mixed, min_instruments=2)
        assert not result.valid
        assert PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value in result.error_codes

    def test_filtered_full_coverage_panel_passes_validation(self) -> None:
        candidates = tuple(
            _full_calendar_series(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK")
        )
        filtered = filter_panel_series_to_full_bound_calendar_coverage_v1(
            candidates,
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        ).selected
        result = validate_panel_series_v1(filtered, min_instruments=5)
        assert result.valid
        assert result.panel_alignment_check == "PASS"

    def test_validator_remains_strict_if_partial_slips_through(self) -> None:
        mixed = (
            _full_calendar_series("1INCH"),
            _partial_calendar_series("RENDER", start_offset_hours=2384),
        )
        assert not has_full_bound_panel_calendar_coverage_v1(
            mixed[1].bars,
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        result = validate_panel_series_v1(mixed, min_instruments=2)
        assert PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value in result.error_codes


class TestBindingImmutability:
    def test_versioned_binding_digests_unchanged(self) -> None:
        payload = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        assert payload["binding"]["digest_bindings"]["config_digest"]["value"] == (
            "b6f3890379bec953ef8930d64ea50fd262b80d8b9067628c90c3d2da59913f3b"
        )
        assert payload["binding"]["digest_bindings"]["data_digest"]["value"] == (
            "fe2cb0975f73a4c115ce14d230e74869155afeaaff973c22dbb89175bfa5137f"
        )
        assert (
            payload["panel_dataset_binding"]["panel_calendar_start_utc"] == PANEL_CALENDAR_START_UTC
        )
        assert payload["panel_dataset_binding"]["panel_calendar_end_utc"] == PANEL_CALENDAR_END_UTC


@pytest.mark.skipif(not PARTIAL_RAW_ROOT.is_dir(), reason="partial raw staging unavailable")
class TestPartialRawReuseProbe:
    def test_partial_raw_full_coverage_filter_yields_panel_validation_pass(self) -> None:
        raw_dir = PARTIAL_RAW_ROOT / "raw"
        instruments = _load_instruments_snapshot(raw_dir)
        native_to_canonical = {}
        for inst in instruments:
            pair = _canonicalize_swap_instrument(inst)
            if pair is not None:
                native_to_canonical[pair[1]] = pair[0]

        candidates: list[InstrumentPanelSeriesV1] = []
        for native_id, raw_paths in group_raw_paths_by_native_instrument_v1(raw_dir).items():
            instrument_id = native_to_canonical.get(native_id)
            if instrument_id is None:
                continue
            merged_rows, merge_error = _load_merged_rows_for_instrument(raw_paths)
            assert merge_error is None
            if not merged_rows:
                continue
            all_bars = normalize_okx_candles_to_panel_bars(instrument_id, merged_rows)
            bound_bars = _filter_bars_to_period(
                all_bars,
                period_start_utc=PANEL_CALENDAR_START_UTC,
                period_end_utc=PANEL_CALENDAR_END_UTC,
            )
            if not bound_bars:
                continue
            candidates.append(
                InstrumentPanelSeriesV1(
                    instrument_id=instrument_id,
                    native_instrument_id=native_id,
                    bars=bound_bars,
                    series_digest="0" * 64,
                )
            )

        filtered = filter_panel_series_to_full_bound_calendar_coverage_v1(
            tuple(candidates),
            period_start_utc=PANEL_CALENDAR_START_UTC,
            period_end_utc=PANEL_CALENDAR_END_UTC,
        )
        assert len(filtered.selected) >= 5
        assert filtered.excluded_partial_count >= 1
        validation = validate_panel_series_v1(filtered.selected, min_instruments=5)
        assert validation.valid
        assert validation.panel_alignment_check == "PASS"
