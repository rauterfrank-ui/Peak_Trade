"""PT1H multi-instrument OKX panel dataset v1 with funding_rate field.

Narrow extension of pit_okx_pt1h_panel_ohlcv_dataset_v1 for funding-carry research.
Research-only; no network, credentials, or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    MANIFEST_VERSION as OHLCV_MANIFEST_VERSION,
    PanelBarV1,
    PanelValidationErrorCode,
    PanelValidationResultV1,
    _parse_float,
)

PACKAGE_MARKER = "PIT_OKX_PT1H_PANEL_FUNDING_DATASET_V1=true"
MANIFEST_VERSION = "pit_okx_pt1h_panel_funding_dataset_manifest_v1"
PANEL_DATASET_VERSION = "v1"
FUNDING_FIELD = "funding_rate"


class FundingPanelValidationErrorCode(str, Enum):
    MISSING_FUNDING_RATE = "MISSING_FUNDING_RATE"
    INVALID_FUNDING_RATE = "INVALID_FUNDING_RATE"


@dataclass(frozen=True)
class PanelBarWithFundingV1:
    instrument_id: str
    timestamp_utc: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    funding_rate: str
    is_final: bool


@dataclass(frozen=True)
class InstrumentFundingPanelSeriesV1:
    instrument_id: str
    native_instrument_id: str
    bars: tuple[PanelBarWithFundingV1, ...]
    series_digest: str


def compute_implementation_digest_v1() -> str:
    return compute_sha256_digest(
        {
            "module": "pit_okx_pt1h_panel_funding_dataset_v1",
            "manifest_version": MANIFEST_VERSION,
            "funding_field": FUNDING_FIELD,
            "ohlcv_manifest_version": OHLCV_MANIFEST_VERSION,
        }
    )


def panel_bar_with_funding_from_ohlcv_v1(
    bar: PanelBarV1,
    *,
    funding_rate: str,
) -> PanelBarWithFundingV1:
    return PanelBarWithFundingV1(
        instrument_id=bar.instrument_id,
        timestamp_utc=bar.timestamp_utc,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        funding_rate=funding_rate,
        is_final=bar.is_final,
    )


def validate_funding_panel_series_v1(
    series: InstrumentFundingPanelSeriesV1,
    *,
    expected_timestamps: Sequence[str] | None = None,
) -> PanelValidationResultV1:
    extra_codes: list[str] = []
    for bar in series.bars:
        if expected_timestamps is not None and bar.timestamp_utc not in expected_timestamps:
            extra_codes.append(PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value)
            break
        if not bar.funding_rate:
            extra_codes.append(FundingPanelValidationErrorCode.MISSING_FUNDING_RATE.value)
            break
        parsed = _parse_float(bar.funding_rate)
        if parsed is None:
            extra_codes.append(FundingPanelValidationErrorCode.INVALID_FUNDING_RATE.value)
            break
    valid = not extra_codes
    return PanelValidationResultV1(
        valid=valid,
        error_codes=tuple(extra_codes),
        duplicate_check="NOT_RUN_SINGLE_SERIES",
        gap_check="NOT_RUN_SINGLE_SERIES",
        out_of_order_check="NOT_RUN_SINGLE_SERIES",
        future_leakage_check="NOT_RUN_SINGLE_SERIES",
        ohlc_consistency_check="NOT_RUN_SINGLE_SERIES",
        volume_validation_check="NOT_RUN_SINGLE_SERIES",
        panel_alignment_check="NOT_RUN_SINGLE_SERIES",
    )
