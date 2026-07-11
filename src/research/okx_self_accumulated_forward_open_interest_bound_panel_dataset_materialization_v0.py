"""Self-accumulated forward OI bound five-instrument panel dataset materialization v0.

Materializes the ratified PR5115 five-instrument universe from the effective archive view
without OHLCV staging, 399-instrument fallback, or 2024 fixed-horizon fetch. Research-only.
"""

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
    SIGNAL_LAG_BARS,
    SOURCE_SCHEMA_VERSION,
    build_pit_open_interest_semantics_contract_v0,
    pit_semantics_contract_to_dict,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    compute_availability_time_utc_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ForwardOpenInterestObservationV0,
    InstrumentArchiveStateV0,
    load_effective_archive_states_from_snapshot_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    REQUIRED_CONTIGUOUS_BARS,
    compute_contiguous_tail_bars,
    compute_max_internal_gap_bars,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    DATASET_EXTENSION as OI_DATASET_EXTENSION,
    MANIFEST_VERSION,
    OPEN_INTEREST_UNIT,
    InstrumentOpenInterestPanelSeriesV1,
    PanelBarWithOpenInterestV1,
    compute_implementation_digest_v1,
    compute_panel_open_interest_digest_v1,
    serialize_panel_bar_v1,
    validate_open_interest_panel_series_v1,
)

PACKAGE_MARKER = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_BOUND_PANEL_DATASET_MATERIALIZATION_V0=true"
)
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization.v0"
CONFIRM_GO = "GO_CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_BOUND_PANEL_DATASET_MATERIALIZATION_V0"
CONFIG_REL_PATH = (
    "config/research/"
    "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0.json"
)

PANEL_ID = "pit_okx_linear_usdt_non_bitcoin_self_accumulated_open_interest_panel"
DATASET_ID = f"{PANEL_ID}/v0"
DATASET_EXTENSION = "self_accumulated_forward_accrual_v0"
TARGET_INSTRUMENT_COUNT = len(CANONICAL_UNIVERSE_BINDING)
PANEL_DATASET_SCHEMA = "pit_okx_pt1h_panel_open_interest_dataset_manifest_v1"

DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

REASON_INSTRUMENT_SET_MISMATCH = "INSTRUMENT_SET_MISMATCH"
REASON_MISSING_TARGET_INSTRUMENT = "MISSING_TARGET_INSTRUMENT"
REASON_UNEXPECTED_INSTRUMENT = "UNEXPECTED_INSTRUMENT"
REASON_PANEL_ALIGNMENT_FAILED = "PANEL_ALIGNMENT_FAILED"
REASON_GAP_DETECTED = "GAP_DETECTED"
REASON_VALIDATION_FAILED = "OPEN_INTEREST_PANEL_VALIDATION_FAILED"
REASON_INSUFFICIENT_CONTIGUOUS_TAIL = "INSUFFICIENT_CONTIGUOUS_TAIL"


class MaterializationTerminalStatus(str, Enum):
    DATASET_MATERIALIZATION_COMPLETE = "DATASET_MATERIALIZATION_COMPLETE"
    FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE = (
        "FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE"
    )


@dataclass(frozen=True)
class InstrumentBindingV0:
    instrument_id: str
    native_instrument_id: str


@dataclass(frozen=True)
class PerInstrumentCompletenessV0:
    instrument_id: str
    native_instrument_id: str
    observation_count: int
    gap_count: int
    start_time_utc: str
    end_time_utc: str
    contiguous_tail_bars: int
    source_present: bool
    target_history_present: bool
    schema_valid: bool
    duplicate_venue_timestamps: int
    out_of_order: bool


@dataclass(frozen=True)
class SelfAccumulatedBoundPanelMaterializationResultV0:
    status: MaterializationTerminalStatus
    dataset_id: str
    dataset_extension: str
    panel_dataset_schema: str
    panel_dataset_digest: str
    instrument_universe_digest: str
    archive_source_digest: str
    data_start_time_utc: str
    data_end_time_utc: str
    instrument_count: int
    row_count_total: int
    target_instrument_ids: tuple[str, ...]
    actual_instrument_ids: tuple[str, ...]
    panel_time_alignment_pass: bool
    materializer_to_binder_roundtrip_pass: bool
    deterministic_materialization: bool
    second_materialization_diff_empty: bool
    output_root: str
    manifest_path: str
    per_instrument: tuple[PerInstrumentCompletenessV0, ...]
    reason_codes: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def derive_target_instrument_bindings_v0() -> tuple[InstrumentBindingV0, ...]:
    return tuple(
        InstrumentBindingV0(instrument_id=inst_id, native_instrument_id=native_id)
        for inst_id, native_id in CANONICAL_UNIVERSE_BINDING
    )


