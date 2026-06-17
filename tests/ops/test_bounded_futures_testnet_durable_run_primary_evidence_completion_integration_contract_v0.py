"""Static + offline bounded Futures Testnet durable run primary evidence completion (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
PE-21 + PE-16 + Gap-4 + Gap-2a.1 durable run-root completion static integration only.
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
    PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED,
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
    compute_run_identity_digest,
    default_minimal_completion_integration_input,
    default_minimal_safety_snapshot,
    evaluate_durable_run_primary_evidence_completion_integration,
    serialize_completion_integration_input_canonical,
    validate_durable_run_primary_evidence_completion_integration_input,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    ManifestEntry,
    PACKAGE_MARKER as PE21_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import FOLLOWUP_RUN_GATE

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
    assert "bounded_futures_testnet_preflight_packet_archive_contract_v0" in integration_text
    assert "scripts.ops.primary_evidence_retention_v0" in integration_text
    assert PE21_PACKAGE_MARKER in PE21_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in PE16_MODULE.read_text(encoding="utf-8")
    assert PE21_MODULE.exists()
    assert PE16_MODULE.exists()
    assert PRIMARY_EVIDENCE_MODULE.exists()
    assert GAP4_TEST_OWNER.exists()
    assert GAP2A1_TEST_OWNER.exists()
    assert PE16_ARCHIVE_OWNER == str(PE16_MODULE.relative_to(REPO_ROOT))
    assert GAP4_COMPLETION_OWNER == str(GAP4_TEST_OWNER.relative_to(REPO_ROOT))
    assert GAP2A1_ENFORCEMENT_OWNER == str(GAP2A1_TEST_OWNER.relative_to(REPO_ROOT))


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_RUN_COMPLETION_RECORDED is False
    assert PRIMARY_EVIDENCE_OPERATIONALLY_ACCEPTED is False
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
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_durable_run_primary_evidence_completion_integration(
        default_minimal_completion_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["operative_run_completion_recorded"] is False
    assert result["primary_evidence_operationally_accepted"] is False
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
    integration_input = default_minimal_completion_integration_input(source_revision="")
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
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
