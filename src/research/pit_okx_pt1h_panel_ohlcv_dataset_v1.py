"""PT1H multi-instrument OKX panel OHLCV dataset v1 — pure validation and manifest core.

Research-only, non-authorizing. No network, no I/O, no runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.pit_futures_universe_manifest_v1 import (
    compute_sha256_digest,
    is_valid_rfc3339_utc,
)

PACKAGE_MARKER = "PIT_OKX_PT1H_PANEL_OHLCV_DATASET_V1=true"
MANIFEST_VERSION = "pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1"
PANEL_DATASET_VERSION = "v1"
BAR_GRANULARITY = "PT1H"
OKX_BAR_PARAM = "1H"
BAR_GRANULARITY_SECONDS = 3600
PANEL_ID = "pit_okx_linear_usdt_non_bitcoin_pt1h_panel"
PANEL_ALIGNMENT_SEMANTICS = "common_utc_hourly_close_intersection_no_forward_fill"
TIMESTAMP_SEMANTICS = "utc_bar_close_exclusive_end"
TIMEZONE = "UTC"


class PanelValidationErrorCode(str, Enum):
    INVALID_BAR_GRANULARITY = "INVALID_BAR_GRANULARITY"
    INSUFFICIENT_INSTRUMENTS = "INSUFFICIENT_INSTRUMENTS"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    OUT_OF_ORDER_TIMESTAMP = "OUT_OF_ORDER_TIMESTAMP"
    GAP_DETECTED = "GAP_DETECTED"
    OHLC_INCONSISTENT = "OHLC_INCONSISTENT"
    INVALID_VOLUME = "INVALID_VOLUME"
    NON_FINAL_BAR = "NON_FINAL_BAR"
    BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
    PANEL_ALIGNMENT_MISMATCH = "PANEL_ALIGNMENT_MISMATCH"
    FUTURE_LEAKAGE = "FUTURE_LEAKAGE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"


@dataclass(frozen=True)
class PanelBarV1:
    instrument_id: str
    timestamp_utc: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    is_final: bool


@dataclass(frozen=True)
class InstrumentPanelSeriesV1:
    instrument_id: str
    native_instrument_id: str
    bars: tuple[PanelBarV1, ...]
    series_digest: str


@dataclass(frozen=True)
class PanelValidationResultV1:
    valid: bool
    error_codes: tuple[str, ...]
    duplicate_check: str
    gap_check: str
    out_of_order_check: str
    future_leakage_check: str
    ohlc_consistency_check: str
    volume_validation_check: str
    panel_alignment_check: str


@dataclass(frozen=True)
class BoundCalendarPanelFilterResultV1:
    selected: tuple[InstrumentPanelSeriesV1, ...]
    excluded_empty_count: int
    excluded_partial_count: int


@dataclass(frozen=True)
class PanelDatasetManifestV1:
    manifest_version: str
    panel_id: str
    dataset_version: str
    bar_granularity: str
    panel_alignment_semantics: str
    timestamp_semantics: str
    timezone: str
    instrument_ids: tuple[str, ...]
    native_instrument_ids: tuple[str, ...]
    lifecycle_registry_ref: str
    lifecycle_registry_digest: str
    period_start_utc: str
    period_end_utc: str
    panel_row_count: int
    config_digest: str
    implementation_digest: str
    source_provenance_digest: str
    normalized_panel_digest: str
    manifest_digest: str


def compute_implementation_digest() -> str:
    return compute_sha256_digest(
        {
            "module": "pit_okx_pt1h_panel_ohlcv_dataset_v1",
            "manifest_version": MANIFEST_VERSION,
            "bar_granularity": BAR_GRANULARITY,
        }
    )


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_bound_panel_calendar_timestamps_v1(
    period_start_utc: str,
    period_end_utc: str,
) -> tuple[str, ...]:
    """Build inclusive bound-panel UTC hourly timestamps for fetch/validation parity."""
    start = datetime.strptime(period_start_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    end = datetime.strptime(period_end_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    timestamps: list[str] = []
    cur = start
    while cur <= end:
        timestamps.append(cur.strftime("%Y-%m-%dT%H:%M:%SZ"))
        cur += timedelta(hours=1)
    return tuple(timestamps)


def has_full_bound_panel_calendar_coverage_v1(
    bars: Sequence[PanelBarV1],
    *,
    period_start_utc: str,
    period_end_utc: str,
) -> bool:
    expected = build_bound_panel_calendar_timestamps_v1(period_start_utc, period_end_utc)
    if len(bars) != len(expected):
        return False
    actual = [bar.timestamp_utc for bar in bars]
    return actual == list(expected)


def filter_panel_series_to_full_bound_calendar_coverage_v1(
    candidates: Sequence[InstrumentPanelSeriesV1],
    *,
    period_start_utc: str,
    period_end_utc: str,
) -> BoundCalendarPanelFilterResultV1:
    """Keep only instruments whose bound bars exactly cover the panel calendar."""
    selected: list[InstrumentPanelSeriesV1] = []
    excluded_empty = 0
    excluded_partial = 0
    for series in candidates:
        if not series.bars:
            excluded_empty += 1
            continue
        if not has_full_bound_panel_calendar_coverage_v1(
            series.bars,
            period_start_utc=period_start_utc,
            period_end_utc=period_end_utc,
        ):
            excluded_partial += 1
            continue
        selected.append(series)
    return BoundCalendarPanelFilterResultV1(
        selected=tuple(selected),
        excluded_empty_count=excluded_empty,
        excluded_partial_count=excluded_partial,
    )


def _validate_single_series(
    series: InstrumentPanelSeriesV1,
    *,
    expected_timestamps: Sequence[str] | None = None,
) -> tuple[list[str], str, str, str, str, str, str]:
    errors: list[str] = []
    duplicate_check = "PASS"
    gap_check = "PASS"
    out_of_order_check = "PASS"
    ohlc_check = "PASS"
    volume_check = "PASS"
    alignment_check = "PASS"

    seen_ts: set[str] = set()
    prev_ts: str | None = None
    prev_epoch: int | None = None
    for bar in series.bars:
        if not is_valid_rfc3339_utc(bar.timestamp_utc):
            errors.append(PanelValidationErrorCode.MISSING_REQUIRED_FIELD.value)
            continue
        if bar.timestamp_utc in seen_ts:
            duplicate_check = "FAIL"
            errors.append(PanelValidationErrorCode.DUPLICATE_TIMESTAMP.value)
        seen_ts.add(bar.timestamp_utc)

        epoch = int(
            bar.timestamp_utc.replace("-", "").replace(":", "").replace("T", "").replace("Z", "")
        )
        if prev_epoch is not None and epoch < prev_epoch:
            out_of_order_check = "FAIL"
            errors.append(PanelValidationErrorCode.OUT_OF_ORDER_TIMESTAMP.value)
        if prev_ts is not None:
            prev_dt = datetime.strptime(prev_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            cur_dt = datetime.strptime(bar.timestamp_utc, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            gap_seconds = (cur_dt - prev_dt).total_seconds()
            if gap_seconds > BAR_GRANULARITY_SECONDS:
                gap_check = "FAIL"
                errors.append(PanelValidationErrorCode.GAP_DETECTED.value)
        prev_ts = bar.timestamp_utc
        prev_epoch = epoch

        o = _parse_float(bar.open)
        h = _parse_float(bar.high)
        low = _parse_float(bar.low)
        c = _parse_float(bar.close)
        vol = _parse_float(bar.volume)
        if None in (o, h, low, c, vol):
            errors.append(PanelValidationErrorCode.MISSING_REQUIRED_FIELD.value)
            continue
        assert (
            o is not None
            and h is not None
            and low is not None
            and c is not None
            and vol is not None
        )
        if not (low <= o <= h and low <= c <= h):
            ohlc_check = "FAIL"
            errors.append(PanelValidationErrorCode.OHLC_INCONSISTENT.value)
        if vol < 0:
            volume_check = "FAIL"
            errors.append(PanelValidationErrorCode.INVALID_VOLUME.value)
        if not bar.is_final:
            errors.append(PanelValidationErrorCode.NON_FINAL_BAR.value)

    if expected_timestamps is not None:
        actual = [bar.timestamp_utc for bar in series.bars]
        if actual != list(expected_timestamps):
            alignment_check = "FAIL"
            errors.append(PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value)

    return (
        errors,
        duplicate_check,
        gap_check,
        out_of_order_check,
        ohlc_check,
        volume_check,
        alignment_check,
    )


def validate_panel_series_v1(
    series_list: Sequence[InstrumentPanelSeriesV1],
    *,
    min_instruments: int = 5,
    forbidden_instrument_substrings: frozenset[str] = frozenset({"btc", "xbt", "bitcoin"}),
    generation_cutoff_utc: str | None = None,
) -> PanelValidationResultV1:
    errors: list[str] = []
    if len(series_list) < min_instruments:
        errors.append(PanelValidationErrorCode.INSUFFICIENT_INSTRUMENTS.value)

    for series in series_list:
        lowered = series.instrument_id.lower()
        if any(token in lowered for token in forbidden_instrument_substrings):
            errors.append(PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value)

    canonical_ts: list[str] | None = None
    if series_list:
        canonical_ts = [bar.timestamp_utc for bar in series_list[0].bars]

    dup = gap = ooo = ohlc = vol = align = "PASS"
    for series in series_list:
        series_errors, d, g, o, oh, v, a = _validate_single_series(
            series, expected_timestamps=canonical_ts
        )
        errors.extend(series_errors)
        for label, current in (
            (d, "duplicate"),
            (g, "gap"),
            (o, "ooo"),
            (oh, "ohlc"),
            (v, "vol"),
            (a, "align"),
        ):
            if label == "FAIL":
                if current == "duplicate":
                    dup = "FAIL"
                elif current == "gap":
                    gap = "FAIL"
                elif current == "ooo":
                    ooo = "FAIL"
                elif current == "ohlc":
                    ohlc = "FAIL"
                elif current == "vol":
                    vol = "FAIL"
                elif current == "align":
                    align = "FAIL"

    future_check = "PASS"
    if generation_cutoff_utc and canonical_ts:
        if canonical_ts[-1] > generation_cutoff_utc:
            future_check = "FAIL"
            errors.append(PanelValidationErrorCode.FUTURE_LEAKAGE.value)

    unique_errors = tuple(sorted(set(errors)))
    return PanelValidationResultV1(
        valid=not unique_errors,
        error_codes=unique_errors,
        duplicate_check=dup,
        gap_check=gap,
        out_of_order_check=ooo,
        future_leakage_check=future_check,
        ohlc_consistency_check=ohlc,
        volume_validation_check=vol,
        panel_alignment_check=align,
    )


def compute_series_digest(series: InstrumentPanelSeriesV1) -> str:
    payload = {
        "bars": [
            {
                "close": bar.close,
                "high": bar.high,
                "instrument_id": bar.instrument_id,
                "is_final": bar.is_final,
                "low": bar.low,
                "open": bar.open,
                "timestamp_utc": bar.timestamp_utc,
                "volume": bar.volume,
            }
            for bar in series.bars
        ],
        "instrument_id": series.instrument_id,
        "native_instrument_id": series.native_instrument_id,
    }
    return compute_sha256_digest(payload)


def compute_panel_digest(series_list: Sequence[InstrumentPanelSeriesV1]) -> str:
    return compute_sha256_digest(
        {
            "series_digests": [
                compute_series_digest(series)
                for series in sorted(series_list, key=lambda item: item.instrument_id)
            ]
        }
    )


def build_panel_dataset_manifest_v1(
    *,
    series_list: Sequence[InstrumentPanelSeriesV1],
    lifecycle_registry_ref: str,
    lifecycle_registry_digest: str,
    period_start_utc: str,
    period_end_utc: str,
    config_digest: str,
    source_provenance_digest: str,
) -> PanelDatasetManifestV1:
    normalized_panel_digest = compute_panel_digest(series_list)
    implementation_digest = compute_implementation_digest()
    instrument_ids = tuple(sorted(series.instrument_id for series in series_list))
    native_ids = tuple(
        series.native_instrument_id
        for series in sorted(series_list, key=lambda item: item.instrument_id)
    )
    panel_row_count = sum(len(series.bars) for series in series_list)
    interim = PanelDatasetManifestV1(
        manifest_version=MANIFEST_VERSION,
        panel_id=PANEL_ID,
        dataset_version=PANEL_DATASET_VERSION,
        bar_granularity=BAR_GRANULARITY,
        panel_alignment_semantics=PANEL_ALIGNMENT_SEMANTICS,
        timestamp_semantics=TIMESTAMP_SEMANTICS,
        timezone=TIMEZONE,
        instrument_ids=instrument_ids,
        native_instrument_ids=native_ids,
        lifecycle_registry_ref=lifecycle_registry_ref,
        lifecycle_registry_digest=lifecycle_registry_digest,
        period_start_utc=period_start_utc,
        period_end_utc=period_end_utc,
        panel_row_count=panel_row_count,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        source_provenance_digest=source_provenance_digest,
        normalized_panel_digest=normalized_panel_digest,
        manifest_digest="0" * 64,
    )
    manifest_digest = compute_sha256_digest(
        {
            "bar_granularity": interim.bar_granularity,
            "config_digest": interim.config_digest,
            "dataset_version": interim.dataset_version,
            "implementation_digest": interim.implementation_digest,
            "instrument_ids": list(interim.instrument_ids),
            "lifecycle_registry_digest": interim.lifecycle_registry_digest,
            "lifecycle_registry_ref": interim.lifecycle_registry_ref,
            "manifest_version": interim.manifest_version,
            "normalized_panel_digest": interim.normalized_panel_digest,
            "panel_alignment_semantics": interim.panel_alignment_semantics,
            "panel_id": interim.panel_id,
            "panel_row_count": interim.panel_row_count,
            "period_end_utc": interim.period_end_utc,
            "period_start_utc": interim.period_start_utc,
            "source_provenance_digest": interim.source_provenance_digest,
            "timestamp_semantics": interim.timestamp_semantics,
            "timezone": interim.timezone,
        }
    )
    return PanelDatasetManifestV1(
        manifest_version=interim.manifest_version,
        panel_id=interim.panel_id,
        dataset_version=interim.dataset_version,
        bar_granularity=interim.bar_granularity,
        panel_alignment_semantics=interim.panel_alignment_semantics,
        timestamp_semantics=interim.timestamp_semantics,
        timezone=interim.timezone,
        instrument_ids=interim.instrument_ids,
        native_instrument_ids=interim.native_instrument_ids,
        lifecycle_registry_ref=interim.lifecycle_registry_ref,
        lifecycle_registry_digest=interim.lifecycle_registry_digest,
        period_start_utc=interim.period_start_utc,
        period_end_utc=interim.period_end_utc,
        panel_row_count=interim.panel_row_count,
        config_digest=interim.config_digest,
        implementation_digest=interim.implementation_digest,
        source_provenance_digest=interim.source_provenance_digest,
        normalized_panel_digest=interim.normalized_panel_digest,
        manifest_digest=manifest_digest,
    )


def panel_manifest_to_dict(manifest: PanelDatasetManifestV1) -> dict[str, Any]:
    return {
        "bar_granularity": manifest.bar_granularity,
        "config_digest": manifest.config_digest,
        "dataset_version": manifest.dataset_version,
        "implementation_digest": manifest.implementation_digest,
        "instrument_ids": list(manifest.instrument_ids),
        "lifecycle_registry_digest": manifest.lifecycle_registry_digest,
        "lifecycle_registry_ref": manifest.lifecycle_registry_ref,
        "manifest_digest": manifest.manifest_digest,
        "manifest_version": manifest.manifest_version,
        "native_instrument_ids": list(manifest.native_instrument_ids),
        "normalized_panel_digest": manifest.normalized_panel_digest,
        "panel_alignment_semantics": manifest.panel_alignment_semantics,
        "panel_id": manifest.panel_id,
        "panel_row_count": manifest.panel_row_count,
        "period_end_utc": manifest.period_end_utc,
        "period_start_utc": manifest.period_start_utc,
        "source_provenance_digest": manifest.source_provenance_digest,
        "timestamp_semantics": manifest.timestamp_semantics,
        "timezone": manifest.timezone,
    }
