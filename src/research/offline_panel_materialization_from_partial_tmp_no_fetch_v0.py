"""Offline panel materialization from durable-archive partial tmp (no fetch) v0.

Bounded adapter scope: reuses ``cross_sectional_bound_period_panel_source_materialization_v1``
helpers, applies full-bound-calendar membership filtering, materializes
``extended_chronological_v1`` staging, prepares funding bindings for panel members
only (``--skip-fetch``), and runs CSF/RDM preflight with ``attempt_fetch=False``.

Research-only; no network fetch, runtime, evaluation, or order effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (
    MATERIALIZATION_VERSION as SOURCE_MATERIALIZATION_VERSION,
    MIN_ELIGIBLE_INSTRUMENTS,
    REASON_BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE,
    REASON_MISSING_RAW_DIR,
    REASON_NO_ELIGIBLE_RAW_SERIES,
    REASON_OUTPUT_EXISTS,
    REASON_PANEL_VALIDATION_FAILED,
    BoundPeriodPanelSourceMaterializationResultV1,
    BoundPeriodSourceMaterializationStatus,
    SourceProvenanceEntryV1,
    _canonicalize_swap_instrument,
    _copy_lifecycle_tree,
    _filter_bars_to_period,
    _load_instruments_snapshot,
    _load_merged_rows_for_instrument,
    _stable_digest,
    bound_period_source_result_to_dict,
    group_raw_paths_by_native_instrument_v1,
    normalize_okx_candles_to_panel_bars,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    INFRASTRUCTURE_GO_TOKEN,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    PANEL_CALENDAR_END_UTC,
    PANEL_CALENDAR_START_UTC,
    PANEL_DATASET_ID,
    build_period_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    verify_panel_covers_period_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    PANEL_DATASET_ID as RS_PANEL_DATASET_ID,
)
from src.research.csf_rdm_v0_extended_chronological_v1_staging_funding_panel_materialization_v0 import (
    CANONICAL_FUNDING_OWNER,
    CANONICAL_PREFLIGHT_OWNER,
    MaterializationScopeResultV0,
    run_materialization_scope_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    BAR_GRANULARITY,
    PANEL_DATASET_VERSION,
    InstrumentPanelSeriesV1,
    build_panel_dataset_manifest_v1,
    compute_implementation_digest,
    compute_series_digest,
    filter_panel_series_to_full_bound_calendar_coverage_v1,
    panel_manifest_to_dict,
    validate_panel_series_v1,
)

PACKAGE_MARKER = "OFFLINE_PANEL_MATERIALIZATION_FROM_PARTIAL_TMP_NO_FETCH_V0=true"
MATERIALIZATION_VERSION = "offline_panel_materialization_from_partial_tmp_no_fetch.v0"
CONFIRM_GO = "GO_OFFLINE_PANEL_MATERIALIZATION_FROM_PARTIAL_TMP_NO_FETCH_V0"
CONFIG_REL_PATH = "config/ops/offline_panel_materialization_from_partial_tmp_no_fetch_v0.json"

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_PARTIAL_TMP_SLUG = ".tmp_historical_20260703T181515Z"
DEFAULT_PARTIAL_TMP_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    f"{DEFAULT_PARTIAL_TMP_SLUG}"
)
DEFAULT_OUTPUT_STAGING_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)

SOURCE_OWNER = "src/research/cross_sectional_bound_period_panel_source_materialization_v1.py"
FUNDING_OWNER = CANONICAL_FUNDING_OWNER
PREFLIGHT_OWNER = CANONICAL_PREFLIGHT_OWNER

REASON_EVIDENCE_AMBIGUOUS = "EVIDENCE_AMBIGUOUS"
REASON_PARTIAL_TMP_MISSING = "PARTIAL_TMP_MISSING"
REASON_MEMBERSHIP_FILTER_EMPTY = "MEMBERSHIP_FILTER_EMPTY"
REASON_FUNDING_SCOPE_DRIFT = "FUNDING_SCOPE_DRIFT"
REASON_FETCH_GUARD_BLOCKED = "FETCH_GUARD_BLOCKED"


class OfflinePanelMaterializationVerdict(str, Enum):
    MATERIALIZED_PANEL_FUNDING_PREPARED_PREFLIGHT_COMPLETE = (
        "MATERIALIZED_PANEL_FUNDING_PREPARED_PREFLIGHT_COMPLETE"
    )
    FAIL_CLOSED_PARTIAL_TMP = "FAIL_CLOSED_PARTIAL_TMP"
    FAIL_CLOSED_PANEL_MATERIALIZATION = "FAIL_CLOSED_PANEL_MATERIALIZATION"
    FAIL_CLOSED_FUNDING_BINDING = "FAIL_CLOSED_FUNDING_BINDING"
    FAIL_CLOSED_PREFLIGHT = "FAIL_CLOSED_PREFLIGHT"


@dataclass(frozen=True)
class PartialTmpResolutionV0:
    partial_tmp_root: str
    resolved_from: str
    candidate_count: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class FundingBindingPrepResultV0:
    verdict: str
    staging_root: str
    panel_member_count: int
    funding_instrument_count: int
    skip_fetch: bool
    scope_drift: bool
    payload: dict[str, Any]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class OfflinePanelMaterializationScopeResultV0:
    verdict: OfflinePanelMaterializationVerdict
    partial_tmp_resolution: PartialTmpResolutionV0
    panel_materialization: BoundPeriodPanelSourceMaterializationResultV1 | None
    funding_binding: FundingBindingPrepResultV0 | None
    preflight_scope: MaterializationScopeResultV0 | None
    fetch_run: bool
    network_fetch_run: bool
    full_universe_fetch_run: bool
    materialization_run: bool
    preflight_no_fetch: bool
    economic_evaluation_run: bool
    reason_codes: tuple[str, ...]


def load_offline_panel_materialization_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return {
            "schema_version": MATERIALIZATION_VERSION,
            "partial_tmp_slug": DEFAULT_PARTIAL_TMP_SLUG,
            "partial_tmp_rel": DEFAULT_PARTIAL_TMP_REL,
            "output_staging_rel": DEFAULT_OUTPUT_STAGING_REL,
            "source_owner": SOURCE_OWNER,
            "funding_owner": FUNDING_OWNER,
            "preflight_owner": PREFLIGHT_OWNER,
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_partial_tmp_root_v0(
    durable_evidence_root: Path,
    *,
    explicit_partial_tmp_root: Path | None = None,
    partial_tmp_slug: str = DEFAULT_PARTIAL_TMP_SLUG,
) -> PartialTmpResolutionV0:
    """Resolve the durable-archive partial tmp root; fail-closed when ambiguous."""
    if explicit_partial_tmp_root is not None:
        resolved = explicit_partial_tmp_root.resolve()
        if not resolved.is_dir():
            return PartialTmpResolutionV0(
                partial_tmp_root=str(resolved),
                resolved_from="explicit_path",
                candidate_count=0,
                reason_codes=(REASON_PARTIAL_TMP_MISSING,),
            )
        return PartialTmpResolutionV0(
            partial_tmp_root=str(resolved),
            resolved_from="explicit_path",
            candidate_count=1,
            reason_codes=(),
        )

    dataset_parent = (
        durable_evidence_root / "datasets/admissible_futures/"
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
    )
    candidates = sorted(path for path in dataset_parent.glob(".tmp_historical_*") if path.is_dir())
    slug_matches = [path for path in candidates if path.name == partial_tmp_slug]
    if len(slug_matches) == 1:
        return PartialTmpResolutionV0(
            partial_tmp_root=str(slug_matches[0].resolve()),
            resolved_from="configured_slug",
            candidate_count=len(candidates),
            reason_codes=(),
        )
    if len(slug_matches) > 1:
        return PartialTmpResolutionV0(
            partial_tmp_root="",
            resolved_from="configured_slug",
            candidate_count=len(slug_matches),
            reason_codes=(REASON_EVIDENCE_AMBIGUOUS,),
        )
    if len(candidates) == 1:
        return PartialTmpResolutionV0(
            partial_tmp_root=str(candidates[0].resolve()),
            resolved_from="single_candidate",
            candidate_count=1,
            reason_codes=(),
        )
    return PartialTmpResolutionV0(
        partial_tmp_root="",
        resolved_from="discovery",
        candidate_count=len(candidates),
        reason_codes=(
            REASON_EVIDENCE_AMBIGUOUS if len(candidates) != 1 else REASON_PARTIAL_TMP_MISSING,
        ),
    )


def _output_staging_has_materialized_panel_v0(output_staging_root: Path) -> bool:
    panel_dir = output_staging_root / "panel"
    return (
        panel_dir.is_dir()
        and (panel_dir / "normalized_panel_bars.json").is_file()
        and (panel_dir / "panel_dataset_manifest.json").is_file()
    )


def materialize_offline_panel_from_partial_tmp_v0(
    partial_tmp_root: Path,
    output_staging_root: Path,
    *,
    period_binding: Mapping[str, Any] | None = None,
    min_instruments: int = MIN_ELIGIBLE_INSTRUMENTS,
) -> BoundPeriodPanelSourceMaterializationResultV1:
    """Materialize extended-chronological panel staging from partial-tmp raw (no fetch)."""
    partial_tmp_root = partial_tmp_root.resolve()
    output_staging_root = output_staging_root.resolve()
    period = dict(period_binding or build_period_binding_v0())
    period_start = PANEL_CALENDAR_START_UTC
    period_end = PANEL_CALENDAR_END_UTC

    if output_staging_root.exists() and any(output_staging_root.iterdir()):
        if _output_staging_has_materialized_panel_v0(output_staging_root):
            manifest = json.loads(
                (output_staging_root / "panel" / "panel_dataset_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            instrument_ids = manifest.get("instrument_ids")
            instrument_count = len(instrument_ids) if isinstance(instrument_ids, list) else 0
            return BoundPeriodPanelSourceMaterializationResultV1(
                status=BoundPeriodSourceMaterializationStatus.MATERIALIZED,
                output_staging_root=str(output_staging_root),
                source_staging_root=str(partial_tmp_root),
                period_start_utc=period_start,
                period_end_utc=period_end,
                instrument_count=instrument_count,
                row_count_total=int(manifest.get("row_count_total", 0)),
                data_start_time=str(manifest.get("data_start_time", "")),
                data_end_time=str(manifest.get("data_end_time", "")),
                source_provenance=(),
                reason_codes=(),
            )
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(partial_tmp_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=0,
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=(),
            reason_codes=(REASON_OUTPUT_EXISTS,),
        )

    raw_dir = partial_tmp_root / "raw"
    if not raw_dir.is_dir():
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(partial_tmp_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=0,
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=(),
            reason_codes=(REASON_MISSING_RAW_DIR,),
        )

    instruments = _load_instruments_snapshot(raw_dir)
    native_to_canonical: dict[str, str] = {}
    for inst in instruments:
        pair = _canonicalize_swap_instrument(inst)
        if pair is not None:
            native_to_canonical[pair[1]] = pair[0]

    provenance_entries: list[SourceProvenanceEntryV1] = []
    interim_series: dict[str, InstrumentPanelSeriesV1] = {}
    for native_id, raw_paths in group_raw_paths_by_native_instrument_v1(raw_dir).items():
        instrument_id = native_to_canonical.get(native_id)
        if instrument_id is None:
            continue
        merged_rows, merge_error = _load_merged_rows_for_instrument(raw_paths)
        if merge_error is not None:
            return BoundPeriodPanelSourceMaterializationResultV1(
                status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                output_staging_root=str(output_staging_root),
                source_staging_root=str(partial_tmp_root),
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
            all_bars,
            period_start_utc=period_start,
            period_end_utc=period_end,
        )
        if not bound_bars:
            continue
        source_files = ",".join(path.relative_to(partial_tmp_root).as_posix() for path in raw_paths)
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
        interim_series[instrument_id] = InstrumentPanelSeriesV1(
            instrument_id=instrument_id,
            native_instrument_id=native_id,
            bars=bound_bars,
            series_digest="0" * 64,
        )

    membership = filter_panel_series_to_full_bound_calendar_coverage_v1(
        tuple(interim_series[iid] for iid in sorted(interim_series)),
        period_start_utc=period_start,
        period_end_utc=period_end,
    )
    if len(membership.selected) < min_instruments:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(partial_tmp_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(membership.selected),
            row_count_total=0,
            data_start_time="",
            data_end_time="",
            source_provenance=tuple(provenance_entries),
            reason_codes=(
                REASON_MEMBERSHIP_FILTER_EMPTY,
                REASON_NO_ELIGIBLE_RAW_SERIES,
                REASON_BOUND_PERIOD_SOURCE_DATA_UNAVAILABLE,
            ),
        )

    panel_series = tuple(
        InstrumentPanelSeriesV1(
            instrument_id=series.instrument_id,
            native_instrument_id=series.native_instrument_id,
            bars=series.bars,
            series_digest=compute_series_digest(series),
        )
        for series in membership.selected
    )
    validation = validate_panel_series_v1(panel_series, min_instruments=min_instruments)
    if not validation.valid:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(partial_tmp_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(series.bars) for series in panel_series),
            data_start_time=panel_series[0].bars[0].timestamp_utc if panel_series else "",
            data_end_time=panel_series[0].bars[-1].timestamp_utc if panel_series else "",
            source_provenance=tuple(provenance_entries),
            reason_codes=(REASON_PANEL_VALIDATION_FAILED, *validation.error_codes),
        )

    covers, cover_reasons = verify_panel_covers_period_binding_v0(
        panel_series,
        period_binding=period,
    )
    if not covers:
        return BoundPeriodPanelSourceMaterializationResultV1(
            status=BoundPeriodSourceMaterializationStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            output_staging_root=str(output_staging_root),
            source_staging_root=str(partial_tmp_root),
            period_start_utc=period_start,
            period_end_utc=period_end,
            instrument_count=len(panel_series),
            row_count_total=sum(len(series.bars) for series in panel_series),
            data_start_time=panel_series[0].bars[0].timestamp_utc,
            data_end_time=panel_series[0].bars[-1].timestamp_utc,
            source_provenance=tuple(provenance_entries),
            reason_codes=cover_reasons,
        )

    output_staging_root.mkdir(parents=True, exist_ok=True)
    panel_dir = output_staging_root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    _copy_lifecycle_tree(partial_tmp_root, output_staging_root)

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

    selected_ids = {series.instrument_id for series in panel_series}
    selected_provenance = tuple(
        entry for entry in provenance_entries if entry.instrument_id in selected_ids
    )
    source_provenance_digest = _stable_digest(
        {
            "entries": [
                {
                    "source_file": entry.source_file,
                    "instrument_id": entry.instrument_id,
                    "row_count_bound": entry.row_count_bound,
                }
                for entry in selected_provenance
            ]
        }
    )
    lifecycle_ref = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
    lifecycle_digest = "0" * 64
    source_reg = partial_tmp_root / "lifecycle" / "SOURCE_REGISTRATION.json"
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
    manifest_dict["panel_id"] = RS_PANEL_DATASET_ID
    manifest_dict["dataset_version"] = PANEL_DATASET_VERSION
    manifest_dict["bar_granularity"] = BAR_GRANULARITY
    manifest_dict["dataset_extension"] = "extended_chronological_v1"

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
                "materialization_version": SOURCE_MATERIALIZATION_VERSION,
                "adapter_version": MATERIALIZATION_VERSION,
                "implementation_digest": compute_implementation_digest(),
                "source_staging_root": str(partial_tmp_root),
                "membership_filter": {
                    "period_start_utc": period_start,
                    "period_end_utc": period_end,
                    "candidate_count": len(interim_series),
                    "selected_count": len(panel_series),
                    "excluded_partial_count": membership.excluded_partial_count,
                    "filter_policy": "full_bound_panel_calendar_coverage_exact_timestamps",
                },
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
                    for entry in selected_provenance
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
        source_staging_root=str(partial_tmp_root),
        period_start_utc=period_start,
        period_end_utc=period_end,
        instrument_count=len(panel_series),
        row_count_total=sum(len(series.bars) for series in panel_series),
        data_start_time=data_start,
        data_end_time=data_end,
        source_provenance=selected_provenance,
        reason_codes=(),
    )


def prepare_funding_binding_for_panel_members_v0(
    staging_root: Path,
    *,
    confirm_go: str = INFRASTRUCTURE_GO_TOKEN,
    skip_fetch: bool = True,
) -> FundingBindingPrepResultV0:
    """Prepare funding binding for panel members only; never expands beyond manifest."""
    if not skip_fetch:
        return FundingBindingPrepResultV0(
            verdict="FETCH_GUARD_BLOCKED",
            staging_root=str(staging_root),
            panel_member_count=0,
            funding_instrument_count=0,
            skip_fetch=False,
            scope_drift=True,
            payload={},
            reason_codes=(REASON_FETCH_GUARD_BLOCKED,),
        )

    from scripts.ops import (
        materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 as funding_mod,
    )
    from scripts.ops import (
        materialize_cross_sectional_funding_rate_delta_momentum_v0_bound_panel_funding_dataset_v0 as rdm_funding_mod,
    )

    panel_series, _ = load_panel_series_from_staging(staging_root)
    panel_member_ids = tuple(sorted(series.instrument_id for series in panel_series))
    if not panel_member_ids:
        return FundingBindingPrepResultV0(
            verdict="FAIL_CLOSED_EMPTY_PANEL",
            staging_root=str(staging_root),
            panel_member_count=0,
            funding_instrument_count=0,
            skip_fetch=True,
            scope_drift=False,
            payload={},
            reason_codes=("EMPTY_PANEL_SERIES",),
        )

    funding_mod.CONFIRM_GO = confirm_go
    rdm_funding_mod.CONFIRM_GO = confirm_go
    payload = funding_mod.materialize_bound_panel_funding_dataset_v0(
        confirm=confirm_go,
        staging_root=staging_root,
        skip_fetch=True,
    )

    manifest_path = staging_root / "panel" / "panel_funding_dataset_manifest.json"
    funding_instrument_ids: tuple[str, ...] = ()
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["dataset_extension"] = "extended_chronological_with_funding_v1"
        manifest["panel_id"] = PANEL_DATASET_ID
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raw_ids = manifest.get("instrument_ids")
        if isinstance(raw_ids, list):
            funding_instrument_ids = tuple(sorted(str(item) for item in raw_ids))

    scope_drift = set(funding_instrument_ids) != set(panel_member_ids)
    reason_codes: list[str] = []
    if scope_drift:
        reason_codes.append(REASON_FUNDING_SCOPE_DRIFT)

    return FundingBindingPrepResultV0(
        verdict="FETCH_GUARD_BLOCKED" if scope_drift else str(payload.get("verdict", "UNKNOWN")),
        staging_root=str(staging_root),
        panel_member_count=len(panel_member_ids),
        funding_instrument_count=len(funding_instrument_ids),
        skip_fetch=True,
        scope_drift=scope_drift,
        payload=payload,
        reason_codes=tuple(reason_codes),
    )


def run_offline_panel_materialization_scope_v0(
    *,
    repo_root: Path,
    durable_evidence_root: Path,
    partial_tmp_root: Path | None = None,
    output_staging_root: Path | None = None,
    binding_origin_main_sha: str | None = None,
) -> OfflinePanelMaterializationScopeResultV0:
    """Run offline panel materialization, funding prep, and preflight (no fetch)."""
    config = load_offline_panel_materialization_config_v0(repo_root)
    resolution = resolve_partial_tmp_root_v0(
        durable_evidence_root,
        explicit_partial_tmp_root=partial_tmp_root,
        partial_tmp_slug=str(config.get("partial_tmp_slug", DEFAULT_PARTIAL_TMP_SLUG)),
    )
    if resolution.reason_codes:
        return OfflinePanelMaterializationScopeResultV0(
            verdict=OfflinePanelMaterializationVerdict.FAIL_CLOSED_PARTIAL_TMP,
            partial_tmp_resolution=resolution,
            panel_materialization=None,
            funding_binding=None,
            preflight_scope=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            materialization_run=False,
            preflight_no_fetch=True,
            economic_evaluation_run=False,
            reason_codes=resolution.reason_codes,
        )

    partial_root = Path(resolution.partial_tmp_root)
    output_root = output_staging_root or (
        durable_evidence_root / str(config.get("output_staging_rel", DEFAULT_OUTPUT_STAGING_REL))
    )

    panel_result = materialize_offline_panel_from_partial_tmp_v0(partial_root, output_root)
    materialization_run = panel_result.status is BoundPeriodSourceMaterializationStatus.MATERIALIZED
    if not materialization_run:
        return OfflinePanelMaterializationScopeResultV0(
            verdict=OfflinePanelMaterializationVerdict.FAIL_CLOSED_PANEL_MATERIALIZATION,
            partial_tmp_resolution=resolution,
            panel_materialization=panel_result,
            funding_binding=None,
            preflight_scope=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            materialization_run=False,
            preflight_no_fetch=True,
            economic_evaluation_run=False,
            reason_codes=panel_result.reason_codes,
        )

    funding_result = prepare_funding_binding_for_panel_members_v0(
        output_root,
        skip_fetch=True,
    )
    if funding_result.scope_drift:
        return OfflinePanelMaterializationScopeResultV0(
            verdict=OfflinePanelMaterializationVerdict.FAIL_CLOSED_FUNDING_BINDING,
            partial_tmp_resolution=resolution,
            panel_materialization=panel_result,
            funding_binding=funding_result,
            preflight_scope=None,
            fetch_run=False,
            network_fetch_run=False,
            full_universe_fetch_run=False,
            materialization_run=True,
            preflight_no_fetch=True,
            economic_evaluation_run=False,
            reason_codes=funding_result.reason_codes,
        )

    preflight_scope = run_materialization_scope_v0(
        repo_root=repo_root,
        staging_root=output_root,
        durable_evidence_root=durable_evidence_root,
        binding_origin_main_sha=binding_origin_main_sha,
        attempt_fetch=False,
    )

    if preflight_scope.ready_for_next_pre_evaluation_gate:
        verdict = OfflinePanelMaterializationVerdict.MATERIALIZED_PANEL_FUNDING_PREPARED_PREFLIGHT_COMPLETE
        reason_codes: tuple[str, ...] = ()
    else:
        verdict = OfflinePanelMaterializationVerdict.FAIL_CLOSED_PREFLIGHT
        reason_codes = tuple(
            dict.fromkeys((*funding_result.reason_codes, *preflight_scope.reason_codes))
        )

    return OfflinePanelMaterializationScopeResultV0(
        verdict=verdict,
        partial_tmp_resolution=resolution,
        panel_materialization=panel_result,
        funding_binding=funding_result,
        preflight_scope=preflight_scope,
        fetch_run=False,
        network_fetch_run=False,
        full_universe_fetch_run=False,
        materialization_run=True,
        preflight_no_fetch=True,
        economic_evaluation_run=False,
        reason_codes=reason_codes,
    )


def offline_panel_materialization_scope_result_to_dict(
    result: OfflinePanelMaterializationScopeResultV0,
) -> dict[str, Any]:
    return {
        "schema_version": MATERIALIZATION_VERSION,
        "verdict": result.verdict.value,
        "confirm_go": CONFIRM_GO,
        "package_marker": PACKAGE_MARKER,
        "partial_tmp_resolution": {
            "partial_tmp_root": result.partial_tmp_resolution.partial_tmp_root,
            "resolved_from": result.partial_tmp_resolution.resolved_from,
            "candidate_count": result.partial_tmp_resolution.candidate_count,
            "reason_codes": list(result.partial_tmp_resolution.reason_codes),
        },
        "panel_materialization": (
            bound_period_source_result_to_dict(result.panel_materialization)
            if result.panel_materialization is not None
            else None
        ),
        "funding_binding": (
            {
                "verdict": result.funding_binding.verdict,
                "staging_root": result.funding_binding.staging_root,
                "panel_member_count": result.funding_binding.panel_member_count,
                "funding_instrument_count": result.funding_binding.funding_instrument_count,
                "skip_fetch": result.funding_binding.skip_fetch,
                "scope_drift": result.funding_binding.scope_drift,
                "payload": result.funding_binding.payload,
                "reason_codes": list(result.funding_binding.reason_codes),
            }
            if result.funding_binding is not None
            else None
        ),
        "preflight_scope": (
            {
                "verdict": result.preflight_scope.verdict.value,
                "preflight_status": result.preflight_scope.preflight_status,
                "ready_for_next_pre_evaluation_gate": (
                    result.preflight_scope.ready_for_next_pre_evaluation_gate
                ),
                "reason_codes": list(result.preflight_scope.reason_codes),
            }
            if result.preflight_scope is not None
            else None
        ),
        "fetch_run": result.fetch_run,
        "network_fetch_run": result.network_fetch_run,
        "full_universe_fetch_run": result.full_universe_fetch_run,
        "materialization_run": result.materialization_run,
        "preflight_no_fetch": result.preflight_no_fetch,
        "economic_evaluation_run": result.economic_evaluation_run,
        "reason_codes": list(result.reason_codes),
        "reuse_decisions": {
            "source_owner": SOURCE_OWNER,
            "funding_owner": FUNDING_OWNER,
            "preflight_owner": PREFLIGHT_OWNER,
        },
    }


__all__ = [
    "CONFIRM_GO",
    "CONFIG_REL_PATH",
    "DEFAULT_DURABLE_ARCHIVE_ROOT",
    "DEFAULT_OUTPUT_STAGING_REL",
    "DEFAULT_PARTIAL_TMP_REL",
    "DEFAULT_PARTIAL_TMP_SLUG",
    "FUNDING_OWNER",
    "MATERIALIZATION_VERSION",
    "OfflinePanelMaterializationScopeResultV0",
    "OfflinePanelMaterializationVerdict",
    "PREFLIGHT_OWNER",
    "REASON_EVIDENCE_AMBIGUOUS",
    "REASON_FETCH_GUARD_BLOCKED",
    "REASON_FUNDING_SCOPE_DRIFT",
    "SOURCE_OWNER",
    "FundingBindingPrepResultV0",
    "PartialTmpResolutionV0",
    "load_offline_panel_materialization_config_v0",
    "materialize_offline_panel_from_partial_tmp_v0",
    "offline_panel_materialization_scope_result_to_dict",
    "prepare_funding_binding_for_panel_members_v0",
    "resolve_partial_tmp_root_v0",
    "run_offline_panel_materialization_scope_v0",
]
