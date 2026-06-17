"""Static + offline bounded Futures Testnet durable evidence traceability boundary (v0).

Docs/tests-only. No runtime, network, credentials, operator review, archive writes, or Testnet start.
PE-37 traceability guard over PE-36-validated admission/presentation boundary only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    HANDOFF_STATE_STALE,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE36_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE36_CONTRACT_VERSION,
    default_minimal_pe35_proof_binding,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    ADMISSION_EXECUTED,
    ARCHIVE_WRITTEN,
    AUTHORITY_LIFT,
    BOUNDARY_OWNER,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    MANIFEST_WRITTEN,
    OPERATOR_REVIEW_EXECUTED,
    Pe16ArchiveManifestBinding,
    Pe19Pe20OperatorReviewProofBinding,
    Pe33Pe36ProofChainBinding,
    Pe36BoundaryProofBinding,
    REPLAY_EXECUTED,
    SECOND_ARCHIVE_SURFACE_CREATED,
    SECOND_EVIDENCE_SURFACE_CREATED,
    SECOND_MANIFEST_SURFACE_CREATED,
    DurableEvidenceTraceabilityBoundaryInput,
    compute_admission_identity,
    compute_boundary_input_digest,
    compute_boundary_result_digest,
    compute_operator_review_proof_identity,
    compute_traceability_identity,
    default_minimal_boundary_input,
    default_minimal_pe16_archive_binding,
    default_minimal_pe19_pe20_review_proof_binding,
    default_minimal_pe36_proof_binding,
    default_minimal_proof_chain_binding,
    evaluate_durable_evidence_traceability_boundary,
    serialize_boundary_input_canonical,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    EXPECTED_OPERATOR_NAME,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py"
)
PE16_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
PE19_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0.py"
)
PE20_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0.py"
)
PE33_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0.py"
)
PE34_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py"
)
PE35_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py"
)
PE36_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_CHAIN_DURABLE_EVIDENCE_TRACEABILITY_BOUNDARY_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_CHAIN_DURABLE_EVIDENCE_TRACEABILITY_BOUNDARY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
REVIEW_IDENTITY = "glb-016-bounded-futures-testnet-operator-review"


def _assert_all_authorization_flags_false(result: dict[str, object]) -> None:
    assert result["preflight_remains_blocked"] is True
    assert result["global_blocker_lift_authorized"] is False
    assert result["preflight_lift_authorized"] is False
    assert result["ready_for_operator_arming"] is False
    assert result["readiness_decision_authorized"] is False
    assert result["operator_review_authorized"] is False
    assert result["operator_decision_authorized"] is False
    assert result["operator_closure_authorized"] is False
    assert result["execution_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["live_authorized"] is False
    assert result["network_used"] is False
    assert result["credentials_used"] is False
    assert result["exchange_api_called"] is False
    assert result["exchange_request_count"] == 0
    assert result["orders_created"] == 0
    assert result["orders_cancelled"] == 0
    assert result["orders_amended"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["testnet_started"] is False
    assert result["runtime_started"] is False
    assert result["harness_started"] is False
    assert result["subprocess_started"] is False


def _valid_boundary_input(
    source_revision: str = VALID_COMMIT_SHA,
) -> DurableEvidenceTraceabilityBoundaryInput:
    return default_minimal_boundary_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
        review_identity=REVIEW_IDENTITY,
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_CHAIN_DURABLE_EVIDENCE_TRACEABILITY_BOUNDARY_CONTRACT_V0=true"
        in BOUNDARY_MODULE.read_text(encoding="utf-8")
    )


def test_pe16_pe19_pe20_pe33_pe34_pe35_pe36_owners_referenced_not_duplicated() -> None:
    boundary_text = BOUNDARY_MODULE.read_text(encoding="utf-8")
    assert "compute_archive_identity" in boundary_text
    assert "evaluate_operator_review_admission_presentation_boundary" in boundary_text
    assert "evaluate_operator_review(" not in boundary_text
    assert "persist_operator_review_proof_package" not in boundary_text
    assert "import subprocess" not in boundary_text
    assert "ARCHIVE_WRITTEN = False" in boundary_text
    assert "REPLAY_EXECUTED = False" in boundary_text
    assert PE16_MODULE.exists()
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE33_MODULE.exists()
    assert PE34_MODULE.exists()
    assert PE35_MODULE.exists()
    assert PE36_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert SECOND_EVIDENCE_SURFACE_CREATED is False
    assert SECOND_ARCHIVE_SURFACE_CREATED is False
    assert SECOND_MANIFEST_SURFACE_CREATED is False
    assert ARCHIVE_WRITTEN is False
    assert MANIFEST_WRITTEN is False
    assert REPLAY_EXECUTED is False
    assert ADMISSION_EXECUTED is False
    assert OPERATOR_REVIEW_EXECUTED is False
    assert AUTHORITY_LIFT is False


def test_happy_path_coherent_proof_archive_manifest_chain() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_durable_evidence_traceability_boundary(boundary_input)
    assert result["boundary_pass"] is True
    assert result["durable_evidence_traceability_boundary_satisfied"] is True
    assert result["traceability_identity"] is not None
    assert result["admission_identity"] is not None
    assert result["secret_fields_present"] is False
    assert result["decision_preselected"] is False
    assert result["archive_written"] is False
    assert result["manifest_written"] is False
    assert result["replay_executed"] is False
    assert result["admission_executed"] is False
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_missing_pe33_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(
        boundary_input.proof_chain,
        pe33_integration_proof_digest="",
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_missing_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(boundary_input.proof_chain, pe34_handoff_digest="")
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_missing_pe35_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(
        boundary_input.proof_chain,
        pe35_boundary_input_digest="",
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_missing_pe36_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(
        boundary_input.proof_chain,
        pe36_boundary_result_digest="",
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_proof_digest_drift_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(
        boundary_input.proof_chain,
        pe33_integration_proof_digest="0" * 64,
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("PE-33" in r or "pe33" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_archive = replace(
        boundary_input.pe16_archive_binding,
        source_revision=ALT_COMMIT_SHA,
    )
    broken = replace(boundary_input, pe16_archive_binding=broken_archive)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_archive_identity_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_archive = replace(
        boundary_input.pe16_archive_binding,
        archive_identity="1" * 64,
    )
    broken = replace(boundary_input, pe16_archive_binding=broken_archive)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("archive_identity" in r for r in result["fail_reasons"])


def test_manifest_identity_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_archive = replace(
        boundary_input.pe16_archive_binding,
        archive_manifest_digest="2" * 64,
    )
    broken = replace(boundary_input, pe16_archive_binding=broken_archive)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("archive_manifest_digest" in r for r in result["fail_reasons"])


def test_wrong_canonical_owner_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe36_proof,
        boundary_owner="wrong.owner.alias.v0",
    )
    broken = replace(boundary_input, pe36_proof=broken_proof)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("boundary_owner" in r for r in result["fail_reasons"])


def test_wrong_proof_chain_order_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    chain = boundary_input.proof_chain
    broken_chain = Pe33Pe36ProofChainBinding(
        pe33_integration_proof_digest=chain.pe34_handoff_digest,
        pe34_handoff_digest=chain.pe33_integration_proof_digest,
        pe35_boundary_input_digest=chain.pe35_boundary_input_digest,
        pe35_boundary_result_digest=chain.pe35_boundary_result_digest,
        pe36_boundary_input_digest=chain.pe36_boundary_input_digest,
        pe36_boundary_result_digest=chain.pe36_boundary_result_digest,
        pe36_presentation_projection_digest=chain.pe36_presentation_projection_digest,
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_incomplete_proof_chain_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_chain = replace(
        boundary_input.proof_chain,
        pe35_boundary_result_digest="3" * 64,
    )
    broken = replace(boundary_input, proof_chain=broken_chain)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False


def test_duplicate_admission_identity_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    baseline = evaluate_durable_evidence_traceability_boundary(boundary_input)
    assert baseline["admission_identity"] is not None
    broken = replace(
        boundary_input,
        bound_admission_identities=(baseline["admission_identity"],),
    )
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("duplicate admission" in r for r in result["fail_reasons"])


def test_replay_bound_traceability_identity_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    baseline = evaluate_durable_evidence_traceability_boundary(boundary_input)
    assert baseline["traceability_identity"] is not None
    broken = replace(
        boundary_input,
        bound_traceability_identities=(baseline["traceability_identity"],),
    )
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("replay" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_durable_evidence_traceability_boundary(
        boundary_input,
        extra_traceability_fields=("unexpected_field",),
    )
    assert result["boundary_pass"] is False


def test_secret_credential_command_action_fields_fail_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_durable_evidence_traceability_boundary(
        boundary_input,
        injected_traceability_overrides={"api_key": "secret-value"},
    )
    assert result["boundary_pass"] is False
    assert any("forbidden" in r for r in result["fail_reasons"])


def test_decision_preselection_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_durable_evidence_traceability_boundary(
        boundary_input,
        selected_decision="approve",
        default_approve=True,
        implicit_approve=True,
    )
    assert result["boundary_pass"] is False
    assert result["decision_preselected"] is False


def test_deterministic_output_identical_inputs() -> None:
    first = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    second = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    assert compute_boundary_input_digest(first) == compute_boundary_input_digest(second)
    first_result = evaluate_durable_evidence_traceability_boundary(first)
    second_result = evaluate_durable_evidence_traceability_boundary(second)
    assert first_result["traceability_identity"] == second_result["traceability_identity"]
    assert first_result["boundary_result_digest"] == second_result["boundary_result_digest"]


def test_inputs_not_mutated() -> None:
    boundary_input = _valid_boundary_input()
    before = serialize_boundary_input_canonical(boundary_input)
    evaluate_durable_evidence_traceability_boundary(boundary_input)
    after = serialize_boundary_input_canonical(boundary_input)
    assert before == after


def test_no_file_archive_environment_git_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in PE-37 tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    result = evaluate_durable_evidence_traceability_boundary(_valid_boundary_input())
    assert result["durable_evidence_traceability_boundary_satisfied"] is True


def test_negative_pe36_state_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe36_boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            boundary_input.pe36_boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe36_proof = Pe36BoundaryProofBinding(
        boundary_owner=broken_pe36.pe35_proof.boundary_owner,
        source_revision=broken_pe36.pe35_boundary_input.pe34_handoff.source_revision,
        boundary_input_digest=broken_pe36.pe35_proof.boundary_input_digest,
        boundary_result_digest=None,
        presentation_projection_digest=None,
        operator_review_admission_presentation_boundary_satisfied=False,
    )
    broken = replace(
        boundary_input,
        pe36_boundary_input=broken_pe36,
        pe36_proof=broken_pe36_proof,
        pe16_archive_binding=default_minimal_pe16_archive_binding(broken_pe36),
        pe19_pe20_review_proof=default_minimal_pe19_pe20_review_proof_binding(broken_pe36),
    )
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["durable_evidence_traceability_boundary_satisfied"] is False


def test_pe36_owner_constants_coherent() -> None:
    boundary_input = _valid_boundary_input()
    assert boundary_input.pe36_proof.boundary_owner == PE36_BOUNDARY_OWNER
    assert PE36_BOUNDARY_OWNER == PE36_CONTRACT_VERSION
    assert BOUNDARY_OWNER == CONTRACT_VERSION


def test_pe16_pe19_pe20_owner_bindings_coherent() -> None:
    boundary_input = _valid_boundary_input()
    assert boundary_input.pe16_archive_binding.archive_owner == ARCHIVE_CONTRACT_VERSION
    assert boundary_input.pe19_pe20_review_proof.review_input_owner == PE19_CONTRACT_VERSION
    assert boundary_input.pe19_pe20_review_proof.package_owner == PE20_CONTRACT_VERSION


def test_operator_review_proof_identity_deterministic() -> None:
    binding = _valid_boundary_input().pe19_pe20_review_proof
    first = compute_operator_review_proof_identity(
        review_input_owner=binding.review_input_owner,
        package_owner=binding.package_owner,
        source_revision=binding.source_revision,
        review_input_digest=binding.review_input_digest,
        package_binding_digest=binding.package_binding_digest,
    )
    second = compute_operator_review_proof_identity(
        review_input_owner=binding.review_input_owner,
        package_owner=binding.package_owner,
        source_revision=binding.source_revision,
        review_input_digest=binding.review_input_digest,
        package_binding_digest=binding.package_binding_digest,
    )
    assert first == second
    assert first == binding.operator_review_proof_identity


def test_traceability_identity_and_admission_identity_coherent() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_durable_evidence_traceability_boundary(boundary_input)
    assert result["traceability_identity"] is not None
    assert result["admission_identity"] is not None
    expected_traceability = compute_traceability_identity(
        source_revision=VALID_COMMIT_SHA,
        proof_chain=boundary_input.proof_chain,
        archive_identity=boundary_input.pe16_archive_binding.archive_identity,
        archive_manifest_digest=boundary_input.pe16_archive_binding.archive_manifest_digest,
        operator_review_proof_identity=boundary_input.pe19_pe20_review_proof.operator_review_proof_identity,
    )
    assert result["traceability_identity"] == expected_traceability
    expected_admission = compute_admission_identity(
        pe36_boundary_result_digest=boundary_input.proof_chain.pe36_boundary_result_digest,
        presentation_projection_digest=boundary_input.proof_chain.pe36_presentation_projection_digest,
    )
    assert result["admission_identity"] == expected_admission


def test_boundary_result_digest_only_when_satisfied() -> None:
    valid = _valid_boundary_input()
    valid_result = evaluate_durable_evidence_traceability_boundary(valid)
    assert valid_result["boundary_result_digest"] is not None
    assert valid_result["traceability_identity"] is not None
    assert valid_result["boundary_result_digest"] == compute_boundary_result_digest(
        valid,
        durable_evidence_traceability_boundary_satisfied=True,
        traceability_identity=valid_result["traceability_identity"],
    )

    broken_pe36_proof = replace(
        valid.pe36_proof,
        boundary_result_digest="f" * 64,
    )
    broken = replace(valid, pe36_proof=broken_pe36_proof)
    broken_result = evaluate_durable_evidence_traceability_boundary(broken)
    assert broken_result["boundary_result_digest"] is None


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    boundary_input = default_minimal_boundary_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    instrument = boundary_input.pe36_boundary_input.pe35_boundary_input.pe34_handoff.instrument
    assert instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in instrument
    assert "BTC" not in instrument
    result = evaluate_durable_evidence_traceability_boundary(boundary_input)
    assert result["durable_evidence_traceability_boundary_satisfied"] is True


def test_wrong_pe19_pe20_review_proof_identity_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_review = replace(
        boundary_input.pe19_pe20_review_proof,
        operator_review_proof_identity="9" * 64,
    )
    broken = replace(boundary_input, pe19_pe20_review_proof=broken_review)
    result = evaluate_durable_evidence_traceability_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("operator_review_proof_identity" in r for r in result["fail_reasons"])
