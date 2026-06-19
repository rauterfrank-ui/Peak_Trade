"""Static + offline bounded Futures Testnet preflight execution readiness review lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, operator review, or Testnet start.
PE-38 static PE-26/PE-32/PE-37/PE-34/PE-35/PE-19/PE-20/PE-25/pilot-composition binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    default_minimal_pe35_proof_binding,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    CONTRACT_VERSION as PE37_CONTRACT_VERSION,
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CANONICAL_BLOCKER_STATE,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_BLOCKER_LIFT_EXECUTED,
    OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
    OPERATIVE_OPERATOR_DECISION_CREATED,
    OPERATIVE_OPERATOR_REVIEW_EXECUTED,
    OPERATIVE_READINESS_DECISION_CREATED,
    PREFLIGHT_REMAINS_BLOCKED,
    REVIEW_LIFECYCLE_MODE,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    ReviewLifecycleProofChainBinding,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_preflight_execution_readiness_review_lifecycle_integration,
    serialize_integration_input_canonical,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE32_CONTRACT_VERSION,
    PE39_BRIDGE_OWNER,
)

from tests.ops.pe38_coherent_fixture_patch_v0 import apply_pe38_coherent_fixture_patch

apply_pe38_coherent_fixture_patch()

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0.py"
)
PE26_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"
)
PE32_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0.py"
)
PE37_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0.py"
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
PE39_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge_contract_v0.py"
)
PE25_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py"
)

PILOT_READINESS_MODULE = REPO_ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def _valid_integration_input(
    source_revision: str = VALID_COMMIT_SHA,
):
    return default_minimal_integration_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )


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
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["private_readonly_authorized"] is False
    assert result["validate_only_authorized"] is False
    assert result["tiny_order_authorized"] is False
    assert result["reconciliation_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
    assert result["pilot_start_authorized"] is False
    assert result["promotion_authorized"] is False
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
    assert result["testnet_started"] is False
    assert result["runtime_started"] is False
    assert result["harness_started"] is False
    assert result["subprocess_started"] is False


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_upstream_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0"
        in (integration_text)
    )
    assert "bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0" in (
        integration_text
    )
    assert (
        "evaluate_pe39_admission_presentation_operator_closure_lifecycle_bridge" in integration_text
    )
    assert "pe39_bridge_integration_proof" in integration_text
    assert "pe40_readiness_decision_proof_chain" in integration_text
    assert (
        "bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0"
        in (integration_text)
    )
    assert "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0" in (
        integration_text
    )
    assert "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0" in (
        integration_text
    )
    assert "check_bounded_pilot_readiness" in integration_text
    assert "evaluate_operator_review(" not in integration_text
    assert "import subprocess" not in integration_text
    assert "open(" not in integration_text
    assert PE26_MODULE.exists()
    assert PE32_MODULE.exists()
    assert PE37_MODULE.exists()
    assert PE34_MODULE.exists()
    assert PE35_MODULE.exists()
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE25_MODULE.exists()
    assert PE39_MODULE.exists()
    assert PILOT_READINESS_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_PREFLIGHT_EXECUTION_READINESS_REVIEW_LIFECYCLE_READINESS is False
    assert OPERATIVE_READINESS_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_CLOSURE_EXECUTED is False
    assert OPERATIVE_OPERATOR_REVIEW_EXECUTED is False
    assert OPERATIVE_BLOCKER_LIFT_EXECUTED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False
    assert PREFLIGHT_REMAINS_BLOCKED is True


def test_happy_path_passes() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert (
        result[
            "preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review"
        ]
        is True
    )
    assert (
        result["pe38_preflight_execution_readiness_review_lifecycle_static_integration_proven"]
        is True
    )
    assert result["pe38_preflight_readiness_review_lifecycle_bound"] is True
    assert result["pe39_admission_presentation_operator_closure_bridge_bound"] is True
    assert result["pe40_readiness_decision_pe39_proof_chain_bound"] is True
    assert result["pe32_readiness_decision_lifecycle_bound"] is True
    assert result["admission_presentation_lifecycle_bound"] is True
    assert result["pe25_operator_closure_bound"] is True
    assert result["pe34_handoff_bound"] is True
    assert result["pe35_staleness_revocation_recovery_bound"] is True
    assert result["pe36_admission_presentation_bound"] is True
    assert result["pe37_durable_traceability_bound"] is True
    assert result["static_pe12_lifecycle_chain_complete"] is True
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        _valid_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    _assert_all_authorization_flags_false(result)


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = _valid_integration_input()
    right = _valid_integration_input()
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_preflight_execution_readiness_review_lifecycle_integration(left)
    right_result = evaluate_preflight_execution_readiness_review_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        preflight_execution_readiness_review_lifecycle_eligibility_for_separate_operator_review=True,
    )


def test_missing_pe26_assembly_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe26_assembly_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe26_assembly_digest required" in r for r in result["fail_reasons"])


def test_missing_pe32_integration_proof_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe32_integration_proof_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe32_integration_proof_digest required" in r for r in result["fail_reasons"])


def test_missing_pe37_traceability_identity_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe37_traceability_identity="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe37_traceability_identity required" in r for r in result["fail_reasons"])


def test_missing_pe19_review_input_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe19_review_input_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe19_review_input_digest required" in r for r in result["fail_reasons"])


def test_missing_pe20_review_input_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe20_review_input_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe20_review_input_digest required" in r for r in result["fail_reasons"])


def test_missing_pe34_handoff_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe34_handoff_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe34_handoff_digest required" in r for r in result["fail_reasons"])


def test_missing_pe35_boundary_result_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe35_boundary_result_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe35_boundary_result_digest required" in r for r in result["fail_reasons"])


def test_missing_pe25_closure_result_digest_fails() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(integration_input.proof_chain, pe25_closure_result_digest="")
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe25_closure_result_digest required" in r for r in result["fail_reasons"])


def test_empty_integration_id_fails() -> None:
    integration_input = _valid_integration_input()
    broken = replace(integration_input, integration_id="")
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("integration_id required" in r for r in result["fail_reasons"])


def test_empty_adapter_id_fails() -> None:
    integration_input = _valid_integration_input()
    broken = replace(integration_input, adapter_id="")
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("adapter_id required" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_source_revision=ALT_COMMIT_SHA,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_pe26_assembly_digest_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe26_assembly_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe26_assembly_digest mismatch" in r for r in result["fail_reasons"])


def test_pe32_integration_proof_digest_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe32_integration_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe32_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe37_traceability_identity_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe37_traceability_identity="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe37_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_pe34_handoff_digest_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe34_handoff_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe34_handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_pe25_closure_result_digest_mismatch_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe25_closure_result_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe25_closure_result_digest mismatch" in r for r in result["fail_reasons"])


def test_wrong_pe26_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe26_assembly_proof,
        assembly_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe26_assembly_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("assembly_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe32_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe32_readiness_proof,
        integration_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe32_readiness_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("integration_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe37_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe37_traceability_proof,
        traceability_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe37_traceability_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("traceability_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe34_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe34_handoff_proof,
        handoff_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe34_handoff_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("handoff_owner must be" in r for r in result["fail_reasons"])


def test_wrong_pe35_canonical_owner_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe35_staleness_proof,
        boundary_owner="wrong.owner.v0",
    )
    broken = replace(integration_input, pe35_staleness_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("boundary_owner must be" in r for r in result["fail_reasons"])


def test_wrong_proof_chain_order_fails_closed() -> None:
    integration_input = _valid_integration_input()
    chain = integration_input.proof_chain
    broken_chain = ReviewLifecycleProofChainBinding(
        pe39_bridge_proof_digest=chain.pe40_pe32_integration_proof_digest,
        pe39_admission_integration_proof_digest=chain.pe39_admission_integration_proof_digest,
        pe40_pe32_integration_proof_digest=chain.pe39_bridge_proof_digest,
        pe38_referenced_pe40_pe32_proof_digest=chain.pe38_referenced_pe40_pe32_proof_digest,
        pe26_assembly_digest=chain.pe32_integration_proof_digest,
        pe32_integration_proof_digest=chain.pe26_assembly_digest,
        pe37_boundary_result_digest=chain.pe37_boundary_result_digest,
        pe37_traceability_identity=chain.pe37_traceability_identity,
        pe19_review_input_digest=chain.pe19_review_input_digest,
        pe20_review_input_digest=chain.pe20_review_input_digest,
        pe34_handoff_digest=chain.pe34_handoff_digest,
        pe35_boundary_result_digest=chain.pe35_boundary_result_digest,
        pe25_closure_result_digest=chain.pe25_closure_result_digest,
        pilot_composition_pe32_proof_digest=chain.pilot_composition_pe32_proof_digest,
        pilot_composition_pe26_assembly_digest=chain.pilot_composition_pe26_assembly_digest,
    )
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe39_bridge_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_incomplete_proof_chain_fails_closed() -> None:
    integration_input = _valid_integration_input()
    broken_chain = replace(
        integration_input.proof_chain,
        pe35_boundary_result_digest="3" * 64,
    )
    broken = replace(integration_input, proof_chain=broken_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("pe35_boundary_result_digest mismatch" in r for r in result["fail_reasons"])


def test_blocker_state_not_blocked_fails() -> None:
    integration_input = _valid_integration_input()
    broken_proof = replace(
        integration_input.pe32_readiness_proof,
        blocker_state="lifted",
    )
    broken = replace(integration_input, pe32_readiness_proof=broken_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("blocker_state must be" in r for r in result["fail_reasons"])


def test_stale_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken_pe26 = replace(
        integration_input.pe26_assembly_input,
        pe37_traceability_boundary_input=broken_pe37,
    )
    broken = replace(
        integration_input,
        pe26_assembly_input=broken_pe26,
        pe37_traceability_boundary_input=broken_pe37,
        pe35_boundary_input=broken_pe35,
    )
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_revoked_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken_pe26 = replace(
        integration_input.pe26_assembly_input,
        pe37_traceability_boundary_input=broken_pe37,
    )
    broken = replace(
        integration_input,
        pe26_assembly_input=broken_pe26,
        pe37_traceability_boundary_input=broken_pe37,
        pe35_boundary_input=broken_pe35,
    )
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_superseded_handoff_fails() -> None:
    integration_input = _valid_integration_input()
    broken_pe35 = replace(
        integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        integration_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    broken_pe37 = replace(
        integration_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    broken_pe26 = replace(
        integration_input.pe26_assembly_input,
        pe37_traceability_boundary_input=broken_pe37,
    )
    broken = replace(
        integration_input,
        pe26_assembly_input=broken_pe26,
        pe37_traceability_boundary_input=broken_pe37,
        pe35_boundary_input=broken_pe35,
    )
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False


def test_replay_bound_traceability_identity_fails() -> None:
    integration_input = _valid_integration_input()
    baseline = evaluate_durable_evidence_traceability_boundary(
        integration_input.pe37_traceability_boundary_input
    )
    assert baseline["traceability_identity"] is not None
    broken = replace(
        integration_input,
        bound_traceability_identities=(baseline["traceability_identity"],),
    )
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("replay" in r for r in result["fail_reasons"])


def test_duplicate_admission_identity_fails() -> None:
    integration_input = _valid_integration_input()
    baseline = evaluate_durable_evidence_traceability_boundary(
        integration_input.pe37_traceability_boundary_input
    )
    assert baseline["admission_identity"] is not None
    broken = replace(
        integration_input,
        bound_admission_identities=(baseline["admission_identity"],),
    )
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(broken)
    assert result["integration_pass"] is False
    assert any("duplicate admission" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        extra_fields={"unexpected_field": "value"},
    )
    assert result["integration_pass"] is False
    assert any("unknown extra field" in r for r in result["fail_reasons"])


def test_secret_credential_command_authority_decision_fields_fail() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        extra_fields={
            "api_key": "secret-value",
            "operator_decision": True,
            "execution_authorized": True,
            "live_action": "run",
        },
    )
    assert result["integration_pass"] is False
    assert any("forbidden extra field" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        loose_boolean_eligibility=True,
    )
    assert result["integration_pass"] is False
    assert any("loose_boolean_eligibility" in r for r in result["fail_reasons"])


def test_loose_authority_booleans_rejected() -> None:
    integration_input = _valid_integration_input()
    for kwargs in (
        {"readiness_decision_authorized": True},
        {"operator_review_authorized": True},
        {"operator_decision_authorized": True},
        {"operator_closure_authorized": True},
        {"global_blocker_lift_authorized": True},
        {"preflight_lift_authorized": True},
        {"execution_authorized": True},
        {"live_authorized": True},
        {"pilot_start_authorized": True},
        {"promotion_authorized": True},
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"selected_decision": "approve"},
        {"default_approve": True},
        {"implicit_approve": True},
    ):
        result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
            integration_input, **kwargs
        )
        assert result["integration_pass"] is False


def test_inputs_not_mutated() -> None:
    integration_input = _valid_integration_input()
    before = serialize_integration_input_canonical(integration_input)
    evaluate_preflight_execution_readiness_review_lifecycle_integration(integration_input)
    after = serialize_integration_input_canonical(integration_input)
    assert before == after


def test_no_file_git_network_subprocess_usage_in_module_text() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "import subprocess" not in integration_text
    assert "import os" not in integration_text
    assert "open(" not in integration_text
    assert "git." not in integration_text
    assert "requests." not in integration_text
    assert "urllib" not in integration_text


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    assert integration_input.instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in integration_input.instrument
    assert "BTC" not in integration_input.instrument
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration.v0"
    )
    assert REVIEW_LIFECYCLE_MODE == (
        "static_preflight_execution_readiness_review_lifecycle_integration_proof_only"
    )
    assert CANONICAL_BLOCKER_STATE == "blocked"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.global_blocker_lift_authorized is False
    assert snapshot.operator_review_authorized is False
    assert snapshot.futures_only is True


def test_owner_constants_coherent() -> None:
    integration_input = _valid_integration_input()
    assert integration_input.pe26_assembly_proof.assembly_owner == PE26_CONTRACT_VERSION
    assert integration_input.pe32_readiness_proof.integration_owner == PE32_CONTRACT_VERSION
    assert integration_input.pe37_traceability_proof.traceability_owner == PE37_CONTRACT_VERSION
    assert integration_input.pe34_handoff_proof.handoff_owner == PE34_CONTRACT_VERSION
    assert integration_input.pe19_pe20_review_proof.review_input_owner == PE19_CONTRACT_VERSION
    assert integration_input.pe19_pe20_review_proof.package_owner == PE20_CONTRACT_VERSION
    assert integration_input.pe25_closure_proof.closure_owner == PE25_CONTRACT_VERSION


def test_input_mutation_changes_digest() -> None:
    left = _valid_integration_input()
    right = replace(left, integration_id="mutated-integration-id")
    assert compute_integration_input_digest(left) != compute_integration_input_digest(right)
    left_result = evaluate_preflight_execution_readiness_review_lifecycle_integration(left)
    right_result = evaluate_preflight_execution_readiness_review_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] != right_result["integration_proof_digest"]


def test_no_filesystem_git_network_subprocess_at_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in PE-38 tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        _valid_integration_input()
    )
    assert result["integration_pass"] is True


def test_missing_pe39_bridge_proof_digest_fails() -> None:
    integration_input = _valid_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        bridge_proof_digest="",
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bridge_proof_digest required" in r for r in result["fail_reasons"])


def test_missing_pe40_readiness_decision_proof_chain_slot_fails() -> None:
    integration_input = _valid_integration_input()
    bad_chain = replace(
        integration_input.pe40_readiness_decision_proof_chain,
        pe39_bridge_proof_digest="",
    )
    bad = replace(integration_input, pe40_readiness_decision_proof_chain=bad_chain)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe39_bridge_proof_digest required" in r for r in result["fail_reasons"])


def test_pe38_references_wrong_pe40_proof_fails() -> None:
    integration_input = _valid_integration_input()
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(
        integration_input,
        expected_pe40_pe32_integration_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe40_pe32_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe39_owner_identity_drift_fails() -> None:
    integration_input = _valid_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        bridge_owner="wrong.owner.v0",
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bridge_owner must be" in r for r in result["fail_reasons"])


def test_missing_admission_presentation_lifecycle_binding_fails() -> None:
    integration_input = _valid_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        admission_presentation_lifecycle_bound=False,
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_preflight_execution_readiness_review_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "admission_presentation_lifecycle_bound must be True" in r for r in result["fail_reasons"]
    )


def test_pe39_canonical_owner_matches_expected() -> None:
    assert PE39_BRIDGE_OWNER == (
        "bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge.v0"
    )
