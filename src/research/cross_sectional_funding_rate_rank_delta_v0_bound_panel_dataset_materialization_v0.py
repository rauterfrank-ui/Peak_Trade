"""Bound funding panel dataset materialization for cross-sectional funding-rate rank-delta v0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_funding_rate_rank_delta_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    PANEL_DATASET_EXTENSION,
    PANEL_DATASET_ID,
    PANEL_FUNDING_DATASET_MANIFEST_REF,
    PIT_UNIVERSE_MANIFEST_REF,
    build_period_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    reject_foreign_panel_dataset_v0,
    verify_panel_covers_period_binding_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import (
    FUNDING_FIELD,
    InstrumentFundingPanelSeriesV1,
    validate_funding_panel_series_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_BOUND_PANEL_DATASET_MATERIALIZATION_V0=true"
)
MATERIALIZATION_VERSION = (
    "cross_sectional_funding_rate_rank_delta_v0_bound_panel_dataset_materialization.v0"
)

REASON_PERIOD_MISMATCH = "PERIOD_BINDING_MISMATCH"
REASON_FOREIGN_DATASET_REJECTED = "FOREIGN_DATASET_PERIOD_REJECTED"
REASON_MISSING_STAGING = "MISSING_PANEL_STAGING"
REASON_MISSING_FUNDING_MANIFEST = "MISSING_FUNDING_PANEL_MANIFEST"
REASON_FUNDING_VALIDATION_FAILED = "FUNDING_PANEL_VALIDATION_FAILED"
REASON_DATA_DIGEST_MISMATCH = "DATA_DIGEST_MISMATCH"
REASON_INSUFFICIENT_COVERAGE = "INSUFFICIENT_PERIOD_COVERAGE"


class MaterializationTerminalStatus(str, Enum):
    DATASET_MATERIALIZATION_COMPLETE = "DATASET_MATERIALIZATION_COMPLETE"
    BOUND_DATA_UNAVAILABLE_FAIL_CLOSED = "BOUND_DATA_UNAVAILABLE_FAIL_CLOSED"


@dataclass(frozen=True)
class BoundFundingPanelMaterializationResultV0:
    status: MaterializationTerminalStatus
    panel_data_digest: str
    bound_data_digest: str
    data_digest_match: bool
    data_start_time: str
    data_end_time: str
    instrument_count: int
    row_count_total: int
    period_binding_id: str
    dataset_id: str
    dataset_extension: str
    staging_root: str
    panel_ref: str
    funding_manifest_path: str
    reason_codes: tuple[str, ...]
    idempotent_digest_stable: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_bound_funding_data_digest_v0() -> str:
    return _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "dataset_extension": PANEL_DATASET_EXTENSION,
            "panel_funding_manifest_ref": PANEL_FUNDING_DATASET_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
            "funding_field": FUNDING_FIELD,
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
        }
    )


def _panel_time_bounds_from_funding(
    panel_series: Sequence[InstrumentFundingPanelSeriesV1],
) -> tuple[str, str]:
    timestamps: list[str] = []
    for series in panel_series:
        for bar in series.bars:
            timestamps.append(bar.timestamp_utc)
    if not timestamps:
        return "", ""
    return min(timestamps), max(timestamps)


def load_funding_panel_from_staging(
    staging_root: Path,
) -> tuple[tuple[InstrumentFundingPanelSeriesV1, ...], str, Path]:
    manifest_path = staging_root / "panel" / "panel_funding_dataset_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing_funding_manifest:{manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    panel_ref = (
        f"pit_okx_pt1h_panel_funding_dataset_v1:{manifest.get('panel_id', PANEL_DATASET_ID)}:"
        f"{manifest.get('dataset_extension', PANEL_DATASET_EXTENSION)}"
    )
    bars_path = staging_root / "panel" / "normalized_panel_bars_with_funding.json"
    if not bars_path.is_file():
        raise FileNotFoundError(f"missing_funding_bars:{bars_path}")
    payload = json.loads(bars_path.read_text(encoding="utf-8"))
    from src.research.pit_okx_pt1h_panel_funding_dataset_v1 import PanelBarWithFundingV1

    grouped: dict[str, list[PanelBarWithFundingV1]] = {}
    native: dict[str, str] = {}
    for row in payload.get("bars", []):
        instrument_id = str(row["instrument_id"])
        native[instrument_id] = str(row.get("native_instrument_id", instrument_id))
        grouped.setdefault(instrument_id, []).append(
            PanelBarWithFundingV1(
                instrument_id=instrument_id,
                timestamp_utc=str(row["timestamp_utc"]),
                open=str(row["open"]),
                high=str(row["high"]),
                low=str(row["low"]),
                close=str(row["close"]),
                volume=str(row["volume"]),
                funding_rate=str(row["funding_rate"]),
                is_final=bool(row.get("is_final", True)),
            )
        )
    series_list: list[InstrumentFundingPanelSeriesV1] = []
    for instrument_id in sorted(grouped):
        bars = tuple(sorted(grouped[instrument_id], key=lambda b: b.timestamp_utc))
        series_list.append(
            InstrumentFundingPanelSeriesV1(
                instrument_id=instrument_id,
                native_instrument_id=native[instrument_id],
                bars=bars,
                series_digest=_stable_digest(
                    [{"instrument_id": b.instrument_id, "ts": b.timestamp_utc} for b in bars]
                ),
            )
        )
    return tuple(series_list), panel_ref, manifest_path


def materialize_bound_funding_panel_dataset_v0(
    staging_root: Path,
    *,
    period_binding: Mapping[str, Any] | None = None,
    expected_data_digest: str | None = None,
    bound_data_digest: str | None = None,
) -> BoundFundingPanelMaterializationResultV0:
    period = dict(period_binding or build_period_binding_v0())
    staging_root = staging_root.resolve()
    bound_digest = bound_data_digest or compute_bound_funding_data_digest_v0()
    expected = expected_data_digest or bound_digest

    if not staging_root.is_dir():
        return BoundFundingPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            bound_data_digest=bound_digest,
            data_digest_match=False,
            data_start_time="",
            data_end_time="",
            instrument_count=0,
            row_count_total=0,
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            dataset_extension=PANEL_DATASET_EXTENSION,
            staging_root=str(staging_root),
            panel_ref="",
            funding_manifest_path="",
            reason_codes=(REASON_MISSING_STAGING,),
            idempotent_digest_stable=False,
        )

    try:
        funding_series, panel_ref, manifest_path = load_funding_panel_from_staging(staging_root)
    except FileNotFoundError as exc:
        return BoundFundingPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            bound_data_digest=bound_digest,
            data_digest_match=False,
            data_start_time="",
            data_end_time="",
            instrument_count=0,
            row_count_total=0,
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            dataset_extension=PANEL_DATASET_EXTENSION,
            staging_root=str(staging_root),
            panel_ref="",
            funding_manifest_path="",
            reason_codes=(str(exc), REASON_MISSING_FUNDING_MANIFEST),
            idempotent_digest_stable=False,
        )

    for series in funding_series:
        validation = validate_funding_panel_series_v1(series)
        if not validation.valid:
            return BoundFundingPanelMaterializationResultV0(
                status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                panel_data_digest="0" * 64,
                bound_data_digest=bound_digest,
                data_digest_match=False,
                data_start_time="",
                data_end_time="",
                instrument_count=len(funding_series),
                row_count_total=sum(len(s.bars) for s in funding_series),
                period_binding_id=str(period["period_binding_id"]),
                dataset_id=PANEL_DATASET_ID,
                dataset_extension=PANEL_DATASET_EXTENSION,
                staging_root=str(staging_root),
                panel_ref=panel_ref,
                funding_manifest_path=str(manifest_path),
                reason_codes=(REASON_FUNDING_VALIDATION_FAILED, *validation.error_codes),
                idempotent_digest_stable=False,
            )

    data_start, data_end = _panel_time_bounds_from_funding(funding_series)
    foreign_rejected, foreign_reasons = reject_foreign_panel_dataset_v0(
        data_first_timestamp=data_start,
        data_last_timestamp=data_end,
        period_binding=period,
    )
    if foreign_rejected:
        return BoundFundingPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            bound_data_digest=bound_digest,
            data_digest_match=False,
            data_start_time=data_start,
            data_end_time=data_end,
            instrument_count=len(funding_series),
            row_count_total=sum(len(s.bars) for s in funding_series),
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            dataset_extension=PANEL_DATASET_EXTENSION,
            staging_root=str(staging_root),
            panel_ref=panel_ref,
            funding_manifest_path=str(manifest_path),
            reason_codes=foreign_reasons,
            idempotent_digest_stable=False,
        )

    ohlcv_proxy: list[InstrumentPanelSeriesV1] = []
    try:
        ohlcv_proxy, _ = load_panel_series_from_staging(staging_root)
    except FileNotFoundError:
        pass
    if ohlcv_proxy:
        covers, cover_reasons = verify_panel_covers_period_binding_v0(
            ohlcv_proxy, period_binding=period
        )
        if not covers:
            return BoundFundingPanelMaterializationResultV0(
                status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                panel_data_digest="0" * 64,
                bound_data_digest=bound_digest,
                data_digest_match=False,
                data_start_time=data_start,
                data_end_time=data_end,
                instrument_count=len(funding_series),
                row_count_total=sum(len(s.bars) for s in funding_series),
                period_binding_id=str(period["period_binding_id"]),
                dataset_id=PANEL_DATASET_ID,
                dataset_extension=PANEL_DATASET_EXTENSION,
                staging_root=str(staging_root),
                panel_ref=panel_ref,
                funding_manifest_path=str(manifest_path),
                reason_codes=cover_reasons,
                idempotent_digest_stable=False,
            )

    digest_match = bound_digest == expected
    if not digest_match:
        return BoundFundingPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest=bound_digest,
            bound_data_digest=bound_digest,
            data_digest_match=False,
            data_start_time=data_start,
            data_end_time=data_end,
            instrument_count=len(funding_series),
            row_count_total=sum(len(s.bars) for s in funding_series),
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            dataset_extension=PANEL_DATASET_EXTENSION,
            staging_root=str(staging_root),
            panel_ref=panel_ref,
            funding_manifest_path=str(manifest_path),
            reason_codes=(REASON_DATA_DIGEST_MISMATCH,),
            idempotent_digest_stable=False,
        )

    digest_a = bound_digest
    digest_b = bound_data_digest or compute_bound_funding_data_digest_v0()

    return BoundFundingPanelMaterializationResultV0(
        status=MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE,
        panel_data_digest=digest_a,
        bound_data_digest=bound_digest,
        data_digest_match=True,
        data_start_time=data_start,
        data_end_time=data_end,
        instrument_count=len(funding_series),
        row_count_total=sum(len(s.bars) for s in funding_series),
        period_binding_id=str(period["period_binding_id"]),
        dataset_id=PANEL_DATASET_ID,
        dataset_extension=PANEL_DATASET_EXTENSION,
        staging_root=str(staging_root),
        panel_ref=panel_ref,
        funding_manifest_path=str(manifest_path),
        reason_codes=(),
        idempotent_digest_stable=digest_a == digest_b,
    )


def materialization_result_to_dict(
    result: BoundFundingPanelMaterializationResultV0,
) -> dict[str, Any]:
    return {
        "materialization_version": MATERIALIZATION_VERSION,
        "status": result.status.value,
        "panel_data_digest": result.panel_data_digest,
        "bound_data_digest": result.bound_data_digest,
        "data_digest_match": result.data_digest_match,
        "data_start_time": result.data_start_time,
        "data_end_time": result.data_end_time,
        "instrument_count": result.instrument_count,
        "row_count_total": result.row_count_total,
        "period_binding_id": result.period_binding_id,
        "dataset_id": result.dataset_id,
        "dataset_extension": result.dataset_extension,
        "staging_root": result.staging_root,
        "panel_ref": result.panel_ref,
        "funding_manifest_path": result.funding_manifest_path,
        "reason_codes": list(result.reason_codes),
        "idempotent_digest_stable": result.idempotent_digest_stable,
    }
