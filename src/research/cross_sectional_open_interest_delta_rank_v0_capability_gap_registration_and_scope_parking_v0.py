"""Capability-gap registration and scope parking for cross_sectional_open_interest_delta_rank/v0.

Registers fail-closed PARKED status after NO_ADMISSIBLE_PUBLIC_HISTORICAL_OI_SOURCE discovery.
Preserves live/forward OI collection and self-accumulated archive path. Research-only.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_CAPABILITY_GAP_REGISTRATION_AND_SCOPE_PARKING_V0=true"
SCHEMA_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking.v0"
)
REGISTRATION_ID = (
    "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0"
)
OPERATOR_GO_TOKEN = "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_CAPABILITY_GAP_REGISTRATION_AND_SCOPE_PARKING_V0"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0.json"
)
DATASET_REGISTRY_REL_PATH = (
    "config/research/cross_sectional_open_interest_delta_rank_v0_dataset_registry_entry_v0.json"
)

RESEARCH_SCOPE = "cross_sectional_open_interest_delta_rank/v0"
STRATEGY_ID = "cross_sectional_open_interest_delta_rank"
STRATEGY_VERSION = "v0"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_open_interest_panel/v0"

CAPABILITY_STATUS = "HISTORICAL_OI_SOURCE_MISSING"
SCOPE_STATUS = "PARKED"
PARKING_CLASS = "EXTERNAL_DATA_CAPABILITY_GAP"
PARK_REASON = "NO_ADMISSIBLE_PUBLIC_HISTORICAL_SOURCE"
SOURCE_CAPABILITY_VERDICT = "NO_ADMISSIBLE_PUBLIC_HISTORICAL_OI_SOURCE_FAIL_CLOSED_CAPABILITY_GAP"

FETCHER_OWNER = "okx_historical_open_interest_public_fetch_v0"
MATERIALIZER_OWNER = (
    "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0"
)
PIT_CONTRACT_OWNER = "cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0"
PANEL_SCHEMA_OWNER = "pit_okx_pt1h_panel_open_interest_dataset_v1"
REUSE_DECISION = "CONSOLIDATE_TO_EXISTING_OWNER"

REOPEN_REQUIRES = "ADMISSIBLE_SOURCE_RATIFICATION_AND_OVERLAP_VALIDATION"
PRIMARY_FORWARD_DATA_PATH = "SELF_ACCUMULATED_HISTORY"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/okx_historical_open_interest_archive_or_extended_retention_capability_slice_read_only_v0_20260710T185257Z"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = (
    "CORE_SYSTEM_DEVELOPMENT_CONTINUE_LIVE_OI_SELF_ACCUMULATED_FORWARD_COLLECTION_V0"
)
NEXT_OPERATOR_GO = "GO_CORE_SYSTEM_DEVELOPMENT_CONTINUE"


class RegistrationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class SourceEvidenceValidation:
    bundle_path: Path
    manifest_verify_rc: int
    manifest_digest: str
    capability_classification: str


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_registration_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "registration_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def verify_manifest_sha256(bundle_dir: Path) -> int:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return 1
    result = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return 0 if result.returncode == 0 else 1


def manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def validate_source_evidence_preconditions(
    *,
    source_evidence_dir: Path = SOURCE_EVIDENCE_DIR,
) -> SourceEvidenceValidation:
    if not source_evidence_dir.is_dir():
        raise ValueError(f"missing_source_evidence_dir:{source_evidence_dir}")
    manifest_verify_rc = verify_manifest_sha256(source_evidence_dir)
    if manifest_verify_rc != 0:
        raise ValueError(f"source_manifest_verify_failed:{source_evidence_dir}")
    classification = _load_json(source_evidence_dir / "capability_classification.json")
    if classification.get("classification") != "NO_ADMISSIBLE_PUBLIC_HISTORICAL_OI_SOURCE":
        raise ValueError("source_capability_classification_mismatch")
    return SourceEvidenceValidation(
        bundle_path=source_evidence_dir,
        manifest_verify_rc=manifest_verify_rc,
        manifest_digest=manifest_file_digest(source_evidence_dir),
        capability_classification=classification["classification"],
    )


def build_scope_parking_guard_report() -> dict[str, Any]:
    return {
        "schema_version": "cross_sectional_open_interest_scope_parking_guard_report.v0",
        "research_scope": RESEARCH_SCOPE,
        "capability_status": CAPABILITY_STATUS,
        "scope_status": SCOPE_STATUS,
        "parking_class": PARKING_CLASS,
        "park_reason": PARK_REASON,
        "retry_allowed": False,
        "unchanged_retry_blocked": True,
        "dataset_materialization_2024_allowed": False,
        "economic_evaluation_allowed": False,
        "window_shortening_allowed": False,
        "speculative_fetcher_allowed": False,
        "public_source_reprobe_required": False,
        "live_oi_collection_blocked": False,
        "self_accumulated_archive_allowed": True,
        "historical_backfill_allowed": False,
        "reopen_requires": REOPEN_REQUIRES,
        "primary_forward_data_path": PRIMARY_FORWARD_DATA_PATH,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
    }


def is_scope_parked(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("scope_status") == SCOPE_STATUS


def is_unchanged_retry_blocked(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("unchanged_retry_blocked") is True


def is_economic_evaluation_allowed(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("economic_evaluation_allowed") is True


def is_dataset_materialization_2024_allowed(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("dataset_materialization_2024_allowed") is True


def is_live_oi_collection_blocked(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("live_oi_collection_blocked") is True


def is_self_accumulated_archive_allowed(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("self_accumulated_archive_allowed") is True


def is_historical_backfill_allowed(*, guard: Mapping[str, Any] | None = None) -> bool:
    report = guard or build_scope_parking_guard_report()
    return report.get("historical_backfill_allowed") is True


def materialize_registration_config(
    *,
    source: SourceEvidenceValidation | None = None,
    registration_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    source = source or validate_source_evidence_preconditions()
    payload: dict[str, Any] = {
        "artifact_kind": REGISTRATION_ID,
        "artifact_version": "v0",
        "schema_version": SCHEMA_VERSION,
        "go_token": OPERATOR_GO_TOKEN,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "dataset_id": DATASET_ID,
        "capability_status": CAPABILITY_STATUS,
        "scope_status": SCOPE_STATUS,
        "parking_class": PARKING_CLASS,
        "park_reason": PARK_REASON,
        "source_capability_verdict": SOURCE_CAPABILITY_VERDICT,
        "source_evidence_dir": str(source.bundle_path),
        "source_manifest_verify_rc": source.manifest_verify_rc,
        "source_manifest_digest": source.manifest_digest,
        "source_capability_classification": source.capability_classification,
        "fetcher_owner": FETCHER_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "pit_contract_owner": PIT_CONTRACT_OWNER,
        "panel_schema_owner": PANEL_SCHEMA_OWNER,
        "reuse_decision": REUSE_DECISION,
        "new_owner_justified": False,
        "dataset_registry_ref": DATASET_REGISTRY_REL_PATH,
        "scope_parking_guard_report": build_scope_parking_guard_report(),
        "retry_allowed": False,
        "unchanged_retry_blocked": True,
        "dataset_materialization_2024_allowed": False,
        "economic_evaluation_allowed": False,
        "window_shortening_allowed": False,
        "speculative_fetcher_allowed": False,
        "public_source_reprobe_required": False,
        "live_oi_collection_blocked": False,
        "self_accumulated_archive_allowed": True,
        "historical_backfill_allowed": False,
        "backfill_validation": "REQUIRED_OVERLAP",
        "reopen_requires": REOPEN_REQUIRES,
        "primary_forward_data_path": PRIMARY_FORWARD_DATA_PATH,
        "live_oi_collection": "CONTINUE",
        "historical_backfill": "DEFERRED",
        "core_system_development": "CONTINUE",
        "runbook_progress": "UNBLOCKED",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "bitcoin_present": False,
        "spot_present": False,
        "public_market_data_only": True,
        "credentials_used": False,
        "offline_only": True,
        "no_runtime_or_promotion_action": True,
        "no_scheduler_runtime": True,
        "no_economic_evaluation": True,
        "no_dataset_materialization": True,
        "no_network_probes": True,
        "no_policy_rescue": True,
        "status": "CAPABILITY_GAP_REGISTRATION_AND_SCOPE_PARKING_COMPLETE",
        "verdict": RegistrationVerdict.PASS.value,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "next_operator_go": NEXT_OPERATOR_GO,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    if registration_evidence_dir is not None:
        payload["registration_evidence_dir"] = str(registration_evidence_dir)
    payload["registration_digest"] = compute_registration_digest(payload)
    return payload


def apply_dataset_registry_parking_fields(
    registry: Mapping[str, Any],
    registration: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(registry)
    dataset_registration = dict(updated.get("dataset_registration", {}))
    dataset_registration.update(
        {
            "dataset_materialized": False,
            "dataset_ready": False,
            "materialization_status": "PARKED_EXTERNAL_DATA_CAPABILITY_GAP",
            "scope_status": SCOPE_STATUS,
            "capability_status": CAPABILITY_STATUS,
            "parking_class": PARKING_CLASS,
            "park_reason": PARK_REASON,
            "retry_allowed": False,
            "unchanged_retry_blocked": True,
            "economic_evaluation_allowed": False,
            "dataset_materialization_2024_allowed": False,
            "live_oi_collection_blocked": False,
            "self_accumulated_archive_allowed": True,
            "historical_backfill_allowed": False,
            "reopen_requires": REOPEN_REQUIRES,
            "primary_forward_data_path": PRIMARY_FORWARD_DATA_PATH,
            "capability_gap_registration_ref": REGISTRATION_ID,
            "source_evidence_ref": registration.get("source_evidence_dir"),
            "source_capability_verdict": registration.get("source_capability_verdict"),
        }
    )
    updated["dataset_registration"] = dataset_registration
    updated["scope_parking"] = registration.get("scope_parking_guard_report", {})
    updated["capability_gap_registration_ref"] = REGISTRATION_ID
    updated["scope_status"] = SCOPE_STATUS
    updated["capability_status"] = CAPABILITY_STATUS
    return updated
