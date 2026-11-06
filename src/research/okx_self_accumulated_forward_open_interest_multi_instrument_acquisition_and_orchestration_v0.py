"""Bounded multi-instrument acquisition orchestration for self-accumulated OI archive v0.

Deterministic selection of four additional futures-only, non-Bitcoin instruments from the
canonical sufficiency-contract universe, bounded public OKX historical fetch per instrument
via paginate_bounded_open_interest_v0, and append-only observations.jsonl extension that
preserves existing ETH rows and correction sidecars. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.research.okx_historical_open_interest_public_fetch_v0 import (
    NormalizedOpenInterestObservationV0,
    OpenInterestFetchBudgetGuardV0,
    compute_open_interest_bounded_window_v0,
    paginate_bounded_open_interest_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    ArchiveIntegrityAuditStatus,
    audit_archive_snapshot_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_MANIFEST_FILENAME,
    BAR_INTERVAL_MS,
    COLLECTION_MODE_FORWARD_ONLY,
    CORRECTED_OBSERVATIONS_JSONL_FILENAME,
    MANIFEST_SHA256_FILENAME,
    OBSERVATIONS_JSONL_FILENAME,
    SUPERSESSION_RECORDS_JSONL_FILENAME,
    ForwardOpenInterestObservationV0,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    load_effective_archive_states_from_snapshot_v0,
    observation_from_normalized_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    validate_instrument_for_forward_archive_v0,
    write_manifest_sha256_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    MINIMUM_INSTRUMENT_COUNT,
    REQUIRED_CONTIGUOUS_BARS,
    REQUIRED_OBSERVATION_COUNT,
    assess_materialization_admissibility_v0,
    compute_contiguous_tail_bars,
    compute_max_internal_gap_bars,
    default_sufficiency_policy_v0,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = (
    "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_MULTI_INSTRUMENT_ACQUISITION_"
    "AND_ORCHESTRATION_V0=true"
)
MODULE_VERSION = (
    "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration.v0"
)
CONFIRM_GO = (
    "GO_CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_MULTI_INSTRUMENT_ACQUISITION_"
    "AND_ORCHESTRATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0.json"
)

REQUIRED_ADDITIONAL_INSTRUMENT_COUNT = MINIMUM_INSTRUMENT_COUNT - 1
INITIAL_HISTORY_BARS_PER_NEW_INSTRUMENT = REQUIRED_CONTIGUOUS_BARS
MAX_PAGES_PER_INSTRUMENT = 3
MAX_TOTAL_REQUESTS = 12
MAX_TOTAL_RAW_BYTES = 20_000_000
MAX_RUNTIME_SECONDS = 300

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]

CANONICAL_UNIVERSE_BINDING: tuple[tuple[str, str], ...] = (
    ("okx:linear_perpetual:AVAX:USDT:USDT:perp", "AVAX-USDT-SWAP"),
    ("okx:linear_perpetual:ETH:USDT:USDT:perp", "ETH-USDT-SWAP"),
    ("okx:linear_perpetual:LINK:USDT:USDT:perp", "LINK-USDT-SWAP"),
    ("okx:linear_perpetual:POL:USDT:USDT:perp", "POL-USDT-SWAP"),
    ("okx:linear_perpetual:SOL:USDT:USDT:perp", "SOL-USDT-SWAP"),
)


class AcquisitionTerminalStatus(str, Enum):
    VALIDATE_ONLY_PASS = "VALIDATE_ONLY_PASS"
    ACQUISITION_COMPLETE = "ACQUISITION_COMPLETE"
    FAIL_CLOSED_OPERATOR_GO = "FAIL_CLOSED_OPERATOR_GO"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_NO_ADDITIONAL_INSTRUMENTS_NEEDED = "FAIL_CLOSED_NO_ADDITIONAL_INSTRUMENTS_NEEDED"
    FAIL_CLOSED_INELIGIBLE_INSTRUMENT = "FAIL_CLOSED_INELIGIBLE_INSTRUMENT"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_APPEND = "FAIL_CLOSED_APPEND"
    FAIL_CLOSED_PERSISTENCE = "FAIL_CLOSED_PERSISTENCE"
    FAIL_CLOSED_VALIDATION = "FAIL_CLOSED_VALIDATION"
    FAIL_CLOSED_ETH_PREFIX = "FAIL_CLOSED_ETH_PREFIX"


@dataclass(frozen=True)
class AcquisitionInstrumentBindingV0:
    instrument_id: str
    native_instrument_id: str
    okx_record: dict[str, Any]


@dataclass(frozen=True)
class InstrumentFetchResultV0:
    instrument_id: str
    native_instrument_id: str
    observation_count: int
    fetched_timestamps_utc: tuple[str, ...]
    fail_reason: str | None
    request_count: int


@dataclass(frozen=True)
class MultiInstrumentAcquisitionResultV0:
    status: AcquisitionTerminalStatus
    selected_instruments: tuple[AcquisitionInstrumentBindingV0, ...]
    fetch_results: tuple[InstrumentFetchResultV0, ...]
    appended_observation_count: int
    observations_jsonl_byte_identical_prefix: bool
    network_request_count: int
    instrument_count_before: int
    instrument_count_after: int
    observation_count_before: int
    observation_count_after: int
    archive_integrity_pass: bool
    full_history_zero_gap_pass: bool
    materialization_admissible: bool
    reason_codes: tuple[str, ...]


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_okx_instrument_record_v0(native_instrument_id: str) -> dict[str, Any]:
    base_asset = native_instrument_id.replace("-USDT-SWAP", "")
    return {
        "instId": native_instrument_id,
        "instType": "SWAP",
        "uly": f"{base_asset}-USDT",
        "state": "live",
        "settleCcy": "USDT",
        "listTime": "1609459200000",
        "ctType": "linear",
        "expTime": "",
    }


def build_orchestration_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "historical_fetch_owner": "okx_historical_open_interest_public_fetch_v0",
        "historical_fetch_function": "paginate_bounded_open_interest_v0",
        "instrument_eligibility_owner": "okx_production_instrument_lifecycle_source_v1",
        "instrument_universe_owner": (
            "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
            "and_materialization_admissibility_contract_v0"
        ),
        "canonical_universe_binding": [
            {"instrument_id": inst_id, "native_instrument_id": native_id}
            for inst_id, native_id in CANONICAL_UNIVERSE_BINDING
        ],
        "required_additional_instrument_count": REQUIRED_ADDITIONAL_INSTRUMENT_COUNT,
        "initial_history_bars_per_new_instrument": INITIAL_HISTORY_BARS_PER_NEW_INSTRUMENT,
        "required_contiguous_bars": REQUIRED_CONTIGUOUS_BARS,
        "required_observation_count": REQUIRED_OBSERVATION_COUNT,
        "minimum_instrument_count": MINIMUM_INSTRUMENT_COUNT,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def select_additional_instruments_v0(
    existing_instrument_ids: Sequence[str],
    *,
    required_count: int = REQUIRED_ADDITIONAL_INSTRUMENT_COUNT,
) -> tuple[AcquisitionInstrumentBindingV0, ...]:
    """Deterministic selection: canonical universe sorted by instrument_id, excluding existing."""
    existing = set(existing_instrument_ids)
    selected: list[AcquisitionInstrumentBindingV0] = []
    for instrument_id, native_instrument_id in CANONICAL_UNIVERSE_BINDING:
        if instrument_id in existing:
            continue
        record = build_okx_instrument_record_v0(native_instrument_id)
        eligible, resolved_id, reason = validate_instrument_for_forward_archive_v0(record)
        if not eligible or resolved_id is None:
            raise ValueError(f"INELIGIBLE_CANONICAL_INSTRUMENT:{instrument_id}:{reason}")
        selected.append(
            AcquisitionInstrumentBindingV0(
                instrument_id=resolved_id,
                native_instrument_id=native_instrument_id,
                okx_record=record,
            )
        )
        if len(selected) >= required_count:
            break
    return tuple(selected)


def compute_aligned_fetch_window_v0(
    *,
    tail_end_venue_utc: str,
    bar_count: int = INITIAL_HISTORY_BARS_PER_NEW_INSTRUMENT,
) -> Any:
    end_ms = _parse_utc_ms(tail_end_venue_utc) + BAR_INTERVAL_MS
    start_ms = _parse_utc_ms(tail_end_venue_utc) - (bar_count - 1) * BAR_INTERVAL_MS
    return compute_open_interest_bounded_window_v0(
        start_inclusive_utc=_format_utc_ms(start_ms),
        end_exclusive_utc=_format_utc_ms(end_ms),
        lookback_k=0,
        signal_lag_bars=0,
    )


def _latest_effective_tail_end_utc(states: Sequence[InstrumentArchiveStateV0]) -> str:
    latest_ms = max(obs.venue_timestamp_ms for state in states for obs in state.observations)
    return _format_utc_ms(latest_ms)


def fetch_bounded_initial_history_for_instrument_v0(
    *,
    binding: AcquisitionInstrumentBindingV0,
    window: Any,
    fetcher: PublicGetFetcher,
    rate_limiter: Callable[[], None],
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, dict[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    budget: OpenInterestFetchBudgetGuardV0,
) -> tuple[list[NormalizedOpenInterestObservationV0], str | None, int]:
    pages_before = budget.current_instrument_pages
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
        return observations, fail_reason, request_count
    if pages_before == budget.current_instrument_pages and request_count == 0:
        return observations, "NO_REQUEST_EXECUTED", request_count
    return observations, None, request_count


def normalized_rows_to_forward_observations_v0(
    rows: Sequence[NormalizedOpenInterestObservationV0],
    *,
    collected_at_utc: str,
    required_bar_count: int = INITIAL_HISTORY_BARS_PER_NEW_INSTRUMENT,
) -> list[ForwardOpenInterestObservationV0]:
    observations: list[ForwardOpenInterestObservationV0] = []
    for row in sorted(rows, key=lambda item: item.observation_time_ms):
        obs = observation_from_normalized_v0(
            row,
            collected_at_utc=collected_at_utc,
            collection_mode=COLLECTION_MODE_FORWARD_ONLY,
        )
        if obs is None:
            raise ValueError(f"INVALID_NORMALIZATION:{row.observation_time_utc}")
        observations.append(obs)
    if len(observations) < required_bar_count:
        raise ValueError(f"INSUFFICIENT_FETCHED_BARS:{len(observations)}<{required_bar_count}")
    tail = observations[-required_bar_count:]
    gaps = compute_max_internal_gap_bars(tail)
    if gaps > 0:
        raise ValueError(f"FETCHED_TAIL_GAP_DETECTED:{gaps}")
    return tail


def _load_observations_jsonl_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    content = path.read_text(encoding="utf-8")
    return [line for line in content.splitlines() if line.strip()]


def _snapshot_prior_archive_state_v0(target_archive_path: Path) -> Path:
    prior_dir = Path(tempfile.mkdtemp(prefix="oi_archive_prior_"))
    for name in (
        OBSERVATIONS_JSONL_FILENAME,
        ARCHIVE_MANIFEST_FILENAME,
        CORRECTED_OBSERVATIONS_JSONL_FILENAME,
        SUPERSESSION_RECORDS_JSONL_FILENAME,
        MANIFEST_SHA256_FILENAME,
    ):
        source = target_archive_path / name
        if source.is_file():
            shutil.copy2(source, prior_dir / name)
    return prior_dir


def append_new_instrument_rows_preserving_prefix_v0(
    *,
    target_archive_path: Path,
    prior_observations_lines: Sequence[str],
    new_rows: Sequence[Mapping[str, Any]],
) -> tuple[bool, int]:
    jsonl_path = target_archive_path / OBSERVATIONS_JSONL_FILENAME
    existing_lines = _load_observations_jsonl_lines(jsonl_path)
    if list(existing_lines) != list(prior_observations_lines):
        return False, 0
    merged = list(existing_lines) + [serialize_canonical_json(dict(row)) for row in new_rows]
    new_lines = merged[len(existing_lines) :]
    new_lines.sort(
        key=lambda line: (
            json.loads(line)["instrument_id"],
            json.loads(line)["venue_timestamp_ms"],
        )
    )
    merged = list(existing_lines) + new_lines
    jsonl_path.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")
    return True, len(new_rows)


def _update_archive_manifest_v0(
    *,
    target_archive_path: Path,
    observation_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    manifest_path = target_archive_path / ARCHIVE_MANIFEST_FILENAME
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    )
    sorted_rows = sorted(
        [dict(row) for row in observation_rows],
        key=lambda row: (row["instrument_id"], row["venue_timestamp_ms"]),
    )
    archive_digest = compute_sha256_digest({"rows": sorted_rows})
    instrument_ids = sorted({str(row["instrument_id"]) for row in sorted_rows})
    manifest.update(
        {
            "observation_count": len(sorted_rows),
            "instrument_count": len({str(row["instrument_id"]) for row in sorted_rows}),
            "archive_digest": archive_digest,
            "bitcoin_present": False,
            "futures_only": True,
            "historical_backfill_allowed": False,
            "append_only": True,
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def validate_post_acquisition_v0(
    *,
    target_archive_path: Path,
    prior_snapshot_dir: Path,
    as_of_utc: str,
) -> dict[str, Any]:
    effective_states = load_effective_archive_states_from_snapshot_v0(target_archive_path)
    audit = audit_archive_snapshot_v0(
        snapshot_dir=target_archive_path,
        prior_snapshot_dir=prior_snapshot_dir,
    )
    admissibility = assess_materialization_admissibility_v0(
        archive_root=target_archive_path,
        as_of_utc=as_of_utc,
    )
    eth_state = next(
        (state for state in effective_states if state.native_instrument_id == "ETH-USDT-SWAP"),
        None,
    )
    eth_gap_count = 0
    if eth_state is not None:
        eth_gap_count = compute_max_internal_gap_bars(eth_state.observations)
    duplicate_count = 0
    out_of_order_count = 0
    if audit.status is ArchiveIntegrityAuditStatus.FAIL:
        for code in audit.reason_codes:
            if "CONFLICTING_DUPLICATE" in code:
                duplicate_count += 1
            if "OUT_OF_ORDER_TIMESTAMP" in code:
                out_of_order_count += 1
    per_instrument = []
    for state in effective_states:
        per_instrument.append(
            {
                "instrument_id": state.instrument_id,
                "native_instrument_id": state.native_instrument_id,
                "observation_count": len(state.observations),
                "contiguous_tail_bars": compute_contiguous_tail_bars(state.observations),
                "max_internal_gap_bars": compute_max_internal_gap_bars(state.observations),
            }
        )
    return {
        "archive_integrity_pass": audit.status is ArchiveIntegrityAuditStatus.PASS,
        "integrity_status": audit.status.value,
        "full_history_zero_gap_pass": all(
            item["max_internal_gap_bars"] == 0 for item in per_instrument
        ),
        "materialization_admissible": admissibility.dataset_materialization_allowed,
        "instrument_count_after": len(effective_states),
        "observation_count_after": sum(len(state.observations) for state in effective_states),
        "eth_gap_count": eth_gap_count,
        "duplicate_timestamp_count": duplicate_count,
        "out_of_order_count": out_of_order_count,
        "per_instrument": per_instrument,
        "admissibility_reason_codes": list(admissibility.reason_codes),
    }


def execute_multi_instrument_acquisition_v0(
    *,
    confirm: str,
    enabled: bool,
    target_archive_path: Path,
    collected_at_utc: str,
    as_of_utc: str,
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
) -> MultiInstrumentAcquisitionResultV0:
    if not enabled:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_DEFAULT_OFF,
            selected_instruments=(),
            fetch_results=(),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=False,
            network_request_count=0,
            instrument_count_before=0,
            instrument_count_after=0,
            observation_count_before=0,
            observation_count_after=0,
            archive_integrity_pass=False,
            full_history_zero_gap_pass=False,
            materialization_admissible=False,
            reason_codes=("DEFAULT_OFF_ENABLED_FLAG_REQUIRED",),
        )
    if confirm != CONFIRM_GO:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_OPERATOR_GO,
            selected_instruments=(),
            fetch_results=(),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=False,
            network_request_count=0,
            instrument_count_before=0,
            instrument_count_after=0,
            observation_count_before=0,
            observation_count_after=0,
            archive_integrity_pass=False,
            full_history_zero_gap_pass=False,
            materialization_admissible=False,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )

    prior_lines = _load_observations_jsonl_lines(target_archive_path / OBSERVATIONS_JSONL_FILENAME)
    effective_before = load_effective_archive_states_from_snapshot_v0(target_archive_path)
    instrument_count_before = len(effective_before)
    observation_count_before = sum(len(state.observations) for state in effective_before)
    existing_ids = [state.instrument_id for state in effective_before]

    try:
        selected = select_additional_instruments_v0(existing_ids)
    except ValueError as exc:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_INELIGIBLE_INSTRUMENT,
            selected_instruments=(),
            fetch_results=(),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=True,
            network_request_count=0,
            instrument_count_before=instrument_count_before,
            instrument_count_after=instrument_count_before,
            observation_count_before=observation_count_before,
            observation_count_after=observation_count_before,
            archive_integrity_pass=False,
            full_history_zero_gap_pass=False,
            materialization_admissible=False,
            reason_codes=(str(exc),),
        )

    if not selected:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_NO_ADDITIONAL_INSTRUMENTS_NEEDED,
            selected_instruments=(),
            fetch_results=(),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=True,
            network_request_count=0,
            instrument_count_before=instrument_count_before,
            instrument_count_after=instrument_count_before,
            observation_count_before=observation_count_before,
            observation_count_after=observation_count_before,
            archive_integrity_pass=False,
            full_history_zero_gap_pass=False,
            materialization_admissible=False,
            reason_codes=("TARGET_INSTRUMENT_COUNT_ALREADY_SATISFIED",),
        )

    tail_end_utc = _latest_effective_tail_end_utc(effective_before)
    window = compute_aligned_fetch_window_v0(tail_end_venue_utc=tail_end_utc)
    budget = OpenInterestFetchBudgetGuardV0(
        max_instruments=len(selected),
        max_pages_per_instrument=MAX_PAGES_PER_INSTRUMENT,
        max_total_requests=MAX_TOTAL_REQUESTS,
        max_total_raw_bytes=MAX_TOTAL_RAW_BYTES,
        max_runtime_seconds=MAX_RUNTIME_SECONDS,
    )

    fetch_results: list[InstrumentFetchResultV0] = []
    rows_to_append: list[dict[str, Any]] = []
    network_request_count = 0

    for binding in selected:
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
                return MultiInstrumentAcquisitionResultV0(
                    status=AcquisitionTerminalStatus.FAIL_CLOSED_FETCH,
                    selected_instruments=selected,
                    fetch_results=tuple(fetch_results),
                    appended_observation_count=0,
                    observations_jsonl_byte_identical_prefix=True,
                    network_request_count=network_request_count,
                    instrument_count_before=instrument_count_before,
                    instrument_count_after=instrument_count_before,
                    observation_count_before=observation_count_before,
                    observation_count_after=observation_count_before,
                    archive_integrity_pass=False,
                    full_history_zero_gap_pass=False,
                    materialization_admissible=False,
                    reason_codes=("FETCH_DEPENDENCIES_REQUIRED",),
                )
            instrument_raw_dir = raw_dir / binding.native_instrument_id
            normalized_rows, fail_reason, request_count = (
                fetch_bounded_initial_history_for_instrument_v0(
                    binding=binding,
                    window=window,
                    fetcher=fetcher,
                    rate_limiter=rate_limiter,
                    fetch_with_retry=fetch_with_retry,
                    build_url=build_url,
                    parse_json=parse_json,
                    raw_dir=instrument_raw_dir,
                    budget=budget,
                )
            )
        network_request_count += request_count
        fetched_ts = tuple(sorted({row.observation_time_utc for row in normalized_rows}))
        fetch_results.append(
            InstrumentFetchResultV0(
                instrument_id=binding.instrument_id,
                native_instrument_id=binding.native_instrument_id,
                observation_count=len(normalized_rows),
                fetched_timestamps_utc=fetched_ts,
                fail_reason=fail_reason,
                request_count=request_count,
            )
        )
        if fail_reason:
            return MultiInstrumentAcquisitionResultV0(
                status=AcquisitionTerminalStatus.FAIL_CLOSED_FETCH,
                selected_instruments=selected,
                fetch_results=tuple(fetch_results),
                appended_observation_count=0,
                observations_jsonl_byte_identical_prefix=True,
                network_request_count=network_request_count,
                instrument_count_before=instrument_count_before,
                instrument_count_after=instrument_count_before,
                observation_count_before=observation_count_before,
                observation_count_after=observation_count_before,
                archive_integrity_pass=False,
                full_history_zero_gap_pass=False,
                materialization_admissible=False,
                reason_codes=(fail_reason,),
            )
        try:
            forward_obs = normalized_rows_to_forward_observations_v0(
                normalized_rows,
                collected_at_utc=collected_at_utc,
            )
        except ValueError as exc:
            return MultiInstrumentAcquisitionResultV0(
                status=AcquisitionTerminalStatus.FAIL_CLOSED_APPEND,
                selected_instruments=selected,
                fetch_results=tuple(fetch_results),
                appended_observation_count=0,
                observations_jsonl_byte_identical_prefix=True,
                network_request_count=network_request_count,
                instrument_count_before=instrument_count_before,
                instrument_count_after=instrument_count_before,
                observation_count_before=observation_count_before,
                observation_count_after=observation_count_before,
                archive_integrity_pass=False,
                full_history_zero_gap_pass=False,
                materialization_admissible=False,
                reason_codes=(str(exc),),
            )
        state = InstrumentArchiveStateV0(
            instrument_id=binding.instrument_id,
            native_instrument_id=binding.native_instrument_id,
        )
        for obs in forward_obs:
            append_result = append_forward_observation_v0(
                state,
                obs,
                preconditions_checked=True,
            )
            if append_result.verdict.value not in {"APPENDED", "DUPLICATE_SKIPPED"}:
                return MultiInstrumentAcquisitionResultV0(
                    status=AcquisitionTerminalStatus.FAIL_CLOSED_APPEND,
                    selected_instruments=selected,
                    fetch_results=tuple(fetch_results),
                    appended_observation_count=0,
                    observations_jsonl_byte_identical_prefix=True,
                    network_request_count=network_request_count,
                    instrument_count_before=instrument_count_before,
                    instrument_count_after=instrument_count_before,
                    observation_count_before=observation_count_before,
                    observation_count_after=observation_count_before,
                    archive_integrity_pass=False,
                    full_history_zero_gap_pass=False,
                    materialization_admissible=False,
                    reason_codes=(append_result.reason_code or append_result.verdict.value,),
                )
            if append_result.verdict.value == "APPENDED":
                rows_to_append.append(serialize_observation_v0(obs))

    if validate_only or not execute_mutation:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.VALIDATE_ONLY_PASS,
            selected_instruments=selected,
            fetch_results=tuple(fetch_results),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=True,
            network_request_count=network_request_count,
            instrument_count_before=instrument_count_before,
            instrument_count_after=instrument_count_before + len(selected),
            observation_count_before=observation_count_before,
            observation_count_after=observation_count_before + len(rows_to_append),
            archive_integrity_pass=True,
            full_history_zero_gap_pass=True,
            materialization_admissible=False,
            reason_codes=(),
        )

    prior_snapshot_dir = _snapshot_prior_archive_state_v0(target_archive_path)
    prefix_ok, appended_count = append_new_instrument_rows_preserving_prefix_v0(
        target_archive_path=target_archive_path,
        prior_observations_lines=prior_lines,
        new_rows=rows_to_append,
    )
    if not prefix_ok:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_ETH_PREFIX,
            selected_instruments=selected,
            fetch_results=tuple(fetch_results),
            appended_observation_count=0,
            observations_jsonl_byte_identical_prefix=False,
            network_request_count=network_request_count,
            instrument_count_before=instrument_count_before,
            instrument_count_after=instrument_count_before,
            observation_count_before=observation_count_before,
            observation_count_after=observation_count_before,
            archive_integrity_pass=False,
            full_history_zero_gap_pass=False,
            materialization_admissible=False,
            reason_codes=("OBSERVATIONS_JSONL_PREFIX_DRIFT",),
        )

    merged_rows = [
        json.loads(line)
        for line in _load_observations_jsonl_lines(
            target_archive_path / OBSERVATIONS_JSONL_FILENAME
        )
    ]
    _update_archive_manifest_v0(
        target_archive_path=target_archive_path,
        observation_rows=merged_rows,
    )
    write_manifest_sha256_v0(target_archive_path)

    validation = validate_post_acquisition_v0(
        target_archive_path=target_archive_path,
        prior_snapshot_dir=prior_snapshot_dir,
        as_of_utc=as_of_utc,
    )
    if not validation["archive_integrity_pass"]:
        return MultiInstrumentAcquisitionResultV0(
            status=AcquisitionTerminalStatus.FAIL_CLOSED_VALIDATION,
            selected_instruments=selected,
            fetch_results=tuple(fetch_results),
            appended_observation_count=appended_count,
            observations_jsonl_byte_identical_prefix=True,
            network_request_count=network_request_count,
            instrument_count_before=instrument_count_before,
            instrument_count_after=validation["instrument_count_after"],
            observation_count_before=observation_count_before,
            observation_count_after=validation["observation_count_after"],
            archive_integrity_pass=False,
            full_history_zero_gap_pass=validation["full_history_zero_gap_pass"],
            materialization_admissible=validation["materialization_admissible"],
            reason_codes=("ARCHIVE_INTEGRITY_FAIL",),
        )

    return MultiInstrumentAcquisitionResultV0(
        status=AcquisitionTerminalStatus.ACQUISITION_COMPLETE,
        selected_instruments=selected,
        fetch_results=tuple(fetch_results),
        appended_observation_count=appended_count,
        observations_jsonl_byte_identical_prefix=True,
        network_request_count=network_request_count,
        instrument_count_before=instrument_count_before,
        instrument_count_after=validation["instrument_count_after"],
        observation_count_before=observation_count_before,
        observation_count_after=validation["observation_count_after"],
        archive_integrity_pass=validation["archive_integrity_pass"],
        full_history_zero_gap_pass=validation["full_history_zero_gap_pass"],
        materialization_admissible=validation["materialization_admissible"],
        reason_codes=(),
    )


def result_to_report_dict_v0(result: MultiInstrumentAcquisitionResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "selected_instruments": [
            {
                "instrument_id": item.instrument_id,
                "native_instrument_id": item.native_instrument_id,
            }
            for item in result.selected_instruments
        ],
        "fetch_results": [
            {
                "instrument_id": item.instrument_id,
                "native_instrument_id": item.native_instrument_id,
                "observation_count": item.observation_count,
                "fetched_timestamps_utc": list(item.fetched_timestamps_utc),
                "fail_reason": item.fail_reason,
                "request_count": item.request_count,
            }
            for item in result.fetch_results
        ],
        "appended_observation_count": result.appended_observation_count,
        "observations_jsonl_byte_identical_prefix": result.observations_jsonl_byte_identical_prefix,
        "network_request_count": result.network_request_count,
        "instrument_count_before": result.instrument_count_before,
        "instrument_count_after": result.instrument_count_after,
        "observation_count_before": result.observation_count_before,
        "observation_count_after": result.observation_count_after,
        "archive_integrity_pass": result.archive_integrity_pass,
        "full_history_zero_gap_pass": result.full_history_zero_gap_pass,
        "materialization_admissible": result.materialization_admissible,
        "reason_codes": list(result.reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def compute_module_digest_v0() -> str:
    return hashlib.sha256(
        json.dumps(build_orchestration_config_v0(), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
