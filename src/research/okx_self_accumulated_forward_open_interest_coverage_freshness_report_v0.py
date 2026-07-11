"""OKX self-accumulated forward open-interest archive coverage/freshness report v0.

Offline-only deterministic report over existing archive snapshots.
Reuses archive v0 and integrity audit v0 owners. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    STALE_THRESHOLD_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0 import (
    MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA,
    ArchiveIntegrityAuditStatus,
    audit_archive_snapshot_v0,
    audit_result_to_dict_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_KIND,
    ARCHIVE_SCHEMA_VERSION,
    BAR_INTERVAL_MS,
    MODULE_VERSION as ARCHIVE_MODULE_VERSION,
    GapStalenessStatus,
    InstrumentArchiveStateV0,
    OBSERVATIONS_JSONL_FILENAME,
    OverlapValidationReadinessV0,
    assess_gap_and_staleness_v0,
    build_overlap_validation_readiness_v0,
    observation_from_row_dict_v0,
    serialize_canonical_json,
    serialize_observation_v0,
)

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_COVERAGE_FRESHNESS_REPORT_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_coverage_freshness_report.v0"
CONFIRM_GO = "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_COVERAGE_FRESHNESS_REPORT_V0"
CONFIG_REL_PATH = (
    "config/research/okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0.json"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NOT_APPLICABLE = "NOT_APPLICABLE"


class CoverageFreshnessArchiveStatus(str, Enum):
    VALID_EMPTY = "VALID_EMPTY"
    NON_EMPTY_VALID = "NON_EMPTY_VALID"
    INVALID_OR_CORRUPT = "INVALID_OR_CORRUPT"
    MISSING_ARCHIVE_ROOT = "MISSING_ARCHIVE_ROOT"
    MISSING_ARCHIVE = "MISSING_ARCHIVE"


class CoverageStatus(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SUFFICIENT = "SUFFICIENT"


class FreshnessStatus(str, Enum):
    VALID_EMPTY = "VALID_EMPTY"
    OK = "OK"
    STALE = "STALE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ContinuityStatus(str, Enum):
    VALID_EMPTY = "VALID_EMPTY"
    OK = "OK"
    GAP = "GAP"
    STALE = "STALE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class CoverageFreshnessReportResultV0:
    schema_version: str
    report_id: str
    archive_root: str
    as_of_utc: str
    archive_status: str
    archive_row_count: int
    archive_instrument_count: int
    earliest_observation_utc: str | None
    latest_observation_utc: str | None
    archive_horizon_seconds: int | None
    freshness_age_seconds: int | str
    freshness_status: str
    continuity_status: str
    coverage_status: str
    integrity_status: str
    sufficient_for_overlap_validation: bool
    sufficient_for_source_ratification: bool
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT
    overlap_readiness: Mapping[str, Any] | None = None
    integrity_audit: Mapping[str, Any] | None = None


def compute_report_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json(
            {
                "module": "okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0",
                "module_version": MODULE_VERSION,
                "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
                "audit_owner": "okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0",
                "confirm_go": CONFIRM_GO,
                "min_observations_for_sufficient_data": MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA,
                "stale_threshold_bars": STALE_THRESHOLD_BARS,
            }
        ).encode("utf-8")
    ).hexdigest()


def build_report_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "audit_owner": "okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0",
        "research_scope": RESEARCH_SCOPE,
        "default_enabled": False,
        "operator_go_required": True,
        "offline_only": True,
        "no_network_collection": True,
        "no_collector_execution": True,
        "no_economic_evaluation": True,
        "no_dataset_materialization": True,
        "no_overlap_validation": True,
        "no_source_ratification": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "implementation_digest": compute_report_implementation_digest_v0(),
    }


def _parse_utc_ms(value: str) -> int:
    from datetime import datetime, timezone

    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _format_utc_ms(ms: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_archive_states_v0(snapshot_dir: Path) -> list[InstrumentArchiveStateV0]:
    jsonl_path = snapshot_dir / OBSERVATIONS_JSONL_FILENAME
    if not jsonl_path.is_file():
        return []
    states_by_id: dict[str, InstrumentArchiveStateV0] = {}
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        obs, reason = observation_from_row_dict_v0(row)
        if obs is None:
            raise ValueError(f"UNEXPECTED_INVALID_ROW:{reason}")
        state = states_by_id.get(obs.instrument_id)
        if state is None:
            state = InstrumentArchiveStateV0(
                instrument_id=obs.instrument_id,
                native_instrument_id=obs.native_instrument_id,
            )
            states_by_id[obs.instrument_id] = state
        state.observations.append(obs)
        state.index_by_venue_ms[obs.venue_timestamp_ms] = obs
    for state in states_by_id.values():
        state.observations.sort(key=lambda o: o.venue_timestamp_ms)
    return list(states_by_id.values())


def _continuity_status_from_states(
    states: Sequence[InstrumentArchiveStateV0],
) -> ContinuityStatus:
    if not states or all(not s.observations for s in states):
        return ContinuityStatus.VALID_EMPTY
    worst = ContinuityStatus.OK
    for state in states:
        prior = None
        for obs in state.observations:
            assessment = assess_gap_and_staleness_v0(obs, prior=prior)
            if assessment.status is GapStalenessStatus.GAP:
                return ContinuityStatus.GAP
            if assessment.status is GapStalenessStatus.STALE:
                worst = ContinuityStatus.STALE
            prior = obs
    return worst


def _freshness_status_from_latest(
    *,
    latest_venue_ms: int | None,
    as_of_ms: int,
) -> tuple[FreshnessStatus, int | str]:
    if latest_venue_ms is None:
        return FreshnessStatus.VALID_EMPTY, NOT_APPLICABLE
    age_seconds = max(0, (as_of_ms - latest_venue_ms) // 1000)
    staleness_hours = (as_of_ms - latest_venue_ms) // BAR_INTERVAL_MS
    if staleness_hours > STALE_THRESHOLD_BARS:
        return FreshnessStatus.STALE, age_seconds
    return FreshnessStatus.OK, age_seconds


def _overlap_readiness_dict(readiness: OverlapValidationReadinessV0) -> dict[str, Any]:
    return {
        "status": readiness.status,
        "archive_observation_count": readiness.archive_observation_count,
        "earliest_venue_timestamp_utc": readiness.earliest_venue_timestamp_utc,
        "latest_venue_timestamp_utc": readiness.latest_venue_timestamp_utc,
        "overlap_validation_executable": readiness.overlap_validation_executable,
        "overlap_validation_blocked_reason": readiness.overlap_validation_blocked_reason,
    }


def _compute_report_id_v0(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "report_id"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _base_result_fields(
    *,
    archive_root: str,
    as_of_utc: str,
    archive_status: CoverageFreshnessArchiveStatus,
    integrity_status: str,
    archive_row_count: int,
    archive_instrument_count: int,
    earliest_observation_utc: str | None,
    latest_observation_utc: str | None,
    archive_horizon_seconds: int | None,
    freshness_age_seconds: int | str,
    freshness_status: FreshnessStatus,
    continuity_status: ContinuityStatus,
    coverage_status: CoverageStatus,
    sufficient_for_overlap_validation: bool,
    sufficient_for_source_ratification: bool,
    reason_codes: Sequence[str] = (),
    overlap_readiness: Mapping[str, Any] | None = None,
    integrity_audit: Mapping[str, Any] | None = None,
) -> CoverageFreshnessReportResultV0:
    payload = {
        "schema_version": MODULE_VERSION,
        "archive_root": archive_root,
        "as_of_utc": as_of_utc,
        "archive_status": archive_status.value,
        "archive_row_count": archive_row_count,
        "archive_instrument_count": archive_instrument_count,
        "earliest_observation_utc": earliest_observation_utc,
        "latest_observation_utc": latest_observation_utc,
        "archive_horizon_seconds": archive_horizon_seconds,
        "freshness_age_seconds": freshness_age_seconds,
        "freshness_status": freshness_status.value,
        "continuity_status": continuity_status.value,
        "coverage_status": coverage_status.value,
        "integrity_status": integrity_status,
        "sufficient_for_overlap_validation": sufficient_for_overlap_validation,
        "sufficient_for_source_ratification": sufficient_for_source_ratification,
        "reason_codes": list(reason_codes),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    report_id = _compute_report_id_v0(payload)
    return CoverageFreshnessReportResultV0(
        report_id=report_id,
        overlap_readiness=dict(overlap_readiness) if overlap_readiness is not None else None,
        integrity_audit=dict(integrity_audit) if integrity_audit is not None else None,
        **payload,
    )


def generate_coverage_freshness_report_v0(
    *,
    archive_root: Path | None,
    as_of_utc: str,
) -> CoverageFreshnessReportResultV0:
    """Generate one offline coverage/freshness report. No network or collector execution."""
    if archive_root is None:
        return _base_result_fields(
            archive_root="",
            as_of_utc=as_of_utc,
            archive_status=CoverageFreshnessArchiveStatus.MISSING_ARCHIVE_ROOT,
            integrity_status=ArchiveIntegrityAuditStatus.FAIL.value,
            archive_row_count=0,
            archive_instrument_count=0,
            earliest_observation_utc=None,
            latest_observation_utc=None,
            archive_horizon_seconds=None,
            freshness_age_seconds=NOT_APPLICABLE,
            freshness_status=FreshnessStatus.NOT_APPLICABLE,
            continuity_status=ContinuityStatus.INSUFFICIENT_DATA,
            coverage_status=CoverageStatus.INSUFFICIENT_DATA,
            sufficient_for_overlap_validation=False,
            sufficient_for_source_ratification=False,
            reason_codes=("MISSING_ARCHIVE_ROOT",),
        )

    archive_root_str = str(archive_root)
    if not archive_root.exists():
        return _base_result_fields(
            archive_root=archive_root_str,
            as_of_utc=as_of_utc,
            archive_status=CoverageFreshnessArchiveStatus.MISSING_ARCHIVE,
            integrity_status=ArchiveIntegrityAuditStatus.FAIL.value,
            archive_row_count=0,
            archive_instrument_count=0,
            earliest_observation_utc=None,
            latest_observation_utc=None,
            archive_horizon_seconds=None,
            freshness_age_seconds=NOT_APPLICABLE,
            freshness_status=FreshnessStatus.NOT_APPLICABLE,
            continuity_status=ContinuityStatus.INSUFFICIENT_DATA,
            coverage_status=CoverageStatus.INSUFFICIENT_DATA,
            sufficient_for_overlap_validation=False,
            sufficient_for_source_ratification=False,
            reason_codes=("MISSING_ARCHIVE",),
        )

    audit = audit_archive_snapshot_v0(snapshot_dir=archive_root)
    audit_dict = audit_result_to_dict_v0(audit)
    as_of_ms = _parse_utc_ms(as_of_utc)

    if audit.status is ArchiveIntegrityAuditStatus.FAIL:
        return _base_result_fields(
            archive_root=archive_root_str,
            as_of_utc=as_of_utc,
            archive_status=CoverageFreshnessArchiveStatus.INVALID_OR_CORRUPT,
            integrity_status=audit.status.value,
            archive_row_count=audit.observation_count,
            archive_instrument_count=audit.instrument_count,
            earliest_observation_utc=None,
            latest_observation_utc=None,
            archive_horizon_seconds=None,
            freshness_age_seconds=NOT_APPLICABLE,
            freshness_status=FreshnessStatus.NOT_APPLICABLE,
            continuity_status=ContinuityStatus.INSUFFICIENT_DATA,
            coverage_status=CoverageStatus.INSUFFICIENT_DATA,
            sufficient_for_overlap_validation=False,
            sufficient_for_source_ratification=False,
            reason_codes=tuple(audit.reason_codes) or ("INTEGRITY_AUDIT_FAIL",),
            integrity_audit=audit_dict,
        )

    if audit.status is ArchiveIntegrityAuditStatus.VALID_EMPTY:
        overlap = build_overlap_validation_readiness_v0([])
        return _base_result_fields(
            archive_root=archive_root_str,
            as_of_utc=as_of_utc,
            archive_status=CoverageFreshnessArchiveStatus.VALID_EMPTY,
            integrity_status=audit.status.value,
            archive_row_count=0,
            archive_instrument_count=0,
            earliest_observation_utc=None,
            latest_observation_utc=None,
            archive_horizon_seconds=None,
            freshness_age_seconds=NOT_APPLICABLE,
            freshness_status=FreshnessStatus.VALID_EMPTY,
            continuity_status=ContinuityStatus.VALID_EMPTY,
            coverage_status=CoverageStatus.INSUFFICIENT_DATA,
            sufficient_for_overlap_validation=False,
            sufficient_for_source_ratification=False,
            reason_codes=("ARCHIVE_EMPTY",),
            overlap_readiness=_overlap_readiness_dict(overlap),
            integrity_audit=audit_dict,
        )

    states = _load_archive_states_v0(archive_root)
    overlap = build_overlap_validation_readiness_v0(states)
    all_obs = [obs for state in states for obs in state.observations]
    earliest_ms = min(o.venue_timestamp_ms for o in all_obs)
    latest_ms = max(o.venue_timestamp_ms for o in all_obs)
    earliest_utc = _format_utc_ms(earliest_ms)
    latest_utc = _format_utc_ms(latest_ms)
    horizon_seconds = max(0, (latest_ms - earliest_ms) // 1000)
    freshness_status, freshness_age = _freshness_status_from_latest(
        latest_venue_ms=latest_ms,
        as_of_ms=as_of_ms,
    )
    continuity_status = _continuity_status_from_states(states)

    if audit.status is ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA:
        coverage_status = CoverageStatus.INSUFFICIENT_DATA
        archive_status = CoverageFreshnessArchiveStatus.NON_EMPTY_VALID
        reason_codes: tuple[str, ...] = ("INSUFFICIENT_OBSERVATION_COUNT",)
    else:
        coverage_status = CoverageStatus.SUFFICIENT
        archive_status = CoverageFreshnessArchiveStatus.NON_EMPTY_VALID
        reason_codes = ()

    sufficient_overlap = (
        overlap.overlap_validation_executable
        and audit.status is ArchiveIntegrityAuditStatus.PASS
        and audit.observation_count >= MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA
    )
    sufficient_ratification = sufficient_overlap

    return _base_result_fields(
        archive_root=archive_root_str,
        as_of_utc=as_of_utc,
        archive_status=archive_status,
        integrity_status=audit.status.value,
        archive_row_count=audit.observation_count,
        archive_instrument_count=audit.instrument_count,
        earliest_observation_utc=earliest_utc,
        latest_observation_utc=latest_utc,
        archive_horizon_seconds=horizon_seconds,
        freshness_age_seconds=freshness_age,
        freshness_status=freshness_status,
        continuity_status=continuity_status,
        coverage_status=coverage_status,
        sufficient_for_overlap_validation=sufficient_overlap,
        sufficient_for_source_ratification=sufficient_ratification,
        reason_codes=reason_codes,
        overlap_readiness=_overlap_readiness_dict(overlap),
        integrity_audit=audit_dict,
    )


def report_result_to_dict_v0(result: CoverageFreshnessReportResultV0) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "report_id": result.report_id,
        "archive_root": result.archive_root,
        "as_of_utc": result.as_of_utc,
        "archive_status": result.archive_status,
        "archive_row_count": result.archive_row_count,
        "archive_instrument_count": result.archive_instrument_count,
        "earliest_observation_utc": result.earliest_observation_utc,
        "latest_observation_utc": result.latest_observation_utc,
        "archive_horizon_seconds": result.archive_horizon_seconds,
        "freshness_age_seconds": result.freshness_age_seconds,
        "freshness_status": result.freshness_status,
        "continuity_status": result.continuity_status,
        "coverage_status": result.coverage_status,
        "integrity_status": result.integrity_status,
        "sufficient_for_overlap_validation": result.sufficient_for_overlap_validation,
        "sufficient_for_source_ratification": result.sufficient_for_source_ratification,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "archive_kind": ARCHIVE_KIND,
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "archive_module_version": ARCHIVE_MODULE_VERSION,
        "report_module_version": MODULE_VERSION,
        "overlap_readiness": result.overlap_readiness,
        "integrity_audit": result.integrity_audit,
    }
