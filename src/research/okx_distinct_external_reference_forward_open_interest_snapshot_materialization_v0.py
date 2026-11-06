"""Distinct external reference forward OI snapshot materialization v0.

Bounded public OKX rubik open-interest-history fetch materialized into a physically
separate observations.jsonl snapshot for overlap validation. Reuses historical fetch
and archive observation serialization owners. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
    OpenInterestBoundedWindowV0,
    OpenInterestFetchBudgetGuardV0,
    compute_open_interest_bounded_window_v0,
    deduplicate_open_interest_observations_v0,
    paginate_bounded_open_interest_v0,
    parse_okx_open_interest_history_row_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_SCHEMA_VERSION,
    COLLECTION_MODE_FORWARD_ONLY,
    OBSERVATIONS_JSONL_FILENAME,
    ForwardOpenInterestObservationV0,
    observation_from_normalized_v0,
    observation_from_row_dict_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    validate_instrument_for_forward_archive_v0,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = (
    "OKX_DISTINCT_EXTERNAL_REFERENCE_FORWARD_OPEN_INTEREST_SNAPSHOT_MATERIALIZATION_V0=true"
)
MODULE_VERSION = "okx_distinct_external_reference_forward_open_interest_snapshot_materialization.v0"
CONFIRM_GO = (
    "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_DISTINCT_EXTERNAL_REFERENCE_"
    "BOUNDED_ACQUISITION_AND_OFFLINE_MATERIALIZATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0.json"
)
DATASET_ID = "okx_distinct_external_reference_forward_open_interest_snapshot_v0"
PROVENANCE_FILENAME = "provenance.json"
DATASET_MANIFEST_FILENAME = "dataset_manifest.json"
ACQUISITION_REPORT_FILENAME = "acquisition_report.json"
MANIFEST_SHA256_FILENAME = "MANIFEST.sha256"
RAW_FETCH_DIRNAME = "raw_fetch"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class MaterializationTerminalStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FAIL_CLOSED_OPERATOR_GO = "FAIL_CLOSED_OPERATOR_GO"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_INELIGIBLE_INSTRUMENT = "FAIL_CLOSED_INELIGIBLE_INSTRUMENT"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_EMPTY_OUTPUT = "FAIL_CLOSED_EMPTY_OUTPUT"
    FAIL_CLOSED_NO_OVERLAP = "FAIL_CLOSED_NO_OVERLAP"
    FAIL_CLOSED_SELF_ARCHIVE_MUTATION = "FAIL_CLOSED_SELF_ARCHIVE_MUTATION"
    FAIL_CLOSED_NOT_DISTINCT = "FAIL_CLOSED_NOT_DISTINCT"
    FAIL_CLOSED_RAW_REMATERIALIZATION = "FAIL_CLOSED_RAW_REMATERIALIZATION"


@dataclass(frozen=True)
class SelfArchiveOverlapWindowV0:
    instrument_id: str
    native_instrument_id: str
    fetch_start_inclusive_utc: str
    fetch_end_exclusive_utc: str
    self_venue_timestamp_ms: tuple[int, ...]
    self_observation_count: int


@dataclass(frozen=True)
class DistinctExternalReferenceMaterializationResultV0:
    status: MaterializationTerminalStatus
    dataset_id: str
    output_dir: str
    external_reference_input: str
    instrument_id: str | None
    native_instrument_id: str | None
    fetch_window_start_utc: str | None
    fetch_window_end_utc: str | None
    raw_record_count: int
    materialized_observation_count: int
    exact_overlap_candidate_count: int
    output_schema: str
    distinct_from_self_archive: bool
    deterministic_materialization: bool
    second_materialization_diff_empty: bool
    self_archive_mutation: bool
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_materializer_config_v0() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / CONFIG_REL_PATH
    return json.loads(config_path.read_text(encoding="utf-8"))


def compute_implementation_digest_v0() -> str:
    return compute_sha256_digest(
        {
            "module": "okx_distinct_external_reference_forward_open_interest_snapshot_materialization_v0",
            "module_version": MODULE_VERSION,
            "confirm_go": CONFIRM_GO,
            "dataset_id": DATASET_ID,
            "output_schema_version": ARCHIVE_SCHEMA_VERSION,
        }
    )


def _resolve_jsonl_path(source: Path) -> Path | None:
    if source.is_file() and source.name.endswith(".jsonl"):
        return source
    if source.is_dir():
        candidate = source / OBSERVATIONS_JSONL_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_self_archive_overlap_window_v0(self_archive_source: Path) -> SelfArchiveOverlapWindowV0:
    jsonl_path = _resolve_jsonl_path(self_archive_source)
    if jsonl_path is None:
        raise ValueError("MISSING_SELF_ACCUMULATED_OBSERVATIONS_JSONL")
    venue_ms_values: list[int] = []
    instrument_id: str | None = None
    native_instrument_id: str | None = None
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        obs, reason = observation_from_row_dict_v0(row)
        if obs is None:
            raise ValueError(reason or "INVALID_SELF_ARCHIVE_ROW")
        if instrument_id is None:
            instrument_id = obs.instrument_id
            native_instrument_id = obs.native_instrument_id
        if obs.instrument_id != instrument_id:
            raise ValueError("MULTIPLE_INSTRUMENTS_IN_SELF_ARCHIVE")
        venue_ms_values.append(obs.venue_timestamp_ms)
    if not venue_ms_values or instrument_id is None or native_instrument_id is None:
        raise ValueError("EMPTY_SELF_ARCHIVE")
    venue_ms_values.sort()
    start_ms = venue_ms_values[0]
    end_ms = venue_ms_values[-1] + 3_600_000
    return SelfArchiveOverlapWindowV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        fetch_start_inclusive_utc=_format_utc_ms(start_ms),
        fetch_end_exclusive_utc=_format_utc_ms(end_ms),
        self_venue_timestamp_ms=tuple(venue_ms_values),
        self_observation_count=len(venue_ms_values),
    )


def compute_fetch_window_v0(overlap: SelfArchiveOverlapWindowV0) -> OpenInterestBoundedWindowV0:
    return compute_open_interest_bounded_window_v0(
        start_inclusive_utc=overlap.fetch_start_inclusive_utc,
        end_exclusive_utc=overlap.fetch_end_exclusive_utc,
        lookback_k=0,
        signal_lag_bars=0,
    )


def build_fetch_budget_v0(config: Mapping[str, Any]) -> OpenInterestFetchBudgetGuardV0:
    return OpenInterestFetchBudgetGuardV0(
        max_instruments=int(config["max_instruments"]),
        max_pages_per_instrument=int(config["max_pages_per_instrument"]),
        max_total_requests=int(config["max_total_requests"]),
        max_total_raw_bytes=int(config["max_total_raw_bytes"]),
        max_runtime_seconds=int(config["max_runtime_seconds"]),
    )


def normalize_fetched_observations_v0(
    normalized_rows: Sequence[NormalizedOpenInterestObservationV0],
    *,
    collected_at_utc: str,
) -> list[ForwardOpenInterestObservationV0]:
    observations: list[ForwardOpenInterestObservationV0] = []
    for row in normalized_rows:
        obs = observation_from_normalized_v0(
            row,
            collected_at_utc=collected_at_utc,
            collection_mode=COLLECTION_MODE_FORWARD_ONLY,
        )
        if obs is not None:
            observations.append(obs)
    observations.sort(key=lambda item: item.venue_timestamp_ms)
    return observations


def parse_raw_fetch_payloads_v0(raw_dir: Path) -> list[NormalizedOpenInterestObservationV0]:
    if not raw_dir.is_dir():
        return []
    all_obs: list[NormalizedOpenInterestObservationV0] = []
    for path in sorted(raw_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, list) or not row:
                continue
            parsed = parse_okx_open_interest_history_row_v0(
                row,
                instrument_id="",
                native_instrument_id="",
            )
            if parsed is not None:
                all_obs.append(parsed)
    return list(deduplicate_open_interest_observations_v0(all_obs))


def load_raw_fetch_observations_v0(
    raw_dir: Path,
    *,
    instrument_id: str,
    native_instrument_id: str,
    window: OpenInterestBoundedWindowV0,
) -> list[NormalizedOpenInterestObservationV0]:
    parsed = parse_raw_fetch_payloads_v0(raw_dir)
    filtered: list[NormalizedOpenInterestObservationV0] = []
    for obs in parsed:
        if not (window.oi_fetch_start_ms <= obs.observation_time_ms < window.end_exclusive_ms):
            continue
        filtered.append(
            NormalizedOpenInterestObservationV0(
                instrument_id=instrument_id,
                native_instrument_id=native_instrument_id,
                observation_time_ms=obs.observation_time_ms,
                observation_time_utc=obs.observation_time_utc,
                open_interest_raw=obs.open_interest_raw,
                open_interest_unit=obs.open_interest_unit,
                source_schema_version=obs.source_schema_version,
                source_record_key=f"{native_instrument_id}:{obs.observation_time_ms}",
            )
        )
    return list(deduplicate_open_interest_observations_v0(filtered))


def count_exact_overlap_candidates_v0(
    observations: Sequence[ForwardOpenInterestObservationV0],
    *,
    self_venue_timestamp_ms: Sequence[int],
) -> int:
    external_ts = {obs.venue_timestamp_ms for obs in observations}
    return sum(1 for ts in self_venue_timestamp_ms if ts in external_ts)


def write_observations_jsonl_v0(
    observations: Sequence[ForwardOpenInterestObservationV0],
    *,
    output_path: Path,
) -> str:
    rows = [serialize_observation_v0(obs) for obs in observations]
    rows.sort(key=lambda item: (item["instrument_id"], item["venue_timestamp_ms"]))
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(serialize_canonical_json(row) + "\n")
    return compute_sha256_digest({"rows": rows})


def write_bundle_manifest_sha256_v0(bundle_dir: Path) -> None:
    entries: list[str] = []
    for path in sorted(bundle_dir.iterdir()):
        if path.name == MANIFEST_SHA256_FILENAME:
            continue
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{digest}  {path.name}")
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    rel = child.relative_to(bundle_dir).as_posix()
                    digest = hashlib.sha256(child.read_bytes()).hexdigest()
                    entries.append(f"{digest}  {rel}")
    (bundle_dir / MANIFEST_SHA256_FILENAME).write_text("\n".join(entries) + "\n", encoding="utf-8")


def materialize_distinct_external_reference_snapshot_v0(
    *,
    confirm: str,
    instrument: Mapping[str, Any],
    self_archive_source: Path,
    output_dir: Path,
    collected_at_utc: str,
    enabled: bool = False,
    fetcher: PublicGetFetcher | None = None,
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]] | None = None,
    build_url: Callable[[str, dict[str, str]], str] | None = None,
    parse_json: Callable[[bytes], dict[str, Any]] | None = None,
    rate_limiter: Callable[[], None] | None = None,
    raw_fetch_dir: Path | None = None,
    skip_fetch: bool = False,
    verify_deterministic_rematerialization: bool = True,
) -> DistinctExternalReferenceMaterializationResultV0:
    config = build_materializer_config_v0()
    if confirm != CONFIRM_GO:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_OPERATOR_GO,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=None,
            native_instrument_id=None,
            fetch_window_start_utc=None,
            fetch_window_end_utc=None,
            raw_record_count=0,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )
    if not enabled:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_DEFAULT_OFF,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=None,
            native_instrument_id=None,
            fetch_window_start_utc=None,
            fetch_window_end_utc=None,
            raw_record_count=0,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("DEFAULT_OFF_ENABLED_FLAG_REQUIRED",),
        )

    self_jsonl = _resolve_jsonl_path(self_archive_source)
    if self_jsonl is None:
        raise ValueError("MISSING_SELF_ACCUMULATED_OBSERVATIONS_JSONL")
    before_self_digest = _sha256_bytes(self_jsonl.read_bytes())

    eligible, instrument_id, reason = validate_instrument_for_forward_archive_v0(instrument)
    if not eligible or instrument_id is None:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_INELIGIBLE_INSTRUMENT,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=None,
            native_instrument_id=str(instrument.get("instId", "")),
            fetch_window_start_utc=None,
            fetch_window_end_utc=None,
            raw_record_count=0,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=(reason or "INELIGIBLE_INSTRUMENT",),
        )

    native_instrument_id = str(instrument["instId"])
    overlap = load_self_archive_overlap_window_v0(self_archive_source)
    if overlap.instrument_id != instrument_id:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_INELIGIBLE_INSTRUMENT,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
            fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
            raw_record_count=0,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("INSTRUMENT_MISMATCH_WITH_SELF_ARCHIVE",),
        )

    try:
        resolved_self = self_archive_source.resolve()
        resolved_output = output_dir.resolve()
    except OSError:
        resolved_self = self_archive_source
        resolved_output = output_dir
    if resolved_self == resolved_output:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_NOT_DISTINCT,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
            fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
            raw_record_count=0,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=False,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("SAME_OUTPUT_PATH_AS_SELF_ARCHIVE",),
        )

    window = compute_fetch_window_v0(overlap)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = raw_fetch_dir or (output_dir / RAW_FETCH_DIRNAME)
    raw_dir.mkdir(parents=True, exist_ok=True)

    normalized_rows: list[NormalizedOpenInterestObservationV0]
    fail_reason: str | None = None
    if skip_fetch:
        normalized_rows = load_raw_fetch_observations_v0(
            raw_dir,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            window=window,
        )
    else:
        if (
            fetcher is None
            or fetch_with_retry is None
            or build_url is None
            or parse_json is None
            or rate_limiter is None
        ):
            raise ValueError("FETCH_DEPENDENCIES_REQUIRED")
        budget = build_fetch_budget_v0(config)
        normalized_rows, fail_reason = paginate_bounded_open_interest_v0(
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            window=window,
            fetcher=fetcher,
            rate_limiter=rate_limiter,
            fetch_with_retry=fetch_with_retry,
            build_url=build_url,
            parse_json=parse_json,
            raw_dir=raw_dir,
            budget=budget,
        )
        if fail_reason:
            return DistinctExternalReferenceMaterializationResultV0(
                status=MaterializationTerminalStatus.FAIL_CLOSED_FETCH,
                dataset_id=DATASET_ID,
                output_dir=str(output_dir),
                external_reference_input=str(output_dir),
                instrument_id=instrument_id,
                native_instrument_id=native_instrument_id,
                fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
                fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
                raw_record_count=len(list(raw_dir.glob("*.json"))),
                materialized_observation_count=0,
                exact_overlap_candidate_count=0,
                output_schema=ARCHIVE_SCHEMA_VERSION,
                distinct_from_self_archive=True,
                deterministic_materialization=False,
                second_materialization_diff_empty=False,
                self_archive_mutation=False,
                reason_codes=(fail_reason,),
            )

    observations = normalize_fetched_observations_v0(
        normalized_rows,
        collected_at_utc=collected_at_utc,
    )
    raw_record_count = len(normalized_rows)
    if not observations:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_EMPTY_OUTPUT,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
            fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
            raw_record_count=raw_record_count,
            materialized_observation_count=0,
            exact_overlap_candidate_count=0,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=True,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("EMPTY_MATERIALIZED_OBSERVATIONS",),
        )

    exact_overlap = count_exact_overlap_candidates_v0(
        observations,
        self_venue_timestamp_ms=overlap.self_venue_timestamp_ms,
    )
    if exact_overlap < 1:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_NO_OVERLAP,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
            fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
            raw_record_count=raw_record_count,
            materialized_observation_count=len(observations),
            exact_overlap_candidate_count=exact_overlap,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=True,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=False,
            reason_codes=("NO_EXACT_VENUE_TIMESTAMP_OVERLAP",),
        )

    observations_path = output_dir / OBSERVATIONS_JSONL_FILENAME
    rows_digest = write_observations_jsonl_v0(observations, output_path=observations_path)

    source_payload_digests = sorted(
        _sha256_bytes(path.read_bytes()) for path in sorted(raw_dir.glob("*.json"))
    )
    provenance = {
        "schema_version": "okx_distinct_external_reference_forward_open_interest_snapshot_provenance.v0",
        "dataset_id": DATASET_ID,
        "role": "EXTERNAL_REFERENCE",
        "acquisition_owner": config["acquisition_owner"],
        "materializer_owner": config["materializer_owner"],
        "source_endpoint": SOURCE_ENDPOINT,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "public_endpoint": "https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history",
        "instrument_id": instrument_id,
        "native_instrument_id": native_instrument_id,
        "fetch_window_start_utc": overlap.fetch_start_inclusive_utc,
        "fetch_window_end_utc": overlap.fetch_end_exclusive_utc,
        "acquisition_timestamp_utc": collected_at_utc,
        "self_archive_source_ref": str(self_archive_source.resolve()),
        "distinct_from_self_archive": True,
        "source_payload_digests": source_payload_digests,
        "observations_digest": rows_digest,
    }
    (output_dir / PROVENANCE_FILENAME).write_text(
        json.dumps(provenance, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    dataset_manifest = {
        "schema_version": DATASET_ID,
        "dataset_id": DATASET_ID,
        "output_schema_version": ARCHIVE_SCHEMA_VERSION,
        "output_filename": OBSERVATIONS_JSONL_FILENAME,
        "module_version": MODULE_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "observation_count": len(observations),
        "instrument_count": 1,
        "rows_digest": rows_digest,
        "implementation_digest": compute_implementation_digest_v0(),
        "config_digest": compute_sha256_digest(config),
        "immutable_after_materialization": True,
        "overlap_validation_status": "NOT_EXECUTED",
    }
    (output_dir / DATASET_MANIFEST_FILENAME).write_text(
        json.dumps(dataset_manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    acquisition_report = {
        "schema_version": "okx_distinct_external_reference_forward_open_interest_acquisition_report.v0",
        "status": MaterializationTerminalStatus.COMPLETE.value,
        "fetch_window_start_utc": overlap.fetch_start_inclusive_utc,
        "fetch_window_end_utc": overlap.fetch_end_exclusive_utc,
        "raw_record_count": raw_record_count,
        "materialized_observation_count": len(observations),
        "exact_overlap_candidate_count": exact_overlap,
        "self_archive_observation_count": overlap.self_observation_count,
        "skip_fetch": skip_fetch,
        "network_fetch_executed": not skip_fetch,
    }
    (output_dir / ACQUISITION_REPORT_FILENAME).write_text(
        json.dumps(acquisition_report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    write_bundle_manifest_sha256_v0(output_dir)

    after_self_digest = _sha256_bytes(self_jsonl.read_bytes())
    self_archive_mutation = before_self_digest != after_self_digest
    if self_archive_mutation:
        return DistinctExternalReferenceMaterializationResultV0(
            status=MaterializationTerminalStatus.FAIL_CLOSED_SELF_ARCHIVE_MUTATION,
            dataset_id=DATASET_ID,
            output_dir=str(output_dir),
            external_reference_input=str(output_dir),
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
            fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
            raw_record_count=raw_record_count,
            materialized_observation_count=len(observations),
            exact_overlap_candidate_count=exact_overlap,
            output_schema=ARCHIVE_SCHEMA_VERSION,
            distinct_from_self_archive=True,
            deterministic_materialization=False,
            second_materialization_diff_empty=False,
            self_archive_mutation=True,
            reason_codes=("SELF_ARCHIVE_DIGEST_CHANGED",),
        )

    remat_a = output_dir.parent / "_remat_a"
    remat_b = output_dir.parent / "_remat_b"
    second_materialization_diff_empty = False
    if verify_deterministic_rematerialization:
        for remat in (remat_a, remat_b):
            if remat.exists():
                for child in sorted(remat.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink()
                for child in sorted(remat.glob("*"), reverse=True):
                    if child.is_dir():
                        child.rmdir()
                remat.rmdir()
        rematerialize_results: list[bytes] = []
        for remat in (remat_a, remat_b):
            remat.mkdir(parents=True, exist_ok=True)
            remat_result = materialize_distinct_external_reference_snapshot_v0(
                confirm=confirm,
                instrument=instrument,
                self_archive_source=self_archive_source,
                output_dir=remat,
                collected_at_utc=collected_at_utc,
                enabled=True,
                skip_fetch=True,
                raw_fetch_dir=raw_dir,
                verify_deterministic_rematerialization=False,
            )
            if remat_result.status != MaterializationTerminalStatus.COMPLETE:
                return DistinctExternalReferenceMaterializationResultV0(
                    status=MaterializationTerminalStatus.FAIL_CLOSED_RAW_REMATERIALIZATION,
                    dataset_id=DATASET_ID,
                    output_dir=str(output_dir),
                    external_reference_input=str(output_dir),
                    instrument_id=instrument_id,
                    native_instrument_id=native_instrument_id,
                    fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
                    fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
                    raw_record_count=raw_record_count,
                    materialized_observation_count=len(observations),
                    exact_overlap_candidate_count=exact_overlap,
                    output_schema=ARCHIVE_SCHEMA_VERSION,
                    distinct_from_self_archive=True,
                    deterministic_materialization=False,
                    second_materialization_diff_empty=False,
                    self_archive_mutation=False,
                    reason_codes=tuple(remat_result.reason_codes),
                )
            rematerialize_results.append((remat / OBSERVATIONS_JSONL_FILENAME).read_bytes())
        second_materialization_diff_empty = rematerialize_results[0] == rematerialize_results[1]
        for remat in (remat_a, remat_b):
            for child in sorted(remat.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
            for child in sorted(remat.glob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            remat.rmdir()

    return DistinctExternalReferenceMaterializationResultV0(
        status=MaterializationTerminalStatus.COMPLETE,
        dataset_id=DATASET_ID,
        output_dir=str(output_dir),
        external_reference_input=str(output_dir),
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        fetch_window_start_utc=overlap.fetch_start_inclusive_utc,
        fetch_window_end_utc=overlap.fetch_end_exclusive_utc,
        raw_record_count=raw_record_count,
        materialized_observation_count=len(observations),
        exact_overlap_candidate_count=exact_overlap,
        output_schema=ARCHIVE_SCHEMA_VERSION,
        distinct_from_self_archive=True,
        deterministic_materialization=True,
        second_materialization_diff_empty=second_materialization_diff_empty,
        self_archive_mutation=False,
    )


def materialization_result_to_dict_v0(
    result: DistinctExternalReferenceMaterializationResultV0,
) -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "status": result.status.value,
        "dataset_id": result.dataset_id,
        "output_dir": result.output_dir,
        "external_reference_input": result.external_reference_input,
        "instrument_id": result.instrument_id,
        "native_instrument_id": result.native_instrument_id,
        "fetch_window_start_utc": result.fetch_window_start_utc,
        "fetch_window_end_utc": result.fetch_window_end_utc,
        "raw_record_count": result.raw_record_count,
        "materialized_observation_count": result.materialized_observation_count,
        "exact_overlap_candidate_count": result.exact_overlap_candidate_count,
        "output_schema": result.output_schema,
        "distinct_from_self_archive": result.distinct_from_self_archive,
        "deterministic_materialization": result.deterministic_materialization,
        "second_materialization_diff_empty": result.second_materialization_diff_empty,
        "self_archive_mutation": result.self_archive_mutation,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "research_scope": RESEARCH_SCOPE,
        "module_version": MODULE_VERSION,
        "config_schema_version": build_materializer_config_v0()["schema_version"],
    }


def exit_code_for_materialization_result_v0(
    result: DistinctExternalReferenceMaterializationResultV0,
) -> int:
    if result.status == MaterializationTerminalStatus.COMPLETE:
        return 0
    return 2
