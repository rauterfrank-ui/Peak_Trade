"""OKX self-accumulated forward open-interest archive integrity audit v0.

Offline-only deterministic validation boundary for archive snapshots.
Reuses canonical archive serialization, digest, and manifest owners. Research-only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    RESEARCH_SCOPE,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (
    ARCHIVE_KIND,
    ARCHIVE_MANIFEST_FILENAME,
    ARCHIVE_SCHEMA_VERSION,
    MANIFEST_SHA256_FILENAME,
    MODULE_VERSION as ARCHIVE_MODULE_VERSION,
    OBSERVATIONS_JSONL_FILENAME,
    ForwardOpenInterestObservationV0,
    canonical_observation_key_v0,
    compute_implementation_digest_v0,
    compute_observation_digest_v0,
    observation_from_row_dict_v0,
    serialize_canonical_json,
    serialize_observation_v0,
    verify_manifest_sha256_v0,
    write_manifest_sha256_v0,
)
from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = "OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_INTEGRITY_AUDIT_V0=true"
MODULE_VERSION = "okx_self_accumulated_forward_open_interest_archive_integrity_audit.v0"
CONFIRM_GO = "GO_OKX_SELF_ACCUMULATED_FORWARD_OPEN_INTEREST_ARCHIVE_INTEGRITY_AUDIT_V0"
CONFIG_REL_PATH = (
    "config/research/okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0.json"
)

MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA = 2
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


class ArchiveIntegrityAuditStatus(str, Enum):
    PASS = "PASS"
    VALID_EMPTY = "VALID_EMPTY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FAIL = "FAIL"


class ArchiveIntegrityFailureClass(str, Enum):
    MALFORMED_JSON = "MALFORMED_JSON"
    TRUNCATED_JSONL_LINE = "TRUNCATED_JSONL_LINE"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
    OUT_OF_ORDER_TIMESTAMP = "OUT_OF_ORDER_TIMESTAMP"
    IDEMPOTENT_DUPLICATE = "IDEMPOTENT_DUPLICATE"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    ARCHIVE_DIGEST_MISMATCH = "ARCHIVE_DIGEST_MISMATCH"
    MANIFEST_MISMATCH = "MANIFEST_MISMATCH"
    MANIFEST_MISSING = "MANIFEST_MISSING"
    INVALID_INSTRUMENT_SEMANTICS = "INVALID_INSTRUMENT_SEMANTICS"
    LOOKAHEAD_VIOLATION = "LOOKAHEAD_VIOLATION"
    BITCOIN_INSTRUMENT_BLOCKED = "BITCOIN_INSTRUMENT_BLOCKED"
    HISTORICAL_PREFIX_MUTATED = "HISTORICAL_PREFIX_MUTATED"
    HISTORICAL_ROW_REMOVED = "HISTORICAL_ROW_REMOVED"
    ROUNDTRIP_INSTABILITY = "ROUNDTRIP_INSTABILITY"


@dataclass(frozen=True)
class ArchiveIntegrityAuditResultV0:
    status: ArchiveIntegrityAuditStatus
    snapshot_dir: str
    observation_count: int
    instrument_count: int
    reason_codes: tuple[str, ...] = ()
    failure_classes: tuple[str, ...] = ()
    archive_digest: str | None = None
    manifest_digest_match: bool | None = None
    manifest_sha256_verify_rc: int | None = None
    append_only_prefix_verified: bool | None = None
    jsonl_consistency_verified: bool = False
    digest_chain_verified: bool = False
    deterministic_audit_digest: str | None = None
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT
    economic_evaluation_executed: bool = False


def compute_audit_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json(
            {
                "module": "okx_self_accumulated_forward_open_interest_archive_integrity_audit_v0",
                "module_version": MODULE_VERSION,
                "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
                "confirm_go": CONFIRM_GO,
                "min_observations_for_sufficient_data": MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA,
            }
        ).encode("utf-8")
    ).hexdigest()


def build_audit_config_v0() -> dict[str, Any]:
    return {
        "schema_version": MODULE_VERSION,
        "go_token": CONFIRM_GO,
        "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
        "research_scope": RESEARCH_SCOPE,
        "default_enabled": False,
        "operator_go_required": True,
        "offline_only": True,
        "no_network_collection": True,
        "no_economic_evaluation": True,
        "no_dataset_materialization": True,
        "no_overlap_validation": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "implementation_digest": compute_audit_implementation_digest_v0(),
    }


def _failure_class_for_reason(reason: str) -> str:
    mapping = {
        "MALFORMED_JSON": ArchiveIntegrityFailureClass.MALFORMED_JSON.value,
        "TRUNCATED_JSONL_LINE": ArchiveIntegrityFailureClass.TRUNCATED_JSONL_LINE.value,
        "MISSING_REQUIRED_FIELD": ArchiveIntegrityFailureClass.MISSING_REQUIRED_FIELD.value,
        "INVALID_FIELD_TYPE": ArchiveIntegrityFailureClass.INVALID_FIELD_TYPE.value,
        "DIGEST_MISMATCH": ArchiveIntegrityFailureClass.DIGEST_MISMATCH.value,
        "LOOKAHEAD_VIOLATION": ArchiveIntegrityFailureClass.LOOKAHEAD_VIOLATION.value,
        "BITCOIN_INSTRUMENT_BLOCKED": ArchiveIntegrityFailureClass.BITCOIN_INSTRUMENT_BLOCKED.value,
        "INVALID_BAR_INTERVAL": ArchiveIntegrityFailureClass.SCHEMA_DRIFT.value,
        "INVALID_OPEN_INTEREST_UNIT": ArchiveIntegrityFailureClass.SCHEMA_DRIFT.value,
        "SCHEMA_DRIFT_SOURCE_SCHEMA_VERSION": ArchiveIntegrityFailureClass.SCHEMA_DRIFT.value,
        "SCHEMA_DRIFT_SOURCE_ENDPOINT": ArchiveIntegrityFailureClass.SCHEMA_DRIFT.value,
        "INVALID_COLLECTION_MODE": ArchiveIntegrityFailureClass.SCHEMA_DRIFT.value,
        "OUT_OF_ORDER_TIMESTAMP": ArchiveIntegrityFailureClass.OUT_OF_ORDER_TIMESTAMP.value,
        "CONFLICTING_DUPLICATE": ArchiveIntegrityFailureClass.CONFLICTING_DUPLICATE.value,
        "ARCHIVE_DIGEST_MISMATCH": ArchiveIntegrityFailureClass.ARCHIVE_DIGEST_MISMATCH.value,
        "MANIFEST_MISMATCH": ArchiveIntegrityFailureClass.MANIFEST_MISMATCH.value,
        "MANIFEST_MISSING": ArchiveIntegrityFailureClass.MANIFEST_MISSING.value,
        "HISTORICAL_PREFIX_MUTATED": ArchiveIntegrityFailureClass.HISTORICAL_PREFIX_MUTATED.value,
        "HISTORICAL_ROW_REMOVED": ArchiveIntegrityFailureClass.HISTORICAL_ROW_REMOVED.value,
        "ROUNDTRIP_INSTABILITY": ArchiveIntegrityFailureClass.ROUNDTRIP_INSTABILITY.value,
    }
    return mapping.get(reason, ArchiveIntegrityFailureClass.INVALID_INSTRUMENT_SEMANTICS.value)


def _canonical_row_lines_from_jsonl(jsonl_path: Path) -> list[str]:
    if not jsonl_path.is_file():
        return []
    lines: list[str] = []
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        lines.append(serialize_canonical_json(row))
    return lines


def _verify_historical_prefix_v0(
    *,
    prior_snapshot_dir: Path,
    current_snapshot_dir: Path,
) -> tuple[bool, str | None]:
    prior_lines = _canonical_row_lines_from_jsonl(prior_snapshot_dir / OBSERVATIONS_JSONL_FILENAME)
    current_lines = _canonical_row_lines_from_jsonl(
        current_snapshot_dir / OBSERVATIONS_JSONL_FILENAME
    )
    if len(current_lines) < len(prior_lines):
        return False, "HISTORICAL_ROW_REMOVED"
    for index, prior_line in enumerate(prior_lines):
        if current_lines[index] != prior_line:
            return False, "HISTORICAL_PREFIX_MUTATED"
    return True, None


def _parse_jsonl_rows_v0(
    jsonl_path: Path,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    observations: list[dict[str, Any]] = []
    reason_codes: list[str] = []
    failure_classes: list[str] = []
    if not jsonl_path.is_file():
        return observations, reason_codes, failure_classes
    content = jsonl_path.read_text(encoding="utf-8")
    if content and not content.endswith("\n"):
        reason = "TRUNCATED_JSONL_LINE"
        reason_codes.append(reason)
        failure_classes.append(_failure_class_for_reason(reason))
        return observations, reason_codes, failure_classes
    for line_number, raw in enumerate(content.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            reason = "MALFORMED_JSON"
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            return observations, reason_codes, failure_classes
        if not isinstance(row, dict):
            reason = "INVALID_FIELD_TYPE"
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            return observations, reason_codes, failure_classes
        observations.append(row)
    return observations, reason_codes, failure_classes


def _validate_observation_rows_v0(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[ForwardOpenInterestObservationV0], list[str], list[str], bool]:
    parsed: list[ForwardOpenInterestObservationV0] = []
    reason_codes: list[str] = []
    failure_classes: list[str] = []
    roundtrip_ok = True
    seen: dict[tuple[str, int], ForwardOpenInterestObservationV0] = {}
    last_key_by_instrument: dict[str, int] = {}

    for line_number, row in enumerate(rows, start=1):
        obs, reason = observation_from_row_dict_v0(row)
        if obs is None:
            assert reason is not None
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            return parsed, reason_codes, failure_classes, False

        roundtrip_row = serialize_observation_v0(obs)
        if serialize_canonical_json(roundtrip_row) != serialize_canonical_json(dict(row)):
            reason = "ROUNDTRIP_INSTABILITY"
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            roundtrip_ok = False
            return parsed, reason_codes, failure_classes, False

        key = canonical_observation_key_v0(obs.instrument_id, obs.venue_timestamp_ms)
        prior_ts = last_key_by_instrument.get(obs.instrument_id)
        if prior_ts is not None and obs.venue_timestamp_ms < prior_ts:
            reason = "OUT_OF_ORDER_TIMESTAMP"
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            return parsed, reason_codes, failure_classes, False
        last_key_by_instrument[obs.instrument_id] = obs.venue_timestamp_ms

        existing = seen.get(key)
        if existing is not None:
            if (
                existing.open_interest_raw == obs.open_interest_raw
                and existing.observation_digest == obs.observation_digest
            ):
                continue
            reason = "CONFLICTING_DUPLICATE"
            reason_codes.append(f"{reason}:line={line_number}")
            failure_classes.append(_failure_class_for_reason(reason))
            return parsed, reason_codes, failure_classes, False
        seen[key] = obs
        parsed.append(obs)

    return parsed, reason_codes, failure_classes, roundtrip_ok


def _sorted_serialized_rows(
    observations: Sequence[ForwardOpenInterestObservationV0],
) -> list[dict[str, Any]]:
    rows = [serialize_observation_v0(obs) for obs in observations]
    rows.sort(key=lambda row: (row["instrument_id"], row["venue_timestamp_ms"]))
    return rows


def audit_archive_snapshot_v0(
    *,
    snapshot_dir: Path,
    prior_snapshot_dir: Path | None = None,
    require_manifest_sha256: bool = False,
) -> ArchiveIntegrityAuditResultV0:
    """Audit one offline archive snapshot directory. No network access."""
    jsonl_path = snapshot_dir / OBSERVATIONS_JSONL_FILENAME
    manifest_path = snapshot_dir / ARCHIVE_MANIFEST_FILENAME
    rows_raw, parse_reasons, parse_failures = _parse_jsonl_rows_v0(jsonl_path)
    if parse_reasons:
        return ArchiveIntegrityAuditResultV0(
            status=ArchiveIntegrityAuditStatus.FAIL,
            snapshot_dir=str(snapshot_dir),
            observation_count=0,
            instrument_count=0,
            reason_codes=tuple(parse_reasons),
            failure_classes=tuple(parse_failures),
            jsonl_consistency_verified=False,
        )

    if not rows_raw:
        status = ArchiveIntegrityAuditStatus.VALID_EMPTY
        manifest_sha256_rc: int | None = None
        if (snapshot_dir / MANIFEST_SHA256_FILENAME).is_file():
            manifest_sha256_rc = verify_manifest_sha256_v0(snapshot_dir)
        elif require_manifest_sha256:
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=0,
                instrument_count=0,
                reason_codes=("MANIFEST_MISSING",),
                failure_classes=(ArchiveIntegrityFailureClass.MANIFEST_MISSING.value,),
            )
        result = ArchiveIntegrityAuditResultV0(
            status=status,
            snapshot_dir=str(snapshot_dir),
            observation_count=0,
            instrument_count=0,
            manifest_sha256_verify_rc=manifest_sha256_rc,
            jsonl_consistency_verified=True,
            digest_chain_verified=manifest_path.is_file() is False,
        )
        return _finalize_audit_result_v0(result)

    observations, row_reasons, row_failures, roundtrip_ok = _validate_observation_rows_v0(rows_raw)
    if row_reasons:
        return ArchiveIntegrityAuditResultV0(
            status=ArchiveIntegrityAuditStatus.FAIL,
            snapshot_dir=str(snapshot_dir),
            observation_count=len(observations),
            instrument_count=len({obs.instrument_id for obs in observations}),
            reason_codes=tuple(row_reasons),
            failure_classes=tuple(row_failures),
            jsonl_consistency_verified=False,
            digest_chain_verified=False,
        )

    serialized_rows = _sorted_serialized_rows(observations)
    archive_digest = compute_sha256_digest({"rows": serialized_rows})
    digest_chain_verified = True
    manifest_digest_match: bool | None = None

    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("archive_digest") != archive_digest:
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=len(observations),
                instrument_count=len({obs.instrument_id for obs in observations}),
                reason_codes=("ARCHIVE_DIGEST_MISMATCH",),
                failure_classes=(ArchiveIntegrityFailureClass.ARCHIVE_DIGEST_MISMATCH.value,),
                archive_digest=archive_digest,
                jsonl_consistency_verified=True,
                digest_chain_verified=False,
            )
        if manifest.get("observation_count") != len(observations):
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=len(observations),
                instrument_count=len({obs.instrument_id for obs in observations}),
                reason_codes=("MANIFEST_MISMATCH",),
                failure_classes=(ArchiveIntegrityFailureClass.MANIFEST_MISMATCH.value,),
                archive_digest=archive_digest,
                manifest_digest_match=False,
                jsonl_consistency_verified=True,
                digest_chain_verified=False,
            )
        manifest_digest_match = True
        if manifest.get("implementation_digest") != compute_implementation_digest_v0():
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=len(observations),
                instrument_count=len({obs.instrument_id for obs in observations}),
                reason_codes=("MANIFEST_MISMATCH",),
                failure_classes=(ArchiveIntegrityFailureClass.MANIFEST_MISMATCH.value,),
                archive_digest=archive_digest,
                manifest_digest_match=False,
                jsonl_consistency_verified=True,
                digest_chain_verified=False,
            )

    manifest_sha256_rc: int | None = None
    if (snapshot_dir / MANIFEST_SHA256_FILENAME).is_file():
        manifest_sha256_rc = verify_manifest_sha256_v0(snapshot_dir)
        if manifest_sha256_rc != 0:
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=len(observations),
                instrument_count=len({obs.instrument_id for obs in observations}),
                reason_codes=("MANIFEST_MISMATCH",),
                failure_classes=(ArchiveIntegrityFailureClass.MANIFEST_MISMATCH.value,),
                archive_digest=archive_digest,
                manifest_digest_match=manifest_digest_match,
                manifest_sha256_verify_rc=manifest_sha256_rc,
                jsonl_consistency_verified=True,
                digest_chain_verified=digest_chain_verified,
            )
    elif require_manifest_sha256:
        return ArchiveIntegrityAuditResultV0(
            status=ArchiveIntegrityAuditStatus.FAIL,
            snapshot_dir=str(snapshot_dir),
            observation_count=len(observations),
            instrument_count=len({obs.instrument_id for obs in observations}),
            reason_codes=("MANIFEST_MISSING",),
            failure_classes=(ArchiveIntegrityFailureClass.MANIFEST_MISSING.value,),
            archive_digest=archive_digest,
            jsonl_consistency_verified=True,
            digest_chain_verified=digest_chain_verified,
        )

    append_only_prefix_verified: bool | None = None
    if prior_snapshot_dir is not None:
        prefix_ok, prefix_reason = _verify_historical_prefix_v0(
            prior_snapshot_dir=prior_snapshot_dir,
            current_snapshot_dir=snapshot_dir,
        )
        append_only_prefix_verified = prefix_ok
        if not prefix_ok:
            assert prefix_reason is not None
            return ArchiveIntegrityAuditResultV0(
                status=ArchiveIntegrityAuditStatus.FAIL,
                snapshot_dir=str(snapshot_dir),
                observation_count=len(observations),
                instrument_count=len({obs.instrument_id for obs in observations}),
                reason_codes=(prefix_reason,),
                failure_classes=(_failure_class_for_reason(prefix_reason),),
                archive_digest=archive_digest,
                manifest_digest_match=manifest_digest_match,
                manifest_sha256_verify_rc=manifest_sha256_rc,
                append_only_prefix_verified=False,
                jsonl_consistency_verified=True,
                digest_chain_verified=digest_chain_verified,
            )

    status = ArchiveIntegrityAuditStatus.PASS
    if len(observations) < MIN_OBSERVATIONS_FOR_SUFFICIENT_DATA:
        status = ArchiveIntegrityAuditStatus.INSUFFICIENT_DATA

    result = ArchiveIntegrityAuditResultV0(
        status=status,
        snapshot_dir=str(snapshot_dir),
        observation_count=len(observations),
        instrument_count=len({obs.instrument_id for obs in observations}),
        archive_digest=archive_digest,
        manifest_digest_match=manifest_digest_match,
        manifest_sha256_verify_rc=manifest_sha256_rc,
        append_only_prefix_verified=append_only_prefix_verified,
        jsonl_consistency_verified=True,
        digest_chain_verified=digest_chain_verified and roundtrip_ok,
    )
    return _finalize_audit_result_v0(result)


def _finalize_audit_result_v0(
    result: ArchiveIntegrityAuditResultV0,
) -> ArchiveIntegrityAuditResultV0:
    payload = {
        "status": result.status.value,
        "snapshot_dir": result.snapshot_dir,
        "observation_count": result.observation_count,
        "instrument_count": result.instrument_count,
        "reason_codes": list(result.reason_codes),
        "failure_classes": list(result.failure_classes),
        "archive_digest": result.archive_digest,
        "manifest_digest_match": result.manifest_digest_match,
        "manifest_sha256_verify_rc": result.manifest_sha256_verify_rc,
        "append_only_prefix_verified": result.append_only_prefix_verified,
        "jsonl_consistency_verified": result.jsonl_consistency_verified,
        "digest_chain_verified": result.digest_chain_verified,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
    }
    digest = hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()
    return ArchiveIntegrityAuditResultV0(
        status=result.status,
        snapshot_dir=result.snapshot_dir,
        observation_count=result.observation_count,
        instrument_count=result.instrument_count,
        reason_codes=result.reason_codes,
        failure_classes=result.failure_classes,
        archive_digest=result.archive_digest,
        manifest_digest_match=result.manifest_digest_match,
        manifest_sha256_verify_rc=result.manifest_sha256_verify_rc,
        append_only_prefix_verified=result.append_only_prefix_verified,
        jsonl_consistency_verified=result.jsonl_consistency_verified,
        digest_chain_verified=result.digest_chain_verified,
        deterministic_audit_digest=digest,
        authority_effect=result.authority_effect,
        runtime_effect=result.runtime_effect,
        economic_evaluation_executed=result.economic_evaluation_executed,
    )


def audit_result_to_dict_v0(result: ArchiveIntegrityAuditResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "snapshot_dir": result.snapshot_dir,
        "observation_count": result.observation_count,
        "instrument_count": result.instrument_count,
        "reason_codes": list(result.reason_codes),
        "failure_classes": list(result.failure_classes),
        "archive_digest": result.archive_digest,
        "manifest_digest_match": result.manifest_digest_match,
        "manifest_sha256_verify_rc": result.manifest_sha256_verify_rc,
        "append_only_prefix_verified": result.append_only_prefix_verified,
        "jsonl_consistency_verified": result.jsonl_consistency_verified,
        "digest_chain_verified": result.digest_chain_verified,
        "deterministic_audit_digest": result.deterministic_audit_digest,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "archive_kind": ARCHIVE_KIND,
        "archive_schema_version": ARCHIVE_SCHEMA_VERSION,
        "archive_module_version": ARCHIVE_MODULE_VERSION,
        "audit_module_version": MODULE_VERSION,
    }


def write_audit_evidence_bundle_v0(
    *,
    result: ArchiveIntegrityAuditResultV0,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "integrity_audit_result.json").write_text(
        json.dumps(audit_result_to_dict_v0(result), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "integrity_contract.json").write_text(
        json.dumps(build_audit_config_v0(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256_v0(output_dir)
    return output_dir