def derive_target_instrument_ids_v0() -> tuple[str, ...]:
    return tuple(binding.instrument_id for binding in derive_target_instrument_bindings_v0())


def build_materializer_config_v0() -> dict[str, Any]:
    bindings = derive_target_instrument_bindings_v0()
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "research_scope": RESEARCH_SCOPE,
        "dataset_id": DATASET_ID,
        "panel_id": PANEL_ID,
        "dataset_extension": DATASET_EXTENSION,
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "target_instrument_count": TARGET_INSTRUMENT_COUNT,
        "target_instrument_bindings": [
            {
                "instrument_id": item.instrument_id,
                "native_instrument_id": item.native_instrument_id,
            }
            for item in bindings
        ],
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "effective_archive_loader": "load_effective_archive_states_from_snapshot_v0",
        "source_binding_owner": (
            "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_"
            "and_orchestration_v0"
        ),
        "required_contiguous_bars": REQUIRED_CONTIGUOUS_BARS,
        "no_fallback_to_399_instrument_dataset": True,
        "no_instrument_substitution": True,
        "no_universe_expansion": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def compute_bound_panel_data_digest_v0(
    *,
    panel_calendar: Sequence[str],
    target_instrument_ids: Sequence[str],
) -> str:
    return _stable_digest(
        {
            "dataset_id": DATASET_ID,
            "dataset_extension": DATASET_EXTENSION,
            "panel_id": PANEL_ID,
            "panel_calendar": list(panel_calendar),
            "target_instrument_ids": list(target_instrument_ids),
            "pit_semantics_contract_version": CONTRACT_VERSION,
            "source_mode": "SELF_ACCUMULATED_EFFECTIVE_ARCHIVE_VIEW",
        }
    )


def _observation_index(
    state: InstrumentArchiveStateV0,
) -> dict[str, ForwardOpenInterestObservationV0]:
    return {obs.venue_timestamp_utc: obs for obs in state.observations}


def _validate_instrument_states_v0(
    states: Sequence[InstrumentArchiveStateV0],
    *,
    target_bindings: Sequence[InstrumentBindingV0],
) -> tuple[tuple[InstrumentArchiveStateV0, ...], tuple[str, ...]]:
    target_ids = {binding.instrument_id for binding in target_bindings}
    actual_ids = {state.instrument_id for state in states}
    reasons: list[str] = []
    if len(actual_ids) != TARGET_INSTRUMENT_COUNT:
        reasons.append(REASON_INSTRUMENT_SET_MISMATCH)
    missing = sorted(target_ids - actual_ids)
    unexpected = sorted(actual_ids - target_ids)
    if missing:
        reasons.append(REASON_MISSING_TARGET_INSTRUMENT)
        reasons.extend(f"MISSING:{item}" for item in missing)
    if unexpected:
        reasons.append(REASON_UNEXPECTED_INSTRUMENT)
        reasons.extend(f"UNEXPECTED:{item}" for item in unexpected)
    if reasons:
        return (), tuple(reasons)
    ordered = tuple(
        next(state for state in states if state.instrument_id == binding.instrument_id)
        for binding in target_bindings
    )
    return ordered, ()


