"""Static + offline bounded Futures Testnet private-readonly lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, private API execution, or Testnet start.
PE-28 static PE-26 assembly + canonical private-readonly proof binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    PACKAGE_MARKER as PE11_PACKAGE_MARKER,
    PRIVATE_READONLY_MODE,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_PRIVATE_READONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    default_minimal_assembly_input,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EXCHANGE_API_CALLED,
    GLOBAL_PRIVATE_READONLY_LIFECYCLE_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_ADAPTER_CALLED,
    OPERATIVE_PRIVATE_READONLY_EXECUTED,
    PE11_CONTRACT_VERSION,
    PE26_ASSEMBLY_OWNER,
    PRIVATE_READONLY_OWNER,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    PrivateReadonlyProofBinding,
    Pe26AssemblyProofBinding,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_private_readonly_proof_digest,
    default_minimal_integration_input,
    default_minimal_pe26_assembly_proof,
    default_minimal_private_readonly_proof,
    default_minimal_safety_snapshot,
    evaluate_private_readonly_lifecycle_integration,
    serialize_integration_input_canonical,
    serialize_private_readonly_proof_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0.py"
)
PE26_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
PRIVATE_READONLY_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_private_readonly_contract_v0.py"
)
PRIVATE_READONLY_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_private_readonly_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PRIVATE_READONLY_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_PRIVATE_READONLY_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_PRIVATE_READONLY_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_pe26_and_private_readonly_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert (
        "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert "bounded_futures_private_readonly_contract_v0" in integration_text
    assert "evaluate_phase_transition" not in integration_text
    assert "run_private_readonly_reachability" not in integration_text
    assert "resolve_private_readonly_credentials_from_environ" not in integration_text
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE11_PACKAGE_MARKER in PRIVATE_READONLY_MODULE.read_text(encoding="utf-8")
    assert PE26_MODULE.exists()
    assert PRIVATE_READONLY_TEST.is_file()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_PRIVATE_READONLY_LIFECYCLE_READINESS is False
    assert OPERATIVE_PRIVATE_READONLY_EXECUTED is False
    assert OPERATIVE_ADAPTER_CALLED is False
    assert EXCHANGE_API_CALLED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False


def test_valid_pe26_assembly_plus_private_readonly_proof_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_private_readonly_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["private_readonly_lifecycle_eligibility"] is True
    assert result["pe28_private_readonly_lifecycle_static_integration_proven"] is True
    assert result["assigned_lifecycle_phase"] == PHASE_PRIVATE_READONLY
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_private_readonly_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["private_readonly_lifecycle_eligibility"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["private_readonly_authorized"] is False
    assert result["pilot_start_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["operator_closure_authorized"] is False
    assert result["operator_decision_authorized"] is False
    assert result["network_allowed"] is False
    assert result["credentials_allowed"] is False
    assert result["orders_allowed"] is False
    assert result["scheduler_runtime_allowed"] is False
    assert result["network_used"] is False
    assert result["credentials_used"] is False
    assert result["secret_material_read"] is False
    assert result["secret_material_stored"] is False
    assert result["orders_created"] == 0
    assert result["orders_cancelled"] == 0
    assert result["orders_amended"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["global_private_readonly_lifecycle_readiness"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["runtime_started"] is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_private_readonly_lifecycle_integration(left)
    right_result = evaluate_private_readonly_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        private_readonly_lifecycle_eligibility=True,
    )


def test_private_readonly_proof_digest_stability() -> None:
    left = default_minimal_private_readonly_proof()
    right = default_minimal_private_readonly_proof()
    assert serialize_private_readonly_proof_canonical(
        left
    ) == serialize_private_readonly_proof_canonical(right)
    assert compute_private_readonly_proof_digest(left) == compute_private_readonly_proof_digest(
        right
    )


def test_lifecycle_phase_not_private_readonly_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase=PHASE_ZERO_ORDER,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert result["private_readonly_lifecycle_eligibility"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_missing_pe26_assembly_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.pe26_assembly_proof, assembly_input_digest="")
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assembly_input_digest required" in r for r in result["fail_reasons"])


def test_incomplete_pe26_assembly_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_assembly = replace(
        integration_input.pe26_assembly_input.pe17_completeness_truth_proof,
        internal_static_chain_complete=False,
    )
    bad_pe26 = replace(
        integration_input.pe26_assembly_input,
        pe17_completeness_truth_proof=bad_assembly,
    )
    bad_proof = default_minimal_pe26_assembly_proof(bad_pe26)
    bad = replace(
        integration_input,
        pe26_assembly_input=bad_pe26,
        pe26_assembly_proof=bad_proof,
    )
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("PE-26 assembly evaluation failed" in r for r in result["fail_reasons"])


def test_negative_pe26_assembly_proof_flags_fail() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe26_assembly_proof,
        pe26_integration_pass=False,
        preflight_execution_readiness_assembly_complete=False,
    )
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe26_integration_pass must be true" in r for r in result["fail_reasons"])
    assert any(
        "preflight_execution_readiness_assembly_complete must be true" in r
        for r in result["fail_reasons"]
    )


def test_wrong_assembly_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.pe26_assembly_proof, assembly_result_digest="0" * 64)
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assembly_result_digest mismatch" in r for r in result["fail_reasons"])


def test_wrong_source_revision_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_private_readonly_lifecycle_integration(
        integration_input,
        expected_source_revision="0" * 40,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_missing_private_readonly_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.private_readonly_proof, private_readonly_proof_digest="")
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("private_readonly_proof_digest required" in r for r in result["fail_reasons"])


def test_wrong_private_readonly_owner_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.private_readonly_proof,
        private_readonly_owner="src/ops/wrong_private_readonly.py",
    )
    bad_proof = replace(
        bad_proof,
        private_readonly_proof_digest=compute_private_readonly_proof_digest(bad_proof),
    )
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("private_readonly_owner must be" in r for r in result["fail_reasons"])


def test_wrong_private_readonly_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.private_readonly_proof,
        private_readonly_proof_digest="0" * 64,
    )
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("private_readonly_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_not_read_only_capability_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(read_only_capability=False)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("read_only_capability must be true" in r for r in result["fail_reasons"])


def test_trading_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(trading_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("trading_capability must be false" in r for r in result["fail_reasons"])


def test_order_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(order_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("order_capability must be false" in r for r in result["fail_reasons"])


def test_cancel_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(cancel_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("cancel_capability must be false" in r for r in result["fail_reasons"])


def test_amend_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(amend_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("amend_capability must be false" in r for r in result["fail_reasons"])


def test_flatten_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(flatten_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("flatten_capability must be false" in r for r in result["fail_reasons"])


def test_transfer_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(transfer_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("transfer_capability must be false" in r for r in result["fail_reasons"])


def test_withdrawal_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(withdrawal_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("withdrawal_capability must be false" in r for r in result["fail_reasons"])


def test_deposit_capability_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(deposit_capability=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("deposit_capability must be false" in r for r in result["fail_reasons"])


def test_credential_material_present_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(credential_material_present=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("credential_material_present must be false" in r for r in result["fail_reasons"])


def test_network_used_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(network_used=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_used must be false" in r for r in result["fail_reasons"])


def test_exchange_api_called_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(exchange_api_called=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("exchange_api_called must be false" in r for r in result["fail_reasons"])


def test_account_state_queried_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(account_state_queried=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("account_state_queried must be false" in r for r in result["fail_reasons"])


def test_runtime_started_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(runtime_started=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("runtime_started must be false" in r for r in result["fail_reasons"])


def test_adapter_called_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(adapter_called=True)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_called must be false" in r for r in result["fail_reasons"])


def test_orders_created_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(orders_created=1)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_created must be 0" in r for r in result["fail_reasons"])


def test_orders_cancelled_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(orders_cancelled=1)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_cancelled must be 0" in r for r in result["fail_reasons"])


def test_orders_amended_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(orders_amended=1)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_amended must be 0" in r for r in result["fail_reasons"])


def test_positions_changed_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(positions_changed=1)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("positions_changed must be 0" in r for r in result["fail_reasons"])


def test_plan_only_not_proven_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = _private_readonly_with(plan_only=False, private_readonly_static_proven=False)
    bad = replace(integration_input, private_readonly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("plan_only must be true" in r for r in result["fail_reasons"])
    assert any("private_readonly_static_proven must be true" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_private_readonly_lifecycle_integration(
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
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"exchange_api_called_override": True},
        {"account_state_queried_override": True},
    ):
        result = evaluate_private_readonly_lifecycle_integration(integration_input, **kwargs)
        assert result["integration_pass"] is False
        assert result["private_readonly_lifecycle_eligibility"] is False


def test_unknown_lifecycle_state_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_private_readonly_lifecycle_integration(
        integration_input,
        unknown_lifecycle_state="not_a_real_phase",
    )
    assert result["integration_pass"] is False
    assert any("unknown lifecycle state" in r for r in result["fail_reasons"])


def test_wrong_pe26_assembly_owner_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.pe26_assembly_proof, assembly_owner="wrong.owner")
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assembly_owner must be" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_private_readonly_owner_matches_pe12_canonical_owner() -> None:
    assert PRIVATE_READONLY_OWNER == PHASE_CANONICAL_OWNERS[PHASE_PRIVATE_READONLY]
    assert PE26_ASSEMBLY_OWNER == PE26_CONTRACT_VERSION


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == "bounded_futures_testnet_private_readonly_lifecycle_integration.v0"
    assert PE11_CONTRACT_VERSION == "bounded_futures_private_readonly.v0"
    assert PRIVATE_READONLY_MODE == "private_readonly_reachability_only"


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.execution_authorized is False
    assert snapshot.live_authorized is False
    assert snapshot.zero_order_authorized is False
    assert snapshot.private_readonly_authorized is False
    assert snapshot.network_allowed is False
    assert snapshot.credentials_allowed is False
    assert snapshot.orders_allowed is False
    assert snapshot.scheduler_runtime_allowed is False
    assert snapshot.futures_only is True
    assert snapshot.bitcoin_direction_allowed is False


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_private_readonly_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_btc_placeholder_instrument_rejected() -> None:
    assembly = default_minimal_assembly_input(instrument="PF_XBTUSD")
    integration_input = default_minimal_integration_input(instrument="PF_XBTUSD")
    bad = replace(
        integration_input,
        pe26_assembly_input=assembly,
        pe26_assembly_proof=default_minimal_pe26_assembly_proof(assembly),
    )
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("forbidden orientation" in r for r in result["fail_reasons"])


def test_pe26_assembly_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    bad_assembly = replace(
        integration_input.pe26_assembly_input,
        source_revision="0" * 40,
    )
    bad_proof = default_minimal_pe26_assembly_proof(bad_assembly)
    bad = replace(
        integration_input,
        pe26_assembly_input=bad_assembly,
        pe26_assembly_proof=bad_proof,
    )
    result = evaluate_private_readonly_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def _private_readonly_with(**overrides: object) -> PrivateReadonlyProofBinding:
    base = default_minimal_private_readonly_proof()
    mutated = replace(base, **overrides)
    return replace(
        mutated, private_readonly_proof_digest=compute_private_readonly_proof_digest(mutated)
    )
