"""Bound panel dataset materialization for cross-sectional relative-strength v0.

Fail-closed materialization validating staging panel data against the frozen
period_binding from PR #4790. No dataset or period substitution.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    PANEL_DATASET_ID,
    build_period_binding_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    compute_semantic_data_digest_v0,
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    validate_panel_series_v1,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BOUND_PANEL_DATASET_MATERIALIZATION_V0=true"
MATERIALIZATION_VERSION = (
    "cross_sectional_relative_strength_v0_bound_panel_dataset_materialization.v0"
)

REASON_PERIOD_MISMATCH = "PERIOD_BINDING_MISMATCH"
REASON_FOREIGN_DATASET_REJECTED = "FOREIGN_DATASET_PERIOD_REJECTED"
REASON_MISSING_STAGING = "MISSING_PANEL_STAGING"
REASON_PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
REASON_INSUFFICIENT_COVERAGE = "INSUFFICIENT_PERIOD_COVERAGE"

FORBIDDEN_FOREIGN_FIRST_TIMESTAMP = "2026-07-02T12:00:00Z"


class MaterializationTerminalStatus(str, Enum):
    DATASET_MATERIALIZATION_COMPLETE = "DATASET_MATERIALIZATION_COMPLETE"
    BOUND_DATA_UNAVAILABLE_FAIL_CLOSED = "BOUND_DATA_UNAVAILABLE_FAIL_CLOSED"


@dataclass(frozen=True)
class BoundPanelMaterializationResultV0:
    status: MaterializationTerminalStatus
    panel_data_digest: str
    data_start_time: str
    data_end_time: str
    instrument_count: int
    row_count_total: int
    period_binding_id: str
    dataset_id: str
    staging_root: str
    panel_ref: str
    reason_codes: tuple[str, ...]
    idempotent_digest_stable: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _panel_time_bounds(
    panel_series: Sequence[InstrumentPanelSeriesV1],
) -> tuple[str, str]:
    timestamps: list[str] = []
    for series in panel_series:
        for bar in series.bars:
            timestamps.append(bar.timestamp_utc)
    if not timestamps:
        return "", ""
    return min(timestamps), max(timestamps)


def verify_panel_covers_period_binding_v0(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    period_binding: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    data_start, data_end = _panel_time_bounds(panel_series)
    if not data_start or not data_end:
        return False, (REASON_INSUFFICIENT_COVERAGE,)

    training_start = str(period_binding["training_start"])
    out_of_sample_end = str(period_binding["out_of_sample_end"])

    if data_start > training_start:
        reasons.append(f"{REASON_INSUFFICIENT_COVERAGE}:data_start_after_training_start")
    if data_end < out_of_sample_end:
        reasons.append(f"{REASON_INSUFFICIENT_COVERAGE}:data_end_before_out_of_sample_end")

    if data_start >= FORBIDDEN_FOREIGN_FIRST_TIMESTAMP:
        reasons.append(REASON_FOREIGN_DATASET_REJECTED)

    return not reasons, tuple(reasons)


def reject_foreign_panel_dataset_v0(
    *,
    data_first_timestamp: str,
    data_last_timestamp: str,
    period_binding: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    """Reject known foreign dataset windows that do not match bound period."""
    reasons: list[str] = []
    training_start = str(period_binding["training_start"])
    out_of_sample_end = str(period_binding["out_of_sample_end"])

    if data_first_timestamp >= FORBIDDEN_FOREIGN_FIRST_TIMESTAMP:
        reasons.append(REASON_FOREIGN_DATASET_REJECTED)
    if data_first_timestamp > training_start or data_last_timestamp < out_of_sample_end:
        reasons.append(REASON_PERIOD_MISMATCH)
    return bool(reasons), tuple(reasons)


def compute_bound_panel_data_digest_v0(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    universe_manifest_digest: str = "0" * 64,
    source_registration_digest: str = "0" * 64,
) -> str:
    return compute_semantic_data_digest_v0(
        series_list=panel_series,
        universe_manifest_digest=universe_manifest_digest,
        source_registration_digest=source_registration_digest,
        dataset_id=PANEL_DATASET_ID,
        dataset_version="v1",
        dataset_schema_version="pit_cross_sectional_research_dataset_envelope.v0",
    )


def materialize_bound_panel_dataset_v0(
    staging_root: Path,
    *,
    period_binding: Mapping[str, Any] | None = None,
    universe_manifest_digest: str = "0" * 64,
    source_registration_digest: str = "0" * 64,
) -> BoundPanelMaterializationResultV0:
    """Materialize bound panel dataset from staging; fail-closed on mismatch."""
    period = dict(period_binding or build_period_binding_v0())
    staging_root = staging_root.resolve()

    if not staging_root.is_dir():
        return BoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            data_start_time="",
            data_end_time="",
            instrument_count=0,
            row_count_total=0,
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            staging_root=str(staging_root),
            panel_ref="",
            reason_codes=(REASON_MISSING_STAGING,),
            idempotent_digest_stable=False,
        )

    try:
        panel_series, panel_ref = load_panel_series_from_staging(staging_root)
    except FileNotFoundError as exc:
        return BoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            data_start_time="",
            data_end_time="",
            instrument_count=0,
            row_count_total=0,
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            staging_root=str(staging_root),
            panel_ref="",
            reason_codes=(str(exc), REASON_MISSING_STAGING),
            idempotent_digest_stable=False,
        )

    validation = validate_panel_series_v1(panel_series, min_instruments=5)
    if not validation.valid:
        return BoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            data_start_time="",
            data_end_time="",
            instrument_count=len(panel_series),
            row_count_total=sum(len(s.bars) for s in panel_series),
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            staging_root=str(staging_root),
            panel_ref=panel_ref,
            reason_codes=(REASON_PANEL_VALIDATION_FAILED, *validation.error_codes),
            idempotent_digest_stable=False,
        )

    data_start, data_end = _panel_time_bounds(panel_series)
    foreign_rejected, foreign_reasons = reject_foreign_panel_dataset_v0(
        data_first_timestamp=data_start,
        data_last_timestamp=data_end,
        period_binding=period,
    )
    if foreign_rejected:
        return BoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            data_start_time=data_start,
            data_end_time=data_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(s.bars) for s in panel_series),
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            staging_root=str(staging_root),
            panel_ref=panel_ref,
            reason_codes=foreign_reasons,
            idempotent_digest_stable=False,
        )

    covers, cover_reasons = verify_panel_covers_period_binding_v0(
        panel_series, period_binding=period
    )
    if not covers:
        return BoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            panel_data_digest="0" * 64,
            data_start_time=data_start,
            data_end_time=data_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(s.bars) for s in panel_series),
            period_binding_id=str(period["period_binding_id"]),
            dataset_id=PANEL_DATASET_ID,
            staging_root=str(staging_root),
            panel_ref=panel_ref,
            reason_codes=cover_reasons,
            idempotent_digest_stable=False,
        )

    digest_a = compute_bound_panel_data_digest_v0(
        panel_series,
        universe_manifest_digest=universe_manifest_digest,
        source_registration_digest=source_registration_digest,
    )
    digest_b = compute_bound_panel_data_digest_v0(
        panel_series,
        universe_manifest_digest=universe_manifest_digest,
        source_registration_digest=source_registration_digest,
    )

    return BoundPanelMaterializationResultV0(
        status=MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE,
        panel_data_digest=digest_a,
        data_start_time=data_start,
        data_end_time=data_end,
        instrument_count=len(panel_series),
        row_count_total=sum(len(s.bars) for s in panel_series),
        period_binding_id=str(period["period_binding_id"]),
        dataset_id=PANEL_DATASET_ID,
        staging_root=str(staging_root),
        panel_ref=panel_ref,
        reason_codes=(),
        idempotent_digest_stable=digest_a == digest_b,
    )


def materialization_result_to_dict(result: BoundPanelMaterializationResultV0) -> dict[str, Any]:
    return {
        "materialization_version": MATERIALIZATION_VERSION,
        "status": result.status.value,
        "panel_data_digest": result.panel_data_digest,
        "data_start_time": result.data_start_time,
        "data_end_time": result.data_end_time,
        "instrument_count": result.instrument_count,
        "row_count_total": result.row_count_total,
        "period_binding_id": result.period_binding_id,
        "dataset_id": result.dataset_id,
        "staging_root": result.staging_root,
        "panel_ref": result.panel_ref,
        "reason_codes": list(result.reason_codes),
        "idempotent_digest_stable": result.idempotent_digest_stable,
    }