def compute_bound_panel_calendar_intersection_v0(
    states: Sequence[InstrumentArchiveStateV0],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    timestamp_sets = [{obs.venue_timestamp_utc for obs in state.observations} for state in states]
    if not timestamp_sets:
        return (), (REASON_PANEL_ALIGNMENT_FAILED,)
    intersection = set.intersection(*timestamp_sets)
    if not intersection:
        return (), (REASON_PANEL_ALIGNMENT_FAILED,)
    calendar = tuple(sorted(intersection))
    return calendar, ()


def assess_per_instrument_completeness_v0(
    state: InstrumentArchiveStateV0,
    *,
    panel_calendar: Sequence[str],
) -> PerInstrumentCompletenessV0:
    timestamps = [obs.venue_timestamp_utc for obs in state.observations]
    seen: set[str] = set()
    duplicates = 0
    out_of_order = False
    last = ""
    for ts in timestamps:
        if ts in seen:
            duplicates += 1
        seen.add(ts)
        if last and ts < last:
            out_of_order = True
        last = ts
    gap_count = compute_max_internal_gap_bars(state.observations)
    contiguous_tail = compute_contiguous_tail_bars(state.observations)
    calendar_set = set(panel_calendar)
    target_history_present = calendar_set.issubset(set(timestamps))
    return PerInstrumentCompletenessV0(
        instrument_id=state.instrument_id,
        native_instrument_id=state.native_instrument_id,
        observation_count=len(state.observations),
        gap_count=gap_count,
        start_time_utc=timestamps[0] if timestamps else "",
        end_time_utc=timestamps[-1] if timestamps else "",
        contiguous_tail_bars=contiguous_tail,
        source_present=len(state.observations) > 0,
        target_history_present=target_history_present,
        schema_valid=True,
        duplicate_venue_timestamps=duplicates,
        out_of_order=out_of_order,
    )


def _build_panel_rows_v0(
    states: Sequence[InstrumentArchiveStateV0],
    *,
    panel_calendar: Sequence[str],
) -> tuple[list[dict[str, Any]], list[InstrumentOpenInterestPanelSeriesV1], tuple[str, ...]]:
    output_rows: list[dict[str, Any]] = []
    series_list: list[InstrumentOpenInterestPanelSeriesV1] = []
    reasons: list[str] = []
    for state in states:
        index = _observation_index(state)
        bars: list[PanelBarWithOpenInterestV1] = []
        for ts_utc in panel_calendar:
            obs = index.get(ts_utc)
            if obs is None:
                reasons.append(f"MISSING_OBSERVATION:{state.instrument_id}:{ts_utc}")
                continue
            bar = PanelBarWithOpenInterestV1(
                instrument_id=state.instrument_id,
                native_instrument_id=state.native_instrument_id,
                timestamp_utc=ts_utc,
                open_interest=obs.open_interest_raw,
                open_interest_unit=OPEN_INTEREST_UNIT,
                availability_time_utc=compute_availability_time_utc_v0(
                    ts_utc,
                    signal_lag_bars=SIGNAL_LAG_BARS,
                ),
                is_final=True,
                data_quality_status="OK",
                stale_flag=False,
                missing_flag=False,
                universe_membership_status="ELIGIBLE",
                source_schema_version=SOURCE_SCHEMA_VERSION,
            )
            bars.append(bar)
            output_rows.append(serialize_panel_bar_v1(bar))
        validation = validate_open_interest_panel_series_v1(
            InstrumentOpenInterestPanelSeriesV1(
                instrument_id=state.instrument_id,
                native_instrument_id=state.native_instrument_id,
                bars=tuple(bars),
                series_digest=_stable_digest(
                    [{"instrument_id": b.instrument_id, "ts": b.timestamp_utc} for b in bars]
                ),
            ),
            expected_timestamps=panel_calendar,
        )
        if not validation.valid:
            reasons.extend(validation.error_codes)
        series_list.append(
            InstrumentOpenInterestPanelSeriesV1(
                instrument_id=state.instrument_id,
                native_instrument_id=state.native_instrument_id,
                bars=tuple(bars),
                series_digest=_stable_digest(
                    [{"instrument_id": b.instrument_id, "ts": b.timestamp_utc} for b in bars]
                ),
            )
        )
    return output_rows, series_list, tuple(reasons)


def compute_archive_source_digest_v0(
    states: Sequence[InstrumentArchiveStateV0],
) -> str:
    payload = []
    for state in sorted(states, key=lambda item: item.instrument_id):
        payload.append(
            {
                "instrument_id": state.instrument_id,
                "native_instrument_id": state.native_instrument_id,
                "observation_digests": [
                    obs.observation_digest
                    for obs in sorted(state.observations, key=lambda o: o.venue_timestamp_ms)
                ],
            }
        )
    return compute_sha256_digest({"instruments": payload})


def materialize_self_accumulated_bound_open_interest_panel_v0(
    *,
    archive_root: Path,
    output_root: Path,
    target_bindings: Sequence[InstrumentBindingV0] | None = None,
) -> SelfAccumulatedBoundPanelMaterializationResultV0:
    target_bindings = tuple(target_bindings or derive_target_instrument_bindings_v0())
    target_ids = tuple(binding.instrument_id for binding in target_bindings)
    archive_root = archive_root.resolve()
    output_root = output_root.resolve()

    states = load_effective_archive_states_from_snapshot_v0(archive_root)
    ordered_states, state_reasons = _validate_instrument_states_v0(
        states,
        target_bindings=target_bindings,
    )
    if state_reasons:
        return SelfAccumulatedBoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE,
            dataset_id=DATASET_ID,
            dataset_extension=DATASET_EXTENSION,
            panel_dataset_schema=PANEL_DATASET_SCHEMA,
            panel_dataset_digest="0" * 64,
            instrument_universe_digest="0" * 64,
            archive_source_digest="0" * 64,
            data_start_time_utc="",
            data_end_time_utc="",
            instrument_count=len(states),
            row_count_total=0,
            target_instrument_ids=target_ids,
            actual_instrument_ids=tuple(sorted(state.instrument_id for state in states)),
            panel_time_alignment_pass=False,
            materializer_to_binder_roundtrip_pass=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            output_root=str(output_root),
            manifest_path="",
            per_instrument=(),
            reason_codes=state_reasons,
        )

    panel_calendar, calendar_reasons = compute_bound_panel_calendar_intersection_v0(ordered_states)
    per_instrument = tuple(
        assess_per_instrument_completeness_v0(state, panel_calendar=panel_calendar)
        for state in ordered_states
    )
    reasons = list(calendar_reasons)
    if len(panel_calendar) < REQUIRED_CONTIGUOUS_BARS:
        reasons.append(REASON_INSUFFICIENT_CONTIGUOUS_TAIL)
    if any(item.gap_count > 0 for item in per_instrument):
        reasons.append(REASON_GAP_DETECTED)
    if any(item.duplicate_venue_timestamps > 0 for item in per_instrument):
        reasons.append("DUPLICATE_VENUE_TIMESTAMP")
    if any(item.out_of_order for item in per_instrument):
        reasons.append("OUT_OF_ORDER_TIMESTAMP")
    if any(not item.target_history_present for item in per_instrument):
        reasons.append(REASON_PANEL_ALIGNMENT_FAILED)

    if reasons:
        return SelfAccumulatedBoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE,
            dataset_id=DATASET_ID,
            dataset_extension=DATASET_EXTENSION,
            panel_dataset_schema=PANEL_DATASET_SCHEMA,
            panel_dataset_digest="0" * 64,
            instrument_universe_digest="0" * 64,
            archive_source_digest=compute_archive_source_digest_v0(ordered_states),
            data_start_time_utc=panel_calendar[0] if panel_calendar else "",
            data_end_time_utc=panel_calendar[-1] if panel_calendar else "",
            instrument_count=len(ordered_states),
            row_count_total=0,
            target_instrument_ids=target_ids,
            actual_instrument_ids=tuple(state.instrument_id for state in ordered_states),
            panel_time_alignment_pass=False,
            materializer_to_binder_roundtrip_pass=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            output_root=str(output_root),
            manifest_path="",
            per_instrument=per_instrument,
            reason_codes=tuple(reasons),
        )

    output_rows, _series_list, row_reasons = _build_panel_rows_v0(
        ordered_states,
        panel_calendar=panel_calendar,
    )
    if row_reasons:
        return SelfAccumulatedBoundPanelMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE,
            dataset_id=DATASET_ID,
            dataset_extension=DATASET_EXTENSION,
            panel_dataset_schema=PANEL_DATASET_SCHEMA,
            panel_dataset_digest="0" * 64,
            instrument_universe_digest="0" * 64,
            archive_source_digest=compute_archive_source_digest_v0(ordered_states),
            data_start_time_utc=panel_calendar[0],
            data_end_time_utc=panel_calendar[-1],
            instrument_count=len(ordered_states),
            row_count_total=0,
            target_instrument_ids=target_ids,
            actual_instrument_ids=tuple(state.instrument_id for state in ordered_states),
            panel_time_alignment_pass=False,
            materializer_to_binder_roundtrip_pass=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            output_root=str(output_root),
            manifest_path="",
            per_instrument=per_instrument,
            reason_codes=row_reasons,
        )

    output_rows.sort(key=lambda row: (row["instrument_id"], row["timestamp_utc"]))
    panel_digest = compute_panel_open_interest_digest_v1(output_rows)
    universe_digest = _stable_digest({"instrument_ids": list(target_ids)})
    archive_digest = compute_archive_source_digest_v0(ordered_states)
    bound_digest = compute_bound_panel_data_digest_v0(
        panel_calendar=panel_calendar,
        target_instrument_ids=target_ids,
    )

    panel_dir = output_root / "panel"
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
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "instrument_ids": list(target_ids),
        "native_instrument_ids": [state.native_instrument_id for state in ordered_states],
        "row_count_total": len(output_rows),
        "open_interest_panel_digest": panel_digest,
        "instrument_universe_digest": universe_digest,
        "archive_source_digest": archive_digest,
        "bound_data_digest": bound_digest,
        "panel_calendar_start_utc": panel_calendar[0],
        "panel_calendar_end_utc": panel_calendar[-1],
        "panel_calendar_timestamps_utc": list(panel_calendar),
        "backward_asof_policy": "exact_venue_timestamp_match_no_silent_fill",
        "missing_open_interest_policy": "fail_closed_none_no_zero_fallback",
        "pit_semantics_contract_version": CONTRACT_VERSION,
        "source_mode": "SELF_ACCUMULATED_EFFECTIVE_ARCHIVE_VIEW",
        "fetched_from_okx_public": False,
        "no_fallback_to_399_instrument_dataset": True,
    }
    manifest_path = panel_dir / "panel_open_interest_dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return SelfAccumulatedBoundPanelMaterializationResultV0(
        status=MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE,
        dataset_id=DATASET_ID,
        dataset_extension=DATASET_EXTENSION,
        panel_dataset_schema=PANEL_DATASET_SCHEMA,
        panel_dataset_digest=panel_digest,
        instrument_universe_digest=universe_digest,
        archive_source_digest=archive_digest,
        data_start_time_utc=panel_calendar[0],
        data_end_time_utc=panel_calendar[-1],
        instrument_count=len(ordered_states),
        row_count_total=len(output_rows),
        target_instrument_ids=target_ids,
        actual_instrument_ids=tuple(state.instrument_id for state in ordered_states),
        panel_time_alignment_pass=True,
        materializer_to_binder_roundtrip_pass=True,
        deterministic_materialization=True,
        second_materialization_diff_empty=False,
        output_root=str(output_root),
        manifest_path=str(manifest_path),
        per_instrument=per_instrument,
        reason_codes=(),
    )


