"""Static + offline bounded Futures Testnet preflight execution readiness assembly (v0).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
PE-26 static PE-12..PE-25 preflight execution readiness assembly proof composition only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0 import (
    PACKAGE_MARKER as GLB012_PACKAGE_MARKER,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_PREFLIGHT_EXECUTION_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_APPROVAL_CREATED,
    OPERATIVE_CAPITAL_REALLOCATION_EXECUTED,
    OPERATIVE_FLATTEN_EXECUTED,
    OPERATIVE_GO_NO_GO_CREATED,
    OPERATIVE_KILLSWITCH_EXECUTED,
    OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
    OPERATIVE_OPERATOR_DECISION_CREATED,
    OPERATIVE_PILOT_EXECUTED,
    OPERATIVE_PREFLIGHT_EXECUTION,
    OPERATIVE_RATCHET_APPLIED,
    OPERATIVE_READINESS_DECISION_CREATED,
    OPERATIVE_RECONCILIATION_EXECUTED,
    OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
    OPERATIVE_RISK_EVALUATION_EXECUTED,
    OPERATIVE_SLOT_RELEASE_EXECUTED,
    ORDER_STATE_QUERIED,
    POSITION_STATE_QUERIED,
    TESTNET_RUN_STARTED,
    ZERO_ORDER_CAPABILITY_OWNER,
    Pe19ReviewProofBinding,
    AssemblySafetySnapshot,
    compute_assembly_input_digest,
    compute_assembly_result_digest,
    compute_lifecycle_matrix_digest,
    default_minimal_assembly_input,
    default_minimal_safety_snapshot,
    evaluate_preflight_execution_readiness_assembly_lifecycle_integration,
    serialize_assembly_input_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSEMBLY_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
PE14_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
PE15_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
)
PE16_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
PE17_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0.py"
)
PE18_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_source_state_capture_contract_v0.py"
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
GLB012_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py"
)
PE21_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0.py"
)
PE22_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
PE23_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0.py"
)
PE24_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0.py"
)
PE25_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_ASSEMBLY_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_ASSEMBLY_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_PREFLIGHT_EXECUTION_READINESS_ASSEMBLY_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in ASSEMBLY_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_through_pe25_owners_referenced_not_duplicated() -> None:
    lifecycle_text = LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE12_PACKAGE_MARKER in lifecycle_text
    assembly_text = ASSEMBLY_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in assembly_text
    assert "bounded_futures_testnet_preflight_packet_contract_v0" in assembly_text
    assert "bounded_futures_testnet_preflight_packet_builder_contract_v0" in assembly_text
    assert "bounded_futures_testnet_preflight_packet_replay_contract_v0" in assembly_text
    assert "bounded_futures_testnet_preflight_packet_archive_contract_v0" in assembly_text
    assert (
        "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0" in assembly_text
    )
    assert "bounded_futures_testnet_preflight_source_state_capture_contract_v0" in assembly_text
    assert (
        "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0"
        in assembly_text
    )
    assert (
        "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0"
        in assembly_text
    )
    assert (
        "bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0"
        in assembly_text
    )
    assert (
        "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0"
        in assembly_text
    )
    assert (
        "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0" in assembly_text
    )
    assert (
        "bounded_futures_testnet_capital_slot_ratchet_release_lifecycle_integration_contract_v0"
        in assembly_text
    )
    assert (
        "bounded_futures_testnet_pilot_envelope_lifecycle_integration_contract_v0" in assembly_text
    )
    assert (
        "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0"
        in assembly_text
    )
    assert "evaluate_phase_transition" not in assembly_text
    assert PE13_MODULE.exists()
    assert PE14_MODULE.exists()
    assert PE15_MODULE.exists()
    assert PE16_MODULE.exists()
    assert PE17_MODULE.exists()
    assert PE18_MODULE.exists()
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert GLB012_MODULE.exists()
    assert PE21_MODULE.exists()
    assert PE22_MODULE.exists()
    assert PE23_MODULE.exists()
    assert PE24_MODULE.exists()
    assert PE25_MODULE.exists()
    assert GLB012_PACKAGE_MARKER in GLB012_MODULE.read_text(encoding="utf-8")


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_PREFLIGHT_EXECUTION_READINESS is False
    assert OPERATIVE_PREFLIGHT_EXECUTION is False
    assert OPERATIVE_OPERATOR_CLOSURE_EXECUTED is False
    assert OPERATIVE_OPERATOR_DECISION_CREATED is False
    assert OPERATIVE_APPROVAL_CREATED is False
    assert OPERATIVE_GO_NO_GO_CREATED is False
    assert OPERATIVE_PILOT_EXECUTED is False
    assert OPERATIVE_READINESS_DECISION_CREATED is False
    assert OPERATIVE_RECONCILIATION_EXECUTED is False
    assert OPERATIVE_RISK_EVALUATION_EXECUTED is False
    assert OPERATIVE_KILLSWITCH_EXECUTED is False
    assert OPERATIVE_FLATTEN_EXECUTED is False
    assert OPERATIVE_RATCHET_APPLIED is False
    assert OPERATIVE_SLOT_RELEASE_EXECUTED is False
    assert OPERATIVE_CAPITAL_REALLOCATION_EXECUTED is False
    assert OPERATIVE_RESERVE_MOVEMENT_EXECUTED is False
    assert POSITION_STATE_QUERIED is False
    assert ORDER_STATE_QUERIED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_assembly_input_canonical(left) == serialize_assembly_input_canonical(right)
    assert compute_assembly_input_digest(left) == compute_assembly_input_digest(right)
    left_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(left)
    right_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(right)
    assert left_result["assembly_result_digest"] == right_result["assembly_result_digest"]


def test_valid_full_pe12_through_pe25_composition_passes() -> None:
    assembly_input = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(assembly_input)
    assert result["integration_pass"] is True
    assert result["preflight_execution_readiness_assembly_complete"] is True
    assert result["assembly_review_eligible"] is True
    assert result["pe12_preflight_execution_readiness_assembly_proven"] is True
    assert result["assembly_result_digest"] == compute_assembly_result_digest(
        assembly_input,
        preflight_execution_readiness_assembly_complete=True,
    )
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        default_minimal_assembly_input()
    )
    assert result["integration_pass"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["network_allowed"] is False
    assert result["credentials_allowed"] is False
    assert result["orders_allowed"] is False
    assert result["operator_closure_authorized"] is False
    assert result["operator_decision_authorized"] is False
    assert result["pilot_start_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["global_preflight_execution_readiness"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False


def test_missing_pe12_lifecycle_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_matrix = replace(assembly_input.lifecycle_matrix_proof, lifecycle_matrix_digest="")
    bad = replace(assembly_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "lifecycle_matrix_proof: lifecycle_matrix_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe13_packet_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe13 = replace(assembly_input.pe13_packet_proof, packet_digest="")
    bad = replace(assembly_input, pe13_packet_proof=bad_pe13)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe13_packet_proof: packet_digest required" in r for r in result["fail_reasons"])


def test_missing_pe14_builder_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe14 = replace(assembly_input.pe14_builder_proof, input_capture_digest="")
    bad = replace(assembly_input, pe14_builder_proof=bad_pe14)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe14_builder_proof: input_capture_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe15_replay_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe15 = replace(assembly_input.pe15_replay_proof, replay_manifest_digest="")
    bad = replace(assembly_input, pe15_replay_proof=bad_pe15)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe15_replay_proof: replay_manifest_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe16_archive_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe16 = replace(assembly_input.pe16_archive_proof, archive_identity="")
    bad = replace(assembly_input, pe16_archive_proof=bad_pe16)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe16_archive_proof: archive_identity required" in r for r in result["fail_reasons"])


def test_missing_pe17_completeness_truth_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe17 = replace(
        assembly_input.pe17_completeness_truth_proof, internal_static_chain_complete=False
    )
    bad = replace(assembly_input, pe17_completeness_truth_proof=bad_pe17)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe17_completeness_truth_proof: internal_static_chain_complete must be true" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe18_source_state_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe18 = replace(assembly_input.pe18_source_state_proof, source_state_digest="")
    bad = replace(assembly_input, pe18_source_state_proof=bad_pe18)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe18_source_state_proof: source_state_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe19_review_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe19 = replace(assembly_input.pe19_review_proof, review_proof_digest="")
    bad = replace(assembly_input, pe19_review_proof=bad_pe19)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: review_proof_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe20_durable_package_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe20 = replace(assembly_input.pe20_durable_review_package, package_id="")
    bad = replace(assembly_input, pe20_durable_review_package=bad_pe20)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe20_durable_review_package: package_id required" in r for r in result["fail_reasons"]
    )


def test_missing_glb012_capability_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_glb = replace(assembly_input.glb012_capability_proof, integration_proof_digest="")
    bad = replace(assembly_input, glb012_capability_proof=bad_glb)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "glb012_capability_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe21_reconciliation_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe21 = replace(
        assembly_input.pe21_reconciliation_primary_evidence_proof, integration_proof_digest=""
    )
    bad = replace(assembly_input, pe21_reconciliation_primary_evidence_proof=bad_pe21)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe21_reconciliation_primary_evidence_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe22_risk_killswitch_flatten_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe22 = replace(
        assembly_input.pe22_risk_killswitch_flatten_proof, integration_proof_digest=""
    )
    bad = replace(assembly_input, pe22_risk_killswitch_flatten_proof=bad_pe22)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe22_risk_killswitch_flatten_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe23_capital_slot_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe23 = replace(
        assembly_input.pe23_capital_slot_ratchet_release_proof, integration_proof_digest=""
    )
    bad = replace(assembly_input, pe23_capital_slot_ratchet_release_proof=bad_pe23)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe23_capital_slot_ratchet_release_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe24_pilot_envelope_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe24 = replace(assembly_input.pe24_pilot_envelope_proof, integration_proof_digest="")
    bad = replace(assembly_input, pe24_pilot_envelope_proof=bad_pe24)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe24_pilot_envelope_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe25_operator_closure_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe25 = replace(assembly_input.pe25_operator_closure_proof, closure_result_digest="")
    bad = replace(assembly_input, pe25_operator_closure_proof=bad_pe25)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe25_operator_closure_proof: closure_result_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_zero_order_capability_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_zero = replace(assembly_input.zero_order_capability_proof, capability_proof_digest="")
    bad = replace(assembly_input, zero_order_capability_proof=bad_zero)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "zero_order_capability_proof: capability_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_digest_mismatch_fails() -> None:
    assembly_input = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input,
        expected_packet_digest="f" * 64,
    )
    assert result["integration_pass"] is False
    assert any("pe13_packet_proof: packet_digest mismatch" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    assembly_input = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_dirty_source_state_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe18 = replace(assembly_input.pe18_source_state_proof, dirty_state=True)
    bad = replace(assembly_input, pe18_source_state_proof=bad_pe18)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("dirty_state must be false" in r for r in result["fail_reasons"])


def test_dirty_source_state_flag_injection_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, dirty_source_state=True
    )
    assert result["integration_pass"] is False
    assert any("dirty_source_state=true is not allowed" in r for r in result["fail_reasons"])


def test_replay_manifest_verify_rc_nonzero_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe15 = replace(assembly_input.pe15_replay_proof, manifest_verify_rc=1)
    bad = replace(assembly_input, pe15_replay_proof=bad_pe15)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe15_replay_proof: manifest_verify_rc must be 0" in r for r in result["fail_reasons"]
    )


def test_archive_manifest_verify_rc_nonzero_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe16 = replace(assembly_input.pe16_archive_proof, manifest_verify_rc=1)
    bad = replace(assembly_input, pe16_archive_proof=bad_pe16)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe16_archive_proof: manifest_verify_rc must be 0" in r for r in result["fail_reasons"]
    )


def test_missing_durable_primary_evidence_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe21 = replace(
        assembly_input.pe21_reconciliation_primary_evidence_proof,
        durable_primary_evidence_binding_proven=False,
    )
    bad = replace(assembly_input, pe21_reconciliation_primary_evidence_proof=bad_pe21)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "durable_primary_evidence_binding_proven must be true" in r for r in result["fail_reasons"]
    )


def test_missing_reconciliation_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe21 = replace(
        assembly_input.pe21_reconciliation_primary_evidence_proof, pe21_integration_pass=False
    )
    bad = replace(assembly_input, pe21_reconciliation_primary_evidence_proof=bad_pe21)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe21_integration_pass must be true" in r for r in result["fail_reasons"])


def test_missing_risk_killswitch_flatten_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe22 = replace(
        assembly_input.pe22_risk_killswitch_flatten_proof, pe22_integration_pass=False
    )
    bad = replace(assembly_input, pe22_risk_killswitch_flatten_proof=bad_pe22)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_integration_pass must be true" in r for r in result["fail_reasons"])


def test_missing_capital_slot_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe23 = replace(
        assembly_input.pe23_capital_slot_ratchet_release_proof, pe23_integration_pass=False
    )
    bad = replace(assembly_input, pe23_capital_slot_ratchet_release_proof=bad_pe23)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe23_integration_pass must be true" in r for r in result["fail_reasons"])


def test_missing_pilot_envelope_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe24 = replace(assembly_input.pe24_pilot_envelope_proof, pilot_envelope_static_ready=False)
    bad = replace(assembly_input, pe24_pilot_envelope_proof=bad_pe24)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe24_pilot_envelope_proof: pilot_envelope_static_ready must be true" in r
        for r in result["fail_reasons"]
    )


def test_missing_operator_closure_binding_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe25 = replace(
        assembly_input.pe25_operator_closure_proof, operator_closure_static_complete=False
    )
    bad = replace(assembly_input, pe25_operator_closure_proof=bad_pe25)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe25_operator_closure_proof: operator_closure_static_complete must be true" in r
        for r in result["fail_reasons"]
    )


def test_loose_boolean_true_without_canonical_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe17 = replace(
        assembly_input.pe17_completeness_truth_proof,
        internal_static_chain_complete=True,
        completeness_status="incomplete",
    )
    bad = replace(assembly_input, pe17_completeness_truth_proof=bad_pe17)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("completeness_status must be" in r for r in result["fail_reasons"])


def test_loose_boolean_readiness_flag_injection_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, loose_boolean_readiness=True
    )
    assert result["integration_pass"] is False
    assert any("loose_boolean_readiness=true is not allowed" in r for r in result["fail_reasons"])


def test_implicit_default_approve_without_review_proof_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_pe19 = Pe19ReviewProofBinding(
        review_input_digest="",
        decision_record_digest="",
        review_proof_digest="",
        review_valid=True,
        decision="approve",
        reason_code="evidence_complete",
        non_authorizing=True,
        ready_for_operator_arming=False,
        execution_authorized=False,
        live_authorized=False,
        evidence_manifest_verify_rc=0,
    )
    bad = replace(assembly_input, pe19_review_proof=bad_pe19)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: review_input_digest required" in r for r in result["fail_reasons"]
    )


def test_unknown_lifecycle_state_rejected() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, unknown_lifecycle_state="unknown_phase"
    )
    assert result["integration_pass"] is False
    assert any("unknown lifecycle state" in r for r in result["fail_reasons"])


def test_unsupported_lifecycle_phase_in_input_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    bad_matrix = replace(
        assembly_input.lifecycle_matrix_proof, assigned_lifecycle_phase="unknown_phase"
    )
    bad = replace(assembly_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_assembly_complete_without_proof_chain_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, assembly_complete_without_proof_chain=True
    )
    assert result["integration_pass"] is False
    assert any("without full proof chain is insufficient" in r for r in result["fail_reasons"])


def test_positive_execution_authority_flag_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, execution_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("execution_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_zero_order_authority_flag_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, zero_order_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("zero_order_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_network_flag_fails() -> None:
    assembly_input = default_minimal_assembly_input()
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(
        assembly_input, network_allowed=True
    )
    assert result["integration_pass"] is False
    assert any("network_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_btc_oriented_input_fails() -> None:
    assembly_input = default_minimal_assembly_input(instrument="PF_XBTUSD")
    result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(assembly_input)
    assert result["integration_pass"] is False
    assert any("forbidden orientation" in r for r in result["fail_reasons"])


def test_input_mutation_changes_digest() -> None:
    base = default_minimal_assembly_input(source_revision=VALID_COMMIT_SHA)
    mutated = replace(base, assembly_id="preflight-execution-readiness-assembly-002")
    assert compute_assembly_input_digest(base) != compute_assembly_input_digest(mutated)


def test_zero_order_capability_owner_is_canonical() -> None:
    assembly_input = default_minimal_assembly_input()
    assert (
        assembly_input.zero_order_capability_proof.capability_owner == ZERO_ORDER_CAPABILITY_OWNER
    )
    assert PHASE_ZERO_ORDER == "zero_order"
    assert PHASE_STATIC_PREFLIGHT == "static_preflight"


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    assembly_input = default_minimal_assembly_input()
    assert assembly_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_contract_version_constants() -> None:
    assert (
        CONTRACT_VERSION
        == "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration.v0"
    )


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert isinstance(snapshot, AssemblySafetySnapshot)
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.zero_order_authorized is False
