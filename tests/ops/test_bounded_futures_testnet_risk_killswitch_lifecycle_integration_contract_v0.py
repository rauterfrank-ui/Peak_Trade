"""Static + offline bounded Futures Testnet risk/killswitch lifecycle integration (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
PE-22 static PE-12 tiny_order Risk/KillSwitch/Flatten binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_RISK_KILLSWITCH_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_FLATTEN_EXECUTED,
    OPERATIVE_KILLSWITCH_EXECUTED,
    OPERATIVE_RISK_EVALUATION_EXECUTED,
    PACKAGE_MARKER,
    TESTNET_RUN_STARTED,
    ContractVersionsInput,
    FlattenStateProof,
    IntegrationSafetySnapshot,
    KillSwitchEvaluationProof,
    KillSwitchPolicyBinding,
    KillSwitchStateBinding,
    LifecycleMatrixProof,
    LifecycleStateBinding,
    RiskContextBinding,
    RiskEvaluationProof,
    RiskKillswitchLifecycleIntegrationInput,
    RiskPolicyBinding,
    RiskSnapshotBinding,
    TinyOrderGateMatrixProof,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_tiny_order_gate_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_risk_killswitch_lifecycle_integration,
    evaluate_risk_static_proof,
    serialize_integration_input_canonical,
    validate_risk_killswitch_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    FLATTEN_BINDING_REFERENCE,
    FOLLOWUP_RUN_GATE,
    KILLSWITCH_BINDING_REFERENCE,
    PE12_CONTRACT_VERSION,
    RISK_CONTRACT_REFERENCE,
)
from src.risk_layer.kill_switch.state import KillSwitchState

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
RISK_GATE_MODULE = REPO_ROOT / "src" / "ops" / "gates" / "risk_gate.py"
KILLSWITCH_MODULE = (
    REPO_ROOT / "src" / "ops" / "order_capability_killswitch_abort_binding_contract_v1.py"
)
FLATTEN_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_contract_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RISK_KILLSWITCH_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_RISK_KILLSWITCH_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in INTEGRATION_MODULE.read_text(encoding="utf-8")


def test_pe12_risk_killswitch_flatten_owners_referenced_not_duplicated() -> None:
    lifecycle_text = LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE12_PACKAGE_MARKER in lifecycle_text
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert "gates.risk_gate" in integration_text
    assert "order_capability_killswitch_abort_binding_contract_v1" in integration_text
    assert "bounded_futures_testnet_contract_v0" in integration_text
    assert "evaluate_risk" in integration_text
    assert "evaluate_phase_transition" not in integration_text
    assert RISK_GATE_MODULE.exists()
    assert KILLSWITCH_MODULE.exists()
    assert FLATTEN_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_RISK_EVALUATION_EXECUTED is False
    assert OPERATIVE_KILLSWITCH_EXECUTED is False
    assert OPERATIVE_FLATTEN_EXECUTED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert GLOBAL_RISK_KILLSWITCH_READINESS is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_risk_killswitch_lifecycle_integration(left)
    right_result = evaluate_risk_killswitch_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]


def test_valid_pe12_tiny_order_risk_killswitch_flatten_binding_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["pe12_tiny_order_risk_killswitch_flatten_static_integration_proven"] is True
    assert result["integration_proof_digest"] == compute_integration_proof_digest(integration_input)
    assert result["fail_reasons"] == []
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["authority_lift"] is False
    assert result["global_risk_killswitch_readiness"] is False


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_risk_killswitch_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["operative_risk_evaluation_executed"] is False
    assert result["operative_killswitch_executed"] is False
    assert result["operative_flatten_executed"] is False
    assert result["lifecycle_transition_executed"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["contract_implementation_only"] is True


def test_missing_tiny_order_gate_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_gate = TinyOrderGateMatrixProof(
        pe12_contract_version=PE12_CONTRACT_VERSION,
        lifecycle_matrix_digest="",
        tiny_order_gate_digest=compute_tiny_order_gate_digest(),
        operator_go_token="GO_BOUNDED_FUTURES_TESTNET_TINY_ORDER_V0",
    )
    bad = replace(integration_input, tiny_order_gate_proof=bad_gate)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_matrix_digest required" in r for r in result["fail_reasons"])


def test_missing_risk_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.risk_evaluation_proof, proof_digest="")
    bad = replace(integration_input, risk_evaluation_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("risk_evaluation_proof: proof_digest required" in r for r in result["fail_reasons"])


def test_missing_killswitch_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.killswitch_evaluation_proof, proof_digest="")
    bad = replace(integration_input, killswitch_evaluation_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "killswitch_evaluation_proof: proof_digest required" in r for r in result["fail_reasons"]
    )


def test_missing_flatten_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.flatten_state_proof, proof_digest="")
    bad = replace(integration_input, flatten_state_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("flatten_state_proof: proof_digest required" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_incomplete_commit_sha_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision="abc123")
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("source_revision must be full 40-char" in r for r in result["fail_reasons"])


def test_unknown_contract_version_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_versions = replace(
        integration_input.contract_versions,
        integration="unknown.integration.v99",
    )
    bad = replace(integration_input, contract_versions=bad_versions)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("contract_versions: integration must be" in r for r in result["fail_reasons"])


def test_instrument_adapter_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(
        integration_input.lifecycle_state_before,
        adapter_id="other_adapter",
    )
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_id mismatch" in r for r in result["fail_reasons"])


def test_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        lifecycle_matrix_digest="f" * 64,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_matrix_digest mismatch" in r for r in result["fail_reasons"])


def test_unknown_risk_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.risk_snapshot,
        limits_enabled=False,
    )
    bad = replace(integration_input, risk_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("limits_enabled must be true" in r for r in result["fail_reasons"])


def test_violated_risk_invariant_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_context = replace(
        integration_input.risk_context,
        order_notional_usd=9999.0,
    )
    bad = replace(integration_input, risk_context=bad_context)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("evaluation_allow mismatch" in r for r in result["fail_reasons"])


def test_unresolved_risk_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.risk_evaluation_proof,
        evaluation_allow=True,
        deny_reason="kill_switch",
    )
    bad = replace(integration_input, risk_evaluation_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("deny_reason mismatch" in r for r in result["fail_reasons"])


def test_active_killswitch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_state = replace(
        integration_input.killswitch_state,
        killswitch_state=KillSwitchState.KILLED.name,
        state_digest="",
    )
    from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
        compute_killswitch_state_digest,
    )

    bad_state = replace(
        bad_state,
        state_digest=compute_killswitch_state_digest(bad_state),
    )
    bad_proof = replace(
        integration_input.killswitch_evaluation_proof,
        normalized_state="KILLED",
        killswitch_clear=True,
        state_digest=bad_state.state_digest,
    )
    bad = replace(
        integration_input,
        killswitch_state=bad_state,
        killswitch_evaluation_proof=bad_proof,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("triggered state" in r for r in result["fail_reasons"])


def test_tripped_killswitch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_state = replace(integration_input.killswitch_state, killswitch_state="TRIPPED")
    from src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0 import (
        compute_killswitch_state_digest,
    )

    bad_state = replace(
        bad_state,
        state_digest=compute_killswitch_state_digest(bad_state),
    )
    bad_proof = replace(
        integration_input.killswitch_evaluation_proof,
        normalized_state="TRIPPED",
        state_digest=bad_state.state_digest,
    )
    bad = replace(
        integration_input,
        killswitch_state=bad_state,
        killswitch_evaluation_proof=bad_proof,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("tripped state" in r for r in result["fail_reasons"])


def test_killswitch_state_proof_contradiction_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.killswitch_evaluation_proof,
        killswitch_clear=False,
    )
    bad = replace(integration_input, killswitch_evaluation_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("killswitch_clear" in r for r in result["fail_reasons"])


def test_required_flatten_unproven_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.flatten_state_proof,
        proof_pass=False,
    )
    bad = replace(integration_input, flatten_state_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("proof_pass must be true" in r for r in result["fail_reasons"])


def test_required_flat_state_false_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.flatten_state_proof,
        position_flattened_by_end=False,
    )
    bad = replace(integration_input, flatten_state_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("position_flattened_by_end required" in r for r in result["fail_reasons"])


def test_flatten_position_contradiction_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.flatten_state_proof,
        position_flattened_by_end=True,
        position_quantity=1.0,
    )
    bad = replace(integration_input, flatten_state_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("flatten/position contradiction" in r for r in result["fail_reasons"])


def test_unsupported_lifecycle_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase="unsupported_phase",
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_lifecycle_gate_contradiction_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, orders_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_allowed must be False" in r for r in result["fail_reasons"])


def test_boolean_risk_ok_without_full_proof_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        risk_ok_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert any("risk_ok=true without full proof chain" in r for r in result["fail_reasons"])


def test_boolean_killswitch_clear_without_full_proof_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        killswitch_clear_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert any(
        "killswitch_clear=true without full proof chain" in r for r in result["fail_reasons"]
    )


def test_boolean_flat_without_full_proof_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        flat_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert any("flat=true without full proof chain" in r for r in result["fail_reasons"])


def test_positive_network_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, network_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_execution_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, execution_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("execution_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_live_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, live_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("live_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_credential_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, credentials_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("credentials_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_order_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, orders_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_allowed must be False" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "instrument",
    ["BTC/EUR", "BTCUSDT", "PF_XBTUSD"],
)
def test_btc_xbt_spot_oriented_input_fails(instrument: str) -> None:
    integration_input = default_minimal_integration_input(instrument=instrument)
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False


def test_bitcoin_direction_allowed_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, bitcoin_direction_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bitcoin_direction_allowed must be False" in r for r in result["fail_reasons"])


def test_safety_snapshot_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.safety_snapshot,
        followup_run_gate="AUTO_GO",
    )
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("followup_run_gate must be" in r for r in result["fail_reasons"])


def test_lifecycle_state_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        expected_lifecycle_state_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("lifecycle_state_digest mismatch" in r for r in result["fail_reasons"])


def test_risk_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        expected_risk_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("risk_evaluation_proof: proof_digest mismatch" in r for r in result["fail_reasons"])


def test_killswitch_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        expected_killswitch_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any(
        "killswitch_evaluation_proof: proof_digest mismatch" in r for r in result["fail_reasons"]
    )


def test_flatten_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_risk_killswitch_lifecycle_integration(
        integration_input,
        expected_flatten_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("flatten_state_proof: proof_digest mismatch" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_tiny_order_gate_digest_matches_canonical_identity() -> None:
    digest = compute_tiny_order_gate_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.tiny_order_gate_proof.tiny_order_gate_digest == digest


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == "bounded_futures_testnet_risk_killswitch_lifecycle_integration.v0"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.execution_authorized is False
    assert snapshot.live_authorized is False
    assert snapshot.zero_order_authorized is False
    assert snapshot.network_allowed is False
    assert snapshot.credentials_allowed is False
    assert snapshot.orders_allowed is False
    assert snapshot.scheduler_runtime_allowed is False
    assert snapshot.futures_only is True
    assert snapshot.bitcoin_direction_allowed is False
    assert snapshot.followup_run_gate == FOLLOWUP_RUN_GATE


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_risk_gate_reused_not_duplicated() -> None:
    integration_input = default_minimal_integration_input()
    static_eval = evaluate_risk_static_proof(
        snapshot=integration_input.risk_snapshot,
        context=integration_input.risk_context,
    )
    assert static_eval["evaluation_allow"] is True
    assert static_eval["proof_pass"] is True


def test_binding_references_match_preflight_packet_contract() -> None:
    integration_input = default_minimal_integration_input()
    assert integration_input.risk_policy.contract_reference == RISK_CONTRACT_REFERENCE
    assert integration_input.killswitch_policy.binding_reference == KILLSWITCH_BINDING_REFERENCE
    assert integration_input.flatten_state_proof.binding_reference == FLATTEN_BINDING_REFERENCE


def test_capital_slot_pilot_envelope_not_included() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "capital_slot" not in integration_text.lower()
    assert "pilot_envelope" not in integration_text.lower()


def test_boolean_proof_pass_false_without_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.risk_evaluation_proof, proof_pass=False)
    bad = replace(integration_input, risk_evaluation_proof=bad_proof)
    assert validate_risk_killswitch_lifecycle_integration_input(bad)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["pe12_tiny_order_risk_killswitch_flatten_static_integration_proven"] is False


def test_lifecycle_before_must_be_validate_only() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(
        integration_input.lifecycle_state_before,
        assigned_lifecycle_phase=PHASE_TINY_ORDER,
    )
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_before" in r for r in result["fail_reasons"])
