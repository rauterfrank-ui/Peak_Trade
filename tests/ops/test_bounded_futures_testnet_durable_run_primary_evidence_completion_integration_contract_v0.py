"""Static + offline bounded Futures Testnet durable run primary evidence completion (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
PE-31 + PE-21 + PE-22 + PE-23 + PE-24 + PE-35 + PE-37 + PE-16 + Gap-4 + Gap-2a.1 durable run-root
completion static integration only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    MANIFEST_FILENAME,
)
from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    CAPITAL_REALLOCATION_EXECUTED,
    CAPITAL_SLOT_RATCHET_EXECUTED,
    CAPITAL_SLOT_RELEASE_EXECUTED,
    RESERVE_TOP_UP_EXECUTED,
    ARCHIVE_READ,
    ARCHIVE_WRITTEN,
    AUTHORITY_LIFT,
    COMPLETION_INTEGRATION_OWNER,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EVIDENCE_MODE_DURABLE,
    EVIDENCE_MODE_PLANNED,
    EVIDENCE_MODE_SIMULATED,
    EVIDENCE_MODE_TMP_ONLY,
    FILESYSTEM_ACCESSED,
    GAP2A1_ENFORCEMENT_OWNER,
    GAP4_COMPLETION_OWNER,
    GLOBAL_RUN_COMPLETION_READINESS,
    MANIFEST_READ,
    MANIFEST_WRITTEN,
    OPERATIVE_RUN_COMPLETION_RECORDED,
    PACKAGE_MARKER,
    PE16_ARCHIVE_OWNER,
    PE21_INTEGRATION_OWNER,
    PE31_INTEGRATION_OWNER,
    PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED,
    RECONCILIATION_EXECUTED,
    FLATTEN_EXECUTED,
    KILLSWITCH_TRIGGERED,
    PE22_INTEGRATION_OWNER,
    PE23_INTEGRATION_OWNER,
    PE24_INTEGRATION_OWNER,
    PE35_INTEGRATION_OWNER,
    PE34_INTEGRATION_OWNER,
    PE36_INTEGRATION_OWNER,
    PE37_INTEGRATION_OWNER,
    RECOVERY_EXECUTED,
    RESUME_EXECUTED,
    RETRY_EXECUTED,
    REPLAY_EXECUTED,
    STATE_MUTATED,
    PARTIAL_FAILURE_OPERATIONALLY_RESOLVED,
    PILOT_ENVELOPE_EXECUTED,
    PILOT_STARTED,
    RISK_EVALUATION_EXECUTED,
    PROOF_LIFECYCLE_CURRENT,
    PROOF_LIFECYCLE_DUPLICATE,
    PROOF_LIFECYCLE_REPLAY,
    PROOF_LIFECYCLE_REVOKED,
    PROOF_LIFECYCLE_STALE,
    PROOF_LIFECYCLE_SUPERSEDED,
    RUN_STARTED,
    SUPPORTED_RUN_TYPE,
    ArtifactChecksumEntry,
    DurableRunPrimaryEvidenceCompletionIntegrationInput,
    compute_completion_integration_input_digest,
    compute_manifest_digest,
    compute_completion_identity_digest,
    compute_run_identity_digest,
    default_minimal_completion_integration_input,
    default_minimal_pe22_integration_proof,
    default_minimal_pe23_integration_proof,
    default_minimal_pe24_integration_proof,
    default_minimal_pe35_integration_proof,
    default_minimal_pe37_integration_proof,
    default_minimal_pe31_integration_proof,
    default_minimal_safety_snapshot,
    evaluate_durable_run_primary_evidence_completion_integration,
    serialize_completion_integration_input_canonical,
    validate_durable_run_primary_evidence_completion_integration_input,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HANDOFF_STATE_CURRENT,
    HANDOFF_STATE_RECOVERY_REQUIRED,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
    HandoffLifecycleMetadata,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    compute_boundary_result_digest as compute_pe35_boundary_result_digest,
    evaluate_handoff_staleness_revocation_recovery_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    BOUNDARY_OWNER as PE37_BOUNDARY_OWNER,
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    ManifestEntry,
    PACKAGE_MARKER as PE21_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import FOLLOWUP_RUN_GATE
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_pe31_integration_input,
    evaluate_reconciliation_review_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE23_CONTRACT_VERSION,
    CapitalSlotReleaseReason,
    default_minimal_integration_input as default_minimal_pe23_integration_input,
    evaluate_capital_slot_ratchet_release_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE22_CONTRACT_VERSION,
    FlattenStateProof,
    KillSwitchEvaluationProof,
    RiskEvaluationProof,
    default_minimal_integration_input as default_minimal_pe22_integration_input,
    evaluate_risk_killswitch_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE24_CONTRACT_VERSION,
    Pe19ReviewProofBinding,
    default_minimal_integration_input as default_minimal_pe24_integration_input,
    evaluate_pilot_envelope_lifecycle_integration,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
)
PE21_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"
)
PE16_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
PE31_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
)
PE31_TEST_OWNER = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
)
PE22_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
PE22_TEST_OWNER = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
PE23_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
)
PE23_TEST_OWNER = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
)
PE24_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py"
)
PE24_TEST_OWNER = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py"
)
PE21_TEST_OWNER = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"
)
PRIMARY_EVIDENCE_MODULE = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
GAP4_TEST_OWNER = REPO_ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_contract_v0.py"
GAP2A1_TEST_OWNER = (
    REPO_ROOT / "tests" / "ops" / "test_gap2a1_primary_evidence_enforcement_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_DURABLE_RUN_PRIMARY_EVIDENCE_COMPLETION_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_DURABLE_RUN_PRIMARY_EVIDENCE_COMPLETION_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
DURABLE_ARCHIVE_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in INTEGRATION_MODULE.read_text(encoding="utf-8")


def test_canonical_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert "bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0" in (
        integration_text
    )
    assert (
        "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0"
        in integration_text
    )
    assert "bounded_futures_testnet_preflight_packet_archive_contract_v0" in integration_text
    assert "scripts.ops.primary_evidence_retention_v0" in integration_text
    assert PE21_PACKAGE_MARKER in PE21_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in PE16_MODULE.read_text(encoding="utf-8")
    assert PE21_MODULE.exists()
    assert PE16_MODULE.exists()
    assert PE31_MODULE.exists()
    assert PE31_TEST_OWNER.exists()
    assert PE22_MODULE.exists()
    assert PE22_TEST_OWNER.exists()
    assert PE23_MODULE.exists()
    assert PE23_TEST_OWNER.exists()
    assert PE24_MODULE.exists()
    assert PE24_TEST_OWNER.exists()
    assert PE21_TEST_OWNER.exists()
    assert PRIMARY_EVIDENCE_MODULE.exists()
    assert GAP4_TEST_OWNER.exists()
    assert GAP2A1_TEST_OWNER.exists()
    assert PE16_ARCHIVE_OWNER == str(PE16_MODULE.relative_to(REPO_ROOT))
    assert GAP4_COMPLETION_OWNER == str(GAP4_TEST_OWNER.relative_to(REPO_ROOT))
    assert GAP2A1_ENFORCEMENT_OWNER == str(GAP2A1_TEST_OWNER.relative_to(REPO_ROOT))
    assert PE31_INTEGRATION_OWNER == PE31_CONTRACT_VERSION
    assert PE22_INTEGRATION_OWNER == PE22_CONTRACT_VERSION
    assert PE23_INTEGRATION_OWNER == PE23_CONTRACT_VERSION
    assert PE24_INTEGRATION_OWNER == PE24_CONTRACT_VERSION


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_RUN_COMPLETION_RECORDED is False
    assert PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED is False
    assert RECONCILIATION_EXECUTED is False
    assert RISK_EVALUATION_EXECUTED is False
    assert KILLSWITCH_TRIGGERED is False
    assert FLATTEN_EXECUTED is False
    assert CAPITAL_SLOT_RATCHET_EXECUTED is False
    assert CAPITAL_SLOT_RELEASE_EXECUTED is False
    assert CAPITAL_REALLOCATION_EXECUTED is False
    assert RESERVE_TOP_UP_EXECUTED is False
    assert PILOT_ENVELOPE_EXECUTED is False
    assert PILOT_STARTED is False
    assert RECOVERY_EXECUTED is False
    assert RESUME_EXECUTED is False
    assert RETRY_EXECUTED is False
    assert REPLAY_EXECUTED is False
    assert STATE_MUTATED is False
    assert PARTIAL_FAILURE_OPERATIONALLY_RESOLVED is False
    assert RUN_STARTED is False
    assert ARCHIVE_READ is False
    assert ARCHIVE_WRITTEN is False
    assert MANIFEST_READ is False
    assert MANIFEST_WRITTEN is False
    assert FILESYSTEM_ACCESSED is False
    assert AUTHORITY_LIFT is False
    assert GLOBAL_RUN_COMPLETION_READINESS is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_completion_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_completion_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_completion_integration_input_canonical(
        left
    ) == serialize_completion_integration_input_canonical(right)
    assert compute_completion_integration_input_digest(
        left
    ) == compute_completion_integration_input_digest(right)
    left_result = evaluate_durable_run_primary_evidence_completion_integration(left)
    right_result = evaluate_durable_run_primary_evidence_completion_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]


def test_coherent_static_completion_happy_path_passes() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["completion_static_proven"] is True
    assert result["completion_claimed"] is True
    assert result["pe21_integration_pass"] is True
    assert result["pe31_integration_pass"] is True
    assert result["pe22_integration_pass"] is True
    assert result["pe23_integration_pass"] is True
    assert result["pe24_integration_pass"] is True
    assert result["pe35_boundary_pass"] is True
    assert result["durable_run_primary_evidence_completion_bound"] is True
    assert result["pe21_reconciliation_primary_evidence_bound"] is True
    assert result["pe31_reconciliation_review_bound"] is True
    assert result["pe22_risk_killswitch_flatten_lifecycle_bound"] is True
    assert result["pe23_capital_slot_ratchet_release_lifecycle_bound"] is True
    assert result["pe24_pilot_envelope_lifecycle_bound"] is True
    assert result["pe35_handoff_recovery_boundary_bound"] is True
    assert result["recovery_boundary_bound"] is True
    assert result["partial_failure_recovery_bound"] is True
    assert result["pe37_boundary_pass"] is True
    assert result["pe37_operator_review_chain_durable_evidence_traceability_bound"] is True
    assert result["pe34_handoff_bound"] is True
    assert result["pe35_staleness_revocation_recovery_bound"] is True
    assert result["pe36_admission_presentation_bound"] is True
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_durable_run_primary_evidence_completion_integration(
        default_minimal_completion_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["operative_run_completion_recorded"] is False
    assert result["primary_evidence_operationally_accepted"] is False
    assert result["reconciliation_executed"] is False
    assert result["risk_evaluation_executed"] is False
    assert result["killswitch_triggered"] is False
    assert result["flatten_executed"] is False
    assert result["capital_slot_ratchet_executed"] is False
    assert result["capital_slot_release_executed"] is False
    assert result["capital_reallocation_executed"] is False
    assert result["reserve_top_up_executed"] is False
    assert result["pilot_envelope_executed"] is False
    assert result["pilot_started"] is False
    assert result["recovery_executed"] is False
    assert result["resume_executed"] is False
    assert result["retry_executed"] is False
    assert result["replay_executed"] is False
    assert result["state_mutated"] is False
    assert result["partial_failure_operationally_resolved"] is False
    assert result["archive_read"] is False
    assert result["archive_written"] is False
    assert result["manifest_read"] is False
    assert result["manifest_written"] is False
    assert result["filesystem_accessed"] is False
    assert result["run_started"] is False
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
    assert result["global_run_completion_readiness"] is False


def test_missing_run_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input, run_identity=replace(integration_input.run_identity, run_id="")
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_identity: run_id required" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "run_type", ["", "spot", "bitcoin", "btc", "xbt", "paper", "shadow", "live"]
)
def test_invalid_run_type_fails(run_type: str) -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(integration_input, run_type=run_type)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False


def test_missing_source_revision_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(integration_input, source_revision="")
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_wrong_canonical_owner_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe16_archive=replace(integration_input.pe16_archive, archive_owner="wrong/owner.py"),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("archive_owner must be" in r for r in result["fail_reasons"])


def test_missing_durable_run_root_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        durable_run_root=replace(integration_input.durable_run_root, run_root_identity=""),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_root_identity required" in r for r in result["fail_reasons"])


def test_run_root_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        durable_run_root=replace(integration_input.durable_run_root, run_root_digest="f" * 64),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_root_digest mismatch" in r for r in result["fail_reasons"])


def test_tmp_only_evidence_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        durable_run_root=replace(
            integration_input.durable_run_root,
            durable_archive_root="/tmp/evidence",
        ),
        evidence_mode=EVIDENCE_MODE_TMP_ONLY,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("/tmp" in r for r in result["fail_reasons"])


def test_root_escape_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        durable_run_root=replace(
            integration_input.durable_run_root,
            run_root_identity="../escape",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("traversal" in r.lower() or ".." in r for r in result["fail_reasons"])


def test_path_traversal_in_artifact_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_artifacts = (
        ArtifactChecksumEntry(relative_path="../escape.json", digest="a" * 64),
        *integration_input.artifact_checksums[1:],
    )
    bad = replace(integration_input, artifact_checksums=bad_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("traversal" in r.lower() for r in result["fail_reasons"])


def test_missing_required_artifact_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_artifacts = tuple(
        entry
        for entry in integration_input.artifact_checksums
        if entry.relative_path != "RUN_METADATA.json"
    )
    bad = replace(integration_input, artifact_checksums=bad_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("missing required artifact paths" in r for r in result["fail_reasons"])


def test_unexpected_artifact_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_artifacts = (
        *integration_input.artifact_checksums,
        ArtifactChecksumEntry(relative_path="extra/UNEXPECTED.json", digest="a" * 64),
    )
    bad = replace(integration_input, artifact_checksums=bad_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("unexpected artifact paths" in r for r in result["fail_reasons"])


def test_duplicate_artifact_path_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    duplicate = integration_input.artifact_checksums[0]
    bad_artifacts = (*integration_input.artifact_checksums, duplicate)
    bad = replace(integration_input, artifact_checksums=bad_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("duplicate artifact checksum paths" in r for r in result["fail_reasons"])


def test_missing_checksum_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_artifacts = tuple(
        replace(entry, digest="") if entry.relative_path == "RUN_METADATA.json" else entry
        for entry in integration_input.artifact_checksums
    )
    bad = replace(integration_input, artifact_checksums=bad_artifacts)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("invalid artifact checksum" in r for r in result["fail_reasons"])


def test_checksum_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    manifest_entries = integration_input.manifest_proof.manifest_entries
    bad_entries = tuple(
        replace(entry, digest="f" * 64)
        if entry.relative_path == manifest_entries[0].relative_path
        else entry
        for entry in manifest_entries
    )
    bad = replace(
        integration_input,
        manifest_proof=replace(integration_input.manifest_proof, manifest_entries=bad_entries),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("checksum mismatch" in r for r in result["fail_reasons"])


def test_manifest_identity_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        manifest_proof=replace(integration_input.manifest_proof, manifest_identity="0" * 64),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_identity mismatch" in r for r in result["fail_reasons"])


def test_manifest_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        manifest_proof=replace(integration_input.manifest_proof, manifest_digest="0" * 64),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_digest mismatch" in r for r in result["fail_reasons"])


def test_archive_identity_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe16_archive=replace(integration_input.pe16_archive, archive_identity="other/path"),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("archive_identity mismatch" in r for r in result["fail_reasons"])


def test_post_write_verification_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        post_write_verification=replace(
            integration_input.post_write_verification,
            post_write_verification_pass=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("post_write_verification_pass must be true" in r for r in result["fail_reasons"])


def test_manifest_verification_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        manifest_proof=replace(integration_input.manifest_proof, manifest_verify_rc=1),
        post_write_verification=replace(
            integration_input.post_write_verification,
            manifest_verify_rc=1,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_verify_rc must be 0" in r for r in result["fail_reasons"])


def test_pe21_proof_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe21_proof=replace(
            integration_input.pe21_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe31_proof_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe31_reconciliation_review_integration_proof=replace(
            integration_input.pe31_reconciliation_review_integration_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_missing_pe31_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe31_reconciliation_review_integration_proof=replace(
            integration_input.pe31_reconciliation_review_integration_proof,
            pe31_integration_pass=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe31_integration_pass must be true" in r for r in result["fail_reasons"])


def test_pe31_references_wrong_pe21_proof_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe31_input = replace(
        integration_input.pe31_reconciliation_review_integration_input,
        pe21_reconciliation_primary_evidence_integration_proof=replace(
            integration_input.pe31_reconciliation_review_integration_input.pe21_reconciliation_primary_evidence_integration_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe31_reconciliation_review_integration_input=bad_pe31_input,
        pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
            bad_pe31_input
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe21_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_completion_proof_chain_pe31_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe31_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe31_proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_completion_proof_chain_traceability_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            shared_traceability_identity="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("shared_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_unresolved_order_state_in_pe31_review_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_review = replace(
        integration_input.pe31_reconciliation_review_integration_input.reconciliation_review_proof,
        orders_created=1,
    )
    bad_pe31_input = replace(
        integration_input.pe31_reconciliation_review_integration_input,
        reconciliation_review_proof=bad_review,
    )
    bad = replace(
        integration_input,
        pe31_reconciliation_review_integration_input=bad_pe31_input,
        pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
            bad_pe31_input
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("unresolved order state" in r for r in result["fail_reasons"])


def test_unresolved_position_state_in_pe31_review_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_review = replace(
        integration_input.pe31_reconciliation_review_integration_input.reconciliation_review_proof,
        positions_changed=1,
    )
    bad_pe31_input = replace(
        integration_input.pe31_reconciliation_review_integration_input,
        reconciliation_review_proof=bad_review,
    )
    bad = replace(
        integration_input,
        pe31_reconciliation_review_integration_input=bad_pe31_input,
        pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
            bad_pe31_input
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("unresolved position state" in r for r in result["fail_reasons"])


def test_pe31_alone_does_not_authorize_completion() -> None:
    pe31_input = default_minimal_pe31_integration_input()
    pe31_result = evaluate_reconciliation_review_lifecycle_integration(pe31_input)
    assert pe31_result["integration_pass"] is True
    assert pe31_result["operative_reconciliation_executed"] is False
    assert pe31_result["authority_lift"] is False


def test_pe22_alone_does_not_authorize_completion() -> None:
    pe22_input = default_minimal_pe22_integration_input()
    pe22_result = evaluate_risk_killswitch_lifecycle_integration(pe22_input)
    assert pe22_result["integration_pass"] is True
    assert pe22_result["operative_risk_evaluation_executed"] is False
    assert pe22_result["operative_killswitch_executed"] is False
    assert pe22_result["operative_flatten_executed"] is False
    assert pe22_result["authority_lift"] is False


def test_missing_pe22_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_proof_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_proof: integration_proof_digest required" in r for r in result["fail_reasons"])


def test_pe22_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=default_minimal_pe22_integration_proof(
            bad_pe22_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_proof: source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe22_wrong_owner_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_owner="wrong.owner.v0",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_pe22_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_proof: integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            traceability_identity="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe22_run_root_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        lifecycle_matrix_proof=replace(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input.lifecycle_matrix_proof,
            lifecycle_state_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=default_minimal_pe22_integration_proof(
            bad_pe22_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_run_identity_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            run_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_completion_proof_chain_pe22_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe22_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe22_proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe22_risk_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        risk_evaluation_proof=replace(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input.risk_evaluation_proof,
            proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("risk_evaluation_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_killswitch_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        killswitch_evaluation_proof=replace(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input.killswitch_evaluation_proof,
            proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("killswitch_evaluation_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_flatten_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        flatten_state_proof=replace(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input.flatten_state_proof,
            proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("flatten_state_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe22_contradictory_risk_killswitch_flatten_state_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        killswitch_evaluation_proof=replace(
            integration_input.pe22_risk_killswitch_lifecycle_integration_input.killswitch_evaluation_proof,
            killswitch_clear=False,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=replace(
            default_minimal_pe22_integration_proof(
                bad_pe22_input,
                traceability_identity=integration_input.durable_run_root.run_root_digest,
                run_identity_digest=integration_input.run_identity.run_identity_digest,
            ),
            safe_completion_state_proven=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "safe completion state not proven" in r or "PE-22 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe22_missing_safe_completion_state_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe22_input = replace(
        integration_input.pe22_risk_killswitch_lifecycle_integration_input,
        flatten_state_proof=FlattenStateProof(
            proof_digest=integration_input.pe22_risk_killswitch_lifecycle_integration_input.flatten_state_proof.proof_digest,
            proof_pass=False,
            position_flattened_by_end=False,
            cancel_or_close_evidence_valid=False,
            position_quantity=1.0,
            position_must_be_flattened=True,
            binding_reference=integration_input.pe22_risk_killswitch_lifecycle_integration_input.flatten_state_proof.binding_reference,
        ),
    )
    bad = replace(
        integration_input,
        pe22_risk_killswitch_lifecycle_integration_input=bad_pe22_input,
        pe22_risk_killswitch_flatten_proof=replace(
            default_minimal_pe22_integration_proof(
                bad_pe22_input,
                traceability_identity=integration_input.durable_run_root.run_root_digest,
                run_identity_digest=integration_input.run_identity.run_identity_digest,
            ),
            safe_completion_state_proven=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "safe completion state not proven" in r or "PE-22 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe22_pe22_integration_pass_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            pe22_integration_pass=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_integration_pass must be true" in r for r in result["fail_reasons"])


def test_pe22_missing_required_field_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe22_risk_killswitch_flatten_proof,
            risk_evaluation_proof_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("risk_evaluation_proof_digest required" in r for r in result["fail_reasons"])


def test_pe23_alone_does_not_authorize_completion() -> None:
    pe23_input = default_minimal_pe23_integration_input()
    pe23_result = evaluate_capital_slot_ratchet_release_lifecycle_integration(pe23_input)
    assert pe23_result["integration_pass"] is True
    assert pe23_result["operative_ratchet_applied"] is False
    assert pe23_result["operative_slot_release_executed"] is False
    assert pe23_result["operative_capital_reallocation_executed"] is False
    assert pe23_result["operative_reserve_movement_executed"] is False
    assert pe23_result["authority_lift"] is False


def test_missing_pe23_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            integration_proof_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe23_proof: integration_proof_digest required" in r for r in result["fail_reasons"])


def test_pe23_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    bad_pe23_input = replace(
        integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input,
        source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
        pe23_capital_slot_ratchet_release_proof=default_minimal_pe23_integration_proof(
            bad_pe23_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
            completion_identity_digest=compute_completion_identity_digest(
                run_root_digest=integration_input.durable_run_root.run_root_digest,
                manifest_digest=integration_input.manifest_proof.manifest_digest,
                source_revision=integration_input.source_revision,
            ),
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe23_proof: source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe23_wrong_owner_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            integration_owner="wrong.owner.v0",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_pe23_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe23_proof: integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            traceability_identity="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe23_run_root_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe23_input = replace(
        integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input,
        lifecycle_matrix_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input.lifecycle_matrix_proof,
            lifecycle_state_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
        pe23_capital_slot_ratchet_release_proof=default_minimal_pe23_integration_proof(
            bad_pe23_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
            completion_identity_digest=compute_completion_identity_digest(
                run_root_digest=integration_input.durable_run_root.run_root_digest,
                manifest_digest=integration_input.manifest_proof.manifest_digest,
                source_revision=integration_input.source_revision,
            ),
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_run_identity_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            run_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_completion_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            completion_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("completion_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_capital_slot_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            capital_slot_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("capital_slot_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_completion_proof_chain_pe23_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe23_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe23_proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe23_ratchet_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe23_input = replace(
        integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input,
        ratchet_evaluation_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input.ratchet_evaluation_proof,
            proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("ratchet_evaluation_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_release_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe23_input = replace(
        integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input,
        release_eligibility_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input.release_eligibility_proof,
            proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("release_eligibility_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe23_contradictory_ratchet_release_state_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    bad_pe23_input = replace(
        pe23_input,
        release_eligibility_proof=replace(
            pe23_input.release_eligibility_proof,
            release_eligible=True,
            released=True,
            release_reason_code=CapitalSlotReleaseReason.INACTIVITY.value,
        ),
        activity_metrics=replace(
            pe23_input.activity_metrics,
            realized_volatility=pe23_input.capital_slot_config.min_realized_volatility,
            atr_or_range=pe23_input.capital_slot_config.min_atr_or_range,
            time_without_cashflow_step=0,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
        pe23_capital_slot_ratchet_release_proof=default_minimal_pe23_integration_proof(
            bad_pe23_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
            completion_identity_digest=compute_completion_identity_digest(
                run_root_digest=integration_input.durable_run_root.run_root_digest,
                manifest_digest=integration_input.manifest_proof.manifest_digest,
                source_revision=integration_input.source_revision,
            ),
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "inactivity release without breach" in r or "PE-23 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe23_reserve_topup_attempt_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    bad_pe23_input = replace(
        pe23_input,
        reserve_topup_block_proof=replace(
            pe23_input.reserve_topup_block_proof,
            reserve_topup_attempted=True,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "reserve_topup_attempted must be false" in r or "PE-23 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe23_slot_basis_not_following_settled_equity_downward_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    bad_equity = replace(
        pe23_input.equity_basis,
        prior_valid_settled_basis=400.0,
        new_settled_realized_equity=300.0,
        current_slot_basis=400.0,
    )
    bad_pe23_input = replace(pe23_input, equity_basis=bad_equity)
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "slot basis must follow realized loss downward" in r
        or "unallowable slot basis increase" in r
        or "PE-23 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe23_aggressive_ratchet_semantics_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    bad_pe23_input = replace(
        pe23_input,
        ratchet_evaluation_proof=replace(
            pe23_input.ratchet_evaluation_proof,
            can_ratchet=True,
            new_active_slot_base=pe23_input.equity_basis.new_settled_realized_equity + 100.0,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "unallowable slot basis increase" in r or "PE-23 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe23_incoherent_opportunity_cost_release_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe23_input = integration_input.pe23_capital_slot_ratchet_release_lifecycle_integration_input
    bad_pe23_input = replace(
        pe23_input,
        release_eligibility_proof=replace(
            pe23_input.release_eligibility_proof,
            release_eligible=True,
            released=True,
            release_reason_code=CapitalSlotReleaseReason.OPPORTUNITY_COST.value,
        ),
        activity_metrics=replace(
            pe23_input.activity_metrics,
            opportunity_score=pe23_input.capital_slot_config.min_opportunity_score,
        ),
    )
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_lifecycle_integration_input=bad_pe23_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "opportunity release without score breach" in r or "PE-23 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe23_pe23_integration_pass_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            pe23_integration_pass=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe23_integration_pass must be true" in r for r in result["fail_reasons"])


def test_pe23_missing_required_field_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe23_capital_slot_ratchet_release_proof,
            ratchet_evaluation_proof_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("ratchet_evaluation_proof_digest required" in r for r in result["fail_reasons"])


def test_pe24_alone_does_not_authorize_completion() -> None:
    pe24_input = default_minimal_pe24_integration_input()
    pe24_result = evaluate_pilot_envelope_lifecycle_integration(pe24_input)
    assert pe24_result["integration_pass"] is True
    assert pe24_result["operative_pilot_executed"] is False
    assert pe24_result["pilot_start_authorized"] is False
    assert pe24_result["authority_lift"] is False


def test_missing_pe24_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            integration_proof_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe24_proof: integration_proof_digest required" in r for r in result["fail_reasons"])


def test_pe24_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
        pe24_pilot_envelope_lifecycle_proof=default_minimal_pe24_integration_proof(
            bad_pe24_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
            completion_identity_digest=compute_completion_identity_digest(
                run_root_digest=integration_input.durable_run_root.run_root_digest,
                manifest_digest=integration_input.manifest_proof.manifest_digest,
                source_revision=integration_input.source_revision,
            ),
            pe22_integration_proof_digest=integration_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest,
            pe23_integration_proof_digest=integration_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe24_proof: source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe24_wrong_owner_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            integration_owner="wrong.owner.v0",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_pe24_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe24_proof: integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe24_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            traceability_identity="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe24_run_root_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        lifecycle_matrix_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.lifecycle_matrix_proof,
            lifecycle_state_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
        pe24_pilot_envelope_lifecycle_proof=default_minimal_pe24_integration_proof(
            bad_pe24_input,
            traceability_identity=integration_input.durable_run_root.run_root_digest,
            run_identity_digest=integration_input.run_identity.run_identity_digest,
            completion_identity_digest=compute_completion_identity_digest(
                run_root_digest=integration_input.durable_run_root.run_root_digest,
                manifest_digest=integration_input.manifest_proof.manifest_digest,
                source_revision=integration_input.source_revision,
            ),
            pe22_integration_proof_digest=integration_input.pe22_risk_killswitch_flatten_proof.integration_proof_digest,
            pe23_integration_proof_digest=integration_input.pe23_capital_slot_ratchet_release_proof.integration_proof_digest,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_digest mismatch" in r for r in result["fail_reasons"])


def test_pe24_run_identity_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            run_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("run_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe24_completion_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            completion_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("completion_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe24_pilot_envelope_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pilot_envelope_identity_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pilot_envelope_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_completion_proof_chain_pe24_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe24_proof_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe24_proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe24_pilot_review_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe19_review_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe19_review_proof,
            review_proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe19_review_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe24_pilot_safety_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe22_risk_killswitch_flatten_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe22_integration_proof_digest mismatch" in r or "pilot envelope coherence not proven" in r
        for r in result["fail_reasons"]
    )


def test_pe24_pilot_capital_proof_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe23_capital_slot_ratchet_release_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe23_integration_proof_digest mismatch" in r or "pilot envelope coherence not proven" in r
        for r in result["fail_reasons"]
    )


def test_pe24_contradictory_pilot_envelope_state_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        safety_snapshot=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.safety_snapshot,
            pilot_start_authorized=True,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pilot_start_authorized must be False" in r or "PE-24 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe24_missing_pe19_review_coherence_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe19_review_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe19_review_proof,
            review_valid=False,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pilot_envelope_coherence_proven=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pilot envelope coherence not proven" in r or "PE-24 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe24_missing_pe22_safety_coherence_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe22_risk_killswitch_flatten_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe22_risk_killswitch_flatten_proof,
            pe22_integration_pass=False,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pilot_envelope_coherence_proven=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pilot envelope coherence not proven" in r or "PE-24 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe24_missing_pe23_capital_coherence_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_pe24_input = replace(
        integration_input.pe24_pilot_envelope_lifecycle_integration_input,
        pe23_capital_slot_ratchet_release_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_integration_input.pe23_capital_slot_ratchet_release_proof,
            pe23_integration_pass=False,
        ),
    )
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_integration_input=bad_pe24_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pilot_envelope_coherence_proven=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pilot envelope coherence not proven" in r or "PE-24 evaluation failed" in r
        for r in result["fail_reasons"]
    )


def test_pe24_pe24_integration_pass_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pe24_integration_pass=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe24_integration_pass must be true" in r for r in result["fail_reasons"])


def test_pe24_missing_required_field_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe24_pilot_envelope_lifecycle_proof=replace(
            integration_input.pe24_pilot_envelope_lifecycle_proof,
            pe20_package_id="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe20_package_id required" in r for r in result["fail_reasons"])


def test_gap4_completion_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        gap4_completion=replace(
            integration_input.gap4_completion,
            gap4_output_evidence_paths_verified=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "gap4_output_evidence_paths_verified must be False" in r for r in result["fail_reasons"]
    )


def test_gap2a1_enforcement_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        gap2a1_enforcement=replace(
            integration_input.gap2a1_enforcement,
            primary_evidence_enforced=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("primary_evidence_enforced must be False" in r for r in result["fail_reasons"])


def test_completion_true_with_incomplete_evidence_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad_artifacts = tuple(
        entry
        for entry in integration_input.artifact_checksums
        if entry.relative_path != MANIFEST_FILENAME
    )[:-1]
    bad = replace(
        integration_input,
        artifact_checksums=bad_artifacts,
        completion_claimed=True,
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert result["completion_static_proven"] is False


@pytest.mark.parametrize(
    "evidence_mode", [EVIDENCE_MODE_PLANNED, EVIDENCE_MODE_SIMULATED, EVIDENCE_MODE_TMP_ONLY]
)
def test_planned_or_simulated_evidence_rejected_for_completion(evidence_mode: str) -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(integration_input, evidence_mode=evidence_mode, completion_claimed=True)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("evidence_mode" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "lifecycle_state",
    [
        PROOF_LIFECYCLE_STALE,
        PROOF_LIFECYCLE_REVOKED,
        PROOF_LIFECYCLE_SUPERSEDED,
        PROOF_LIFECYCLE_REPLAY,
        PROOF_LIFECYCLE_DUPLICATE,
    ],
)
def test_invalid_proof_lifecycle_states_fail(lifecycle_state: str) -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        proof_lifecycle=replace(integration_input.proof_lifecycle, lifecycle_state=lifecycle_state),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("invalid proof lifecycle state" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    integration_input = default_minimal_completion_integration_input()
    result = evaluate_durable_run_primary_evidence_completion_integration(
        integration_input,
        extra_field_names=("secret_override", "credential_token"),
    )
    assert result["integration_pass"] is False
    assert any("forbidden extra field" in r for r in result["fail_reasons"])


def test_authority_override_fields_fail() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        safety_snapshot=replace(
            integration_input.safety_snapshot,
            execution_authorized=True,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("execution_authorized must be False" in r for r in result["fail_reasons"])


def test_completion_claim_without_proof_chain_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    result = evaluate_durable_run_primary_evidence_completion_integration(
        integration_input,
        completion_claim_without_full_evidence=True,
    )
    assert result["integration_pass"] is False


def test_no_input_mutation_from_evaluation() -> None:
    integration_input = default_minimal_completion_integration_input()
    before = serialize_completion_integration_input_canonical(integration_input)
    evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    after = serialize_completion_integration_input_canonical(integration_input)
    assert before == after
    assert (
        validate_durable_run_primary_evidence_completion_integration_input(integration_input) == []
    )


def test_bounded_durable_run_required_paths_covered() -> None:
    integration_input = default_minimal_completion_integration_input()
    artifact_paths = {entry.relative_path for entry in integration_input.artifact_checksums}
    assert set(BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS) == artifact_paths


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_durable_run_primary_evidence_completion_integration.v0"
    )
    assert COMPLETION_INTEGRATION_OWNER == CONTRACT_VERSION
    assert PE21_INTEGRATION_OWNER.endswith(".v0")
    assert PE22_INTEGRATION_OWNER == PE22_CONTRACT_VERSION
    assert PE23_INTEGRATION_OWNER == PE23_CONTRACT_VERSION
    assert PE24_INTEGRATION_OWNER == PE24_CONTRACT_VERSION
    assert PE35_INTEGRATION_OWNER == PE35_CONTRACT_VERSION
    assert PE34_INTEGRATION_OWNER == PE34_CONTRACT_VERSION
    assert PE36_INTEGRATION_OWNER == PE36_CONTRACT_VERSION
    assert PE37_INTEGRATION_OWNER == PE37_BOUNDARY_OWNER
    assert SUPPORTED_RUN_TYPE == "bounded_futures_testnet"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.execution_authorized is False
    assert snapshot.live_authorized is False
    assert snapshot.evidence_acceptance_authorized is False
    assert snapshot.promotion_authorized is False
    assert snapshot.network_allowed is False
    assert snapshot.credentials_allowed is False
    assert snapshot.orders_allowed is False
    assert snapshot.futures_only is True
    assert snapshot.bitcoin_direction_allowed is False
    assert snapshot.followup_run_gate == FOLLOWUP_RUN_GATE


def test_current_lifecycle_state_passes() -> None:
    integration_input = default_minimal_completion_integration_input()
    assert integration_input.proof_lifecycle.lifecycle_state == PROOF_LIFECYCLE_CURRENT
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True


def test_manifest_digest_matches_canonical_entries() -> None:
    integration_input = default_minimal_completion_integration_input()
    manifest_entries = tuple(
        ManifestEntry(digest=entry.digest, relative_path=entry.relative_path)
        for entry in integration_input.manifest_proof.manifest_entries
    )
    assert integration_input.manifest_proof.manifest_digest == compute_manifest_digest(
        manifest_entries
    )


def test_run_identity_digest_matches_canonical_inputs() -> None:
    integration_input = default_minimal_completion_integration_input(
        source_revision=VALID_COMMIT_SHA
    )
    expected = compute_run_identity_digest(
        run_id=integration_input.run_identity.run_id,
        run_type=integration_input.run_type,
        source_revision=integration_input.source_revision,
    )
    assert integration_input.run_identity.run_identity_digest == expected


def test_pe35_alone_does_not_authorize_completion() -> None:
    pe35_input = default_minimal_completion_integration_input().pe35_handoff_staleness_revocation_recovery_boundary_input
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    assert pe35_result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True
    assert pe35_result["recovery_executed"] is False
    assert pe35_result["authority_lift"] is False


def test_missing_pe35_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            boundary_result_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: boundary_result_digest required" in r for r in result["fail_reasons"])


def test_pe35_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            source_revision=ALT_COMMIT_SHA,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe35_wrong_owner_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            boundary_owner="wrong-owner",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: boundary_owner must be" in r for r in result["fail_reasons"])


def test_pe35_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            boundary_result_digest="f" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: boundary_result_digest mismatch" in r for r in result["fail_reasons"])


def test_pe35_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            traceability_identity="a" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe35_run_identity_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            run_identity_digest="b" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: run_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe35_manifest_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            manifest_identity_digest="c" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: manifest_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe35_completion_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            completion_identity_digest="d" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe35_proof: completion_identity_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe35_handoff_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            handoff_digest="e" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_pe35_handoff_generation_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            handoff_generation=99,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: handoff_generation mismatch" in r for r in result["fail_reasons"])


def test_pe35_recovery_generation_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            recovery_generation=2,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe35_proof: recovery_generation mismatch" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "lifecycle_state",
    [
        HANDOFF_STATE_STALE,
        HANDOFF_STATE_SUPERSEDED,
        HANDOFF_STATE_REVOKED,
        HANDOFF_STATE_RECOVERY_REQUIRED,
    ],
)
def test_pe35_open_partial_failure_states_fail(lifecycle_state: str) -> None:
    integration_input = default_minimal_completion_integration_input()
    pe35_input = integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    bad_pe35 = replace(
        pe35_input,
        lifecycle_metadata=replace(
            pe35_input.lifecycle_metadata,
            lifecycle_state=lifecycle_state,
        ),
    )
    bad = replace(
        integration_input, pe35_handoff_staleness_revocation_recovery_boundary_input=bad_pe35
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("open partial-failure lifecycle state" in r for r in result["fail_reasons"])


def test_pe35_recovery_boundary_bound_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe35_handoff_recovery_boundary_proof=replace(
            integration_input.pe35_handoff_recovery_boundary_proof,
            recovery_boundary_bound=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe35_proof: recovery_boundary_bound must be true" in r for r in result["fail_reasons"]
    )


def test_pe35_completion_proof_chain_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe35_boundary_result_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe35_boundary_result_digest mismatch" in r
        for r in result["fail_reasons"]
    )


def test_pe35_pe21_pe31_pe22_pe23_pe24_pe37_semantics_remain_bound_on_happy_path() -> None:
    result = evaluate_durable_run_primary_evidence_completion_integration(
        default_minimal_completion_integration_input(source_revision=VALID_COMMIT_SHA)
    )
    assert result["pe21_integration_pass"] is True
    assert result["pe31_integration_pass"] is True
    assert result["pe22_integration_pass"] is True
    assert result["pe23_integration_pass"] is True
    assert result["pe24_integration_pass"] is True
    assert result["pe35_boundary_pass"] is True
    assert result["pe37_boundary_pass"] is True
    assert result["pe37_operator_review_chain_durable_evidence_traceability_bound"] is True


def test_pe37_alone_does_not_authorize_completion() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe37_result = evaluate_durable_evidence_traceability_boundary(pe37_input)
    assert pe37_result["durable_evidence_traceability_boundary_satisfied"] is True
    assert pe37_result["operator_review_executed"] is False
    assert pe37_result["admission_executed"] is False
    assert pe37_result["authority_lift"] is False


def test_missing_pe37_proof_binding_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            boundary_result_digest="",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: boundary_result_digest required" in r for r in result["fail_reasons"])


def test_pe37_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            source_revision=ALT_COMMIT_SHA,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe37_wrong_owner_identity_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            traceability_owner="wrong-owner",
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: traceability_owner must be" in r for r in result["fail_reasons"])


def test_pe37_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            boundary_result_digest="f" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: boundary_result_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            traceability_identity="a" * 64,
            review_chain_identity="a" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe37_durable_artifact_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            durable_artifact_identity="b" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe37_proof: durable_artifact_identity mismatch" in r for r in result["fail_reasons"]
    )


def test_pe37_manifest_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            manifest_identity_digest="c" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: manifest_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_run_root_traceability_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            run_identity_digest="d" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: run_identity_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_completion_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            completion_identity_digest="e" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe37_proof: completion_identity_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe37_review_chain_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            review_chain_identity="f" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: review_chain_identity mismatch" in r for r in result["fail_reasons"])


def test_pe37_stale_handoff_lifecycle_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe35_input = pe37_input.pe36_boundary_input.pe35_boundary_input
    stale_pe35 = replace(
        pe35_input,
        lifecycle_metadata=replace(
            pe35_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    stale_pe36 = replace(
        pe37_input.pe36_boundary_input,
        pe35_boundary_input=stale_pe35,
    )
    stale_pe37 = replace(pe37_input, pe36_boundary_input=stale_pe36)
    bad = replace(integration_input, pe37_traceability_boundary_input=stale_pe37)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_boundary_input:" in r for r in result["fail_reasons"])


def test_pe37_revoked_handoff_lifecycle_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe35_input = pe37_input.pe36_boundary_input.pe35_boundary_input
    revoked_pe35 = replace(
        pe35_input,
        lifecycle_metadata=replace(
            pe35_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    revoked_pe36 = replace(
        pe37_input.pe36_boundary_input,
        pe35_boundary_input=revoked_pe35,
    )
    revoked_pe37 = replace(pe37_input, pe36_boundary_input=revoked_pe36)
    bad = replace(integration_input, pe37_traceability_boundary_input=revoked_pe37)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_boundary_input:" in r for r in result["fail_reasons"])


def test_pe37_superseded_handoff_lifecycle_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    pe37_input = integration_input.pe37_traceability_boundary_input
    pe35_input = pe37_input.pe36_boundary_input.pe35_boundary_input
    superseded_pe35 = replace(
        pe35_input,
        lifecycle_metadata=replace(
            pe35_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    superseded_pe36 = replace(
        pe37_input.pe36_boundary_input,
        pe35_boundary_input=superseded_pe35,
    )
    superseded_pe37 = replace(pe37_input, pe36_boundary_input=superseded_pe36)
    bad = replace(integration_input, pe37_traceability_boundary_input=superseded_pe37)
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_boundary_input:" in r for r in result["fail_reasons"])


def test_pe37_pe34_handoff_bound_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            pe34_handoff_bound=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: pe34_handoff_bound must be True" in r for r in result["fail_reasons"])


def test_pe37_pe35_staleness_bound_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            pe35_staleness_revocation_recovery_bound=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe37_proof: pe35_staleness_revocation_recovery_bound must be True" in r
        for r in result["fail_reasons"]
    )


def test_pe37_pe36_admission_presentation_bound_false_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            pe36_admission_presentation_bound=False,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe37_proof: pe36_admission_presentation_bound must be True" in r
        for r in result["fail_reasons"]
    )


def test_pe37_handoff_digest_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            pe34_handoff_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_proof: pe34_handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_admission_presentation_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        pe37_traceability_proof=replace(
            integration_input.pe37_traceability_proof,
            pe36_boundary_result_digest="1" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe37_proof: pe36_boundary_result_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_pe37_completion_proof_chain_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            completion_referenced_pe37_boundary_result_digest="0" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "completion_referenced_pe37_boundary_result_digest mismatch" in r
        for r in result["fail_reasons"]
    )


def test_pe37_traceability_proof_chain_identity_drift_fails() -> None:
    integration_input = default_minimal_completion_integration_input()
    bad = replace(
        integration_input,
        completion_proof_chain=replace(
            integration_input.completion_proof_chain,
            pe37_traceability_identity="2" * 64,
        ),
    )
    result = evaluate_durable_run_primary_evidence_completion_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe37_valid_proof_remains_non_authorizing() -> None:
    result = evaluate_durable_run_primary_evidence_completion_integration(
        default_minimal_completion_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["operative_run_completion_recorded"] is False
    assert result["primary_evidence_operationally_accepted"] is False
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
