"""OKX self-accumulated forward open-interest one-shot collector harness v0.

Default-off, operator-GO-required bounded single-cycle collector wiring public OKX OI
into the canonical self-accumulated archive owner. Research-only; no runtime authority.
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
    SCOPE_STATUS,
    is_scope_parked,
    is_self_accumulated_archive_allowed,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    SOURCE_ENDPOINT,
    SOURCE_SCHEMA_VERSION,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_KIND,
    ARCHIVE_SCHEMA_VERSION,
    COLLECTION_MODE_FORWARD_ONLY,
    CONFIRM_GO as ARCHIVE_CONFIRM_GO,
    MODULE_VERSION as ARCHIVE_MODULE_VERSION,
    OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
    ArchiveAppendResultV0,
    ArchiveAppendVerdict,
    ForwardOpenInterestObservationV0,
    InstrumentArchiveStateV0,
    append_forward_observation_v0,
    assess_gap_and_staleness_v0,
    assert_archive_preconditions_v0,
    build_overlap_validation_readiness_v0,
    compute_implementation_digest_v0 as compute_archive_implementation_digest_v0,
    normalize_forward_open_interest_observation_v0,
    persist_archive_snapshot_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    validate_instrument_for_forward_archive_v0,
    write_manifest_sha256_v0,
)

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ONE_SHOT_COLLECTOR_HARNESS_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_one_shot_collector_harness.v0"
CONFIRM_GO = "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ONE_SHOT_COLLECTOR_HARNESS_V0"
CONFIG_REL_PATH = (
    "config/research/okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0.json"
)

DEFAULT_ENABLED = False
OPERATOR_GO_REQUIRED = True
EXACTLY_ONE_COLLECTION_CYCLE = True
BOUNDED_EXECUTION = True
PUBLIC_READ_ONLY_OKX_ENDPOINTS_ONLY = True
NO_CREDENTIALS = True
NO_SCHEDULER = True
NO_DAEMON = True
NO_LOOPING = True
NO_RETRY_LOOP = True
MAX_REQUESTS_PER_CYCLE = 1
MAX_INSTRUMENTS_PER_CYCLE = 1
OKX_PERIOD = "1H"
PAGE_LIMIT = "1"

PublicGetFetcher = Callable[..., tuple[int, bytes, dict[str, str]]]


class CollectionMode(str, Enum):
    VALIDATE_ONLY = "validate-only"
    COLLECT_ONCE = "collect-once"


class HarnessTerminalVerdict(str, Enum):
    VALIDATE_ONLY_PASS = "VALIDATE_ONLY_PASS"
    COLLECT_ONCE_COMPLETE = "COLLECT_ONCE_COMPLETE"
    FAIL_CLOSED_GO_TOKEN = "FAIL_CLOSED_GO_TOKEN"
    FAIL_CLOSED_DEFAULT_OFF = "FAIL_CLOSED_DEFAULT_OFF"
    FAIL_CLOSED_INELIGIBLE_INSTRUMENT = "FAIL_CLOSED_INELIGIBLE_INSTRUMENT"
    FAIL_CLOSED_FETCH = "FAIL_CLOSED_FETCH"
    FAIL_CLOSED_NORMALIZATION = "FAIL_CLOSED_NORMALIZATION"
    FAIL_CLOSED_APPEND = "FAIL_CLOSED_APPEND"
    FAIL_CLOSED_PERSISTENCE = "FAIL_CLOSED_PERSISTENCE"
    FAIL_CLOSED_SCOPE = "FAIL_CLOSED_SCOPE"


@dataclass(frozen=True)
class OneShotCollectorPolicyContractV0:
    default_enabled: bool
    operator_go_required: bool
    exactly_one_collection_cycle: bool
    bounded_execution: bool
    public_read_only_okx_endpoints_only: bool
    no_credentials: bool
    no_scheduler: bool
    no_daemon: bool
    no_looping: bool
    no_retry_loop: bool
    no_runtime_authority: bool
    no_trading_authority: bool
    research_scope_remains_parked: bool
    overlap_validation_executed: bool


@dataclass(frozen=True)
class OneShotCollectorCliContractV0:
    confirm_parameter: str
    mode_parameter: str
    output_dir_parameter: str
    instrument_file_parameter: str
    fixture_response_parameter: str
    collected_at_utc_parameter: str
    default_mode: str
    machine_readable_final_report: bool
    non_zero_exit_on_policy_failure: bool


@dataclass
class OneShotCollectionCycleResultV0:
    verdict: HarnessTerminalVerdict
    mode: CollectionMode
    instrument_id: str | None
    native_instrument_id: str | None
    observation: ForwardOpenInterestObservationV0 | None
    append_result: ArchiveAppendResultV0 | None
    gap_staleness: dict[str, Any] | None
    overlap_readiness: dict[str, Any] | None
    archive_manifest: dict[str, Any] | None
    evidence_dir: str | None
    request_count: int
    persisted: bool
    reason_codes: tuple[str, ...] = ()
    run_digest: str | None = None


def serialize_canonical_json_local(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_harness_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json_local(
            {
                "module": "okx_self_accumulated_forward_open_interest_one_shot_collector_harness_v0",
                "module_version": MODULE_VERSION,
                "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
                "confirm_go": CONFIRM_GO,
                "max_requests_per_cycle": MAX_REQUESTS_PER_CYCLE,
                "max_instruments_per_cycle": MAX_INSTRUMENTS_PER_CYCLE,
                "source_endpoint": SOURCE_ENDPOINT,
            }
        ).encode("utf-8")
    ).hexdigest()


def build_policy_contract_v0() -> OneShotCollectorPolicyContractV0:
    return OneShotCollectorPolicyContractV0(
        default_enabled=DEFAULT_ENABLED,
        operator_go_required=OPERATOR_GO_REQUIRED,
        exactly_one_collection_cycle=EXACTLY_ONE_COLLECTION_CYCLE,
        bounded_execution=BOUNDED_EXECUTION,
        public_read_only_okx_endpoints_only=PUBLIC_READ_ONLY_OKX_ENDPOINTS_ONLY,
        no_credentials=NO_CREDENTIALS,
        no_scheduler=NO_SCHEDULER,
        no_daemon=NO_DAEMON,
        no_looping=NO_LOOPING,
        no_retry_loop=NO_RETRY_LOOP,
        no_runtime_authority=True,
        no_trading_authority=True,
        research_scope_remains_parked=True,
        overlap_validation_executed=False,
    )


def build_cli_contract_v0() -> OneShotCollectorCliContractV0:
    return OneShotCollectorCliContractV0(
        confirm_parameter="--confirm-go-token",
        mode_parameter="--mode",
        output_dir_parameter="--output-dir",
        instrument_file_parameter="--instrument-file",
        fixture_response_parameter="--fixture-response",
        collected_at_utc_parameter="--collected-at-utc",
        default_mode=CollectionMode.VALIDATE_ONLY.value,
        machine_readable_final_report=True,
        non_zero_exit_on_policy_failure=True,
    )


def build_harness_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "archive_confirm_go": ARCHIVE_CONFIRM_GO,
        "go_token": CONFIRM_GO,
        "research_scope": RESEARCH_SCOPE,
        "scope_status": SCOPE_STATUS,
        "default_enabled": DEFAULT_ENABLED,
        "operator_go_required": OPERATOR_GO_REQUIRED,
        "exactly_one_collection_cycle": EXACTLY_ONE_COLLECTION_CYCLE,
        "bounded_execution": BOUNDED_EXECUTION,
        "max_requests_per_cycle": MAX_REQUESTS_PER_CYCLE,
        "max_instruments_per_cycle": MAX_INSTRUMENTS_PER_CYCLE,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "bar_interval": BAR_INTERVAL,
        "collection_mode_forward_only": COLLECTION_MODE_FORWARD_ONLY,
        "overlap_validation_status": OVERLAP_VALIDATION_STATUS_NOT_EXECUTED,
        "implementation_digest": compute_harness_implementation_digest_v0(),
        "archive_implementation_digest": compute_archive_implementation_digest_v0(),
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
    }


def validate_operator_go_v0(*, confirm: str | None, enabled: bool = False) -> None:
    if not enabled and DEFAULT_ENABLED is False:
        if confirm != CONFIRM_GO:
            raise ValueError("DEFAULT_OFF_OPERATOR_GO_REQUIRED")
    elif confirm != CONFIRM_GO:
        raise ValueError("INVALID_OPERATOR_GO_TOKEN")


def assert_harness_scope_preconditions_v0() -> None:
    assert_archive_preconditions_v0()
    if not is_scope_parked():
        raise ValueError("RESEARCH_SCOPE_MUST_REMAIN_PARKED")
    if not is_self_accumulated_archive_allowed():
        raise ValueError("SELF_ACCUMULATED_ARCHIVE_NOT_ALLOWED")


def utc_now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_latest_oi_request_url_v0(*, native_instrument_id: str) -> str:
    params = {
        "instId": native_instrument_id,
        "period": OKX_PERIOD,
        "limit": PAGE_LIMIT,
    }
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"https://www.okx.com{SOURCE_ENDPOINT}?{query}"


def parse_latest_forward_oi_row_v0(payload: Mapping[str, Any]) -> list[Any] | None:
    if str(payload.get("code", "")) != "0":
        return None
    rows = payload.get("data") or []
    if not isinstance(rows, list) or not rows:
        return None
    row = rows[0]
    if not isinstance(row, list) or not row:
        return None
    return row


def load_archive_state_from_jsonl_v0(
    *,
    jsonl_path: Path,
    instrument_id: str,
    native_instrument_id: str,
) -> InstrumentArchiveStateV0:
    state = InstrumentArchiveStateV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
    )
    if not jsonl_path.is_file():
        return state
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        obs = ForwardOpenInterestObservationV0(
            instrument_id=row["instrument_id"],
            native_instrument_id=row["native_instrument_id"],
            venue_timestamp_ms=row["venue_timestamp_ms"],
            venue_timestamp_utc=row["venue_timestamp_utc"],
            collected_at_ms=row["collected_at_ms"],
            collected_at_utc=row["collected_at_utc"],
            open_interest_raw=row["open_interest_raw"],
            open_interest_unit=row["open_interest_unit"],
            bar_interval=row["bar_interval"],
            source_schema_version=row["source_schema_version"],
            source_endpoint=row["source_endpoint"],
            source_record_key=row["source_record_key"],
            collection_mode=row["collection_mode"],
            observation_digest=row["observation_digest"],
        )
        append_forward_observation_v0(state, obs, preconditions_checked=True)
    return state


def compute_run_digest_v0(result: Mapping[str, Any]) -> str:
    body = {k: v for k, v in result.items() if k not in {"run_digest"}}
    return hashlib.sha256(serialize_canonical_json_local(body).encode("utf-8")).hexdigest()


def run_one_shot_collection_cycle_v0(
    *,
    confirm: str,
    mode: CollectionMode,
    instrument: Mapping[str, Any],
    output_dir: Path | None = None,
    collected_at_utc: str | None = None,
    fixture_response: Mapping[str, Any] | None = None,
    fetcher: PublicGetFetcher | None = None,
    enabled: bool = False,
) -> OneShotCollectionCycleResultV0:
    """Execute exactly one bounded collection cycle. No retry loop."""
    try:
        validate_operator_go_v0(confirm=confirm, enabled=enabled)
        assert_harness_scope_preconditions_v0()
    except ValueError as exc:
        code = str(exc)
        verdict = (
            HarnessTerminalVerdict.FAIL_CLOSED_GO_TOKEN
            if "GO" in code or "DEFAULT_OFF" in code
            else HarnessTerminalVerdict.FAIL_CLOSED_SCOPE
        )
        return OneShotCollectionCycleResultV0(
            verdict=verdict,
            mode=mode,
            instrument_id=None,
            native_instrument_id=None,
            observation=None,
            append_result=None,
            gap_staleness=None,
            overlap_readiness=None,
            archive_manifest=None,
            evidence_dir=None,
            request_count=0,
            persisted=False,
            reason_codes=(code,),
        )

    eligible, instrument_id, reason = validate_instrument_for_forward_archive_v0(instrument)
    native_instrument_id = str(instrument.get("instId", "")).strip()
    if not eligible or instrument_id is None:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_INELIGIBLE_INSTRUMENT,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id or None,
            observation=None,
            append_result=None,
            gap_staleness=None,
            overlap_readiness=None,
            archive_manifest=None,
            evidence_dir=None,
            request_count=0,
            persisted=False,
            reason_codes=(reason or "INELIGIBLE_INSTRUMENT",),
        )

    request_count = 0
    if fixture_response is not None:
        payload = dict(fixture_response)
    else:
        if fetcher is None:
            return OneShotCollectionCycleResultV0(
                verdict=HarnessTerminalVerdict.FAIL_CLOSED_FETCH,
                mode=mode,
                instrument_id=instrument_id,
                native_instrument_id=native_instrument_id,
                observation=None,
                append_result=None,
                gap_staleness=None,
                overlap_readiness=None,
                archive_manifest=None,
                evidence_dir=None,
                request_count=0,
                persisted=False,
                reason_codes=("FETCHER_REQUIRED_WITHOUT_FIXTURE",),
            )
        url = build_latest_oi_request_url_v0(native_instrument_id=native_instrument_id)
        request_count = 1
        status, body, _ = fetcher(url, timeout_seconds=30.0, max_response_bytes=50_000_000)
        if status < 200 or status >= 300:
            return OneShotCollectionCycleResultV0(
                verdict=HarnessTerminalVerdict.FAIL_CLOSED_FETCH,
                mode=mode,
                instrument_id=instrument_id,
                native_instrument_id=native_instrument_id,
                observation=None,
                append_result=None,
                gap_staleness=None,
                overlap_readiness=None,
                archive_manifest=None,
                evidence_dir=None,
                request_count=request_count,
                persisted=False,
                reason_codes=(f"HTTP_{status}",),
            )
        payload = json.loads(body.decode("utf-8"))

    row = parse_latest_forward_oi_row_v0(payload)
    if row is None:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_FETCH,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=None,
            append_result=None,
            gap_staleness=None,
            overlap_readiness=None,
            archive_manifest=None,
            evidence_dir=None,
            request_count=request_count,
            persisted=False,
            reason_codes=("EMPTY_OR_INVALID_OKX_RESPONSE",),
        )

    collected_at = collected_at_utc or utc_now_rfc3339()
    obs = normalize_forward_open_interest_observation_v0(
        row,
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        collected_at_utc=collected_at,
    )
    if obs is None:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_NORMALIZATION,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=None,
            append_result=None,
            gap_staleness=None,
            overlap_readiness=None,
            archive_manifest=None,
            evidence_dir=None,
            request_count=request_count,
            persisted=False,
            reason_codes=("NORMALIZATION_FAILED",),
        )

    state = InstrumentArchiveStateV0(
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
    )
    prior = None
    if output_dir is not None and mode == CollectionMode.COLLECT_ONCE:
        state = load_archive_state_from_jsonl_v0(
            jsonl_path=output_dir / "observations.jsonl",
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
        )
        if state.observations:
            prior = state.observations[-1]

    append_result = append_forward_observation_v0(state, obs, preconditions_checked=True)
    if append_result.verdict in {
        ArchiveAppendVerdict.CONFLICT_REJECTED,
        ArchiveAppendVerdict.BACKFILL_REJECTED,
        ArchiveAppendVerdict.LOOKAHEAD_REJECTED,
        ArchiveAppendVerdict.ARCHIVE_NOT_ALLOWED,
        ArchiveAppendVerdict.INVALID_OBSERVATION,
    }:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_APPEND,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=obs,
            append_result=append_result,
            gap_staleness=None,
            overlap_readiness=None,
            archive_manifest=None,
            evidence_dir=None,
            request_count=request_count,
            persisted=False,
            reason_codes=(append_result.reason_code or append_result.verdict.value,),
        )

    gap = assess_gap_and_staleness_v0(obs, prior=prior)
    overlap = build_overlap_validation_readiness_v0([state])
    gap_dict = {
        "instrument_id": gap.instrument_id,
        "venue_timestamp_utc": gap.venue_timestamp_utc,
        "status": gap.status.value,
        "prior_venue_timestamp_utc": gap.prior_venue_timestamp_utc,
        "gap_hours": gap.gap_hours,
        "staleness_hours": gap.staleness_hours,
        "collected_at_utc": gap.collected_at_utc,
    }
    overlap_dict = {
        "status": overlap.status,
        "archive_observation_count": overlap.archive_observation_count,
        "earliest_venue_timestamp_utc": overlap.earliest_venue_timestamp_utc,
        "latest_venue_timestamp_utc": overlap.latest_venue_timestamp_utc,
        "overlap_validation_executable": overlap.overlap_validation_executable,
        "overlap_validation_blocked_reason": overlap.overlap_validation_blocked_reason,
    }

    if mode == CollectionMode.VALIDATE_ONLY:
        payload_out = {
            "verdict": HarnessTerminalVerdict.VALIDATE_ONLY_PASS.value,
            "mode": mode.value,
            "instrument_id": instrument_id,
            "native_instrument_id": native_instrument_id,
            "observation": serialize_observation_v0(obs),
            "append_preview_verdict": append_result.verdict.value,
            "gap_staleness": gap_dict,
            "overlap_readiness": overlap_dict,
            "request_count": request_count,
            "persisted": False,
        }
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.VALIDATE_ONLY_PASS,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=obs,
            append_result=append_result,
            gap_staleness=gap_dict,
            overlap_readiness=overlap_dict,
            archive_manifest=None,
            evidence_dir=None,
            request_count=request_count,
            persisted=False,
            run_digest=compute_run_digest_v0(payload_out),
        )

    if output_dir is None:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_PERSISTENCE,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=obs,
            append_result=append_result,
            gap_staleness=gap_dict,
            overlap_readiness=overlap_dict,
            archive_manifest=None,
            evidence_dir=None,
            request_count=request_count,
            persisted=False,
            reason_codes=("OUTPUT_DIR_REQUIRED_FOR_COLLECT_ONCE",),
        )

    try:
        archive_manifest = persist_archive_snapshot_v0([state], output_dir=output_dir)
        write_manifest_sha256_v0(output_dir)
    except (OSError, ValueError) as exc:
        return OneShotCollectionCycleResultV0(
            verdict=HarnessTerminalVerdict.FAIL_CLOSED_PERSISTENCE,
            mode=mode,
            instrument_id=instrument_id,
            native_instrument_id=native_instrument_id,
            observation=obs,
            append_result=append_result,
            gap_staleness=gap_dict,
            overlap_readiness=overlap_dict,
            archive_manifest=None,
            evidence_dir=str(output_dir),
            request_count=request_count,
            persisted=False,
            reason_codes=(str(exc),),
        )

    payload_out = {
        "verdict": HarnessTerminalVerdict.COLLECT_ONCE_COMPLETE.value,
        "mode": mode.value,
        "instrument_id": instrument_id,
        "native_instrument_id": native_instrument_id,
        "observation": serialize_observation_v0(obs),
        "append_verdict": append_result.verdict.value,
        "gap_staleness": gap_dict,
        "overlap_readiness": overlap_dict,
        "archive_manifest": archive_manifest,
        "request_count": request_count,
        "persisted": True,
        "archive_kind": ARCHIVE_KIND,
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "archive_module_version": ARCHIVE_MODULE_VERSION,
    }
    return OneShotCollectionCycleResultV0(
        verdict=HarnessTerminalVerdict.COLLECT_ONCE_COMPLETE,
        mode=mode,
        instrument_id=instrument_id,
        native_instrument_id=native_instrument_id,
        observation=obs,
        append_result=append_result,
        gap_staleness=gap_dict,
        overlap_readiness=overlap_dict,
        archive_manifest=archive_manifest,
        evidence_dir=str(output_dir),
        request_count=request_count,
        persisted=True,
        run_digest=compute_run_digest_v0(payload_out),
    )


def result_to_final_report_dict_v0(result: OneShotCollectionCycleResultV0) -> dict[str, Any]:
    return {
        "verdict": result.verdict.value,
        "mode": result.mode.value,
        "instrument_id": result.instrument_id,
        "native_instrument_id": result.native_instrument_id,
        "observation_digest": result.observation.observation_digest if result.observation else None,
        "append_verdict": result.append_result.verdict.value if result.append_result else None,
        "gap_staleness": result.gap_staleness,
        "overlap_readiness": result.overlap_readiness,
        "archive_manifest": result.archive_manifest,
        "evidence_dir": result.evidence_dir,
        "request_count": result.request_count,
        "persisted": result.persisted,
        "reason_codes": list(result.reason_codes),
        "run_digest": result.run_digest,
        "research_scope": RESEARCH_SCOPE,
        "scope_status": SCOPE_STATUS,
        "overlap_validation_executed": False,
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
    }
