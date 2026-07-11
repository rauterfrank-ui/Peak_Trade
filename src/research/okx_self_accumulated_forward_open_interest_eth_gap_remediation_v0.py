"""Bounded ETH PT1H open-interest gap remediation for self-accumulated archive v0.

Public read-only OKX fetch via paginate_bounded_open_interest_v0, gap-insert archive
correction via the canonical correction owner, and effective-archive-view helpers.
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
    ForwardOpenInterestObservationV0,
    OBSERVATIONS_JSONL_FILENAME,
    observation_from_normalized_v0,
    observation_from_row_dict_v0,
    serialize_observation_v0,
)

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ETH_GAP_REMEDIATION_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_eth_gap_remediation.v0"
CONFIRM_GO = "GO_CORE_SYSTEM_DEVELOPMENT_SELF_ACCUMULATED_OI_ETH_GAP_REMEDIATION_IMPLEMENTATION_V0"

ETH_INSTRUMENT_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
ETH_NATIVE_INSTRUMENT_ID = "ETH-USDT-SWAP"

REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC: tuple[str, ...] = (
    "2026-07-11T13:00:00Z",
    "2026-07-11T14:00:00Z",
    "2026-07-11T15:00:00Z",
    "2026-07-11T16:00:00Z",
    "2026-07-11T17:00:00Z",
    "2026-07-11T18:00:00Z",
    "2026-07-11T19:00:00Z",
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class GapFetchValidationVerdict(str, Enum):
    PASS = "PASS"
    FAIL_MISSING_BAR = "FAIL_MISSING_BAR"
    FAIL_UNEXPECTED_BAR = "FAIL_UNEXPECTED_BAR"
    FAIL_DUPLICATE_BAR = "FAIL_DUPLICATE_BAR"
    FAIL_WRONG_INSTRUMENT = "FAIL_WRONG_INSTRUMENT"
    FAIL_WRONG_INTERVAL = "FAIL_WRONG_INTERVAL"
    FAIL_FETCH = "FAIL_FETCH"


@dataclass(frozen=True)
class GapFetchValidationResultV0:
    verdict: GapFetchValidationVerdict
    requested_timestamps_utc: tuple[str, ...]
    fetched_timestamps_utc: tuple[str, ...]
    unexpected_timestamps_utc: tuple[str, ...]
    duplicate_timestamps_utc: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class EthGapRemediationResultV0:
    status: str
    fetch_validation: GapFetchValidationResultV0
    correction_status: str | None
    gap_insert_count: int
    observations_jsonl_byte_identical: bool
    correction_idempotent: bool
    reason_codes: tuple[str, ...]


def _parse_utc_ms(value: str) -> int:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def required_missing_venue_timestamps_ms_v0() -> tuple[int, ...]:
    return tuple(_parse_utc_ms(ts) for ts in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC)


def compute_eth_gap_fetch_window_v0() -> Any:
    start_ms = _parse_utc_ms(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[0])
    end_ms = _parse_utc_ms(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[-1]) + BAR_INTERVAL_MS
    return compute_open_interest_bounded_window_v0(
        start_inclusive_utc=REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC[0],
        end_exclusive_utc=_format_utc_ms(end_ms),
        lookback_k=0,
        signal_lag_bars=0,
    )


def validate_fetched_gap_bars_v0(
    observations: Sequence[NormalizedOpenInterestObservationV0],
    *,
    instrument_id: str = ETH_INSTRUMENT_ID,
    native_instrument_id: str = ETH_NATIVE_INSTRUMENT_ID,
    required_timestamps_utc: Sequence[str] = REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
) -> GapFetchValidationResultV0:
    required_set = set(required_timestamps_utc)
    fetched: list[str] = []
    unexpected: list[str] = []
    duplicates: list[str] = []
    reasons: list[str] = []

    seen: set[str] = set()
    for obs in observations:
        if obs.instrument_id != instrument_id:
            reasons.append(GapFetchValidationVerdict.FAIL_WRONG_INSTRUMENT.value)
            return GapFetchValidationResultV0(
                verdict=GapFetchValidationVerdict.FAIL_WRONG_INSTRUMENT,
                requested_timestamps_utc=tuple(required_timestamps_utc),
                fetched_timestamps_utc=tuple(),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=tuple(reasons),
            )
        if obs.native_instrument_id != native_instrument_id:
            reasons.append(GapFetchValidationVerdict.FAIL_WRONG_INSTRUMENT.value)
            return GapFetchValidationResultV0(
                verdict=GapFetchValidationVerdict.FAIL_WRONG_INSTRUMENT,
                requested_timestamps_utc=tuple(required_timestamps_utc),
                fetched_timestamps_utc=tuple(),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=tuple(reasons),
            )
        ts_utc = obs.observation_time_utc
        if ts_utc in seen:
            duplicates.append(ts_utc)
        seen.add(ts_utc)
        if ts_utc in required_set:
            fetched.append(ts_utc)
        else:
            unexpected.append(ts_utc)

    if duplicates:
        reasons.append(GapFetchValidationVerdict.FAIL_DUPLICATE_BAR.value)
        return GapFetchValidationResultV0(
            verdict=GapFetchValidationVerdict.FAIL_DUPLICATE_BAR,
            requested_timestamps_utc=tuple(required_timestamps_utc),
            fetched_timestamps_utc=tuple(sorted(fetched)),
            unexpected_timestamps_utc=tuple(sorted(unexpected)),
            duplicate_timestamps_utc=tuple(sorted(set(duplicates))),
            reason_codes=tuple(reasons),
        )
    if unexpected:
        reasons.append(GapFetchValidationVerdict.FAIL_UNEXPECTED_BAR.value)
        return GapFetchValidationResultV0(
            verdict=GapFetchValidationVerdict.FAIL_UNEXPECTED_BAR,
            requested_timestamps_utc=tuple(required_timestamps_utc),
            fetched_timestamps_utc=tuple(sorted(fetched)),
            unexpected_timestamps_utc=tuple(sorted(unexpected)),
            duplicate_timestamps_utc=tuple(),
            reason_codes=tuple(reasons),
        )
    missing = sorted(required_set - set(fetched))
    if missing:
        reasons.append(GapFetchValidationVerdict.FAIL_MISSING_BAR.value)
        return GapFetchValidationResultV0(
            verdict=GapFetchValidationVerdict.FAIL_MISSING_BAR,
            requested_timestamps_utc=tuple(required_timestamps_utc),
            fetched_timestamps_utc=tuple(sorted(fetched)),
            unexpected_timestamps_utc=tuple(),
            duplicate_timestamps_utc=tuple(),
            reason_codes=tuple(reasons + [f"MISSING:{ts}" for ts in missing]),
        )
    return GapFetchValidationResultV0(
        verdict=GapFetchValidationVerdict.PASS,
        requested_timestamps_utc=tuple(required_timestamps_utc),
        fetched_timestamps_utc=tuple(sorted(fetched)),
        unexpected_timestamps_utc=tuple(),
        duplicate_timestamps_utc=tuple(),
        reason_codes=tuple(),
    )


def normalized_rows_to_gap_insert_observations_v0(
    rows: Sequence[NormalizedOpenInterestObservationV0],
    *,
    collected_at_utc: str,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item.observation_time_ms):
        if row.observation_time_utc not in REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC:
            continue
        obs = observation_from_normalized_v0(
            row,
            collected_at_utc=collected_at_utc,
            collection_mode=COLLECTION_MODE_FORWARD_ONLY,
        )
        if obs is None:
            raise ValueError(f"INVALID_GAP_INSERT_NORMALIZATION:{row.observation_time_utc}")
        payload = serialize_observation_v0(obs)
        if payload["bar_interval"] != BAR_INTERVAL:
            raise ValueError(GapFetchValidationVerdict.FAIL_WRONG_INTERVAL.value)
        observations.append(payload)
    if len(observations) != len(REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC):
        raise ValueError(GapFetchValidationVerdict.FAIL_MISSING_BAR.value)
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


def build_eth_gap_insert_bound_execution_plan_v0(
    *,
    target_archive_path: Path,
    gap_insert_rows: Sequence[Mapping[str, Any]],
    collection_execution_id: str,
    evidence_ref: str,
) -> dict[str, Any]:
    before_digest = _archive_digest(target_archive_path)
    generation_suffix = "eth_gap_insert_v0"
    return {
        "schema_version": BOUND_EXECUTION_PLAN_SCHEMA_VERSION,
        "operator_go": CONFIRM_GO_EXECUTION,
        "execution_authorized": True,
        "target_archive_path": str(target_archive_path),
        "before_archive_digest": before_digest,
        "expected_after_archive_digest": f"{before_digest}:{generation_suffix}",
        "fixture_observations_to_preserve": _load_observation_digests(target_archive_path),
        "corrected_observations": [dict(row) for row in gap_insert_rows],
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


def fetch_bounded_eth_gap_bars_v0(
    *,
    fetcher: PublicGetFetcher,
    rate_limiter: Callable[[], None],
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, dict[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
) -> tuple[list[NormalizedOpenInterestObservationV0], GapFetchValidationResultV0, str | None]:
    window = compute_eth_gap_fetch_window_v0()
    budget = OpenInterestFetchBudgetGuardV0(
        max_instruments=1,
        max_pages_per_instrument=3,
        max_total_requests=3,
        max_total_raw_bytes=5_000_000,
        max_runtime_seconds=120,
        max_consecutive_empty_pages=1,
    )
    observations, fail_reason = paginate_bounded_open_interest_v0(
        instrument_id=ETH_INSTRUMENT_ID,
        native_instrument_id=ETH_NATIVE_INSTRUMENT_ID,
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
        validation = GapFetchValidationResultV0(
            verdict=GapFetchValidationVerdict.FAIL_FETCH,
            requested_timestamps_utc=REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
            fetched_timestamps_utc=tuple(),
            unexpected_timestamps_utc=tuple(),
            duplicate_timestamps_utc=tuple(),
            reason_codes=(fail_reason,),
        )
        return observations, validation, fail_reason
    validation = validate_fetched_gap_bars_v0(observations)
    return observations, validation, None


def execute_eth_gap_remediation_v0(
    *,
    confirm: str,
    enabled: bool,
    target_archive_path: Path,
    collected_at_utc: str,
    collection_execution_id: str,
    evidence_ref: str,
    fetcher: PublicGetFetcher,
    rate_limiter: Callable[[], None],
    fetch_with_retry: Callable[..., tuple[int, bytes, dict[str, str]]],
    build_url: Callable[[str, dict[str, str]], str],
    parse_json: Callable[[bytes], dict[str, Any]],
    raw_dir: Path,
    execute_mutation: bool,
) -> EthGapRemediationResultV0:
    if confirm != CONFIRM_GO:
        return EthGapRemediationResultV0(
            status="FAIL_CLOSED_OPERATOR_GO",
            fetch_validation=GapFetchValidationResultV0(
                verdict=GapFetchValidationVerdict.FAIL_FETCH,
                requested_timestamps_utc=REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
                fetched_timestamps_utc=tuple(),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=("OPERATOR_GO_MISMATCH",),
            ),
            correction_status=None,
            gap_insert_count=0,
            observations_jsonl_byte_identical=True,
            correction_idempotent=False,
            reason_codes=("OPERATOR_GO_MISMATCH",),
        )
    if not enabled:
        return EthGapRemediationResultV0(
            status="FAIL_CLOSED_DEFAULT_OFF",
            fetch_validation=GapFetchValidationResultV0(
                verdict=GapFetchValidationVerdict.FAIL_FETCH,
                requested_timestamps_utc=REQUIRED_MISSING_VENUE_TIMESTAMPS_UTC,
                fetched_timestamps_utc=tuple(),
                unexpected_timestamps_utc=tuple(),
                duplicate_timestamps_utc=tuple(),
                reason_codes=("DEFAULT_OFF",),
            ),
            correction_status=None,
            gap_insert_count=0,
            observations_jsonl_byte_identical=True,
            correction_idempotent=False,
            reason_codes=("DEFAULT_OFF",),
        )

    before_obs_bytes = (target_archive_path / OBSERVATIONS_JSONL_FILENAME).read_bytes()
    observations, fetch_validation, fail_reason = fetch_bounded_eth_gap_bars_v0(
        fetcher=fetcher,
        rate_limiter=rate_limiter,
        fetch_with_retry=fetch_with_retry,
        build_url=build_url,
        parse_json=parse_json,
        raw_dir=raw_dir,
    )
    if fetch_validation.verdict is not GapFetchValidationVerdict.PASS:
        return EthGapRemediationResultV0(
            status="FAIL_CLOSED_FETCH_VALIDATION",
            fetch_validation=fetch_validation,
            correction_status=None,
            gap_insert_count=0,
            observations_jsonl_byte_identical=True,
            correction_idempotent=False,
            reason_codes=fetch_validation.reason_codes + ((fail_reason,) if fail_reason else ()),
        )

    gap_rows = normalized_rows_to_gap_insert_observations_v0(
        observations,
        collected_at_utc=collected_at_utc,
    )
    bound_plan = build_eth_gap_insert_bound_execution_plan_v0(
        target_archive_path=target_archive_path,
        gap_insert_rows=gap_rows,
        collection_execution_id=collection_execution_id,
        evidence_ref=evidence_ref,
    )
    plan_path = raw_dir / "eth_gap_insert_bound_plan.json"
    plan_path.write_text(json.dumps(bound_plan, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    correction = execute_archive_correction_v0(
        confirm=CONFIRM_GO_EXECUTION,
        validate_only=not execute_mutation,
        execute_mutation=execute_mutation,
        enabled=execute_mutation,
        bound_plan_path=plan_path,
        target_archive_path=target_archive_path,
    )
    after_obs_bytes = (target_archive_path / OBSERVATIONS_JSONL_FILENAME).read_bytes()
    observations_unchanged = before_obs_bytes == after_obs_bytes

    idempotent = correction.status in {
        CorrectionExecutionTerminalStatus.ALREADY_APPLIED_NOOP,
        CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE,
        CorrectionExecutionTerminalStatus.VALIDATE_ONLY_PASS,
    }

    status = (
        "REMEDIATION_COMPLETE"
        if correction.status
        in {
            CorrectionExecutionTerminalStatus.EXECUTION_COMPLETE,
            CorrectionExecutionTerminalStatus.ALREADY_APPLIED_NOOP,
        }
        else str(correction.status.value)
    )

    return EthGapRemediationResultV0(
        status=status,
        fetch_validation=fetch_validation,
        correction_status=str(correction.status.value),
        gap_insert_count=len(gap_rows),
        observations_jsonl_byte_identical=observations_unchanged,
        correction_idempotent=idempotent,
        reason_codes=correction.reason_codes,
    )