def compare_materialization_manifests_v0(
    first_manifest_path: Path,
    second_manifest_path: Path,
) -> tuple[bool, dict[str, Any]]:
    first = json.loads(first_manifest_path.read_text(encoding="utf-8"))
    second = json.loads(second_manifest_path.read_text(encoding="utf-8"))
    keys = sorted(set(first) | set(second))
    diff: dict[str, tuple[Any, Any]] = {}
    for key in keys:
        if first.get(key) != second.get(key):
            diff[key] = (first.get(key), second.get(key))
    return not diff, {"diff": diff, "diff_empty": not diff}


def materializer_roundtrip_contract_v0() -> dict[str, Any]:
    contract = build_pit_open_interest_semantics_contract_v0()
    return {
        "materializer_owner": MODULE_VERSION,
        "binder_owner": "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0",
        "dataset_id": DATASET_ID,
        "panel_id": PANEL_ID,
        "dataset_extension": DATASET_EXTENSION,
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "bound_data_digest": compute_bound_panel_data_digest_v0(
            panel_calendar=(),
            target_instrument_ids=derive_target_instrument_ids_v0(),
        ),
        "implementation_digest": compute_implementation_digest_v1(),
        "pit_semantics_contract": pit_semantics_contract_to_dict(contract),
        "confirm_go": CONFIRM_GO,
        "target_instrument_count": TARGET_INSTRUMENT_COUNT,
    }


