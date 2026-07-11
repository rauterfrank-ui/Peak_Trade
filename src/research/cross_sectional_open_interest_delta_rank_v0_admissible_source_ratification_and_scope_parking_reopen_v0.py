"""Admissible source ratification and scope parking reopen for cross_sectional_open_interest_delta_rank/v0.

Formal offline classification of the corrected self-accumulated OKX forward open-interest
source. Reuses capability-gap registration, overlap validation, archive correction, and
coverage/freshness owners. Research-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0 import (
    CAPABILITY_STATUS as PARKED_CAPABILITY_STATUS,
    CONFIG_REL_PATH as PARKING_CONFIG_REL_PATH,
    DATASET_REGISTRY_REL_PATH,
    PARK_REASON as PARKED_PARK_REASON,
    PARKING_CLASS as PARKED_PARKING_CLASS,
    REGISTRATION_ID as PARKING_REGISTRATION_ID,
    REOPEN_REQUIRES,
    RESEARCH_SCOPE,
    SCOPE_STATUS as PARKED_SCOPE_STATUS,
    STRATEGY_ID,
    STRATEGY_VERSION,
    DATASET_ID,
    compute_registration_digest,
    materialize_registration_config,
    serialize_canonical_json,
    validate_source_evidence_preconditions,
)
from src.research.okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0 import (
    generate_coverage_freshness_report_v0,
    report_result_to_dict_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_overlap_validation_v0 import (
    OverlapValidationStatus,
    OverlapValidationVerdict,
    validate_overlap_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_ADMISSIBLE_SOURCE_RATIFICATION_"
    "AND_SCOPE_PARKING_REOPEN_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_"
    "and_scope_parking_reopen.v0"
)
RATIFICATION_ID = (
    "cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_"
    "and_scope_parking_reopen_v0"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_ADMISSIBLE_SOURCE_RATIFICATION_"
    "AND_SCOPE_PARKING_REOPEN_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_admissible_source_ratification_"
    "and_scope_parking_reopen_v0.json"
)
ENTRY_POINT = "scripts/ops/ratify_and_reopen_cross_sectional_open_interest_delta_rank_v0_admissible_source_v0.py"

PARKING_OWNER = PARKING_REGISTRATION_ID
OVERLAP_VALIDATION_OWNER = "okx_self_accumulated_forward_open_interest_overlap_validation_v0"
ARCHIVE_CORRECTION_OWNER = (
    "okx_self_accumulated_forward_open_interest_archive_correction_and_executable_binding_v0"
)
COVERAGE_FRESHNESS_OWNER = "okx_self_accumulated_forward_open_interest_coverage_freshness_report_v0"
MATERIALIZER_OWNER = (
    "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0"
)
REUSE_DECISION = "EXTEND_EXISTING_PARKING_OWNER"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
CORRECTION_REEXECUTION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/okx_self_accumulated_forward_open_interest_archive_correction_reexecution_v0_20260711T193850Z"
)
OVERLAP_CORRECTED_ARCHIVE_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/okx_self_accumulated_forward_open_interest_overlap_validation_v0_offline_execution_against_corrected_archive_view_20260711T194056Z"
)
PARKING_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_capability_gap_registration_and_scope_parking_v0_20260711T161726Z"
)
PR5111_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5111_merge_closeout_okx_self_accumulated_forward_open_interest_archive_correction_execution_entry_point_v0_20260711T193450Z"
)
PRODUCTION_ARCHIVE_ROOT = (
    DURABLE_ARCHIVE_ROOT
    / "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)
CORRECTED_ARCHIVE_VIEW = PRODUCTION_ARCHIVE_ROOT / "corrected_observations.jsonl"
DISTINCT_EXTERNAL_REFERENCE_INPUT = (
    DURABLE_ARCHIVE_ROOT
    / "datasets/okx_distinct_external_reference_forward_open_interest_snapshot_v0/"
    "okx_linear_perpetual_ETH_USDT_USDT_perp_20260711T110000Z_20260711T130000Z"
)

SCOPE_STATUS_REOPENED = "SOURCE_RATIFIED_SELF_ACCUMULATION_CONTINUE"
CAPABILITY_STATUS_REOPENED = "SELF_ACCUMULATED_SOURCE_RATIFIED_INSUFFICIENT_HISTORY"
MATERIALIZATION_STATUS_REOPENED = "DEFERRED_INSUFFICIENT_HISTORY"
SOURCE_CAPABILITY_VERDICT_RATIFIED = (
    "SELF_ACCUMULATED_FORWARD_OI_ADMISSIBLE_FOR_CONTINUED_COLLECTION_"
    "INSUFFICIENT_FOR_PANEL_MATERIALIZATION"
)
SOURCE_CAPABILITY_CLASSIFICATION_RATIFIED = "SELF_ACCUMULATED_FORWARD_OI_ADMISSIBLE"
PARKING_CLASS_SUPERSEDED = "SUPERSEDED_BY_SOURCE_RATIFICATION"
NEXT_CANONICAL_STEP = (
    "CORE_SYSTEM_DEVELOPMENT_CONTINUE_LIVE_OI_SELF_ACCUMULATED_FORWARD_COLLECTION_V0"
)
NEXT_OPERATOR_GO = "GO_CORE_SYSTEM_DEVELOPMENT_CONTINUE"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
BOUND_OBSERVATION_COUNT = 2


class RatificationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    FAIL_CLOSED = "FAIL_CLOSED"


class SourceRatificationStatus(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    REJECTED = "REJECTED"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"


class ScopeReopenVerdict(str, Enum):
    REOPENED = "REOPENED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class SourceEvidenceBundleValidation:
    bundle_path: Path
    manifest_verify_rc: int
    manifest_digest: str


@dataclass(frozen=True)
class SourceAdmissibilityAssessment:
    source_provenance_verified: bool
    archive_integrity_verified: bool
    overlap_agreement_verified: bool
    source_admissible_for_continued_self_accumulation: bool
    source_sufficient_for_panel_materialization: bool
    source_sufficient_for_economic_evaluation: bool
    source_sufficient_for_runtime_promotion: bool
    observation_count: int
    historical_depth_sufficient: bool
    sample_sufficiency_met: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class RatificationAndReopenResult:
    verdict: RatificationVerdict
    source_ratification_status: SourceRatificationStatus
    overlap_validation_status: str
    scope_status_before: str
    scope_status_after: str
    reopen_verdict: ScopeReopenVerdict
    reopen_requirements_satisfied: bool
    coverage_freshness_reexecution_required: bool
    coverage_freshness_reexecution_status: str
    assessment: SourceAdmissibilityAssessment
    registration_config: dict[str, Any]
    dataset_registry: dict[str, Any]
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


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


def validate_evidence_bundle(bundle_dir: Path) -> SourceEvidenceBundleValidation:
    if not bundle_dir.is_dir():
        raise ValueError(f"missing_evidence_dir:{bundle_dir}")
    manifest_verify_rc = verify_manifest_sha256(bundle_dir)
    if manifest_verify_rc != 0:
        raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    return SourceEvidenceBundleValidation(
        bundle_path=bundle_dir,
        manifest_verify_rc=manifest_verify_rc,
        manifest_digest=manifest_file_digest(bundle_dir),
    )


def validate_required_source_evidence_bundles() -> dict[str, SourceEvidenceBundleValidation]:
    bundles = {
        "correction_reexecution": CORRECTION_REEXECUTION_EVIDENCE_DIR,
        "overlap_corrected_archive": OVERLAP_CORRECTED_ARCHIVE_EVIDENCE_DIR,
        "scope_parking": PARKING_EVIDENCE_DIR,
        "pr5111_closeout": PR5111_CLOSEOUT_DIR,
    }
    return {name: validate_evidence_bundle(path) for name, path in bundles.items()}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def _count_observations_in_jsonl(path: Path) -> int:
    if not path.is_file():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def coverage_freshness_reexecution_required_by_contract() -> bool:
    """Coverage/freshness reexecution is not part of reopen_requires contract."""
    return False


def assess_source_admissibility_v0(
    *,
    overlap_result: Mapping[str, Any],
    correction_reexecution_report: Mapping[str, Any],
    observation_count: int,
) -> SourceAdmissibilityAssessment:
    overlap_pass = (
        overlap_result.get("status") == OverlapValidationStatus.PASS.value
        and overlap_result.get("verdict") == OverlapValidationVerdict.PASS.value
    )
    provenance_pass = correction_reexecution_report.get("PROVENANCE_VALIDATION_PASS") is True
    integrity_pass = correction_reexecution_report.get("INTEGRITY_AUDIT_PASS") is True
    append_only_preserved = correction_reexecution_report.get("APPEND_ONLY_PRESERVED") is True
    historical_preserved = (
        correction_reexecution_report.get("HISTORICAL_EVIDENCE_PRESERVED") is True
    )

    source_provenance_verified = provenance_pass and append_only_preserved and historical_preserved
    archive_integrity_verified = integrity_pass
    overlap_agreement_verified = overlap_pass

    admissible_for_self_accumulation = (
        source_provenance_verified
        and archive_integrity_verified
        and overlap_agreement_verified
        and observation_count >= 1
    )
    historical_depth_sufficient = False
    sample_sufficiency_met = observation_count >= BOUND_OBSERVATION_COUNT
    sufficient_for_panel = False
    sufficient_for_economic = False
    sufficient_for_runtime = False

    reason_codes: list[str] = []
    if not source_provenance_verified:
        reason_codes.append("SOURCE_PROVENANCE_NOT_VERIFIED")
    if not archive_integrity_verified:
        reason_codes.append("ARCHIVE_INTEGRITY_NOT_VERIFIED")
    if not overlap_agreement_verified:
        reason_codes.append("OVERLAP_AGREEMENT_NOT_VERIFIED")
    if observation_count < BOUND_OBSERVATION_COUNT:
        reason_codes.append("BOUND_OBSERVATION_COUNT_BELOW_CONTRACT_MINIMUM")
    reason_codes.append("INSUFFICIENT_HISTORICAL_DEPTH_FOR_PANEL_MATERIALIZATION")
    reason_codes.append("INSUFFICIENT_SAMPLE_FOR_ECONOMIC_EVALUATION")
    reason_codes.append("INSUFFICIENT_SAMPLE_FOR_RUNTIME_PROMOTION")

    return SourceAdmissibilityAssessment(
        source_provenance_verified=source_provenance_verified,
        archive_integrity_verified=archive_integrity_verified,
        overlap_agreement_verified=overlap_agreement_verified,
        source_admissible_for_continued_self_accumulation=admissible_for_self_accumulation,
        source_sufficient_for_panel_materialization=sufficient_for_panel,
        source_sufficient_for_economic_evaluation=sufficient_for_economic,
        source_sufficient_for_runtime_promotion=sufficient_for_runtime,
        observation_count=observation_count,
        historical_depth_sufficient=historical_depth_sufficient,
        sample_sufficiency_met=sample_sufficiency_met,
        reason_codes=tuple(reason_codes),
    )


def build_scope_reopen_guard_report_v0(
    *,
    assessment: SourceAdmissibilityAssessment,
) -> dict[str, Any]:
    return {
        "schema_version": "cross_sectional_open_interest_scope_reopen_guard_report.v0",
        "research_scope": RESEARCH_SCOPE,
        "scope_status": SCOPE_STATUS_REOPENED,
        "capability_status": CAPABILITY_STATUS_REOPENED,
        "parking_class": PARKING_CLASS_SUPERSEDED,
        "prior_scope_status": PARKED_SCOPE_STATUS,
        "prior_capability_status": PARKED_CAPABILITY_STATUS,
        "prior_park_reason": PARKED_PARK_REASON,
        "prior_parking_class": PARKED_PARKING_CLASS,
        "source_ratification_status": SourceRatificationStatus.ADMISSIBLE.value,
        "overlap_validation_status": OverlapValidationStatus.PASS.value,
        "reopen_requires": REOPEN_REQUIRES,
        "reopen_requirements_satisfied": True,
        "dataset_materialization_allowed": False,
        "dataset_materialization_2024_allowed": False,
        "dataset_ready": False,
        "economic_evaluation_allowed": False,
        "economic_validity_offline_gate_pass": False,
        "ready_for_zero_order_runtime": False,
        "ready_for_shadow": False,
        "ready_for_paper": False,
        "ready_for_testnet": False,
        "historical_backfill_allowed": False,
        "live_oi_collection_blocked": False,
        "self_accumulated_archive_allowed": True,
        "retry_allowed": False,
        "unchanged_retry_blocked": True,
        "primary_forward_data_path": "SELF_ACCUMULATED_HISTORY",
        "observation_count_bound": assessment.observation_count,
        "historical_depth_sufficient": assessment.historical_depth_sufficient,
        "sample_sufficiency_met": assessment.sample_sufficiency_met,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
    }


def apply_source_ratification_and_scope_reopen_fields(
    *,
    parking_registration: Mapping[str, Any],
    registry: Mapping[str, Any],
    assessment: SourceAdmissibilityAssessment,
    evidence_bundles: Mapping[str, SourceEvidenceBundleValidation],
    ratification_evidence_dir: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    guard = build_scope_reopen_guard_report_v0(assessment=assessment)
    registration = dict(parking_registration)
    registration.update(
        {
            "artifact_kind": RATIFICATION_ID,
            "schema_version": SCHEMA_VERSION,
            "go_token": CONFIRM_GO,
            "scope_status": SCOPE_STATUS_REOPENED,
            "capability_status": CAPABILITY_STATUS_REOPENED,
            "parking_class": PARKING_CLASS_SUPERSEDED,
            "park_reason": None,
            "source_capability_verdict": SOURCE_CAPABILITY_VERDICT_RATIFIED,
            "source_capability_classification": SOURCE_CAPABILITY_CLASSIFICATION_RATIFIED,
            "source_ratification_status": SourceRatificationStatus.ADMISSIBLE.value,
            "overlap_validation_status": OverlapValidationStatus.PASS.value,
            "source_admissibility_assessment": {
                "source_provenance_verified": assessment.source_provenance_verified,
                "archive_integrity_verified": assessment.archive_integrity_verified,
                "overlap_agreement_verified": assessment.overlap_agreement_verified,
                "source_admissible_for_continued_self_accumulation": (
                    assessment.source_admissible_for_continued_self_accumulation
                ),
                "source_sufficient_for_panel_materialization": (
                    assessment.source_sufficient_for_panel_materialization
                ),
                "source_sufficient_for_economic_evaluation": (
                    assessment.source_sufficient_for_economic_evaluation
                ),
                "source_sufficient_for_runtime_promotion": (
                    assessment.source_sufficient_for_runtime_promotion
                ),
                "observation_count": assessment.observation_count,
                "historical_depth_sufficient": assessment.historical_depth_sufficient,
                "sample_sufficiency_met": assessment.sample_sufficiency_met,
                "reason_codes": list(assessment.reason_codes),
            },
            "prior_parking_registration_ref": PARKING_REGISTRATION_ID,
            "prior_scope_status": PARKED_SCOPE_STATUS,
            "prior_capability_status": PARKED_CAPABILITY_STATUS,
            "prior_park_reason": PARKED_PARK_REASON,
            "prior_parking_evidence_dir": str(PARKING_EVIDENCE_DIR),
            "correction_reexecution_evidence_dir": str(
                evidence_bundles["correction_reexecution"].bundle_path
            ),
            "overlap_corrected_archive_evidence_dir": str(
                evidence_bundles["overlap_corrected_archive"].bundle_path
            ),
            "pr5111_closeout_evidence_dir": str(evidence_bundles["pr5111_closeout"].bundle_path),
            "corrected_archive_view": str(CORRECTED_ARCHIVE_VIEW),
            "production_archive_root": str(PRODUCTION_ARCHIVE_ROOT),
            "bound_observation_count": assessment.observation_count,
            "dataset_materialization_allowed": False,
            "dataset_ready": False,
            "economic_evaluation_allowed": False,
            "economic_validity_offline_gate_pass": False,
            "ready_for_zero_order_runtime": False,
            "ready_for_shadow": False,
            "ready_for_paper": False,
            "ready_for_testnet": False,
            "materialization_status": MATERIALIZATION_STATUS_REOPENED,
            "scope_reopen_guard_report": guard,
            "scope_parking_guard_report": parking_registration.get("scope_parking_guard_report"),
            "status": "SOURCE_RATIFICATION_AND_SCOPE_REOPEN_COMPLETE",
            "verdict": RatificationVerdict.PASS.value,
            "next_canonical_step": NEXT_CANONICAL_STEP,
            "next_operator_go": NEXT_OPERATOR_GO,
            "ratification_owner": RATIFICATION_ID,
            "parking_owner": PARKING_OWNER,
            "overlap_validation_owner": OVERLAP_VALIDATION_OWNER,
            "archive_correction_owner": ARCHIVE_CORRECTION_OWNER,
            "coverage_freshness_owner": COVERAGE_FRESHNESS_OWNER,
            "reuse_decision": REUSE_DECISION,
            "new_owner_justified": False,
            "coverage_freshness_reexecution_required": False,
            "coverage_freshness_reexecution_status": "NOT_REQUIRED_BY_CANONICAL_CONTRACT",
        }
    )
    if ratification_evidence_dir is not None:
        registration["ratification_evidence_dir"] = str(ratification_evidence_dir)
    registration["registration_digest"] = compute_registration_digest(registration)

    updated_registry = dict(registry)
    dataset_registration = dict(updated_registry.get("dataset_registration", {}))
    dataset_registration.update(
        {
            "scope_status": SCOPE_STATUS_REOPENED,
            "capability_status": CAPABILITY_STATUS_REOPENED,
            "materialization_status": MATERIALIZATION_STATUS_REOPENED,
            "dataset_materialized": False,
            "dataset_ready": False,
            "dataset_materialization_allowed": False,
            "dataset_materialization_2024_allowed": False,
            "economic_evaluation_allowed": False,
            "economic_validity_offline_gate_pass": False,
            "park_reason": None,
            "parking_class": PARKING_CLASS_SUPERSEDED,
            "prior_parking_evidence_ref": str(PARKING_EVIDENCE_DIR),
            "source_capability_verdict": SOURCE_CAPABILITY_VERDICT_RATIFIED,
            "source_ratification_status": SourceRatificationStatus.ADMISSIBLE.value,
            "overlap_validation_status": OverlapValidationStatus.PASS.value,
            "source_admissibility_assessment_ref": RATIFICATION_ID,
            "corrected_archive_view_ref": str(CORRECTED_ARCHIVE_VIEW),
            "bound_observation_count": assessment.observation_count,
            "historical_depth_sufficient": assessment.historical_depth_sufficient,
            "sample_sufficiency_met": assessment.sample_sufficiency_met,
            "ready_for_zero_order_runtime": False,
            "ready_for_shadow": False,
            "ready_for_paper": False,
            "ready_for_testnet": False,
            "unchanged_retry_blocked": True,
            "historical_backfill_allowed": False,
            "live_oi_collection_blocked": False,
            "self_accumulated_archive_allowed": True,
            "capability_gap_registration_ref": PARKING_REGISTRATION_ID,
            "source_ratification_ref": RATIFICATION_ID,
        }
    )
    updated_registry["dataset_registration"] = dataset_registration
    updated_registry["scope_reopen"] = guard
    updated_registry["scope_parking"] = registry.get("scope_parking", {})
    updated_registry["scope_status"] = SCOPE_STATUS_REOPENED
    updated_registry["capability_status"] = CAPABILITY_STATUS_REOPENED
    updated_registry["source_ratification_ref"] = RATIFICATION_ID
    updated_registry["capability_gap_registration_ref"] = PARKING_REGISTRATION_ID
    if RATIFICATION_ID not in updated_registry.get("registered_capabilities", []):
        updated_registry["registered_capabilities"] = list(
            updated_registry.get("registered_capabilities", [])
        ) + [RATIFICATION_ID]
    return registration, updated_registry


def execute_source_ratification_and_scope_reopen_v0(
    *,
    confirm_go: str,
    as_of_utc: str,
    enabled: bool = False,
    ratification_evidence_dir: Path | None = None,
) -> RatificationAndReopenResult:
    if not enabled:
        raise ValueError("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")
    if confirm_go != CONFIRM_GO:
        raise ValueError(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")

    evidence_bundles = validate_required_source_evidence_bundles()
    parking_source = validate_source_evidence_preconditions()
    parking_registration = materialize_registration_config(source=parking_source)

    overlap_result_path = OVERLAP_CORRECTED_ARCHIVE_EVIDENCE_DIR / "overlap_validation_result.json"
    overlap_result = _load_json(overlap_result_path)
    correction_report_path = CORRECTION_REEXECUTION_EVIDENCE_DIR / "final_report.txt"
    correction_report = _parse_key_value_report(correction_report_path)
    observation_count = _count_observations_in_jsonl(CORRECTED_ARCHIVE_VIEW)

    assessment = assess_source_admissibility_v0(
        overlap_result=overlap_result,
        correction_reexecution_report=correction_report,
        observation_count=observation_count,
    )

    if not assessment.source_admissible_for_continued_self_accumulation:
        return RatificationAndReopenResult(
            verdict=RatificationVerdict.FAIL_CLOSED,
            source_ratification_status=SourceRatificationStatus.REJECTED,
            overlap_validation_status=str(overlap_result.get("status", "UNKNOWN")),
            scope_status_before=PARKED_SCOPE_STATUS,
            scope_status_after=PARKED_SCOPE_STATUS,
            reopen_verdict=ScopeReopenVerdict.BLOCKED,
            reopen_requirements_satisfied=False,
            coverage_freshness_reexecution_required=coverage_freshness_reexecution_required_by_contract(),
            coverage_freshness_reexecution_status="NOT_REQUIRED_BY_CANONICAL_CONTRACT",
            assessment=assessment,
            registration_config=parking_registration,
            dataset_registry=_load_json(Path(DATASET_REGISTRY_REL_PATH)),
            reason_codes=assessment.reason_codes,
        )

    overlap_live = validate_overlap_v0(
        self_accumulated_source=CORRECTED_ARCHIVE_VIEW,
        external_reference_source=DISTINCT_EXTERNAL_REFERENCE_INPUT,
    )
    overlap_live_status = (
        overlap_live.status.value
        if hasattr(overlap_live.status, "value")
        else str(overlap_live.status)
    )
    if overlap_live_status != OverlapValidationStatus.PASS.value:
        raise ValueError(f"overlap_revalidation_failed:{overlap_live_status}")

    coverage_report = generate_coverage_freshness_report_v0(
        archive_root=PRODUCTION_ARCHIVE_ROOT,
        as_of_utc=as_of_utc,
    )
    _ = report_result_to_dict_v0(coverage_report)

    registry_path = Path(__file__).resolve().parents[2] / DATASET_REGISTRY_REL_PATH
    registry = _load_json(registry_path)
    registration, updated_registry = apply_source_ratification_and_scope_reopen_fields(
        parking_registration=parking_registration,
        registry=registry,
        assessment=assessment,
        evidence_bundles=evidence_bundles,
        ratification_evidence_dir=ratification_evidence_dir,
    )

    return RatificationAndReopenResult(
        verdict=RatificationVerdict.PASS,
        source_ratification_status=SourceRatificationStatus.ADMISSIBLE,
        overlap_validation_status=OverlapValidationStatus.PASS.value,
        scope_status_before=PARKED_SCOPE_STATUS,
        scope_status_after=SCOPE_STATUS_REOPENED,
        reopen_verdict=ScopeReopenVerdict.REOPENED,
        reopen_requirements_satisfied=True,
        coverage_freshness_reexecution_required=coverage_freshness_reexecution_required_by_contract(),
        coverage_freshness_reexecution_status="NOT_REQUIRED_BY_CANONICAL_CONTRACT",
        assessment=assessment,
        registration_config=registration,
        dataset_registry=updated_registry,
    )


def _parse_key_value_report(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {}
    if not path.is_file():
        return report
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.lower() == "true":
            report[key] = True
        elif value.lower() == "false":
            report[key] = False
        else:
            report[key] = value
    return report


def ratification_result_to_dict_v0(result: RatificationAndReopenResult) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "verdict": result.verdict.value,
        "source_ratification_status": result.source_ratification_status.value,
        "overlap_validation_status": result.overlap_validation_status,
        "scope_status_before": result.scope_status_before,
        "scope_status_after": result.scope_status_after,
        "reopen_verdict": result.reopen_verdict.value,
        "reopen_requirements_satisfied": result.reopen_requirements_satisfied,
        "reopen_requires": REOPEN_REQUIRES,
        "coverage_freshness_reexecution_required": result.coverage_freshness_reexecution_required,
        "coverage_freshness_reexecution_status": result.coverage_freshness_reexecution_status,
        "source_admissibility_assessment": {
            "source_provenance_verified": result.assessment.source_provenance_verified,
            "archive_integrity_verified": result.assessment.archive_integrity_verified,
            "overlap_agreement_verified": result.assessment.overlap_agreement_verified,
            "source_admissible_for_continued_self_accumulation": (
                result.assessment.source_admissible_for_continued_self_accumulation
            ),
            "source_sufficient_for_panel_materialization": (
                result.assessment.source_sufficient_for_panel_materialization
            ),
            "source_sufficient_for_economic_evaluation": (
                result.assessment.source_sufficient_for_economic_evaluation
            ),
            "source_sufficient_for_runtime_promotion": (
                result.assessment.source_sufficient_for_runtime_promotion
            ),
            "observation_count": result.assessment.observation_count,
            "historical_depth_sufficient": result.assessment.historical_depth_sufficient,
            "sample_sufficiency_met": result.assessment.sample_sufficiency_met,
            "reason_codes": list(result.assessment.reason_codes),
        },
        "dataset_materialization_allowed": False,
        "dataset_ready": False,
        "economic_evaluation_allowed": False,
        "economic_validity_offline_gate_pass": False,
        "ready_for_zero_order_runtime": False,
        "ready_for_shadow": False,
        "ready_for_paper": False,
        "ready_for_testnet": False,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "reason_codes": list(result.reason_codes),
    }


def build_ratification_config_v0() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / CONFIG_REL_PATH
    return json.loads(config_path.read_text(encoding="utf-8"))


def compute_ratification_implementation_digest_v0() -> str:
    return hashlib.sha256(
        serialize_canonical_json(
            {
                "module": RATIFICATION_ID,
                "schema_version": SCHEMA_VERSION,
                "confirm_go": CONFIRM_GO,
                "entry_point": ENTRY_POINT,
                "parking_owner": PARKING_OWNER,
                "overlap_validation_owner": OVERLAP_VALIDATION_OWNER,
                "archive_correction_owner": ARCHIVE_CORRECTION_OWNER,
                "coverage_freshness_owner": COVERAGE_FRESHNESS_OWNER,
                "reopen_requires": REOPEN_REQUIRES,
                "scope_status_reopened": SCOPE_STATUS_REOPENED,
            }
        ).encode("utf-8")
    ).hexdigest()
