"""Historical panel depth extension for self-accumulated OI archive v0.

Bounded public OKX fetch and archive-correction gap-insert for the canonical
five-instrument panel (AVAX, ETH, LINK, POL, SOL). Extends aligned PT1H history
from the current common tail to at least MINIMUM_REQUIRED_HISTORY_DEPTH bars.
Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
    SOURCE_ENDPOINT,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
    OpenInterestFetchBudgetGuardV0,
    compute_open_interest_bounded_window_v0,
    paginate_bounded_open_interest_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0 import (
    BOUND_EXECUTION_PLAN_SCHEMA_VERSION,
    CONFIRM_GO_EXECUTION,
    CorrectionExecutionTerminalStatus,
    execute_archive_correction_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_MANIFEST_FILENAME,
    BAR_INTERVAL_MS,
    COLLECTION_MODE_FORWARD_ONLY,
    OBSERVATIONS_JSONL_FILENAME,
    ForwardOpenInterestObservationV0,
    InstrumentArchiveStateV0,
    load_effective_archive_states_from_snapshot_v0,
    observation_from_normalized_v0,
    serialize_observation_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    validate_instrument_for_forward_archive_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
    AcquisitionInstrumentBindingV0,
    build_okx_instrument_record_v0,
)

PACKAGE_MARKER = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_HISTORICAL_PANEL_DEPTH_EXTENSION_V0=true"
)
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension.v0"
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_HISTORICAL_PANEL_DEPTH_EXTENSION_"
    "AND_REMATERIALIZATION_IMPLEMENTATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0.json"
)

MINIMUM_REQUIRED_HISTORY_DEPTH = 55
TARGET_HISTORY_BARS = 60
FIRST_RANKABLE_EPOCH_INDEX = LOOKBACK_K + SIGNAL_LAG_BARS
MAX_PAGES_PER_INSTRUMENT = 3
MAX_TOTAL_REQUESTS = 20
MAX_TOTAL_RAW_BYTES = 50_000_000
MAX_RUNTIME_SECONDS = 600

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class HistoricalFetchValidationVerdict(str, Enum):
    PASS = "PASS"
    FAIL_MISSING_BAR = "FAIL_MISSING_BAR"
    FAIL_UNEXPECTED_BAR = "FAIL_UNEXPECTED_BAR"
    FAIL_DUPLICATE_BAR = "FAIL_DUPLICATE_BAR"
    FAIL_WRONG_INSTRUMENT = "FAIL_WRONG_INSTRUMENT"
    FAIL_WRONG_INTERVAL = "FAIL_WRONG_INTERVAL"
    FAIL_FETCH = "FAIL_FETCH"
    FAIL_DIGEST_CONFLICT = "FAIL_DIGEST_CONFLICT"


class HistoricalDepthExtensionTerminalStatus(str, Enum):
    VALIDATE_ONLY_PASS = "VALIDATE_ONLY_PASS"
    EXTENSION_COMPLETE = "EXTENSION_COMPLETE"
    FAIL_CLOSED_OPERATOR_GO = "FAIL_CLOSED_OPERATOR_GO"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_VALIDATION = "FAIL_CLOSED_VALIDATION"
    FAIL_CLOSED_DIGEST_CONFLICT = "FAIL_CLOSED_DIGEST_CONFLICT"
    FAIL_CLOSED_CORRECTION = "FAIL_CLOSED_CORRECTION"


@dataclass(frozen=True)
class HistoricalFetchValidationResultV0:
    instrument_id: str
    verdict: HistoricalFetchValidationVerdict
    requested_timestamps_utc: tuple[str, ...]
    fetched_timestamps_utc: tuple[str, ...]
    missing_timestamps_utc: tuple[str, ...]
    unexpected_timestamps_utc: tuple[str, ...]
    duplicate_timestamps_utc: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalDepthExtensionResultV0:
    status: HistoricalDepthExtensionTerminalStatus
    target_history_bars: int
    history_depth_before: int
    history_depth_after: int
    expected_rankable_epoch_count: int
    fetch_results: tuple[HistoricalFetchValidationResultV0, ...]
    correction_status: str | None
    historical_insert_count: int
    observations_jsonl_byte_identical: bool
    network_request_count: int
    panel_time_alignment_pass: bool
    reason_codes: tuple[str, ...]


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_panel_instrument_bindings_v0() -> tuple[AcquisitionInstrumentBindingV0, ...]:
    bindings: list[AcquisitionInstrumentBindingV0] = []
    for instrument_id, native_instrument_id in CANONICAL_UNIVERSE_BINDING:
        record = build_okx_instrument_record_v0(native_instrument_id)
        eligible, resolved_id, reason = validate_instrument_for_forward_archive_v0(record)
        if not eligible or resolved_id is None:
            raise ValueError(f"INELIGIBLE_CANONICAL_INSTRUMENT:{instrument_id}:{reason}")
        bindings.append(
            AcquisitionInstrumentBindingV0(
                instrument_id=resolved_id,
                native_instrument_id=native_instrument_id,
                okx_record=record,
            )
        )
    return tuple(bindings)


def compute_common_panel_intersection_v0(
    states: Sequence[InstrumentArchiveStateV0],
) -> tuple[str, ...]:
    timestamp_sets = [{obs.venue_timestamp_utc for obs in state.observations} for state in states]
    if not timestamp_sets:
        return ()
    intersection = set.intersection(*timestamp_sets)
    return tuple(sorted(intersection))


def compute_target_panel_calendar_v0(
    *,
    tail_end_venue_utc: str,
    bar_count: int = TARGET_HISTORY_BARS,
) -> tuple[str, ...]:
    end_ms = _parse_utc_ms(tail_end_venue_utc)
    start_ms = end_ms - (bar_count - 1) * BAR_INTERVAL_MS
    timestamps: list[str] = []
    cursor = start_ms
    while cursor <= end_ms:
        timestamps.append(_format_utc_ms(cursor))
        cursor += BAR_INTERVAL_MS
    return tuple(timestamps)


def compute_missing_timestamps_v0(
    *,
    existing_common: Sequence[str],
    target_calendar: Sequence[str],
) -> tuple[str, ...]:
    existing = set(existing_common)
    return tuple(ts for ts in target_calendar if ts not in existing)


def compute_historical_depth_fetch_window_v0(
    *,
    start_inclusive_utc: str,
    end_inclusive_utc: str,
) -> Any:
    end_exclusive_utc = _format_utc_ms(_parse_utc_ms(end_inclusive_utc) + BAR_INTERVAL_MS)
    return compute_open_interest_bounded_window_v0(
        start_inclusive_utc=start_inclusive_utc,
        end_exclusive_utc=end_exclusive_utc,
        lookback_k=0,
        signal_lag_bars=0,
    )


def compute_acquisition_window_v0(
    *,
    tail_end_venue_utc: str,
    bar_count: int = TARGET_HISTORY_BARS,
) -> dict[str, Any]:
    calendar = compute_target_panel_calendar_v0(
        tail_end_venue_utc=tail_end_venue_utc,
        bar_count=bar_count,
    )
    return {
        "tail_end_venue_utc": tail_end_venue_utc,
        "target_history_bars": bar_count,
        "minimum_required_history_depth": MINIMUM_REQUIRED_HISTORY_DEPTH,
        "start_inclusive_utc": calendar[0],
        "end_inclusive_utc": calendar[-1],
        "end_exclusive_utc": _format_utc_ms(_parse_utc_ms(calendar[-1]) + BAR_INTERVAL_MS),
        "first_rankable_epoch_index": FIRST_RANKABLE_EPOCH_INDEX,
        "rank_lookback_k": LOOKBACK_K,
        "signal_lag_bars": SIGNAL_LAG_BARS,
        "expected_rankable_epoch_count": max(bar_count - FIRST_RANKABLE_EPOCH_INDEX, 0),
    }


def _effective_observation_index(
    states: Sequence[InstrumentArchiveStateV0],
) -> dict[tuple[str, str], ForwardOpenInterestObservationV0]:
    index: dict[tuple[str, str], ForwardOpenInterestObservationV0] = {}
    for state in states:
        for obs in state.observations:
            key = (obs.instrument_id, obs.venue_timestamp_utc)
            existing = index.get(key)
            if existing is not None and existing.observation_digest != obs.observation_digest:
                raise ValueError(
                    f"EFFECTIVE_VIEW_DIGEST_CONFLICT:{obs.instrument_id}:{obs.venue_timestamp_utc}"
                )
            index[key] = obs
    return index


def detect_digest_conflicts_v0(
    *,
    effective_index: Mapping[tuple[str, str], ForwardOpenInterestObservationV0],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> tuple[bool, tuple[str, ...]]:
    conflicts: list[str] = []
    for row in candidate_rows:
        instrument_id = str(row["instrument_id"])
        venue_utc = str(row["venue_timestamp_utc"])
        candidate_digest = str(row["observation_digest"])
        existing = effective_index.get((instrument_id, venue_utc))
        if existing is not None and existing.observation_digest != candidate_digest:
            conflicts.append(f"CONFLICTING_DIGEST:{instrument_id}:{venue_utc}")
    return len(conflicts) == 0, tuple(conflicts)


def validate_fetched_historical_bars_v0(
    observations: Sequence[NormalizedOpenInterestObservationV0],
    *,
    instrument_id: str,
    native_instrument_id: str,
    required_timestamps_utc: Sequence[str],
) -> HistoricalFetchValidationResultV0:
    required_set = set(required_timestamps_utc)
    fetched: list[str] = []
    unexpected: list[str] = []
    duplicates: list[str] = []
    reasons: list[str] = []
    seen: set[str] = set()

    for obs in observations:
        if obs.instrument_id != instrument_id:
            return HistoricalFetchValidationResultV0(
                instrument_id=instrument_id,
                verdict=HistoricalFetchValidationVerdict.FAIL_WRONG_INSTRUMENT,
                requested_timestamps_utc=tuple(required_timestamps_utc),
                fetched_timestamps_utc=tuple(),
                missing_timestamps_utc=tuple(
                    sorted(required_set - set(fetched)),
                ),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=(HistoricalFetchValidationVerdict.FAIL_WRONG_INSTRUMENT.value,),
            )
        if obs.native_instrument_id != native_instrument_id:
            return HistoricalFetchValidationResultV0(
                instrument_id=instrument_id,
                verdict=HistoricalFetchValidationVerdict.FAIL_WRONG_INSTRUMENT,
                requested_timestamps_utc=tuple(required_timestamps_utc),
                fetched_timestamps_utc=tuple(),
                missing_timestamps_utc=tuple(required_timestamps_utc),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=(HistoricalFetchValidationVerdict.FAIL_WRONG_INSTRUMENT.value,),
            )
        ts = obs.observation_time_utc
        if ts in seen:
            duplicates.append(ts)
        seen.add(ts)
        if ts in required_set:
            fetched.append(ts)
        else:
            unexpected.append(ts)

    missing = sorted(required_set - set(fetched))
    if duplicates:
        reasons.append(HistoricalFetchValidationVerdict.FAIL_DUPLICATE_BAR.value)
        verdict = HistoricalFetchValidationVerdict.FAIL_DUPLICATE_BAR
    elif missing:
        reasons.append(HistoricalFetchValidationVerdict.FAIL_MISSING_BAR.value)
        verdict = HistoricalFetchValidationVerdict.FAIL_MISSING_BAR
    else:
        verdict = HistoricalFetchValidationVerdict.PASS

    return HistoricalFetchValidationResultV0(
        instrument_id=instrument_id,
        verdict=verdict,
        requested_timestamps_utc=tuple(required_timestamps_utc),
        fetched_timestamps_utc=tuple(sorted(set(fetched))),
        missing_timestamps_utc=tuple(missing),
        unexpected_timestamps_utc=tuple(sorted(set(unexpected))),
        duplicate_timestamps_utc=tuple(sorted(set(duplicates))),
        reason_codes=tuple(reasons),
    )


def normalized_rows_to_historical_insert_observations_v0(
    rows: Sequence[NormalizedOpenInterestObservationV0],
    *,
    collected_at_utc: str,
    required_timestamps_utc: Sequence[str],
) -> list[dict[str, Any]]:
    required_set = set(required_timestamps_utc)
    observations: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item.observation_time_ms):
        if row.observation_time_utc not in required_set:
            continue
        obs = observation_from_normalized_v0(
            row,
            collected_at_utc=collected_at_utc,
            collection_mode=COLLECTION_MODE_FORWARD_ONLY,
        )
        if obs is None:
            raise ValueError(f"INVALID_HISTORICAL_INSERT_NORMALIZATION:{row.observation_time_utc}")
        payload = serialize_observation_v0(obs)
        if payload["bar_interval"] != BAR_INTERVAL:
            raise ValueError(HistoricalFetchValidationVerdict.FAIL_WRONG_INTERVAL.value)
        observations.append(payload)
    if len(observations) != len(required_timestamps_utc):
        raise ValueError(HistoricalFetchValidationVerdict.FAIL_MISSING_BAR.value)
    return observations


def _load_observation_digests(snapshot_dir: Path) -> list[str]:
    jsonl_path = snapshot_dir / OBSERVATIONS_JSONL_FILENAME
    digests: list[str] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        digests.append(str(row["observation_digest"]))
    return digests


def _archive_digest(snapshot_dir: Path) -> str:
    manifest_path = snapshot_dir / ARCHIVE_MANIFEST_FILENAME
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = data.get("archive_digest")
        if isinstance(digest, str) and digest:
            return digest
    digests = _load_observation_digests(snapshot_dir)
    canonical = json.dumps(digests, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_historical_depth_correction_plan_v0(
    *,
    target_archive_path: Path,
    historical_insert_rows: Sequence[Mapping[str, Any]],
    collection_execution_id: str,
    evidence_ref: str,
) -> dict[str, Any]:
    before_digest = _archive_digest(target_archive_path)
    generation_suffix = "historical_panel_depth_extension_v0"
    return {
        "schema_version": BOUND_EXECUTION_PLAN_SCHEMA_VERSION,
        "operator_go": CONFIRM_GO_EXECUTION,
        "execution_authorized": True,
        "target_archive_path": str(target_archive_path),
        "before_archive_digest": before_digest,
        "expected_after_archive_digest": f"{before_digest}:{generation_suffix}",
        "fixture_observations_to_preserve": _load_observation_digests(target_archive_path),
        "corrected_observations": [dict(row) for row in historical_insert_rows],
        "supersession_records": [],
        "collection_binding": {
            "enable_live_fetch": True,
            "fixture_source_used": False,
            "network_allowed": True,
        },
        "collection_execution_id": collection_execution_id,
        "evidence_ref": evidence_ref,
        "executable_binding": {
            "overwrite_allowed": False,
            "external_reference_usage": "VALIDATION_ONLY",
            "historical_evidence_preserved": True,
        },
        "generation_binding": {
            "generation_id": f"{before_digest}:{generation_suffix}",
            "parent_generation_id": before_digest,
            "generation_mode": "CORRECTION",
        },
    }


def build_extension_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "historical_fetch_owner": "okx_historical_open_interest_public_fetch_v0",
        "historical_fetch_function": "paginate_bounded_open_interest_v0",
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "orchestration_owner": (
            "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_"
            "and_orchestration_v0"
        ),
        "materializer_owner": (
            "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
        ),
        "minimum_required_history_depth": MINIMUM_REQUIRED_HISTORY_DEPTH,
        "target_history_bars": TARGET_HISTORY_BARS,
        "first_rankable_epoch_index": FIRST_RANKABLE_EPOCH_INDEX,
        "rank_lookback_k": LOOKBACK_K,
        "signal_lag_bars": SIGNAL_LAG_BARS,
        "instrument_bindings": [
            {"instrument_id": inst_id, "native_instrument_id": native_id}
            for inst_id, native_id in CANONICAL_UNIVERSE_BINDING
        ],
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def fetch_historical_depth_for_instrument_v0(
    *,
    binding: AcquisitionInstrumentBindingV0,
    window: Any,
    required_timestamps_utc: Sequence[str],
    fetcher: PublicGetFetcher,
    rate_limiter: Callable[[], None],
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, dict[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    budget: OpenInterestFetchBudgetGuardV0,
) -> tuple[
    list[NormalizedOpenInterestObservationV0], HistoricalFetchValidationResultV0, str | None, int
]:
    requests_before = budget.total_requests
    observations, fail_reason = paginate_bounded_open_interest_v0(
        instrument_id=binding.instrument_id,
        native_instrument_id=binding.native_instrument_id,
        window=window,
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        fetch_with_retry=fetch_with_retry,
        build_url=build_url,
        parse_json=parse_json,
        raw_dir=raw_dir,
        budget=budget,
    )
    request_count = budget.total_requests - requests_before
    budget.instruments_completed += 1
    budget.current_instrument_pages = 0
    if fail_reason:
        validation = HistoricalFetchValidationResultV0(
            instrument_id=binding.instrument_id,
            verdict=HistoricalFetchValidationVerdict.FAIL_FETCH,
            requested_timestamps_utc=tuple(required_timestamps_utc),
            fetched_timestamps_utc=tuple(),
            missing_timestamps_utc=tuple(required_timestamps_utc),
            unexpected_timestamps_utc=tuple(),
            duplicate_timestamps_utc=tuple(),
            reason_codes=(fail_reason,),
        )
        return observations, validation, fail_reason, request_count
    validation = validate_fetched_historical_bars_v0(
        observations,
        instrument_id=binding.instrument_id,
        native_instrument_id=binding.native_instrument_id,
        required_timestamps_utc=required_timestamps_utc,
    )
    return observations, validation, None, request_count


def validate_post_extension_v0(
    *,
    target_archive_path: Path,
    minimum_depth: int = MINIMUM_REQUIRED_HISTORY_DEPTH,
) -> dict[str, Any]:
    states = load_effective_archive_states_from_snapshot_v0(target_archive_path)
    common = compute_common_panel_intersection_v0(states)
    per_instrument = []
    for state in sorted(states, key=lambda item: item.instrument_id):
        timestamps = [obs.venue_timestamp_utc for obs in state.observations]
        per_instrument.append(
            {
                "instrument_id": state.instrument_id,
                "native_instrument_id": state.native_instrument_id,
                "observation_count": len(state.observations),
                "start_time_utc": timestamps[0] if timestamps else None,
                "end_time_utc": timestamps[-1] if timestamps else None,
            }
        )
    return {
        "history_depth_after": len(common),
        "minimum_required_history_depth": minimum_depth,
        "panel_time_alignment_pass": len(common) >= minimum_depth,
        "common_start_time_utc": common[0] if common else None,
        "common_end_time_utc": common[-1] if common else None,
        "per_instrument": per_instrument,
        "expected_rankable_epoch_count": max(len(common) - FIRST_RANKABLE_EPOCH_INDEX, 0),
    }


def execute_historical_panel_depth_extension_v0(
    *,
    confirm: str,
    enabled: bool,
    target_archive_path: Path,
    collected_at_utc: str,
    collection_execution_id: str,
    evidence_ref: str,
    fetcher: PublicGetFetcher | None = None,
    rate_limiter: Callable[[], None] | None = None,
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]] | None = None,
    build_url: Callable[[str, dict[str, str]], str] | None = None,
    parse_json: Callable[[bytes], dict[str, Any]] | None = None,
    raw_dir: Path | None = None,
    fixture_observations_by_native: Mapping[str, Sequence[NormalizedOpenInterestObservationV0]]
    | None = None,
    execute_mutation: bool = True,
    validate_only: bool = False,
    target_history_bars: int = TARGET_HISTORY_BARS,
) -> HistoricalDepthExtensionResultV0:
    empty_fetch: tuple[HistoricalFetchValidationResultV0, ...] = ()
    if not enabled:
        return HistoricalDepthExtensionResultV0(
            status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_DEFAULT_OFF,
            target_history_bars=target_history_bars,
            history_depth_before=0,
            history_depth_after=0,
            expected_rankable_epoch_count=0,
            fetch_results=empty_fetch,
            correction_status=None,
            historical_insert_count=0,
            observations_jsonl_byte_identical=True,
            network_request_count=0,
            panel_time_alignment_pass=False,
            reason_codes=("DEFAULT_OFF_ENABLED_FLAG_REQUIRED",),
        )
    if confirm != CONFIRM_GO:
        return HistoricalDepthExtensionResultV0(
            status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_OPERATOR_GO,
            target_history_bars=target_history_bars,
            history_depth_before=0,
            history_depth_after=0,
            expected_rankable_epoch_count=0,
            fetch_results=empty_fetch,
            correction_status=None,
            historical_insert_count=0,
            observations_jsonl_byte_identical=True,
            network_request_count=0,
            panel_time_alignment_pass=False,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )

    effective_before = load_effective_archive_states_from_snapshot_v0(target_archive_path)
    common_before = compute_common_panel_intersection_v0(effective_before)
    history_depth_before = len(common_before)
    if not common_before:
        return HistoricalDepthExtensionResultV0(
            status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_VALIDATION,
            target_history_bars=target_history_bars,
            history_depth_before=0,
            history_depth_after=0,
            expected_rankable_epoch_count=0,
            fetch_results=empty_fetch,
            correction_status=None,
            historical_insert_count=0,
            observations_jsonl_byte_identical=True,
            network_request_count=0,
            panel_time_alignment_pass=False,
            reason_codes=("EMPTY_COMMON_PANEL_INTERSECTION",),
        )

    tail_end_utc = common_before[-1]
    target_calendar = compute_target_panel_calendar_v0(
        tail_end_venue_utc=tail_end_utc,
        bar_count=target_history_bars,
    )
    missing_common = compute_missing_timestamps_v0(
        existing_common=common_before,
        target_calendar=target_calendar,
    )
    effective_index = _effective_observation_index(effective_before)
    bindings = derive_panel_instrument_bindings_v0()

    fetch_window = compute_historical_depth_fetch_window_v0(
        start_inclusive_utc=target_calendar[0],
        end_inclusive_utc=target_calendar[-1],
    )
    budget = OpenInterestFetchBudgetGuardV0(
        max_instruments=len(bindings),
        max_pages_per_instrument=MAX_PAGES_PER_INSTRUMENT,
        max_total_requests=MAX_TOTAL_REQUESTS,
        max_total_raw_bytes=MAX_TOTAL_RAW_BYTES,
        max_runtime_seconds=MAX_RUNTIME_SECONDS,
    )

    fetch_results: list[HistoricalFetchValidationResultV0] = []
    all_insert_rows: list[dict[str, Any]] = []
    network_request_count = 0

    for binding in bindings:
        existing_ts = {
            obs.venue_timestamp_utc
            for obs in next(
                state for state in effective_before if state.instrument_id == binding.instrument_id
            ).observations
        }
        required_for_instrument = tuple(ts for ts in missing_common if ts not in existing_ts)
        if not required_for_instrument:
            fetch_results.append(
                HistoricalFetchValidationResultV0(
                    instrument_id=binding.instrument_id,
                    verdict=HistoricalFetchValidationVerdict.PASS,
                    requested_timestamps_utc=(),
                    fetched_timestamps_utc=(),
                    missing_timestamps_utc=(),
                    unexpected_timestamps_utc=(),
                    duplicate_timestamps_utc=(),
                    reason_codes=("NO_FETCH_REQUIRED",),
                )
            )
            continue

        if fixture_observations_by_native is not None:
            fixture_rows = list(
                fixture_observations_by_native.get(binding.native_instrument_id, ())
            )
            fail_reason = None if fixture_rows else "MISSING_FIXTURE_OBSERVATIONS"
            request_count = 0
            normalized_rows = fixture_rows
        else:
            if (
                fetcher is None
                or rate_limiter is None
                or fetch_with_retry is None
                or build_url is None
                or parse_json is None
                or raw_dir is None
            ):
                return HistoricalDepthExtensionResultV0(
                    status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_FETCH,
                    target_history_bars=target_history_bars,
                    history_depth_before=history_depth_before,
                    history_depth_after=history_depth_before,
                    expected_rankable_epoch_count=max(
                        history_depth_before - FIRST_RANKABLE_EPOCH_INDEX, 0
                    ),
                    fetch_results=tuple(fetch_results),
                    correction_status=None,
                    historical_insert_count=0,
                    observations_jsonl_byte_identical=True,
                    network_request_count=network_request_count,
                    panel_time_alignment_pass=False,
                    reason_codes=("FETCH_DEPENDENCIES_REQUIRED",),
                )
            instrument_raw_dir = raw_dir / binding.native_instrument_id
            normalized_rows, validation, fail_reason, request_count = (
                fetch_historical_depth_for_instrument_v0(
                    binding=binding,
                    window=fetch_window,
                    required_timestamps_utc=required_for_instrument,
                    fetcher=fetcher,
                    rate_limiter=rate_limiter,
                    fetch_with_retry=fetch_with_retry,
                    build_url=build_url,
                    parse_json=parse_json,
                    raw_dir=instrument_raw_dir,
                    budget=budget,
                )
            )
            fetch_results.append(validation)
            network_request_count += request_count
            if fail_reason or validation.verdict is not HistoricalFetchValidationVerdict.PASS:
                return HistoricalDepthExtensionResultV0(
                    status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_FETCH,
                    target_history_bars=target_history_bars,
                    history_depth_before=history_depth_before,
                    history_depth_after=history_depth_before,
                    expected_rankable_epoch_count=max(
                        history_depth_before - FIRST_RANKABLE_EPOCH_INDEX, 0
                    ),
                    fetch_results=tuple(fetch_results),
                    correction_status=None,
                    historical_insert_count=0,
                    observations_jsonl_byte_identical=True,
                    network_request_count=network_request_count,
                    panel_time_alignment_pass=False,
                    reason_codes=validation.reason_codes + ((fail_reason,) if fail_reason else ()),
                )

        if fixture_observations_by_native is not None:
            validation = validate_fetched_historical_bars_v0(
                normalized_rows,
                instrument_id=binding.instrument_id,
                native_instrument_id=binding.native_instrument_id,
                required_timestamps_utc=required_for_instrument,
            )
            fetch_results.append(validation)
            if validation.verdict is not HistoricalFetchValidationVerdict.PASS:
                return HistoricalDepthExtensionResultV0(
                    status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_VALIDATION,
                    target_history_bars=target_history_bars,
                    history_depth_before=history_depth_before,
                    history_depth_after=history_depth_before,
                    expected_rankable_epoch_count=max(
                        history_depth_before - FIRST_RANKABLE_EPOCH_INDEX, 0
                    ),
                    fetch_results=tuple(fetch_results),
                    correction_status=None,
                    historical_insert_count=0,
                    observations_jsonl_byte_identical=True,
                    network_request_count=network_request_count,
                    panel_time_alignment_pass=False,
                    reason_codes=validation.reason_codes,
                )

        try:
            insert_rows = normalized_rows_to_historical_insert_observations_v0(
                normalized_rows,
                collected_at_utc=collected_at_utc,
                required_timestamps_utc=required_for_instrument,
            )
        except ValueError as exc:
            return HistoricalDepthExtensionResultV0(
                status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_VALIDATION,
                target_history_bars=target_history_bars,
                history_depth_before=history_depth_before,
                history_depth_after=history_depth_before,
                expected_rankable_epoch_count=max(
                    history_depth_before - FIRST_RANKABLE_EPOCH_INDEX, 0
                ),
                fetch_results=tuple(fetch_results),
                correction_status=None,
                historical_insert_count=0,
                observations_jsonl_byte_identical=True,
                network_request_count=network_request_count,
                panel_time_alignment_pass=False,
                reason_codes=(str(exc),),
            )

        conflict_free, conflicts = detect_digest_conflicts_v0(
            effective_index=effective_index,
            candidate_rows=insert_rows,
        )
        if not conflict_free:
            return HistoricalDepthExtensionResultV0(
                status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_DIGEST_CONFLICT,
                target_history_bars=target_history_bars,
                history_depth_before=history_depth_before,
                history_depth_after=history_depth_before,
                expected_rankable_epoch_count=max(
                    history_depth_before - FIRST_RANKABLE_EPOCH_INDEX, 0
                ),
                fetch_results=tuple(fetch_results),
                correction_status=None,
                historical_insert_count=0,
                observations_jsonl_byte_identical=True,
                network_request_count=network_request_count,
                panel_time_alignment_pass=False,
                reason_codes=conflicts,
            )
        all_insert_rows.extend(insert_rows)

    if validate_only or not execute_mutation:
        post = validate_post_extension_v0(target_archive_path=target_archive_path)
        projected_depth = len(target_calendar)
        return HistoricalDepthExtensionResultV0(
            status=HistoricalDepthExtensionTerminalStatus.VALIDATE_ONLY_PASS,
            target_history_bars=target_history_bars,
            history_depth_before=history_depth_before,
            history_depth_after=projected_depth,
            expected_rankable_epoch_count=max(projected_depth - FIRST_RANKABLE_EPOCH_INDEX, 0),
            fetch_results=tuple(fetch_results),
            correction_status=None,
            historical_insert_count=len(all_insert_rows),
            observations_jsonl_byte_identical=True,
            network_request_count=network_request_count,
            panel_time_alignment_pass=projected_depth >= MINIMUM_REQUIRED_HISTORY_DEPTH,
            reason_codes=(),
        )

    before_obs_bytes = (target_archive_path / OBSERVATIONS_JSONL_FILENAME).read_bytes()
    bound_plan = build_historical_depth_correction_plan_v0(
        target_archive_path=target_archive_path,
        historical_insert_rows=all_insert_rows,
        collection_execution_id=collection_execution_id,
        evidence_ref=evidence_ref,
    )
    plan_path = (raw_dir or Path(".")) / "historical_panel_depth_extension_bound_plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(bound_plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    correction = execute_archive_correction_v0(
        confirm=CONFIRM_GO_EXECUTION,
        validate_only=False,
        execute_mutation=True,
        enabled=True,
        bound_plan_path=plan_path,
        target_archive_path=target_archive_path,
    )
    after_obs_bytes = (target_archive_path / OBSERVATIONS_JSONL_FILENAME).read_bytes()
    post = validate_post_extension_v0(target_archive_path=target_archive_path)

    if correction.status not in {
        CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE,
        CorrectionExecutionTerminalStatus.ALREADY_APPLIED_NOOP,
    }:
        return HistoricalDepthExtensionResultV0(
            status=HistoricalDepthExtensionTerminalStatus.FAIL_CLOSED_CORRECTION,
            target_history_bars=target_history_bars,
            history_depth_before=history_depth_before,
            history_depth_after=post["history_depth_after"],
            expected_rankable_epoch_count=post["expected_rankable_epoch_count"],
            fetch_results=tuple(fetch_results),
            correction_status=str(correction.status.value),
            historical_insert_count=len(all_insert_rows),
            observations_jsonl_byte_identical=before_obs_bytes == after_obs_bytes,
            network_request_count=network_request_count,
            panel_time_alignment_pass=post["panel_time_alignment_pass"],
            reason_codes=correction.reason_codes,
        )

    return HistoricalDepthExtensionResultV0(
        status=HistoricalDepthExtensionTerminalStatus.EXTENSION_COMPLETE,
        target_history_bars=target_history_bars,
        history_depth_before=history_depth_before,
        history_depth_after=post["history_depth_after"],
        expected_rankable_epoch_count=post["expected_rankable_epoch_count"],
        fetch_results=tuple(fetch_results),
        correction_status=str(correction.status.value),
        historical_insert_count=len(all_insert_rows),
        observations_jsonl_byte_identical=before_obs_bytes == after_obs_bytes,
        network_request_count=network_request_count,
        panel_time_alignment_pass=post["panel_time_alignment_pass"],
        reason_codes=(),
    )


def result_to_report_dict_v0(result: HistoricalDepthExtensionResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "target_history_bars": result.target_history_bars,
        "history_depth_before": result.history_depth_before,
        "history_depth_after": result.history_depth_after,
        "expected_rankable_epoch_count": result.expected_rankable_epoch_count,
        "historical_insert_count": result.historical_insert_count,
        "observations_jsonl_byte_identical": result.observations_jsonl_byte_identical,
        "network_request_count": result.network_request_count,
        "panel_time_alignment_pass": result.panel_time_alignment_pass,
        "correction_status": result.correction_status,
        "source_endpoint": SOURCE_ENDPOINT,
        "fetch_results": [
            {
                "instrument_id": item.instrument_id,
                "verdict": item.verdict.value,
                "requested_count": len(item.requested_timestamps_utc),
                "fetched_count": len(item.fetched_timestamps_utc),
                "missing_count": len(item.missing_timestamps_utc),
                "reason_codes": list(item.reason_codes),
            }
            for item in result.fetch_results
        ],
        "reason_codes": list(result.reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
