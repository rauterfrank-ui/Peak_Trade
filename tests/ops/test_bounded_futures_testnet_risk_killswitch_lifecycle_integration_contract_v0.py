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
    OPERATOR_GO_TINY_ORDER,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
)
from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
    REASON_ABORT_ACK_NOT_CONFIRMED,
    REASON_CORRELATION_MISMATCH,
    REASON_KILLSWITCH_TRIPPED,
    REASON_MISSING_EVIDENCE_CORRELATION,
    REASON_PAYLOAD_UNSAFE_FLAGS,
    REASON_TOKEN_MISMATCH,
    OrderCapabilityAbortBindingInput,
    OrderCapabilityBindingVerdict,
    OrderCapabilityKillSwitchSnapshot,
    OrderCapabilityPayloadSafetySummary,
    evaluate_order_capability_abort_binding,
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
PE22_ABORT_NOW_UTC = "2026-06-09T13:00:00Z"
PE22_ABORT_OBSERVED_UTC = "2026-06-09T12:59:30Z"


def _pe22_abort_correlation_id(adapter_id: str) -> str:
    return f"pe22-{adapter_id}"


def _valid_abort_binding_input(
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    **overrides: object,
) -> OrderCapabilityAbortBindingInput:
    correlation_id = _pe22_abort_correlation_id(adapter_id)
    payload = OrderCapabilityPayloadSafetySummary(
        evidence_correlation_id=correlation_id,
        no_submit=True,
        no_network=True,
        execute_authorized=False,
        order_submission_executed=False,
        cancel_executed=False,
        trade_position_mutation_executed=False,
        abort_ack_marker="CONFIRMED",
        operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
        environment="testnet",
    )
    snapshot = OrderCapabilityKillSwitchSnapshot(
        source="pe22_offline_fixture",
        source_id=f"pe22-ks-{adapter_id}",
        source_kind="injected_offline_fixture",
        state="CLEAR",
        observed_at_utc=PE22_ABORT_OBSERVED_UTC,
        ttl_seconds=120,
        correlation_id=correlation_id,
        environment="testnet",
    )
    base = {
        "payload_summary": payload,
        "expected_operator_go_token_binding": OPERATOR_GO_TINY_ORDER,
        "kill_switch_snapshot": snapshot,
        "now_utc": PE22_ABORT_NOW_UTC,
        "expected_environment": "testnet",
    }
    base.update(overrides)
    if "payload_summary" in overrides:
        base["payload_summary"] = overrides["payload_summary"]
    if "kill_switch_snapshot" in overrides:
        base["kill_switch_snapshot"] = overrides["kill_switch_snapshot"]
    return OrderCapabilityAbortBindingInput(**base)


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


def test_valid_abort_binding_with_pe22_prerequisites_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    abort_verdict = evaluate_order_capability_abort_binding(integration_input.abort_binding_input)
    assert abort_verdict.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["fail_reasons"] == []


def test_abort_binding_idempotent_repeat_produces_same_result() -> None:
    integration_input = default_minimal_integration_input()
    first = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    second = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert first == second


def test_missing_abort_binding_correlation_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id="",
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        REASON_MISSING_EVIDENCE_CORRELATION in r or "binding_input required" in r
        for r in result["fail_reasons"]
    )


def test_abort_binding_evaluator_fail_closed_blocks_pe22() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="pe22_offline_fixture",
            source_id="pe22-ks-001",
            source_kind="injected_offline_fixture",
            state="TRIPPED",
            observed_at_utc=PE22_ABORT_OBSERVED_UTC,
            ttl_seconds=120,
            correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_KILLSWITCH_TRIPPED in r for r in result["fail_reasons"])


def test_abort_ack_not_confirmed_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="PENDING",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_ABORT_ACK_NOT_CONFIRMED in r for r in result["fail_reasons"])


def test_abort_payload_unsafe_flags_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            no_submit=False,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_PAYLOAD_UNSAFE_FLAGS in r for r in result["fail_reasons"])


def test_abort_cleanup_cancel_executed_flag_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=True,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_PAYLOAD_UNSAFE_FLAGS in r for r in result["fail_reasons"])


def test_abort_idempotency_not_proven_when_order_submission_executed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=True,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_PAYLOAD_UNSAFE_FLAGS in r for r in result["fail_reasons"])


def test_abort_binding_correlation_mismatch_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id="ev-a",
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        ),
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="pe22_offline_fixture",
            source_id="pe22-ks-001",
            source_kind="injected_offline_fixture",
            state="CLEAR",
            observed_at_utc=PE22_ABORT_OBSERVED_UTC,
            ttl_seconds=120,
            correlation_id="ev-b",
            environment="testnet",
        ),
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(REASON_CORRELATION_MISMATCH in r for r in result["fail_reasons"])


def test_abort_binding_owner_token_drift_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(expected_operator_go_token_binding="GO_OTHER_TOKEN")
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("owner drift" in r or REASON_TOKEN_MISMATCH in r for r in result["fail_reasons"])


def test_abort_binding_payload_owner_drift_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding="GO_OTHER_TOKEN",
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("owner drift" in r or REASON_TOKEN_MISMATCH in r for r in result["fail_reasons"])


