"""PT1H multi-instrument OKX panel dataset v1 with open_interest field.

Narrow extension of pit_okx_pt1h_panel_ohlcv_dataset_v1 for OI-delta research.
Research-only; no network, credentials, or runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    MANIFEST_VERSION as OHLCV_MANIFEST_VERSION,
    PanelBarV1,
    PanelValidationErrorCode,
    PanelValidationResultV1,
    _parse_float,
)

PACKAGE_MARKER = "PIT_OKX_PT1H_PANEL_OPEN_INTEREST_DATASET_V1=true"
MANIFEST_VERSION = "pit_okx_pt1h_panel_open_interest_dataset_manifest_v1"
PANEL_DATASET_VERSION = "v1"
OPEN_INTEREST_FIELD = "open_interest"
OPEN_INTEREST_UNIT = "okx_native_contract_count"
PANEL_ID = "pit_okx_linear_usdt_non_bitcoin_open_interest_panel"
DATASET_EXTENSION = "extended_chronological_with_open_interest_v1"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "instrument_id",
    "native_instrument_id",
    "timestamp_utc",
    "open_interest",
    "open_interest_unit",
    "availability_time_utc",
    "is_final",
    "data_quality_status",
    "stale_flag",
    "missing_flag",
    "universe_membership_status",
    "source_schema_version",
)


class OpenInterestPanelValidationErrorCode(str, Enum):
    MISSING_OPEN_INTEREST = "MISSING_OPEN_INTEREST"
    INVALID_OPEN_INTEREST = "INVALID_OPEN_INTEREST"
    LOOKAHEAD_REJECTED = "LOOKAHEAD_REJECTED"
    STALE_OBSERVATION = "STALE_OBSERVATION"


@dataclass(frozen=True)
class PanelBarWithOpenInterestV1:
    instrument_id: str
    native_instrument_id: str
    timestamp_utc: str
    open_interest: str | None
    open_interest_unit: str
    availability_time_utc: str
    is_final: bool
    data_quality_status: str
    stale_flag: bool
    missing_flag: bool
    universe_membership_status: str
    source_schema_version: str


@dataclass(frozen=True)
class InstrumentOpenInterestPanelSeriesV1:
    instrument_id: str
    native_instrument_id: str
    bars: tuple[PanelBarWithOpenInterestV1, ...]
    series_digest: str


def compute_implementation_digest_v1() -> str:
    return compute_sha256_digest(
        {
            "module": "pit_okx_pt1h_panel_open_interest_dataset_v1",
            "manifest_version": MANIFEST_VERSION,
            "open_interest_field": OPEN_INTEREST_FIELD,
            "open_interest_unit": OPEN_INTEREST_UNIT,
            "ohlcv_manifest_version": OHLCV_MANIFEST_VERSION,
            "canonical_columns": list(CANONICAL_COLUMNS),
        }
    )


def panel_bar_with_open_interest_from_ohlcv_v1(
    bar: PanelBarV1,
    *,
    native_instrument_id: str,
    open_interest: str | None,
    availability_time_utc: str,
    data_quality_status: str = "OK",
    stale_flag: bool = False,
    missing_flag: bool = False,
    universe_membership_status: str = "ELIGIBLE",
    source_schema_version: str = "okx_rubik_open_interest_history.v0",
) -> PanelBarWithOpenInterestV1:
    return PanelBarWithOpenInterestV1(
        instrument_id=bar.instrument_id,
        native_instrument_id=native_instrument_id,
        timestamp_utc=bar.timestamp_utc,
        open_interest=open_interest,
        open_interest_unit=OPEN_INTEREST_UNIT,
        availability_time_utc=availability_time_utc,
        is_final=bar.is_final,
        data_quality_status=data_quality_status,
        stale_flag=stale_flag,
        missing_flag=missing_flag,
        universe_membership_status=universe_membership_status,
        source_schema_version=source_schema_version,
    )


def validate_open_interest_panel_series_v1(
    series: InstrumentOpenInterestPanelSeriesV1,
    *,
    expected_timestamps: Sequence[str] | None = None,
) -> PanelValidationResultV1:
    extra_codes: list[str] = []
    for bar in series.bars:
        if expected_timestamps is not None and bar.timestamp_utc not in expected_timestamps:
            extra_codes.append(PanelValidationErrorCode.PANEL_ALIGNMENT_MISMATCH.value)
            break
        if bar.missing_flag:
            continue
        if bar.open_interest is None:
            extra_codes.append(OpenInterestPanelValidationErrorCode.MISSING_OPEN_INTEREST.value)
            break
        parsed = _parse_float(bar.open_interest)
        if parsed is None or parsed < 0:
            extra_codes.append(OpenInterestPanelValidationErrorCode.INVALID_OPEN_INTEREST.value)
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


def serialize_panel_bar_v1(bar: PanelBarWithOpenInterestV1) -> dict[str, Any]:
    return {
        "instrument_id": bar.instrument_id,
        "native_instrument_id": bar.native_instrument_id,
        "timestamp_utc": bar.timestamp_utc,
        "open_interest": bar.open_interest,
        "open_interest_unit": bar.open_interest_unit,
        "availability_time_utc": bar.availability_time_utc,
        "is_final": bar.is_final,
        "data_quality_status": bar.data_quality_status,
        "stale_flag": bar.stale_flag,
        "missing_flag": bar.missing_flag,
        "universe_membership_status": bar.universe_membership_status,
        "source_schema_version": bar.source_schema_version,
    }


def compute_panel_open_interest_digest_v1(
    rows: Sequence[Mapping[str, Any]],
) -> str:
    semantic_rows = []
    for row in rows:
        semantic_rows.append(
            {col: row.get(col) for col in CANONICAL_COLUMNS if col not in {"availability_time_utc"}}
        )
    return compute_sha256_digest({"rows": semantic_rows})
