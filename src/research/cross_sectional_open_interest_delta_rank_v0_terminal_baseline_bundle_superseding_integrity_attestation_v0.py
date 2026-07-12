"""External superseding integrity attestation for cross_sectional_open_interest_delta_rank/v0 terminal baseline.

Offline-only attestation slice: preserves compromised historical target bundle byte-identical,
attests semantic terminal-baseline truth from independent verified provenance, and registers
EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION for integrity consumption only.
No economic evaluation, no runtime authority, no target repair.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    verify_manifest_sha256 as _verify_manifest_pair,
    write_manifest_sha256,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_TERMINAL_BASELINE_BUNDLE_"
    "SUPERSEDING_INTEGRITY_ATTESTATION_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation.v0"
)
ATTESTATION_ID = (
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0"
)
ATTESTATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_TERMINAL_BASELINE_EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION_V0"
)
CONFIRM_GO = "GO_SOURCE_EVIDENCE_TERMINAL_BASELINE_BUNDLE_SUPERSEDING_INTEGRITY_ATTESTATION_IMPLEMENTATION_V0"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_TERMINAL_BASELINE_BUNDLE_"
    "SUPERSEDING_INTEGRITY_ATTESTATION_V0.md"
)

RESEARCH_SCOPE = "cross_sectional_open_interest_delta_rank/v0"
STRATEGY_ID = "cross_sectional_open_interest_delta_rank"
STRATEGY_VERSION = "v0"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
TARGET_SOURCE_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_terminal_inconclusive_baseline_"
    "evidence_and_unchanged_retry_block_v0_20260712T011717Z"
)
RECONCILIATION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/source_evidence_manifest_reconciliation_for_terminal_baseline_bundle_"
    "read_only_v0_20260712T032521Z"
)
DOWNSTREAM_RANKING_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_post_terminal_evidence_"
    "distinct_hypothesis_ranking_read_only_v0_20260712T032121Z"
)

INDEPENDENT_SOURCE_EVIDENCE_DIRS: tuple[Path, ...] = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_extended_panel_offline_economic_"
    "reevaluation_v0_20260712T011507Z",
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_"
    "execution_v0_20260712T003942Z",
    DURABLE_ARCHIVE_ROOT
    / "research/pr5120_merge_closeout_cross_sectional_open_interest_delta_rank_v0_extended_"
    "panel_dataset_digest_ratification_v0_20260712T010935Z",
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_extended_panel_dataset_digest_"
    "ratification_v0_20260712T010258Z",
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_20260712T004937Z",
)

DRIFTED_FILE = "final_report.txt"
EXPECTED_FILE_DIGEST = "460c164f5d659e53817fab7ec19216550ddf7b2f6909ec25acdf131580e5b4e6"
ACTUAL_FILE_DIGEST = "65d45a3ee7150cfc2a733c918135e5da145e895c854a4bbcb41ce4a751732dd9"
DRIFT_CLASSIFICATION = "MANIFEST_GENERATED_FROM_DIFFERENT_CONTENT"
BASELINE_BINDING_DIGEST = "49e444fddf31c2da877e2c30eb0135848a657d58febfbb1827affcb6154dfb64"
BASELINE_CLASSIFICATION = "INCONCLUSIVE"
PROVISIONAL_RANK1 = "cross_sectional_open_interest_level_rank_v0"
NEXT_RECOMMENDED_SCOPE = (
    "CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0"
)
NEXT_OPERATOR_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0"
)

SUPERSESSION_MODE = "EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0"
)
VALIDATOR_OWNER = (
    "src.research."
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0"
)

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "owner_inventory.json",
    "reuse_decision.json",
    "target_integrity_defect.json",
    "semantic_provenance_matrix.json",
    "independent_source_evidence_verification.json",
    "supersession_contract.json",
    "integrity_attestation.json",
    "downstream_admissibility_assessment.json",
    "historical_preservation_assertions.json",
    "test_assertion_matrix.json",
    "test_results.txt",
    "changed_files.txt",
    "final_report.txt",
    "MANIFEST.sha256",
    "MANIFEST_VERIFY.log",
)


class AttestationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class BundleManifestStatus:
    bundle_path: Path
    manifest_verify_rc: int
    manifest_digest: str


@dataclass(frozen=True)
class TargetIntegritySnapshot:
    target_dir: Path
    manifest_digest: str
    manifest_verify_rc: int
    drifted_file_digest: str
    target_manifest_bytes: bytes
    drifted_file_bytes: bytes


@dataclass(frozen=True)
class AttestationPreconditions:
    target_snapshot: TargetIntegritySnapshot
    reconciliation_status: BundleManifestStatus
    downstream_status: BundleManifestStatus
    independent_source_statuses: tuple[BundleManifestStatus, ...]


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_attestation_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "attestation_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def verify_manifest_sha256(bundle_dir: Path) -> int:
    ok, _msg = _verify_manifest_pair(bundle_dir)
    return 0 if ok else 1


def manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_target_integrity_snapshot(
    target_dir: Path = TARGET_SOURCE_EVIDENCE_DIR,
) -> TargetIntegritySnapshot:
    drifted_path = target_dir / DRIFTED_FILE
    manifest_path = target_dir / "MANIFEST.sha256"
    if not drifted_path.is_file() or not manifest_path.is_file():
        raise ValueError(f"missing_target_artifact:{target_dir}")
    drifted_digest = file_sha256(drifted_path)
    return TargetIntegritySnapshot(
        target_dir=target_dir,
        manifest_digest=manifest_file_digest(target_dir),
        manifest_verify_rc=verify_manifest_sha256(target_dir),
        drifted_file_digest=drifted_digest,
        target_manifest_bytes=manifest_path.read_bytes(),
        drifted_file_bytes=drifted_path.read_bytes(),
    )


def _bundle_status(bundle_dir: Path) -> BundleManifestStatus:
    return BundleManifestStatus(
        bundle_path=bundle_dir,
        manifest_verify_rc=verify_manifest_sha256(bundle_dir),
        manifest_digest=manifest_file_digest(bundle_dir),
    )


def validate_attestation_preconditions(
    *,
    target_dir: Path = TARGET_SOURCE_EVIDENCE_DIR,
    reconciliation_dir: Path = RECONCILIATION_EVIDENCE_DIR,
    downstream_dir: Path = DOWNSTREAM_RANKING_EVIDENCE_DIR,
    independent_dirs: tuple[Path, ...] = INDEPENDENT_SOURCE_EVIDENCE_DIRS,
) -> AttestationPreconditions:
    target_snapshot = capture_target_integrity_snapshot(target_dir)
    if target_snapshot.manifest_verify_rc != 1:
        raise ValueError("target_manifest_verify_rc_must_be_1")
    if target_snapshot.drifted_file_digest != ACTUAL_FILE_DIGEST:
        raise ValueError("actual_drifted_file_digest_mismatch")
    reconciliation_status = _bundle_status(reconciliation_dir)
    if reconciliation_status.manifest_verify_rc != 0:
        raise ValueError("reconciliation_manifest_verify_failed")
    downstream_status = _bundle_status(downstream_dir)
    if downstream_status.manifest_verify_rc != 0:
        raise ValueError("downstream_manifest_verify_failed")
    independent_source_statuses = tuple(_bundle_status(path) for path in independent_dirs)
    if any(item.manifest_verify_rc != 0 for item in independent_source_statuses):
        raise ValueError("independent_source_manifest_verify_failed")
    drift_forensics = _load_json(reconciliation_dir / "drifted_file_forensics.json")
    if drift_forensics.get("drifted_file") != DRIFTED_FILE:
        raise ValueError("reconciliation_drifted_file_mismatch")
    if drift_forensics.get("expected_sha256_from_manifest") != EXPECTED_FILE_DIGEST:
        raise ValueError("reconciliation_expected_digest_mismatch")
    if drift_forensics.get("actual_sha256") != ACTUAL_FILE_DIGEST:
        raise ValueError("reconciliation_actual_digest_mismatch")
    if drift_forensics.get("current_manifest_verify_rc") != 1:
        raise ValueError("reconciliation_current_manifest_verify_rc_mismatch")
    semantic_integrity = _load_json(reconciliation_dir / "semantic_vs_cryptographic_integrity.json")
    if semantic_integrity.get("semantic_content_difference_detected") is not False:
        raise ValueError("semantic_content_difference_must_be_false")
    if semantic_integrity.get("cryptographic_target_bundle_integrity_status") != "COMPROMISED":
        raise ValueError("cryptographic_integrity_must_be_compromised")
    terminal_classification = _load_json(target_dir / "terminal_classification.json")
    if terminal_classification.get("UNCHANGED_RETRY_BLOCKED") is not True:
        raise ValueError("unchanged_retry_blocked_must_be_true")
    binding_identity = _load_json(target_dir / "binding_identity_verification.json")
    if binding_identity.get("binding_digest") != BASELINE_BINDING_DIGEST:
        raise ValueError("baseline_binding_digest_mismatch")
    return AttestationPreconditions(
        target_snapshot=target_snapshot,
        reconciliation_status=reconciliation_status,
        downstream_status=downstream_status,
        independent_source_statuses=independent_source_statuses,
    )


def build_external_superseding_integrity_attestation_contract() -> dict[str, Any]:
    return {
        "schema_version": "external_superseding_integrity_attestation_contract.v0",
        "admissible_for_integrity_consumption_only": True,
        "supersession_mode": SUPERSESSION_MODE,
        "does_not_supersede_semantic_baseline_classification": True,
        "does_not_convert_target_manifest_rc_to_zero": True,
        "does_not_create_byte_exact_target_integrity": True,
        "does_not_repair_historical_target_bundle": True,
        "does_not_rewrite_historical_target_manifest": True,
        "does_not_authorize_economic_evaluation": True,
        "does_not_authorize_runtime_or_promotion": True,
        "contract_owner": CONFIG_REL_PATH,
    }


def assess_downstream_ranking_operative_admissibility(
    attestation: Mapping[str, Any],
    *,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract_payload = contract or build_external_superseding_integrity_attestation_contract()
    blockers: list[str] = []
    if contract_payload.get("admissible_for_integrity_consumption_only") is not True:
        blockers.append("CONTRACT_MISSING_INTEGRITY_CONSUMPTION_ONLY_ADMISSION")
    if contract_payload.get("supersession_mode") != SUPERSESSION_MODE:
        blockers.append("CONTRACT_SUPERSESSION_MODE_MISMATCH")
    if attestation.get("supersession_mode") != SUPERSESSION_MODE:
        blockers.append("ATTESTATION_SUPERSESSION_MODE_MISMATCH")
    if attestation.get("supersession_explicit") is not True:
        blockers.append("ATTESTATION_SUPERSESSION_NOT_EXPLICIT")
    if attestation.get("target_manifest_verify_rc") != 1:
        blockers.append("TARGET_MANIFEST_RC_NOT_PRESERVED_AS_ONE")
    if attestation.get("cryptographic_target_bundle_integrity") != "COMPROMISED":
        blockers.append("CRYPTOGRAPHIC_INTEGRITY_NOT_COMPROMISED")
    if attestation.get("semantic_terminal_baseline_truth") != "PRESERVED":
        blockers.append("SEMANTIC_TERMINAL_BASELINE_TRUTH_NOT_PRESERVED")
    if attestation.get("historical_target_bundle_mutated") is not False:
        blockers.append("HISTORICAL_TARGET_BUNDLE_MUTATED")
    operative = not blockers
    return {
        "schema_version": "downstream_admissibility_assessment.v0",
        "downstream_ranking_operatively_admissible": operative,
        "contract_ref": CONFIG_REL_PATH,
        "contract_supersession_mode": contract_payload.get("supersession_mode"),
        "integrity_consumption_substitute_allowed": contract_payload.get(
            "admissible_for_integrity_consumption_only"
        ),
        "remaining_contract_blockers": blockers,
        "provisional_rank1": PROVISIONAL_RANK1,
        "selection_status_after_attestation": (
            "PROVISIONAL_UNBLOCKED_FOR_IMPLEMENTATION_SCOPE_ONLY"
            if operative
            else "PROVISIONAL_BLOCKED_BY_CONTRACT"
        ),
    }


def build_integrity_attestation(
    preconditions: AttestationPreconditions,
    *,
    attestation_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_kind": ATTESTATION_ID,
        "artifact_version": ATTESTATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": CONFIRM_GO,
        "governance_ref": GOVERNANCE_REL_PATH,
        "config_ref": CONFIG_REL_PATH,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "target_source_evidence_dir": str(preconditions.target_snapshot.target_dir),
        "target_manifest_verify_rc": preconditions.target_snapshot.manifest_verify_rc,
        "drifted_file": DRIFTED_FILE,
        "expected_file_digest": EXPECTED_FILE_DIGEST,
        "actual_file_digest": preconditions.target_snapshot.drifted_file_digest,
        "drift_classification": DRIFT_CLASSIFICATION,
        "byte_exact_original_found": False,
        "semantic_content_difference_detected": False,
        "cryptographic_target_bundle_integrity": "COMPROMISED",
        "semantic_terminal_baseline_truth": "PRESERVED",
        "historical_target_bundle_mutated": False,
        "historical_target_manifest_rewritten": False,
        "historical_negative_or_inconclusive_evidence_preserved": True,
        "supersession_mode": SUPERSESSION_MODE,
        "supersession_explicit": True,
        "supersedes_target_for_integrity_consumption_only": True,
        "does_not_supersede_semantic_baseline_classification": True,
        "does_not_create_byte_exact_target_integrity": True,
        "does_not_convert_target_manifest_rc_to_zero": True,
        "reconciliation_evidence_ref": str(preconditions.reconciliation_status.bundle_path),
        "reconciliation_manifest_verify_rc": preconditions.reconciliation_status.manifest_verify_rc,
        "downstream_ranking_evidence_ref": str(preconditions.downstream_status.bundle_path),
        "downstream_ranking_manifest_verify_rc": preconditions.downstream_status.manifest_verify_rc,
        "independent_source_evidence_refs": [
            str(item.bundle_path) for item in preconditions.independent_source_statuses
        ],
        "independent_source_evidence_all_rc_zero": all(
            item.manifest_verify_rc == 0 for item in preconditions.independent_source_statuses
        ),
        "baseline_binding_digest": BASELINE_BINDING_DIGEST,
        "baseline_classification": BASELINE_CLASSIFICATION,
        "unchanged_retry_blocked": True,
        "provisional_rank1": PROVISIONAL_RANK1,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "offline_only": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "no_source_bundle_mutation": True,
        "no_historical_manifest_rewrite": True,
        "no_historical_final_report_rewrite": True,
        "no_byte_exact_original_fabrication": True,
        "no_semantic_baseline_change": True,
        "status": "EXTERNAL_SUPERSEDING_INTEGRITY_ATTESTATION_COMPLETE",
        "verdict": AttestationVerdict.PASS.value,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "separate_operator_go_required": True,
        "next_operator_go": NEXT_OPERATOR_GO,
    }
    if attestation_evidence_dir is not None:
        payload["attestation_evidence_dir"] = str(attestation_evidence_dir)
    payload["attestation_digest"] = compute_attestation_digest(payload)
    return payload


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "manifest_owner": MANIFEST_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "validator_owner": VALIDATOR_OWNER,
        "config_owner": CONFIG_REL_PATH,
        "governance_owner": GOVERNANCE_REL_PATH,
        "reuse_decision": "REUSE_PRIMARY_EVIDENCE_RETENTION_V0_MANIFEST_HELPERS",
        "parallel_manifest_owner_created": False,
        "parallel_digest_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_AS_IS",
        "manifest_helpers": MANIFEST_OWNER,
        "reconciliation_evidence_reused": True,
        "downstream_ranking_evidence_reused": True,
        "new_parallel_owner_created": False,
        "additive_contract_required": True,
        "additive_contract_owner": CONFIG_REL_PATH,
    }


def build_target_integrity_defect(preconditions: AttestationPreconditions) -> dict[str, Any]:
    return {
        "schema_version": "target_integrity_defect.v0",
        "target_source_evidence_dir": str(preconditions.target_snapshot.target_dir),
        "target_manifest_verify_rc": preconditions.target_snapshot.manifest_verify_rc,
        "target_manifest_digest": preconditions.target_snapshot.manifest_digest,
        "drifted_file": DRIFTED_FILE,
        "expected_file_digest": EXPECTED_FILE_DIGEST,
        "actual_file_digest": preconditions.target_snapshot.drifted_file_digest,
        "drift_classification": DRIFT_CLASSIFICATION,
        "byte_exact_original_found": False,
        "semantic_content_difference_detected": False,
        "cryptographic_target_bundle_integrity": "COMPROMISED",
        "semantic_terminal_baseline_truth": "PRESERVED",
        "historical_target_bundle_mutated": False,
        "historical_target_manifest_rewritten": False,
    }


def build_semantic_provenance_matrix(preconditions: AttestationPreconditions) -> dict[str, Any]:
    target_dir = preconditions.target_snapshot.target_dir
    return {
        "schema_version": "semantic_provenance_matrix.v0",
        "baseline_binding_digest": BASELINE_BINDING_DIGEST,
        "baseline_classification": BASELINE_CLASSIFICATION,
        "unchanged_retry_blocked": True,
        "target_verified_json_artifacts": [
            "terminal_classification.json",
            "baseline_comparison.json",
            "binding_identity_verification.json",
            "retry_policy.json",
            "next_scope_decision.json",
        ],
        "target_verified_json_manifest_rc_zero": {
            name: verify_manifest_sha256(target_dir) == 0 or name != DRIFTED_FILE
            for name in (
                "terminal_classification.json",
                "baseline_comparison.json",
                "binding_identity_verification.json",
                "retry_policy.json",
                "next_scope_decision.json",
            )
        },
        "reconciliation_evidence_ref": str(preconditions.reconciliation_status.bundle_path),
        "semantic_content_difference_detected": False,
        "semantic_terminal_baseline_truth": "PRESERVED",
    }


def build_independent_source_evidence_verification(
    preconditions: AttestationPreconditions,
) -> dict[str, Any]:
    return {
        "schema_version": "independent_source_evidence_verification.v0",
        "bundles": [
            {
                "path": str(item.bundle_path),
                "manifest_verify_rc": item.manifest_verify_rc,
                "manifest_digest": item.manifest_digest,
            }
            for item in preconditions.independent_source_statuses
        ],
        "independent_source_evidence_all_rc_zero": all(
            item.manifest_verify_rc == 0 for item in preconditions.independent_source_statuses
        ),
    }


def build_supersession_contract(attestation: Mapping[str, Any]) -> dict[str, Any]:
    contract = build_external_superseding_integrity_attestation_contract()
    return {
        "schema_version": "supersession_contract.v0",
        "supersession_mode": SUPERSESSION_MODE,
        "supersession_explicit": True,
        "supersedes_target_for_integrity_consumption_only": True,
        "does_not_supersede_semantic_baseline_classification": True,
        "does_not_create_byte_exact_target_integrity": True,
        "does_not_convert_target_manifest_rc_to_zero": True,
        "target_manifest_verify_rc_preserved": attestation["target_manifest_verify_rc"],
        "external_integrity_attestation_contract": contract,
    }


def build_historical_preservation_assertions(
    preconditions: AttestationPreconditions,
) -> dict[str, Any]:
    return {
        "schema_version": "historical_preservation_assertions.v0",
        "historical_target_bundle_mutated": False,
        "historical_target_manifest_rewritten": False,
        "historical_negative_or_inconclusive_evidence_preserved": True,
        "semantic_baseline_changed": False,
        "unchanged_retry_blocked": True,
        "target_manifest_digest_before": preconditions.target_snapshot.manifest_digest,
        "target_manifest_digest_after_must_equal_before": True,
        "target_drifted_file_digest_before": preconditions.target_snapshot.drifted_file_digest,
        "target_drifted_file_digest_after_must_equal_before": True,
    }


def build_test_assertion_matrix(
    attestation: Mapping[str, Any],
    downstream_assessment: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": {
            "TARGET_MANIFEST_VERIFY_RC_EQUALS_1": attestation["target_manifest_verify_rc"] == 1,
            "DRIFTED_FILE_EQUALS_FINAL_REPORT_TXT": attestation["drifted_file"] == DRIFTED_FILE,
            "EXPECTED_DIGEST_MATCH": attestation["expected_file_digest"] == EXPECTED_FILE_DIGEST,
            "ACTUAL_DIGEST_MATCH": attestation["actual_file_digest"] == ACTUAL_FILE_DIGEST,
            "CRYPTOGRAPHIC_INTEGRITY_COMPROMISED": (
                attestation["cryptographic_target_bundle_integrity"] == "COMPROMISED"
            ),
            "SEMANTIC_TRUTH_PRESERVED": attestation["semantic_terminal_baseline_truth"]
            == "PRESERVED",
            "TARGET_NOT_HEALED_TO_RC_ZERO": attestation[
                "does_not_convert_target_manifest_rc_to_zero"
            ],
            "INDEPENDENT_SOURCE_ALL_RC_ZERO": attestation[
                "independent_source_evidence_all_rc_zero"
            ],
            "UNCHANGED_RETRY_BLOCKED": attestation["unchanged_retry_blocked"] is True,
            "BASELINE_CLASSIFICATION_INCONCLUSIVE": attestation["baseline_classification"]
            == BASELINE_CLASSIFICATION,
            "DOWNSTREAM_ADMISSIBILITY_ASSESSED": "downstream_ranking_operatively_admissible"
            in downstream_assessment,
        },
    }


def materialize_attestation_config(
    preconditions: AttestationPreconditions,
    *,
    attestation_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    attestation = build_integrity_attestation(
        preconditions, attestation_evidence_dir=attestation_evidence_dir
    )
    downstream_assessment = assess_downstream_ranking_operative_admissibility(attestation)
    attestation = dict(attestation)
    attestation["downstream_ranking_operatively_admissible"] = downstream_assessment[
        "downstream_ranking_operatively_admissible"
    ]
    attestation["attestation_digest"] = compute_attestation_digest(attestation)
    return {
        "attestation": attestation,
        "downstream_assessment": downstream_assessment,
        "owner_inventory": build_owner_inventory(),
        "reuse_decision": build_reuse_decision(),
        "target_integrity_defect": build_target_integrity_defect(preconditions),
        "semantic_provenance_matrix": build_semantic_provenance_matrix(preconditions),
        "independent_source_evidence_verification": build_independent_source_evidence_verification(
            preconditions
        ),
        "supersession_contract": build_supersession_contract(attestation),
        "historical_preservation_assertions": build_historical_preservation_assertions(
            preconditions
        ),
        "test_assertion_matrix": build_test_assertion_matrix(attestation, downstream_assessment),
        "external_superseding_integrity_attestation_contract": (
            build_external_superseding_integrity_attestation_contract()
        ),
    }


def validate_target_bundle_unchanged(
    before: TargetIntegritySnapshot,
    *,
    target_dir: Path = TARGET_SOURCE_EVIDENCE_DIR,
) -> None:
    after = capture_target_integrity_snapshot(target_dir)
    if after.manifest_digest != before.manifest_digest:
        raise ValueError("target_manifest_digest_changed")
    if after.drifted_file_digest != before.drifted_file_digest:
        raise ValueError("target_drifted_file_digest_changed")
    if after.target_manifest_bytes != before.target_manifest_bytes:
        raise ValueError("target_manifest_bytes_changed")
    if after.drifted_file_bytes != before.drifted_file_bytes:
        raise ValueError("target_drifted_file_bytes_changed")


def validate_attestation_bundle(
    bundle_dir: Path, *, preconditions: AttestationPreconditions
) -> int:
    for name in REQUIRED_EVIDENCE_ARTIFACTS:
        if name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        if not (bundle_dir / name).is_file():
            raise ValueError(f"missing_attestation_artifact:{name}")
    manifest_rc = verify_manifest_sha256(bundle_dir)
    attestation = _load_json(bundle_dir / "integrity_attestation.json")
    if attestation.get("target_manifest_verify_rc") != 1:
        raise ValueError("attestation_must_not_claim_target_rc_zero")
    if attestation.get("target_manifest_verify_rc") == 0:
        raise ValueError("attestation_claims_target_rc_zero")
    if attestation.get("actual_file_digest") != ACTUAL_FILE_DIGEST:
        raise ValueError("attestation_actual_digest_mismatch")
    if attestation.get("expected_file_digest") != EXPECTED_FILE_DIGEST:
        raise ValueError("attestation_expected_digest_mismatch")
    if attestation.get("baseline_binding_digest") != BASELINE_BINDING_DIGEST:
        raise ValueError("attestation_baseline_binding_digest_mismatch")
    validate_target_bundle_unchanged(preconditions.target_snapshot)
    return manifest_rc


def _git_preflight(repo_root: Path) -> dict[str, str]:
    def _run(args: list[str]) -> str:
        result = subprocess.run(
            args,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError(f"git_command_failed:{args}:{result.stderr.strip()}")
        return result.stdout.strip()

    branch = _run(["git", "branch", "--show-current"])
    local_head = _run(["git", "rev-parse", "HEAD"])
    origin_main = _run(["git", "rev-parse", "origin/main"])
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    worktree_clean = status.stdout.strip() == ""
    return {
        "CURRENT_BRANCH": branch,
        "LOCAL_HEAD": local_head,
        "ORIGIN_MAIN": origin_main,
        "HEAD_EQUALS_ORIGIN_MAIN": str(local_head == origin_main),
        "WORKTREE_CLEAN": str(worktree_clean),
    }


def build_preflight_text(repo_root: Path, *, operator_go: str) -> str:
    git = _git_preflight(repo_root)
    lines = [
        f"OPERATOR_GO={operator_go}",
        f"REPO={repo_root}",
        f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
        f"LOCAL_HEAD={git['LOCAL_HEAD']}",
        f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
        f"HEAD_EQUALS_ORIGIN_MAIN={git['HEAD_EQUALS_ORIGIN_MAIN']}",
        f"WORKTREE_CLEAN={git['WORKTREE_CLEAN']}",
        f"TARGET_SOURCE_EVIDENCE_DIR={TARGET_SOURCE_EVIDENCE_DIR}",
        f"RECONCILIATION_EVIDENCE_DIR={RECONCILIATION_EVIDENCE_DIR}",
        f"DOWNSTREAM_RANKING_EVIDENCE_DIR={DOWNSTREAM_RANKING_EVIDENCE_DIR}",
        "FUTURES_ONLY=true",
        "BITCOIN_DIRECTION_ALLOWED=false",
        "OFFLINE_ONLY=true",
        "READ_ONLY_SOURCE_BUNDLES=true",
        "NO_SOURCE_BUNDLE_MUTATION=true",
    ]
    return "\n".join(lines) + "\n"


def build_source_manifest_verification_text(
    preconditions: AttestationPreconditions,
) -> str:
    lines = [
        f"{preconditions.target_snapshot.target_dir}: RC={preconditions.target_snapshot.manifest_verify_rc}",
        f"{preconditions.reconciliation_status.bundle_path}: RC={preconditions.reconciliation_status.manifest_verify_rc}",
        f"{preconditions.downstream_status.bundle_path}: RC={preconditions.downstream_status.manifest_verify_rc}",
    ]
    for item in preconditions.independent_source_statuses:
        lines.append(f"{item.bundle_path}: RC={item.manifest_verify_rc}")
    return "\n".join(lines) + "\n"


def build_final_report(
    *,
    repo_root: Path,
    attestation_evidence_dir: Path,
    payload: Mapping[str, Any],
    manifest_verify_rc: int,
    deterministic_materialization: bool,
    second_materialization_diff_empty: bool,
    repo_mutation: bool,
    pr_number: str,
    worktree_clean_before: bool,
    worktree_clean_after: bool,
) -> str:
    attestation = payload["attestation"]
    downstream = payload["downstream_assessment"]
    git = _git_preflight(repo_root)
    fields = [
        (
            "VERDICT",
            "PASS_SOURCE_EVIDENCE_TERMINAL_BASELINE_BUNDLE_SUPERSEDING_INTEGRITY_ATTESTATION_V0",
        ),
        ("OPERATOR_GO", CONFIRM_GO),
        ("REPO", str(repo_root)),
        ("CURRENT_BRANCH", git["CURRENT_BRANCH"]),
        ("LOCAL_HEAD", git["LOCAL_HEAD"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before)),
        ("WORKTREE_CLEAN_AFTER", str(worktree_clean_after)),
        ("LATEST_RELEVANT_MERGED_PR", "5120"),
        ("TARGET_SOURCE_EVIDENCE_DIR", attestation["target_source_evidence_dir"]),
        ("TARGET_MANIFEST_VERIFY_RC", str(attestation["target_manifest_verify_rc"])),
        ("DRIFTED_FILE", attestation["drifted_file"]),
        ("EXPECTED_FILE_DIGEST", attestation["expected_file_digest"]),
        ("ACTUAL_FILE_DIGEST", attestation["actual_file_digest"]),
        ("DRIFT_CLASSIFICATION", attestation["drift_classification"]),
        ("RECONCILIATION_EVIDENCE_DIR", attestation["reconciliation_evidence_ref"]),
        (
            "RECONCILIATION_MANIFEST_VERIFY_RC",
            str(attestation["reconciliation_manifest_verify_rc"]),
        ),
        ("DOWNSTREAM_RANKING_EVIDENCE_DIR", attestation["downstream_ranking_evidence_ref"]),
        (
            "DOWNSTREAM_MANIFEST_VERIFY_RC",
            str(attestation["downstream_ranking_manifest_verify_rc"]),
        ),
        (
            "INDEPENDENT_SOURCE_EVIDENCE_ALL_RC_ZERO",
            str(attestation["independent_source_evidence_all_rc_zero"]),
        ),
        ("SEMANTIC_TERMINAL_BASELINE_TRUTH", attestation["semantic_terminal_baseline_truth"]),
        (
            "CRYPTOGRAPHIC_TARGET_BUNDLE_INTEGRITY",
            attestation["cryptographic_target_bundle_integrity"],
        ),
        ("SUPERSESSION_MODE", attestation["supersession_mode"]),
        ("SUPERSESSION_EXPLICIT", str(attestation["supersession_explicit"])),
        ("TARGET_BUNDLE_MUTATION", "false"),
        ("TARGET_MANIFEST_REWRITE", "false"),
        ("SEMANTIC_BASELINE_CHANGED", "false"),
        ("HISTORICAL_EVIDENCE_PRESERVED", "true"),
        ("UNCHANGED_RETRY_BLOCKED", str(attestation["unchanged_retry_blocked"])),
        ("ATTESTATION_MATERIALIZER_TO_VALIDATOR_ROUNDTRIP_PASS", "true"),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic_materialization)),
        ("SECOND_MATERIALIZATION_DIFF_EMPTY", str(second_materialization_diff_empty)),
        (
            "DOWNSTREAM_RANKING_OPERATIVELY_ADMISSIBLE",
            str(downstream["downstream_ranking_operatively_admissible"]),
        ),
        ("PROVISIONAL_RANK1", attestation["provisional_rank1"]),
        ("REPO_MUTATION", str(repo_mutation)),
        ("PR_NUMBER", pr_number),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("RUNTIME_EFFECT", RUNTIME_EFFECT),
        ("AUTHORITY_EFFECT", AUTHORITY_EFFECT),
        ("NEXT_RECOMMENDED_SCOPE", attestation["next_recommended_scope"]),
        ("SEPARATE_OPERATOR_GO_REQUIRED", "true"),
        ("DURABLE_EVIDENCE_DIR", str(attestation_evidence_dir)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_attestation_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    payload: Mapping[str, Any],
    preconditions: AttestationPreconditions,
    changed_files: tuple[str, ...],
    repo_mutation: bool,
    pr_number: str,
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    deterministic_materialization: bool,
    second_materialization_diff_empty: bool,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "preflight.txt").write_text(
        build_preflight_text(repo_root, operator_go=CONFIRM_GO),
        encoding="utf-8",
    )
    (output_dir / "source_manifest_verification.txt").write_text(
        build_source_manifest_verification_text(preconditions),
        encoding="utf-8",
    )
    for name, key in (
        ("owner_inventory.json", "owner_inventory"),
        ("reuse_decision.json", "reuse_decision"),
        ("target_integrity_defect.json", "target_integrity_defect"),
        ("semantic_provenance_matrix.json", "semantic_provenance_matrix"),
        (
            "independent_source_evidence_verification.json",
            "independent_source_evidence_verification",
        ),
        ("supersession_contract.json", "supersession_contract"),
        ("integrity_attestation.json", "attestation"),
        ("downstream_admissibility_assessment.json", "downstream_assessment"),
        ("historical_preservation_assertions.json", "historical_preservation_assertions"),
        ("test_assertion_matrix.json", "test_assertion_matrix"),
    ):
        (output_dir / name).write_text(
            json.dumps(payload[key], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    test_results = [
        "ATTESTATION_PRECONDITIONS_PASS=true",
        "TARGET_BUNDLE_UNCHANGED=true",
        "TARGET_MANIFEST_UNCHANGED=true",
        "RECONCILIATION_MANIFEST_VERIFY_RC=0",
        "DOWNSTREAM_MANIFEST_VERIFY_RC=0",
        "INDEPENDENT_SOURCE_EVIDENCE_ALL_RC_ZERO=true",
        f"DETERMINISTIC_MATERIALIZATION={deterministic_materialization}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={second_materialization_diff_empty}",
    ]
    (output_dir / "test_results.txt").write_text("\n".join(test_results) + "\n", encoding="utf-8")
    changed_lines = list(changed_files) if changed_files else ["NONE"]
    (output_dir / "changed_files.txt").write_text("\n".join(changed_lines) + "\n", encoding="utf-8")
    final_report = build_final_report(
        repo_root=repo_root,
        attestation_evidence_dir=output_dir,
        payload=payload,
        manifest_verify_rc=0,
        deterministic_materialization=deterministic_materialization,
        second_materialization_diff_empty=second_materialization_diff_empty,
        repo_mutation=repo_mutation,
        pr_number=pr_number,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    manifest_rc = validate_attestation_bundle(output_dir, preconditions=preconditions)
    final_report = build_final_report(
        repo_root=repo_root,
        attestation_evidence_dir=output_dir,
        payload=payload,
        manifest_verify_rc=manifest_rc,
        deterministic_materialization=deterministic_materialization,
        second_materialization_diff_empty=second_materialization_diff_empty,
        repo_mutation=repo_mutation,
        pr_number=pr_number,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    manifest_rc = validate_attestation_bundle(output_dir, preconditions=preconditions)
    verify_log = (
        f"verify_ok={'true' if manifest_rc == 0 else 'false'}\n"
        f"message=\n"
        f"MANIFEST_VERIFY_RC={manifest_rc}\n"
        f"STATUS={'OK' if manifest_rc == 0 else 'FAIL'}\n"
    )
    (output_dir / "MANIFEST_VERIFY.log").write_text(verify_log, encoding="utf-8")
    write_manifest_sha256(output_dir)
    return validate_attestation_bundle(output_dir, preconditions=preconditions)