def test_abort_binding_lifecycle_adapter_identity_drift_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id="foreign-run-identity",
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        ),
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="pe22_offline_fixture",
            source_id="pe22-ks-001",
            source_kind="injected_offline_fixture",
            state="CLEAR",
            observed_at_utc=PE22_ABORT_OBSERVED_UTC,
            ttl_seconds=120,
            correlation_id="foreign-run-identity",
            environment="testnet",
        ),
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_id identity drift" in r for r in result["fail_reasons"])


def test_abort_killswitch_identity_drift_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="pe22_offline_fixture",
            source_id=f"pe22-ks-{integration_input.adapter_id}",
            source_kind="injected_offline_fixture",
            state="OK",
            observed_at_utc=PE22_ABORT_OBSERVED_UTC,
            ttl_seconds=120,
            correlation_id=_pe22_abort_correlation_id(integration_input.adapter_id),
            environment="testnet",
        )
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("killswitch identity drift" in r for r in result["fail_reasons"])


def test_foreign_abort_proof_fail_closed() -> None:
    integration_input = default_minimal_integration_input()
    bad_abort = _valid_abort_binding_input(
        payload_summary=OrderCapabilityPayloadSafetySummary(
            evidence_correlation_id="foreign-proof-run-999",
            no_submit=True,
            no_network=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            abort_ack_marker="CONFIRMED",
            operator_go_token_binding=OPERATOR_GO_TINY_ORDER,
            environment="testnet",
        ),
        kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
            source="foreign_owner",
            source_id="foreign-proof-run-999",
            source_kind="foreign_fixture",
            state="CLEAR",
            observed_at_utc=PE22_ABORT_OBSERVED_UTC,
            ttl_seconds=120,
            correlation_id="foreign-proof-run-999",
            environment="testnet",
        ),
    )
    bad = replace(integration_input, abort_binding_input=bad_abort)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_id identity drift" in r for r in result["fail_reasons"])


def test_abort_evaluator_none_result_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    integration_input = default_minimal_integration_input()

    def _return_none(
        _inp: OrderCapabilityAbortBindingInput,
    ) -> OrderCapabilityBindingVerdict | None:
        return None

    monkeypatch.setattr(
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.evaluate_order_capability_abort_binding",
        _return_none,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("verdict_none" in r for r in result["fail_reasons"])


def test_abort_evaluator_exception_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    integration_input = default_minimal_integration_input()

    def _raise(
        _inp: OrderCapabilityAbortBindingInput,
    ) -> OrderCapabilityBindingVerdict:
        raise ValueError("abort evaluator failure")

    monkeypatch.setattr(
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.evaluate_order_capability_abort_binding",
        _raise,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("evaluation_exception" in r for r in result["fail_reasons"])


def test_abort_evaluator_unknown_verdict_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
        OrderCapabilityAbortBindingVerdict,
    )

    integration_input = default_minimal_integration_input()

    def _return_blocked(
        inp: OrderCapabilityAbortBindingInput,
    ) -> OrderCapabilityAbortBindingVerdict:
        return OrderCapabilityAbortBindingVerdict(
            verdict=OrderCapabilityBindingVerdict.BLOCKED,
            reason_codes=(),
            evidence_correlation_id=inp.payload_summary.evidence_correlation_id,
            snapshot_age_seconds=None,
            no_authority_change=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            preflight_remains_blocked=True,
            live_ready=False,
            dashboard_truth_granted=False,
        )

    monkeypatch.setattr(
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.evaluate_order_capability_abort_binding",
        _return_blocked,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("verdict_blocked" in r for r in result["fail_reasons"])


def test_abort_repeated_evaluation_inconsistency_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
        OrderCapabilityAbortBindingVerdict,
    )

    integration_input = default_minimal_integration_input()
    call_count = 0

    def _alternate_verdict(
        inp: OrderCapabilityAbortBindingInput,
    ) -> OrderCapabilityAbortBindingVerdict:
        nonlocal call_count
        call_count += 1
        verdict = (
            OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY
            if call_count == 1
            else OrderCapabilityBindingVerdict.FAIL_CLOSED
        )
        return OrderCapabilityAbortBindingVerdict(
            verdict=verdict,
            reason_codes=() if call_count == 1 else (REASON_TOKEN_MISMATCH,),
            evidence_correlation_id=inp.payload_summary.evidence_correlation_id,
            snapshot_age_seconds=None,
            no_authority_change=True,
            execute_authorized=False,
            order_submission_executed=False,
            cancel_executed=False,
            trade_position_mutation_executed=False,
            preflight_remains_blocked=True,
            live_ready=False,
            dashboard_truth_granted=False,
        )

    monkeypatch.setattr(
        "src.ops.bounded_futures_testnet_risk_killswitch_lifecycle_integration_contract_v0.evaluate_order_capability_abort_binding",
        _alternate_verdict,
    )
    result = evaluate_risk_killswitch_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("repeated evaluation inconsistency" in r for r in result["fail_reasons"])


def test_existing_pe22_risk_failure_remains_effective_with_valid_abort_binding() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.risk_evaluation_proof, proof_digest="")
    bad = replace(integration_input, risk_evaluation_proof=bad_proof)
    result = evaluate_risk_killswitch_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("risk_evaluation_proof: proof_digest required" in r for r in result["fail_reasons"])


def test_evaluate_order_capability_abort_binding_referenced_in_integration_module() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "evaluate_order_capability_abort_binding" in integration_text
    assert "abort_binding_input" in integration_text
