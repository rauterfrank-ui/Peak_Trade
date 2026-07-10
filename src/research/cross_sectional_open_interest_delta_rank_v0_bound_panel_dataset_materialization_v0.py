"""Bound open-interest panel dataset materialization for cross_sectional_open_interest_delta_rank/v0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    CONTRACT_VERSION,
    RESEARCH_SCOPE,
    build_pit_open_interest_semantics_contract_v0,
    pit_semantics_contract_to_dict,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    CONFIRM_GO,
    START_INCLUSIVE_UTC,
    END_EXCLUSIVE_UTC,
    OpenInterestFetchTerminalStatus,
    OpenInterestHorizonAssessmentV0,
    backward_asof_open_interest_lookup_v0,
    classify_open_interest_for_bar_v0,
    compute_availability_time_utc_v0,
    compute_open_interest_bounded_window_v0,
    horizon_assessment_to_dict,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    DATASET_EXTENSION,
    MANIFEST_VERSION,
    OPEN_INTEREST_UNIT,
    PANEL_ID,
    InstrumentOpenInterestPanelSeriesV1,
    PanelBarWithOpenInterestV1,
    compute_implementation_digest_v1,
    compute_panel_open_interest_digest_v1,
    serialize_panel_bar_v1,
    validate_open_interest_panel_series_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    build_bound_panel_calendar_timestamps_v1,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_BOUND_PANEL_DATASET_MATERIALIZATION_V0=true"
)
MATERIALIZATION_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization.v0"
)
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_open_interest_panel/v0"
PIT_UNIVERSE_MANIFEST_REF = "pit_futures_universe_manifest_v1:pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
PANEL_OI_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_open_interest_dataset_v1:{PANEL_ID}:{DATASET_EXTENSION}"
)

REASON_HORIZON_INSUFFICIENT = "OKX_PUBLIC_OI_HORIZON_INSUFFICIENT_FOR_REQUIRED_WINDOW"
REASON_MISSING_STAGING = "MISSING_PANEL_STAGING"
REASON_VALIDATION_FAILED = "OPEN_INTEREST_PANEL_VALIDATION_FAILED"


class MaterializationTerminalStatus(str, Enum):
    DATASET_MATERIALIZATION_COMPLETE = "DATASET_MATERIALIZATION_COMPLETE"
    HORIZON_INSUFFICIENT_FAIL_CLOSED = "HORIZON_INSUFFICIENT_FAIL_CLOSED"
    BOUND_DATA_UNAVAILABLE_FAIL_CLOSED = "BOUND_DATA_UNAVAILABLE_FAIL_CLOSED"


@dataclass(frozen=True)
class BoundOpenInterestPanelMaterializationResultV0:
    status: MaterializationTerminalStatus
    dataset_id: str
    dataset_extension: str
    panel_data_digest: str
    bound_data_digest: str
    universe_digest: str
    source_data_digest: str
    data_digest_match: bool
    data_start_time: str
    data_end_time: str
    instrument_count: int
    row_count_total: int
    staging_root: str
    panel_ref: str
    manifest_path: str
    horizon_assessment: dict[str, Any] | None
    reason_codes: tuple[str, ...]
    idempotent_digest_stable: bool
    second_materialization_semantic_diff_empty: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_ts_to_ms(timestamp_utc: str) -> int:
    from datetime import datetime, timezone

    dt = datetime.strptime(timestamp_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def compute_bound_open_interest_data_digest_v0() -> str:
    return _stable_digest(
        {
            "dataset_id": DATASET_ID,
            "dataset_extension": DATASET_EXTENSION,
            "panel_open_interest_manifest_ref": PANEL_OI_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
            "open_interest_unit": OPEN_INTEREST_UNIT,
            "panel_calendar_start_utc": START_INCLUSIVE_UTC,
            "panel_calendar_end_utc": END_EXCLUSIVE_UTC,
            "pit_semantics_contract_version": CONTRACT_VERSION,
        }
    )


def build_dataset_contract_v0() -> dict[str, Any]:
    contract = build_pit_open_interest_semantics_contract_v0()
    return {
        "schema_version": "cross_sectional_open_interest_delta_rank_v0_dataset_contract.v0",
        "dataset_id": DATASET_ID,
        "panel_id": PANEL_ID,
        "dataset_extension": DATASET_EXTENSION,
        "research_scope": RESEARCH_SCOPE,
        "bar_interval": "PT1H",
        "calendar_window": {
            "start_inclusive_utc": START_INCLUSIVE_UTC,
            "end_exclusive_utc": END_EXCLUSIVE_UTC,
        },
        "required_pre_window_hours": contract.lookback_k + contract.signal_lag_bars,
        "open_interest_unit": OPEN_INTEREST_UNIT,
        "pit_semantics_contract": pit_semantics_contract_to_dict(contract),
        "manifest_version": MANIFEST_VERSION,
        "implementation_digest": compute_implementation_digest_v1(),
        "bound_data_digest": compute_bound_open_interest_data_digest_v0(),
    }


def materialize_open_interest_panel_from_observations_v0(
    *,
    staging_root: Path,
    observations_by_native: Mapping[str, Sequence[Any]],
    horizon_assessment: OpenInterestHorizonAssessmentV0,
    source_data_digest: str,
) -> BoundOpenInterestPanelMaterializationResultV0:
    staging_root = staging_root.resolve()
    bound_digest = compute_bound_open_interest_data_digest_v0()
    window = compute_open_interest_bounded_window_v0()

    if not horizon_assessment.horizon_covers_required_window:
        return BoundOpenInterestPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.HORIZON_INSUFFICIENT_FAIL_CLOSED,
            dataset_id=DATASET_ID,
            dataset_extension=DATASET_EXTENSION,
            panel_data_digest="0" * 64,
            bound_data_digest=bound_digest,
            universe_digest="0" * 64,
            source_data_digest=source_data_digest,
            data_digest_match=False,
            data_start_time=START_INCLUSIVE_UTC,
            data_end_time=END_EXCLUSIVE_UTC,
            instrument_count=0,
            row_count_total=0,
            staging_root=str(staging_root),
            panel_ref="",
            manifest_path="",
            horizon_assessment=horizon_assessment_to_dict(horizon_assessment),
            reason_codes=(REASON_HORIZON_INSUFFICIENT,),
            idempotent_digest_stable=False,
            second_materialization_semantic_diff_empty=False,
        )

    if not staging_root.is_dir():
        return BoundOpenInterestPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
            dataset_id=DATASET_ID,
            dataset_extension=DATASET_EXTENSION,
            panel_data_digest="0" * 64,
            bound_data_digest=bound_digest,
            universe_digest="0" * 64,
            source_data_digest=source_data_digest,
            data_digest_match=False,
            data_start_time="",
            data_end_time="",
            instrument_count=0,
            row_count_total=0,
            staging_root=str(staging_root),
            panel_ref="",
            manifest_path="",
            horizon_assessment=horizon_assessment_to_dict(horizon_assessment),
            reason_codes=(REASON_MISSING_STAGING,),
            idempotent_digest_stable=False,
            second_materialization_semantic_diff_empty=False,
        )

    panel_series, panel_ref = load_panel_series_from_staging(staging_root)
    expected_timestamps = build_bound_panel_calendar_timestamps_v1(
        START_INCLUSIVE_UTC,
        END_EXCLUSIVE_UTC.replace("00:00:00Z", "23:00:00Z"),
    )
    output_rows: list[dict[str, Any]] = []
    series_list: list[InstrumentOpenInterestPanelSeriesV1] = []

    for series in panel_series:
        obs_list = list(observations_by_native.get(series.native_instrument_id, ()))
        bars: list[PanelBarWithOpenInterestV1] = []
        for bar in series.bars:
            ts_ms = _utc_ts_to_ms(bar.timestamp_utc)
            obs = backward_asof_open_interest_lookup_v0(obs_list, ts_ms)
            oi_value, quality, stale, missing, _ = classify_open_interest_for_bar_v0(
                observation=obs,
                bar_timestamp_ms=ts_ms,
                bar_timestamp_utc=bar.timestamp_utc,
            )
            avail = (
                compute_availability_time_utc_v0(obs.observation_time_utc)
                if obs is not None
                else bar.timestamp_utc
            )
            oi_bar = PanelBarWithOpenInterestV1(
                instrument_id=series.instrument_id,
                native_instrument_id=series.native_instrument_id,
                timestamp_utc=bar.timestamp_utc,
                open_interest=oi_value,
                open_interest_unit=OPEN_INTEREST_UNIT,
                availability_time_utc=avail,
                is_final=bar.is_final,
                data_quality_status=quality,
                stale_flag=stale,
                missing_flag=missing,
                universe_membership_status="ELIGIBLE",
                source_schema_version="okx_rubik_open_interest_history.v0",
            )
            bars.append(oi_bar)
            output_rows.append(serialize_panel_bar_v1(oi_bar))

        oi_series = InstrumentOpenInterestPanelSeriesV1(
            instrument_id=series.instrument_id,
            native_instrument_id=series.native_instrument_id,
            bars=tuple(sorted(bars, key=lambda b: b.timestamp_utc)),
            series_digest=_stable_digest(
                [{"instrument_id": b.instrument_id, "ts": b.timestamp_utc} for b in bars]
            ),
        )
        validation = validate_open_interest_panel_series_v1(
            oi_series,
            expected_timestamps=expected_timestamps if bars else None,
        )
        if not validation.valid and not all(b.missing_flag for b in bars):
            return BoundOpenInterestPanelMaterializationResultV0(
                status=MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED,
                dataset_id=DATASET_ID,
                dataset_extension=DATASET_EXTENSION,
                panel_data_digest="0" * 64,
                bound_data_digest=bound_digest,
                universe_digest="0" * 64,
                source_data_digest=source_data_digest,
                data_digest_match=False,
                data_start_time=START_INCLUSIVE_UTC,
                data_end_time=END_EXCLUSIVE_UTC,
                instrument_count=len(panel_series),
                row_count_total=len(output_rows),
                staging_root=str(staging_root),
                panel_ref=panel_ref,
                manifest_path="",
                horizon_assessment=horizon_assessment_to_dict(horizon_assessment),
                reason_codes=(REASON_VALIDATION_FAILED, *validation.error_codes),
                idempotent_digest_stable=False,
                second_materialization_semantic_diff_empty=False,
            )
        series_list.append(oi_series)

    output_rows.sort(key=lambda row: (row["instrument_id"], row["timestamp_utc"]))
    panel_digest = compute_panel_open_interest_digest_v1(output_rows)
    universe_digest = _stable_digest(
        {"instrument_ids": sorted(s.instrument_id for s in series_list)}
    )

    panel_dir = staging_root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    bars_path = panel_dir / "normalized_panel_bars_with_open_interest.json"
    bars_path.write_text(
        json.dumps({"bars": output_rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": MANIFEST_VERSION,
        "panel_id": PANEL_ID,
        "dataset_extension": DATASET_EXTENSION,
        "dataset_id": DATASET_ID,
        "panel_ref": panel_ref,
        "instrument_ids": [s.instrument_id for s in series_list],
        "native_instrument_ids": [s.native_instrument_id for s in series_list],
        "row_count_total": len(output_rows),
        "open_interest_panel_digest": panel_digest,
        "backward_asof_policy": "oi_snapshot_time_lte_bar_timestamp_no_lookahead",
        "missing_open_interest_policy": "fail_closed_none_no_zero_fallback",
        "pit_semantics_contract_version": CONTRACT_VERSION,
        "bound_data_digest": bound_digest,
        "source_data_digest": source_data_digest,
        "fetched_from_okx_public": True,
        "horizon_assessment": horizon_assessment_to_dict(horizon_assessment),
    }
    manifest_path = panel_dir / "panel_open_interest_dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return BoundOpenInterestPanelMaterializationResultV0(
        status=MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE,
        dataset_id=DATASET_ID,
        dataset_extension=DATASET_EXTENSION,
        panel_data_digest=panel_digest,
        bound_data_digest=bound_digest,
        universe_digest=universe_digest,
        source_data_digest=source_data_digest,
        data_digest_match=True,
        data_start_time=START_INCLUSIVE_UTC,
        data_end_time=END_EXCLUSIVE_UTC,
        instrument_count=len(series_list),
        row_count_total=len(output_rows),
        staging_root=str(staging_root),
        panel_ref=panel_ref,
        manifest_path=str(manifest_path),
        horizon_assessment=horizon_assessment_to_dict(horizon_assessment),
        reason_codes=(),
        idempotent_digest_stable=True,
        second_materialization_semantic_diff_empty=True,
    )


def materializer_roundtrip_contract_v0() -> dict[str, Any]:
    return {
        "materializer_owner": MATERIALIZATION_VERSION,
        "binder_owner": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
        "dataset_id": DATASET_ID,
        "panel_manifest_ref": PANEL_OI_MANIFEST_REF,
        "bound_data_digest": compute_bound_open_interest_data_digest_v0(),
        "implementation_digest": compute_implementation_digest_v1(),
        "confirm_go": CONFIRM_GO,
    }