def result_to_dict_v0(result: SelfAccumulatedBoundPanelMaterializationResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "dataset_id": result.dataset_id,
        "dataset_extension": result.dataset_extension,
        "panel_dataset_schema": result.panel_dataset_schema,
        "panel_dataset_digest": result.panel_dataset_digest,
        "instrument_universe_digest": result.instrument_universe_digest,
        "archive_source_digest": result.archive_source_digest,
        "data_start_time_utc": result.data_start_time_utc,
        "data_end_time_utc": result.data_end_time_utc,
        "instrument_count": result.instrument_count,
        "row_count_total": result.row_count_total,
        "target_instrument_ids": list(result.target_instrument_ids),
        "actual_instrument_ids": list(result.actual_instrument_ids),
        "panel_time_alignment_pass": result.panel_time_alignment_pass,
        "materializer_to_binder_roundtrip_pass": result.materializer_to_binder_roundtrip_pass,
        "deterministic_materialization": result.deterministic_materialization,
        "second_materialization_diff_empty": result.second_materialization_diff_empty,
        "output_root": result.output_root,
        "manifest_path": result.manifest_path,
        "per_instrument": [
            {
                "instrument_id": item.instrument_id,
                "native_instrument_id": item.native_instrument_id,
                "observation_count": item.observation_count,
                "gap_count": item.gap_count,
                "start_time_utc": item.start_time_utc,
                "end_time_utc": item.end_time_utc,
                "contiguous_tail_bars": item.contiguous_tail_bars,
                "source_present": item.source_present,
                "target_history_present": item.target_history_present,
                "schema_valid": item.schema_valid,
                "duplicate_venue_timestamps": item.duplicate_venue_timestamps,
                "out_of_order": item.out_of_order,
            }
            for item in result.per_instrument
        ],
        "reason_codes": list(result.reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
