"""Static + offline bounded Futures Testnet reconciliation-review lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, reconciliation execution, or Testnet start.
PE-31 static PE-26..PE-30 chain + PE-21 reconciliation/primary-evidence binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    PHASE_PRIVATE_READONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    CONTRACT_VERSION as PE21_CONTRACT_VERSION,
    PrimaryEvidenceBindingInput,
    default_minimal_integration_input as default_minimal_pe21_integration_input,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    default_minimal_assembly_input,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EXCHANGE_API_CALLED,
    GLOBAL_RECONCILIATION_REVIEW_LIFECYCLE_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_ADAPTER_CALLED,
    OPERATIVE_RECONCILIATION_EXECUTED,
    PE21_INTEGRATION_OWNER,
    PE26_ASSEMBLY_OWNER,
    PE27_INTEGRATION_OWNER,
    PE28_INTEGRATION_OWNER,
    PE29_INTEGRATION_OWNER,
    PE30_INTEGRATION_OWNER,
    RECONCILIATION_REVIEW_MODE,
    RECONCILIATION_REVIEW_OWNER,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    Pe21ReconciliationPrimaryEvidenceIntegrationProofBinding,
    Pe30TinyOrderIntegrationProofBinding,
    ReconciliationReviewProofBinding,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_reconciliation_review_proof_digest,
    default_minimal_integration_input,
    default_minimal_pe21_integration_proof,
    default_minimal_pe30_integration_proof,
    default_minimal_reconciliation_review_proof,
    default_minimal_safety_snapshot,
    evaluate_reconciliation_review_lifecycle_integration,
    serialize_integration_input_canonical,
    serialize_reconciliation_review_proof_canonical,
)
from src.ops.bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE30_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_pe30_integration_input,
)
from src.ops.bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE29_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE27_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    PRIMARY_EVIDENCE_OWNER,
    RECONCILIATION_OWNER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
)
PE26_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"
)
PE27_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0.py"
)
PE28_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0.py"
)
PE29_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0.py"
)
PE30_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0.py"
)
PE21_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"
)
RECONCILE_MODULE = REPO_ROOT / "src" / "ops" / "recon" / "reconcile.py"
PRIMARY_EVIDENCE_MODULE = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_RECONCILIATION_REVIEW_LIFECYCLE_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_RECONCILIATION_REVIEW_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
DURABLE_ARCHIVE_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_RECONCILIATION_REVIEW_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_pe26_pe27_pe28_pe29_pe30_pe21_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert (
        "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0" in integration_text
    )
    assert (
        "bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_validate_only_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_tiny_order_lifecycle_integration_contract_v0" in integration_text
    )
    assert (
        "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0"
        in integration_text
    )
    assert "evaluate_phase_transition" not in integration_text
    assert "KrakenTestnetClient" not in integration_text
    assert "import subprocess" not in integration_text
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE26_MODULE.exists()
    assert PE27_MODULE.exists()
    assert PE28_MODULE.exists()
    assert PE29_MODULE.exists()
    assert PE30_MODULE.exists()
    assert PE21_MODULE.exists()
    assert RECONCILE_MODULE.exists()
    assert PRIMARY_EVIDENCE_MODULE.exists()
    assert RECONCILIATION_OWNER == "src/ops/recon/reconcile.py"
    assert PRIMARY_EVIDENCE_OWNER == "scripts/ops/primary_evidence_retention_v0.py"


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_RECONCILIATION_REVIEW_LIFECYCLE_READINESS is False
    assert OPERATIVE_RECONCILIATION_EXECUTED is False
    assert OPERATIVE_ADAPTER_CALLED is False
    assert EXCHANGE_API_CALLED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False


def test_valid_full_chain_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_reconciliation_review_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert (
        result["reconciliation_review_lifecycle_eligibility_for_separate_operator_review"] is True
    )
    assert result["pe31_reconciliation_review_lifecycle_static_integration_proven"] is True
    assert result["pe12_reconciliation_review_static_integration_proven"] is True
    assert result["durable_primary_evidence_binding_proven"] is True
    assert result["assigned_lifecycle_phase"] == PHASE_RECONCILIATION_REVIEW
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_reconciliation_review_lifecycle_integration(
        default_minimal_integration_input()
    )
    assert result["integration_pass"] is True
    assert (
        result["reconciliation_review_lifecycle_eligibility_for_separate_operator_review"] is True
    )
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["private_readonly_authorized"] is False
    assert result["validate_only_authorized"] is False
    assert result["tiny_order_authorized"] is False
    assert result["reconciliation_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
    assert result["network_allowed"] is False
    assert result["credentials_allowed"] is False
    assert result["orders_allowed"] is False
    assert result["scheduler_runtime_allowed"] is False
    assert result["network_used"] is False
    assert result["credentials_used"] is False
    assert result["secret_material_read"] is False
    assert result["secret_material_stored"] is False
    assert result["exchange_request_count"] == 0
    assert result["orders_created"] == 0
    assert result["orders_cancelled"] == 0
    assert result["orders_amended"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["account_state_queried"] is False
    assert result["global_reconciliation_review_lifecycle_readiness"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["runtime_started"] is False
    assert result["harness_started"] is False
    assert result["subprocess_started"] is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_reconciliation_review_lifecycle_integration(left)
    right_result = evaluate_reconciliation_review_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        reconciliation_review_lifecycle_eligibility_for_separate_operator_review=True,
    )


def test_reconciliation_review_proof_digest_stability() -> None:
    pe21_input = default_minimal_pe21_integration_input()
    left = default_minimal_reconciliation_review_proof(pe21_input)
    right = default_minimal_reconciliation_review_proof(pe21_input)
    assert serialize_reconciliation_review_proof_canonical(left) == (
        serialize_reconciliation_review_proof_canonical(right)
    )
    assert compute_reconciliation_review_proof_digest(left) == (
        compute_reconciliation_review_proof_digest(right)
    )


def test_lifecycle_phase_not_reconciliation_review_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase=PHASE_TINY_ORDER,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_skipped_lifecycle_sequence_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(
        integration_input.lifecycle_state_before,
        assigned_lifecycle_phase=PHASE_VALIDATE_ONLY,
    )
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_before" in r for r in result["fail_reasons"])


def test_missing_pe30_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe30_tiny_order_integration_proof,
        integration_proof_digest="",
    )
    bad = replace(integration_input, pe30_tiny_order_integration_proof=bad_proof)
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest required" in r for r in result["fail_reasons"])


def test_negative_pe30_integration_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe30_tiny_order_integration_proof,
        pe30_integration_pass=False,
        tiny_order_lifecycle_eligibility=False,
    )
    bad = replace(integration_input, pe30_tiny_order_integration_proof=bad_proof)
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe30_integration_pass must be true" in r for r in result["fail_reasons"])


def test_wrong_pe30_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe30_tiny_order_integration_proof,
        integration_proof_digest="0" * 64,
    )
    bad = replace(integration_input, pe30_tiny_order_integration_proof=bad_proof)
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_incomplete_pe26_assembly_via_pe30_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_assembly = replace(
        integration_input.pe30_tiny_order_integration_input.pe26_assembly_input.pe17_completeness_truth_proof,
        internal_static_chain_complete=False,
    )
    bad_pe26 = replace(
        integration_input.pe30_tiny_order_integration_input.pe26_assembly_input,
        pe17_completeness_truth_proof=bad_assembly,
    )
    bad_pe30 = replace(
        integration_input.pe30_tiny_order_integration_input,
        pe26_assembly_input=bad_pe26,
    )
    bad_pe30_proof = default_minimal_pe30_integration_proof(bad_pe30)
    bad = replace(
        integration_input,
        pe30_tiny_order_integration_input=bad_pe30,
        pe30_tiny_order_integration_proof=bad_pe30_proof,
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("PE-30 evaluation failed" in r for r in result["fail_reasons"])


def test_missing_pe21_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_proof,
        integration_proof_digest="",
    )
    bad = replace(
        integration_input, pe21_reconciliation_primary_evidence_integration_proof=bad_proof
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest required" in r for r in result["fail_reasons"])


def test_negative_pe21_integration_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_proof,
        pe21_integration_pass=False,
        reconciled=False,
        durable_primary_evidence_binding_proven=False,
    )
    bad = replace(
        integration_input, pe21_reconciliation_primary_evidence_integration_proof=bad_proof
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe21_integration_pass must be true" in r for r in result["fail_reasons"])


def test_wrong_pe21_owner_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_proof,
        integration_owner="wrong.owner",
    )
    bad = replace(
        integration_input, pe21_reconciliation_primary_evidence_integration_proof=bad_proof
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe21_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_proof,
        integration_proof_digest="0" * 64,
    )
    bad = replace(
        integration_input, pe21_reconciliation_primary_evidence_integration_proof=bad_proof
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_reconciliation_result_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_proof,
        reconciliation_result_digest="0" * 64,
    )
    bad = replace(
        integration_input, pe21_reconciliation_primary_evidence_integration_proof=bad_proof
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("reconciliation_result_digest mismatch" in r for r in result["fail_reasons"])


def test_manifest_verify_rc_nonzero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_review = _review_proof_with(manifest_verify_rc=1)
    bad_pe21_input = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_input,
        primary_evidence_binding=replace(
            integration_input.pe21_reconciliation_primary_evidence_integration_input.primary_evidence_binding,
            manifest_verify_rc=1,
        ),
    )
    bad = replace(
        integration_input,
        pe21_reconciliation_primary_evidence_integration_input=bad_pe21_input,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            bad_pe21_input
        ),
        reconciliation_review_proof=bad_review,
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_verify_rc" in r for r in result["fail_reasons"])


def test_tmp_only_evidence_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe21_input = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_input,
        primary_evidence_binding=replace(
            integration_input.pe21_reconciliation_primary_evidence_integration_input.primary_evidence_binding,
            durable_archive_root="/tmp/evidence",
        ),
    )
    bad = replace(
        integration_input,
        pe21_reconciliation_primary_evidence_integration_input=bad_pe21_input,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            bad_pe21_input
        ),
        reconciliation_review_proof=default_minimal_reconciliation_review_proof(bad_pe21_input),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("/tmp" in r for r in result["fail_reasons"])


def test_missing_primary_evidence_artifacts_fails() -> None:
    integration_input = default_minimal_integration_input()
    pe21_input = integration_input.pe21_reconciliation_primary_evidence_integration_input
    bad_binding = replace(
        pe21_input.primary_evidence_binding,
        expected_artifact_filenames=("POSITION_STATE_SNAPSHOT.json",),
    )
    bad_pe21_input = replace(pe21_input, primary_evidence_binding=bad_binding)
    bad = replace(
        integration_input,
        pe21_reconciliation_primary_evidence_integration_input=bad_pe21_input,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            bad_pe21_input
        ),
        reconciliation_review_proof=default_minimal_reconciliation_review_proof(bad_pe21_input),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("missing required artifact" in r for r in result["fail_reasons"])


def test_wrong_source_revision_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input,
        expected_source_revision="0" * 40,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_dirty_source_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input,
        dirty_source_state=True,
    )
    assert result["integration_pass"] is False
    assert any("dirty_source_state=true is not allowed" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input,
        loose_boolean_eligibility=True,
    )
    assert result["integration_pass"] is False
    assert any("loose_boolean_eligibility" in r for r in result["fail_reasons"])


def test_loose_authority_booleans_rejected() -> None:
    integration_input = default_minimal_integration_input()
    for kwargs in (
        {"execution_authorized": True},
        {"live_authorized": True},
        {"zero_order_authorized": True},
        {"private_readonly_authorized": True},
        {"validate_only_authorized": True},
        {"tiny_order_authorized": True},
        {"reconciliation_authorized": True},
        {"evidence_acceptance_authorized": True},
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"exchange_api_called_override": True},
        {"account_state_queried_override": True},
        {"new_evidence_generation": True},
        {"existing_evidence_mutation": True},
    ):
        result = evaluate_reconciliation_review_lifecycle_integration(integration_input, **kwargs)
        assert result["integration_pass"] is False
        assert (
            result["reconciliation_review_lifecycle_eligibility_for_separate_operator_review"]
            is False
        )


def test_unknown_lifecycle_state_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input,
        unknown_lifecycle_state="not_a_real_phase",
    )
    assert result["integration_pass"] is False
    assert any("unknown lifecycle state" in r for r in result["fail_reasons"])


def test_network_used_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        reconciliation_review_proof=_review_proof_with(network_used=True),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_used must be false" in r for r in result["fail_reasons"])


def test_orders_created_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        reconciliation_review_proof=_review_proof_with(orders_created=1),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_created must be 0" in r for r in result["fail_reasons"])


def test_positions_changed_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        reconciliation_review_proof=_review_proof_with(positions_changed=1),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("positions_changed must be 0" in r for r in result["fail_reasons"])


def test_evidence_created_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        reconciliation_review_proof=_review_proof_with(evidence_created=True),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("evidence_created must be false" in r for r in result["fail_reasons"])


def test_evidence_mutated_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        reconciliation_review_proof=_review_proof_with(evidence_mutated=True),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("evidence_mutated must be false" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_reconciliation_review_owner_matches_pe12_canonical_owner() -> None:
    assert RECONCILIATION_REVIEW_OWNER == PHASE_CANONICAL_OWNERS[PHASE_RECONCILIATION_REVIEW]
    assert PE26_ASSEMBLY_OWNER == PE26_CONTRACT_VERSION
    assert PE27_INTEGRATION_OWNER == PE27_CONTRACT_VERSION
    assert PE28_INTEGRATION_OWNER == PE28_CONTRACT_VERSION
    assert PE29_INTEGRATION_OWNER == PE29_CONTRACT_VERSION
    assert PE30_INTEGRATION_OWNER == PE30_CONTRACT_VERSION
    assert PE21_INTEGRATION_OWNER == PE21_CONTRACT_VERSION


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_reconciliation_review_lifecycle_integration.v0"
    )
    assert RECONCILIATION_REVIEW_MODE == "static_review_consistency_proof_only"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.execution_authorized is False
    assert snapshot.reconciliation_authorized is False
    assert snapshot.evidence_acceptance_authorized is False
    assert snapshot.futures_only is True
    assert snapshot.bitcoin_direction_allowed is False


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_reconciliation_review_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_btc_placeholder_instrument_rejected() -> None:
    assembly = default_minimal_assembly_input(instrument="PF_XBTUSD")
    integration_input = default_minimal_integration_input(instrument="PF_XBTUSD")
    bad_pe30 = replace(
        integration_input.pe30_tiny_order_integration_input,
        pe26_assembly_input=assembly,
        instrument="PF_XBTUSD",
    )
    bad = replace(
        integration_input,
        instrument="PF_XBTUSD",
        pe30_tiny_order_integration_input=bad_pe30,
        pe30_tiny_order_integration_proof=default_minimal_pe30_integration_proof(bad_pe30),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("forbidden orientation" in r for r in result["fail_reasons"])


def test_pe30_pe21_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    bad_pe21 = replace(
        integration_input.pe21_reconciliation_primary_evidence_integration_input,
        source_revision="0" * 40,
    )
    bad = replace(
        integration_input,
        pe21_reconciliation_primary_evidence_integration_input=bad_pe21,
        pe21_reconciliation_primary_evidence_integration_proof=default_minimal_pe21_integration_proof(
            bad_pe21
        ),
        reconciliation_review_proof=default_minimal_reconciliation_review_proof(bad_pe21),
    )
    result = evaluate_reconciliation_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_embedded_lifecycle_phases_are_canonical() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    pe30 = integration_input.pe30_tiny_order_integration_input
    assert (
        pe30.pe27_zero_order_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == (PHASE_ZERO_ORDER)
    )
    assert (
        pe30.pe28_private_readonly_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_PRIVATE_READONLY
    )
    assert (
        pe30.pe29_validate_only_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == (PHASE_VALIDATE_ONLY)
    )
    assert pe30.lifecycle_matrix_proof.assigned_lifecycle_phase == PHASE_TINY_ORDER
    assert (
        integration_input.pe21_reconciliation_primary_evidence_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_RECONCILIATION_REVIEW
    )


def _review_proof_with(**overrides: object) -> ReconciliationReviewProofBinding:
    pe21_input = default_minimal_pe21_integration_input()
    base = default_minimal_reconciliation_review_proof(pe21_input)
    mutated = replace(base, **overrides)
    return replace(
        mutated,
        reconciliation_review_proof_digest=compute_reconciliation_review_proof_digest(mutated),
    )
