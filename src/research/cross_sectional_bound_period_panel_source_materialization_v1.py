"""Bound-period panel source materialization for cross-sectional relative-strength v1.

Offline-first: materializes PT1H panel staging for the frozen chronological holdout
window from existing raw OHLCV source files. No network, no synthetic data.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    FORBIDDEN_FOREIGN_FIRST_TIMESTAMP,
    REASON_FOREIGN_DATASET_REJECTED,
    REASON_INSUFFICIENT_COVERAGE,
    REASON_MISSING_STAGING,
    verify_panel_covers_period_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    PANEL_DATASET_ID,
    build_period_binding_v0,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    evaluate_okx_instrument_eligibility_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    PANEL_DATASET_VERSION,
    InstrumentPanelSeriesV1,
    PanelBarV1,
    build_panel_dataset_manifest_v1,
    compute_implementation_digest,
    compute_series_digest,
    panel_manifest_to_dict,
    validate_panel_series_v1,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_BOUND_PERIOD_PANEL_SOURCE_MATERIALIZATION_V1=true"
MATERIALIZATION_VERSION = "cross_sectional_bound_period_panel_source_materialization.v1"
MIN_ELIGIBLE_INSTRUMENTS = 5

REASON_MISSING_RAW_DIR = "MISSING_RAW_DIR"
REASON_MISSING_INSTRUMENTS_SNAPSHOT = "MISSING_INSTRUMENTS_SNAPSHOT"
REASON_NO_ELIGIBLE_RAW_SERIES = "NO_ELIGIBLE_RAW_SERIES"
REASON_BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE = "BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE"
REASON_PANEL_VALIDATION_FAILED = "PANEL_VALIDATION_FAILED"
REASON_OUTPUT_EXISTS = "OUTPUT_STAGING_EXISTS"
REASON_CONFLICTING_DUPLICATE_CANDLES = "CONFLICTING_DUPLICATE_CANDLES"

_RAW_FILENAME_RE = re.compile(r"^ohlcv_(.+)_swap_p\d{4}_[0-9a-f]+\.json$")


class BoundPeriodSourceMaterializationStatus(str, Enum):
    MATERIALIZED = "MATERIALIZED"
    BOUND_DATA_UNAVAILABLE_FAIL_CLOSED = "BOUND_DATA_UNAVAILABLE_FAIL_CLOSED"


@dataclass(frozen=True)
class SourceProvenanceEntryV1:
    source_file: str
    native_instrument_id: str
    instrument_id: str
    row_count_raw: int
    row_count_bound: int
    first_timestamp_utc: str
    last_timestamp_utc: str


@dataclass(frozen=True)
class BoundPeriodPanelSourceMaterializationResultV1:
    status: BoundPeriodSourceMaterializationStatus
    output_staging_root: str
    source_staging_root: str
    period_start_utc: str
    period_end_utc: str
    instrument_count: int
    row_count_total: int
    data_start_time: str
    data_end_time: str
    source_provenance: tuple[SourceProvenanceEntryV1, ...]
    reason_codes: tuple[str, ...]


def _ms_to_rfc3339_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_native_instrument_id_from_raw_filename(filename: str) -> str | None:
    match = _RAW_FILENAME_RE.match(filename)
    if not match:
        return None
    token = match.group(1).replace("_", "-").upper()
    return f"{token}-SWAP"


def normalize_okx_candles_to_panel_bars(
    instrument_id: str,
    rows: Sequence[Sequence[Any]],
) -> tuple[PanelBarV1, ...]:
    bars: list[PanelBarV1] = []
    for row in rows:
        ts = _ms_to_rfc3339_utc(int(str(row[0])))
        is_final = str(row[8]) == "1" if len(row) >= 9 else str(row[5]) == "1"
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts,
                open=str(row[1]),
                high=str(row[2]),
                low=str(row[3]),
                close=str(row[4]),
                volume=str(row[5]),
                is_final=is_final,
            )
        )
    return tuple(sorted(bars, key=lambda item: item.timestamp_utc))


def _load_instruments_snapshot(raw_dir: Path) -> list[dict[str, Any]]:
    candidates = sorted(raw_dir.glob("instruments_all_swap_*.json"))
    if not candidates:
        return []
    payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    data = payload.get("data") or []
    return [dict(item) for item in data if isinstance(item, Mapping)]


def _canonicalize_swap_instrument(inst: Mapping[str, Any]) -> tuple[str, str] | None:
    """Canonicalize one OKX SWAP record using lifecycle eligibility semantics."""
    result = evaluate_okx_instrument_eligibility_v1(inst)
    if not result.eligible or result.instrument_id is None or result.metadata is None:
        return None
    return result.instrument_id, result.metadata.inst_id


def group_raw_paths_by_native_instrument_v1(raw_dir: Path) -> dict[str, tuple[Path, ...]]:
    grouped: dict[str, list[Path]] = {}
    for raw_path in sorted(raw_dir.glob("ohlcv_*_swap_p*.json")):
        native_id = parse_native_instrument_id_from_raw_filename(raw_path.name)
        if native_id is None:
            continue
        grouped.setdefault(native_id, []).append(raw_path)
    return {native_id: tuple(paths) for native_id, paths in sorted(grouped.items())}


def merge_okx_candle_rows_with_dedup_v1(
    rows: Sequence[Sequence[Any]],
) -> tuple[tuple[list[Any], ...], str | None]:
    """Merge candle rows by timestamp; idempotent on identical duplicates, fail-closed on conflict."""
    by_ts: dict[int, list[Any]] = {}
    for row in rows:
        if not row:
            continue
        ts = int(str(row[0]))
        normalized = list(row)
        existing = by_ts.get(ts)
        if existing is None:
            by_ts[ts] = normalized
            continue
        if existing != normalized:
            return (), REASON_CONFLICTING_DUPLICATE_CANDLES
    return tuple(by_ts[ts] for ts in sorted(by_ts)), None


def _load_merged_rows_for_instrument(
    raw_paths: Sequence[Path],
) -> tuple[tuple[list[Any], ...], str | None]:
    combined_rows: list[list[Any]] = []
    for raw_path in raw_paths:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        rows = payload.get("data") or []
        if isinstance(rows, list):
            combined_rows.extend(list(row) for row in rows if row)
    return merge_okx_candle_rows_with_dedup_v1(combined_rows)


def _filter_bars_to_period(
    bars: Sequence[PanelBarV1],
    *,
    period_start_utc: str,
    period_end_utc: str,
) -> tuple[PanelBarV1, ...]:
    return tuple(
        bar
        for bar in bars
        if period_start_utc <= bar.timestamp_utc <= period_end_utc and bar.is_final
    )


def _copy_lifecycle_tree(source_root: Path, output_root: Path) -> None:
    source_lifecycle = source_root / "lifecycle"
    output_lifecycle = output_root / "lifecycle"
    output_lifecycle.mkdir(parents=True, exist_ok=True)
    if not source_lifecycle.is_dir():
        return
    for path in sorted(source_lifecycle.rglob("*")):
        if path.is_file():
            rel = path.relative_to(source_lifecycle)
            dst = output_lifecycle / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(path.read_bytes())


def materialize_bound_period_panel_from_raw_sources_v1(
    source_staging_root: Path,
    output_staging_root: Path,
    *,
    period_binding: Mapping[str, Any] | None = None,
    min_instruments: int = MIN_ELIGIBLE_INSTRUMENTS,
) -> BoundPeriodPanelSourceMaterializationResultV1:
    """Materialize bound-period panel staging from offline raw OHLCV sources."""
    period = dict(period_binding or build_period_binding_v0())
    period_start = str(period["training_start"])
    period_end = str(period["out_of_sample_end"])
    source_staging_root = source_staging_root.resolve()

    if output_staging_root.exists() and any(output_staging_root.iterdir()):
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=0,
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=(),
            reason_codes=(REASON_OUTPUT_EXISTS,),
        )

    raw_dir = source_staging_root / "raw"
    if not raw_dir.is_dir():
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=0,
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=(),
            reason_codes=(REASON_MISSING_RAW_DIR, REASON_MISSING_STAGING),
        )

    instruments = _load_instruments_snapshot(raw_dir)
    if not instruments:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=0,
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=(),
            reason_codes=(REASON_MISSING_INSTRUMENTS_SNAPSHOT,),
        )

    native_to_canonical: dict[str, str] = {}
    for inst in instruments:
        pair = _canonicalize_swap_instrument(inst)
        if pair is not None:
            native_to_canonical[pair[1]] = pair[0]

    provenance_entries: list[SourceProvenanceEntryV1] = []
    series_by_instrument: dict[str, InstrumentPanelSeriesV1] = {}
    grouped_raw_paths = group_raw_paths_by_native_instrument_v1(raw_dir)

    for native_id, raw_paths in grouped_raw_paths.items():
        instrument_id = native_to_canonical.get(native_id)
        if instrument_id is None:
            continue
        merged_rows, merge_error = _load_merged_rows_for_instrument(raw_paths)
        if merge_error is not None:
            return BoundPeriodPanelSourceMaterializationResultV1(
                status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                output_staging_root=str(output_staging_root),
                source_staging_root=str(source_staging_root),
                period_start_utc=period_start,
                period_end_utc=period_end,
                instrument_count=0,
                row_count_total=0,
                data_start_time="",
                data_end_time="",
                source_provenance=(),
                reason_codes=(merge_error,),
            )
        if not merged_rows:
            continue
        all_bars = normalize_okx_candles_to_panel_bars(instrument_id, merged_rows)
        bound_bars = _filter_bars_to_period(
            all_bars, period_start_utc=period_start, period_end_utc=period_end
        )
        if not bound_bars:
            continue
        if bound_bars[0].timestamp_utc >= FORBIDDEN_FOREIGN_FIRST_TIMESTAMP:
            return BoundPeriodPanelSourceMaterializationResultV1(
                status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                output_staging_root=str(output_staging_root),
                source_staging_root=str(source_staging_root),
                period_start_utc=period_start,
                period_end_utc=period_end,
                instrument_count=0,
                row_count_total=0,
                data_start_time=all_bars[0].timestamp_utc,
                data_end_time=all_bars[-1].timestamp_utc,
                source_provenance=(),
                reason_codes=(REASON_FOREIGN_DATASET_REJECTED,),
            )
        source_files = ",".join(
            path.relative_to(source_staging_root).as_posix() for path in raw_paths
        )
        provenance_entries.append(
            SourceProvenanceEntryV1(
                source_file=source_files,
                native_instrument_id=native_id,
                instrument_id=instrument_id,
                row_count_raw=len(all_bars),
                row_count_bound=len(bound_bars),
                first_timestamp_utc=bound_bars[0].timestamp_utc,
                last_timestamp_utc=bound_bars[-1].timestamp_utc,
            )
        )
        interim = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=native_id,
            bars=bound_bars,
            series_digest="0" * 64,
        )
        series_by_instrument[instrument_id] = InstrumentPanelSeriesV1(
            instrument_id=interim.instrument_id,
            native_instrument_id=interim.native_instrument_id,
            bars=interim.bars,
            series_digest=compute_series_digest(interim),
        )

    if len(series_by_instrument) < min_instruments:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(series_by_instrument),
            row_count_total=sum(len(s.bars) for s in series_by_instrument.values()),
            data_start_time="",
            data_end_time="",
            source_provenance=tuple(provenance_entries),
            reason_codes=(
                REASON_NO_ELIGIBLE_RAW_SERIES,
                REASON_BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE,
            ),
        )

    panel_series = tuple(series_by_instrument[iid] for iid in sorted(series_by_instrument))
    validation = validate_panel_series_v1(panel_series, min_instruments=min_instruments)
    if not validation.valid:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(s.bars) for s in panel_series),
            data_start_time=panel_series[0].bars[0].timestamp_utc if panel_series else "",
            data_end_time=panel_series[0].bars[-1].timestamp_utc if panel_series else "",
            source_provenance=tuple(provenance_entries),
            reason_codes=(REASON_PANEL_VALIDATION_FAILED, *validation.error_codes),
        )

    covers, cover_reasons = verify_panel_covers_period_binding_v0(
        panel_series, period_binding=period
    )
    if not covers:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(source_staging_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(s.bars) for s in panel_series),
            data_start_time=panel_series[0].bars[0].timestamp_utc,
            data_end_time=panel_series[0].bars[-1].timestamp_utc,
            source_provenance=tuple(provenance_entries),
            reason_codes=cover_reasons,
        )

    output_staging_root.mkdir(parents=True, exist_ok=True)
    panel_dir = output_staging_root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    _copy_lifecycle_tree(source_staging_root, output_staging_root)

    rows: list[dict[str, object]] = []
    for series in panel_series:
        for bar in series.bars:
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
    rows.sort(key=lambda item: (str(item["instrument_id"]), str(item["timestamp_utc"])))

    source_provenance_digest = _stable_digest(
        {
            "entries": [
                {
                    "source_file": entry.source_file,
                    "instrument_id": entry.instrument_id,
                    "row_count_bound": entry.row_count_bound,
                }
                for entry in provenance_entries
            ]
        }
    )
    lifecycle_ref = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
    lifecycle_digest = "0" * 64
    source_reg = source_staging_root / "lifecycle" / "SOURCE_REGISTRATION.json"
    if source_reg.is_file():
        reg_payload = json.loads(source_reg.read_text(encoding="utf-8"))
        lifecycle_digest = str(reg_payload.get("source_snapshot_digest", lifecycle_digest))

    manifest_obj = build_panel_dataset_manifest_v1(
        series_list=panel_series,
        lifecycle_registry_ref=lifecycle_ref,
        lifecycle_registry_digest=lifecycle_digest,
        period_start_utc=period_start,
        period_end_utc=period_end,
        config_digest=_stable_digest({"period_binding_id": period["period_binding_id"]}),
        source_provenance_digest=source_provenance_digest,
    )
    manifest_dict = panel_manifest_to_dict(manifest_obj)
    manifest_dict["panel_id"] = PANEL_DATASET_ID
    manifest_dict["dataset_version"] = PANEL_DATASET_VERSION
    manifest_dict["bar_granularity"] = BAR_GRANULARITY

    (panel_dir / "normalized_panel_bars.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(manifest_dict, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_staging_root / "SOURCE_PROVENANCE.json").write_text(
        json.dumps(
            {
                "materialization_version": MATERIALIZATION_VERSION,
                "implementation_digest": compute_implementation_digest(),
                "source_staging_root": str(source_staging_root),
                "entries": [
                    {
                        "source_file": entry.source_file,
                        "native_instrument_id": entry.native_instrument_id,
                        "instrument_id": entry.instrument_id,
                        "row_count_raw": entry.row_count_raw,
                        "row_count_bound": entry.row_count_bound,
                        "first_timestamp_utc": entry.first_timestamp_utc,
                        "last_timestamp_utc": entry.last_timestamp_utc,
                    }
                    for entry in provenance_entries
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    data_start = min(bar.timestamp_utc for series in panel_series for bar in series.bars)
    data_end = max(bar.timestamp_utc for series in panel_series for bar in series.bars)
    return BoundPeriodPanelSourceMaterializationResultV1(
        status=BoundPeriodSourceMaterializationStatus.MATERIALIZED,
        output_staging_root=str(output_staging_root),
        source_staging_root=str(source_staging_root),
        period_start_utc=period_start,
        period_end_utc=period_end,
        instrument_count=len(panel_series),
        row_count_total=sum(len(s.bars) for s in panel_series),
        data_start_time=data_start,
        data_end_time=data_end,
        source_provenance=tuple(provenance_entries),
        reason_codes=(),
    )


def bound_period_source_result_to_dict(
    result: BoundPeriodPanelSourceMaterializationResultV1,
) -> dict[str, object]:
    return {
        "materialization_version": MATERIALIZATION_VERSION,
        "status": result.status.value,
        "output_staging_root": result.output_staging_root,
        "source_staging_root": result.source_staging_root,
        "period_start_utc": result.period_start_utc,
        "period_end_utc": result.period_end_utc,
        "instrument_count": result.instrument_count,
        "row_count_total": result.row_count_total,
        "data_start_time": result.data_start_time,
        "data_end_time": result.data_end_time,
        "source_provenance_count": len(result.source_provenance),
        "reason_codes": list(result.reason_codes),
    }
