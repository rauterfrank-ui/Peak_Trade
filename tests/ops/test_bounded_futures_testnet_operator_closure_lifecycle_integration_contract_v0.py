"""Static + offline bounded Futures Testnet operator-closure lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
PE-25 static PE-12 readiness_decision operator-closure proof composition only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_OPERATOR_CLOSURE_READINESS,
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
    OPERATIVE_RATCHET_APPLIED,
    OPERATIVE_READINESS_DECISION_CREATED,
    OPERATIVE_RESERVE_MOVEMENT_EXECUTED,
    OPERATIVE_RISK_EVALUATION_EXECUTED,
    OPERATIVE_SCOPE_SWITCH_EXECUTED,
    OPERATIVE_SLOT_RELEASE_EXECUTED,
    ORDER_STATE_QUERIED,
    POSITION_STATE_QUERIED,
    TESTNET_RUN_STARTED,
    Pe19ReviewProofBinding,
    OperatorClosureSafetySnapshot,
    compute_closure_input_digest,
    compute_closure_result_digest,
    compute_lifecycle_matrix_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_operator_closure_lifecycle_integration,
    serialize_closure_input_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
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

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_CLOSURE_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_CLOSURE_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert "BOUNDED_FUTURES_TESTNET_OPERATOR_CLOSURE_LIFECYCLE_INTEGRATION_CONTRACT_V0=true" in (
        INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_pe19_pe20_pe22_pe23_pe24_owners_referenced_not_duplicated() -> None:
    lifecycle_text = LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE12_PACKAGE_MARKER in lifecycle_text
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0" in (
        integration_text
    )
    assert "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0" in (
        integration_text
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
    assert "evaluate_phase_transition" not in integration_text
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE22_MODULE.exists()
    assert PE23_MODULE.exists()
    assert PE24_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_OPERATOR_CLOSURE_READINESS is False
    assert OPERATIVE_OPERATOR_CLOSURE_EXECUTED is False
    assert OPERATIVE_OPERATOR_DECISION_CREATED is False
    assert OPERATIVE_APPROVAL_CREATED is False
    assert OPERATIVE_GO_NO_GO_CREATED is False
    assert OPERATIVE_PILOT_EXECUTED is False
    assert OPERATIVE_READINESS_DECISION_CREATED is False
    assert OPERATIVE_SCOPE_SWITCH_EXECUTED is False
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
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_closure_input_canonical(left) == serialize_closure_input_canonical(right)
    assert compute_closure_input_digest(left) == compute_closure_input_digest(right)
    left_result = evaluate_operator_closure_lifecycle_integration(left)
    right_result = evaluate_operator_closure_lifecycle_integration(right)
    assert left_result["closure_result_digest"] == right_result["closure_result_digest"]


def test_valid_pe12_pe19_pe20_pe22_pe23_pe24_composition_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_operator_closure_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["operator_closure_static_complete"] is True
    assert result["pe12_operator_closure_static_integration_proven"] is True
    assert result["closure_result_digest"] == compute_closure_result_digest(
        integration_input,
        operator_closure_static_complete=True,
    )
    assert result["fail_reasons"] == []


def test_missing_pe12_readiness_decision_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(integration_input.lifecycle_matrix_proof, lifecycle_matrix_digest="")
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "lifecycle_matrix_proof: lifecycle_matrix_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe19_review_input_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe19 = replace(integration_input.pe19_review_proof, review_input_digest="")
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: review_input_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe19_decision_record_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe19 = replace(integration_input.pe19_review_proof, decision_record_digest="")
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: decision_record_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe19_review_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe19 = replace(integration_input.pe19_review_proof, review_proof_digest="")
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: review_proof_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_pe20_durable_package_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe20 = replace(integration_input.pe20_durable_review_package, package_id="")
    bad = replace(integration_input, pe20_durable_review_package=bad_pe20)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe20_durable_review_package: package_id required" in r for r in result["fail_reasons"]
    )


def test_missing_pe22_risk_killswitch_flatten_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe22 = replace(
        integration_input.pe22_risk_killswitch_flatten_proof, integration_proof_digest=""
    )
    bad = replace(integration_input, pe22_risk_killswitch_flatten_proof=bad_pe22)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe22_risk_killswitch_flatten_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe23_capital_slot_ratchet_release_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe23 = replace(
        integration_input.pe23_capital_slot_ratchet_release_proof, integration_proof_digest=""
    )
    bad = replace(integration_input, pe23_capital_slot_ratchet_release_proof=bad_pe23)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe23_capital_slot_ratchet_release_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_missing_pe24_pilot_envelope_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe24 = replace(integration_input.pe24_pilot_envelope_proof, integration_proof_digest="")
    bad = replace(integration_input, pe24_pilot_envelope_proof=bad_pe24)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe24_pilot_envelope_proof: integration_proof_digest required" in r
        for r in result["fail_reasons"]
    )


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_incomplete_commit_sha_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision="abc123")
    result = evaluate_operator_closure_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("source_revision must be full 40-char" in r for r in result["fail_reasons"])


def test_unknown_contract_version_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_versions = replace(
        integration_input.contract_versions,
        integration="unknown.integration.v99",
    )
    bad = replace(integration_input, contract_versions=bad_versions)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("contract_versions: integration must be" in r for r in result["fail_reasons"])


def test_adapter_id_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(integration_input.lifecycle_state_before, adapter_id="other_adapter")
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_before: adapter_id mismatch" in r for r in result["fail_reasons"])


def test_closure_id_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(closure_id="closure-a")
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input,
        expected_closure_id="closure-b",
    )
    assert result["integration_pass"] is False
    assert any("closure_id mismatch" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(integration_input.lifecycle_matrix_proof, lifecycle_matrix_digest="f" * 64)
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "lifecycle_matrix_proof: lifecycle_matrix_digest mismatch" in r
        for r in result["fail_reasons"]
    )


def test_manifest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe20 = replace(integration_input.pe20_durable_review_package, manifest_verify_rc=1)
    bad = replace(integration_input, pe20_durable_review_package=bad_pe20)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe20_durable_review_package: manifest_verify_rc must be 0" in r
        for r in result["fail_reasons"]
    )


def test_verify_rc_unequal_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe19 = replace(integration_input.pe19_review_proof, evidence_manifest_verify_rc=1)
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("evidence_manifest_verify_rc must be 0" in r for r in result["fail_reasons"])


def test_review_decision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe19 = replace(integration_input.pe19_review_proof, decision="approve")
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "decision must be approve_for_separate_next_phase_review" in r
        for r in result["fail_reasons"]
    )


def test_implicit_default_approve_without_review_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
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
    bad = replace(integration_input, pe19_review_proof=bad_pe19)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe19_review_proof: review_input_digest required" in r for r in result["fail_reasons"]
    )


def test_active_killswitch_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, killswitch_active=True
    )
    assert result["integration_pass"] is False
    assert any("killswitch_active=true is not allowed" in r for r in result["fail_reasons"])


def test_triggered_killswitch_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, killswitch_triggered=True
    )
    assert result["integration_pass"] is False
    assert any("killswitch_triggered=true is not allowed" in r for r in result["fail_reasons"])


def test_unresolved_risk_state_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, unresolved_risk_state=True
    )
    assert result["integration_pass"] is False
    assert any("unresolved_risk_state=true is not allowed" in r for r in result["fail_reasons"])


def test_missing_flatten_proof_fails_via_pe22_binding() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe22 = replace(
        integration_input.pe22_risk_killswitch_flatten_proof, pe22_integration_pass=False
    )
    bad = replace(integration_input, pe22_risk_killswitch_flatten_proof=bad_pe22)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe22_integration_pass must be true" in r for r in result["fail_reasons"])


def test_reserve_topup_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, reserve_topup_allowed=True
    )
    assert result["integration_pass"] is False
    assert any("reserve_topup_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_invalid_ratchet_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, invalid_ratchet=True
    )
    assert result["integration_pass"] is False
    assert any("invalid_ratchet=true is not allowed" in r for r in result["fail_reasons"])


def test_disallowed_slot_basis_increase_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, disallowed_slot_basis_increase=True
    )
    assert result["integration_pass"] is False
    assert any(
        "disallowed_slot_basis_increase=true is not allowed" in r for r in result["fail_reasons"]
    )


def test_manipulated_release_eligibility_fails_via_flag_injection() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, manipulated_release_eligibility=True
    )
    assert result["integration_pass"] is False
    assert any(
        "manipulated_release_eligibility=true is not allowed" in r for r in result["fail_reasons"]
    )


def test_invalid_pilot_envelope_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe24 = replace(
        integration_input.pe24_pilot_envelope_proof, pilot_envelope_static_ready=False
    )
    bad = replace(integration_input, pe24_pilot_envelope_proof=bad_pe24)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "pe24_pilot_envelope_proof: pilot_envelope_static_ready must be true" in r
        for r in result["fail_reasons"]
    )


def test_unsupported_lifecycle_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof, assigned_lifecycle_phase="unknown_phase"
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_operator_closure_static_complete_true_without_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input,
        operator_closure_static_complete_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert any("without full proof chain is insufficient" in r for r in result["fail_reasons"])


def test_positive_operator_closure_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, operator_closure_authorized=True
    )
    assert result["integration_pass"] is False
    assert any(
        "operator_closure_authorized=true is not allowed" in r for r in result["fail_reasons"]
    )


def test_positive_operator_decision_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, operator_decision_authorized=True
    )
    assert result["integration_pass"] is False
    assert any(
        "operator_decision_authorized=true is not allowed" in r for r in result["fail_reasons"]
    )


def test_positive_approve_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, approval_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("approval_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_go_no_go_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, go_no_go_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("go_no_go_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_pilot_start_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, pilot_start_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("pilot_start_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_promotion_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, promotion_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("promotion_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_reallocation_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, capital_reallocation_authorized=True
    )
    assert result["integration_pass"] is False
    assert any(
        "capital_reallocation_authorized=true is not allowed" in r for r in result["fail_reasons"]
    )


def test_positive_network_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, network_allowed=True
    )
    assert result["integration_pass"] is False
    assert any("network_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_runtime_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input,
        scheduler_runtime_allowed=True,
    )
    assert result["integration_pass"] is False
    assert any("scheduler_runtime_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_execution_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, execution_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("execution_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_live_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, live_authorized=True
    )
    assert result["integration_pass"] is False
    assert any("live_authorized=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_credentials_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(
        integration_input, credentials_allowed=True
    )
    assert result["integration_pass"] is False
    assert any("credentials_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_positive_orders_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_operator_closure_lifecycle_integration(integration_input, orders_allowed=True)
    assert result["integration_pass"] is False
    assert any("orders_allowed=true is not allowed" in r for r in result["fail_reasons"])


def test_btc_oriented_input_fails() -> None:
    integration_input = default_minimal_integration_input(instrument="PF_XBTUSD")
    result = evaluate_operator_closure_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("forbidden orientation" in r for r in result["fail_reasons"])


def test_safety_snapshot_drift_fails() -> None:
    snapshot = default_minimal_safety_snapshot()
    bad_snapshot = replace(snapshot, operator_closure_authorized=True)
    integration_input = default_minimal_integration_input()
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_operator_closure_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "safety_snapshot: operator_closure_authorized must be False" in r
        for r in result["fail_reasons"]
    )


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_operator_closure_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["operator_closure_authorized"] is False
    assert result["operator_decision_authorized"] is False
    assert result["global_operator_closure_readiness"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == "bounded_futures_testnet_operator_closure_lifecycle_integration.v0"
    assert PHASE_READINESS_DECISION == "readiness_decision"
    assert PHASE_RECONCILIATION_REVIEW == "reconciliation_review"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.operator_closure_authorized is False
    assert snapshot.operator_decision_authorized is False
    assert snapshot.pilot_start_authorized is False
    assert snapshot.promotion_authorized is False
    assert snapshot.followup_run_gate
