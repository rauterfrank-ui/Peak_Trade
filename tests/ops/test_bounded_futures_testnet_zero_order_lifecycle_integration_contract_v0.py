"""Static + offline bounded Futures Testnet zero-order lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, harness execution, or Testnet start.
PE-27 static PE-26 assembly + harness zero-order proof binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    default_minimal_assembly_input,
)
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_HARNESS_SCRIPT_REL_PATH,
)
from src.ops.bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EXCHANGE_STATE_QUERIED,
    GLOBAL_ZERO_ORDER_LIFECYCLE_READINESS,
    HARNESS_MODE_ZERO_ORDER,
    HARNESS_OWNER,
    HARNESS_VERSION,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_ADAPTER_CALLED,
    OPERATIVE_HARNESS_EXECUTED,
    PE26_ASSEMBLY_OWNER,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    HarnessZeroOrderProofBinding,
    Pe26AssemblyProofBinding,
    compute_harness_proof_digest,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    default_minimal_harness_zero_order_proof,
    default_minimal_integration_input,
    default_minimal_pe26_assembly_proof,
    default_minimal_safety_snapshot,
    evaluate_zero_order_lifecycle_integration,
    serialize_harness_proof_canonical,
    serialize_integration_input_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_zero_order_lifecycle_integration_contract_v0.py"
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
RUNTIME_HARNESS_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_runtime_harness_contract_v0.py"
)
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "ops" / "archive_futures_testnet_harness_v0.py"
HARNESS_TEST = REPO_ROOT / "tests" / "ops" / "test_archive_futures_testnet_harness_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_ZERO_ORDER_LIFECYCLE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_ZERO_ORDER_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_ZERO_ORDER_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_pe26_and_harness_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert (
        "bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert "bounded_futures_testnet_runtime_harness_contract_v0" in integration_text
    assert "evaluate_phase_transition" not in integration_text
    assert "from scripts.ops import archive_futures_testnet_harness_v0" not in integration_text
    assert "import archive_futures_testnet_harness_v0" not in integration_text
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE26_MODULE.exists()
    assert RUNTIME_HARNESS_MODULE.exists()
    assert HARNESS_SCRIPT.is_file()
    assert HARNESS_TEST.is_file()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_ZERO_ORDER_LIFECYCLE_READINESS is False
    assert OPERATIVE_HARNESS_EXECUTED is False
    assert OPERATIVE_ADAPTER_CALLED is False
    assert EXCHANGE_STATE_QUERIED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False


def test_valid_pe26_assembly_plus_harness_proof_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_zero_order_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["zero_order_lifecycle_eligibility"] is True
    assert result["pe27_zero_order_lifecycle_static_integration_proven"] is True
    assert result["assigned_lifecycle_phase"] == PHASE_ZERO_ORDER
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_zero_order_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["zero_order_lifecycle_eligibility"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
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
    assert result["orders_created"] == 0
    assert result["cancels_created"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["global_zero_order_lifecycle_readiness"] is False
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
    left_result = evaluate_zero_order_lifecycle_integration(left)
    right_result = evaluate_zero_order_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        zero_order_lifecycle_eligibility=True,
    )


def test_harness_proof_digest_stability() -> None:
    left = default_minimal_harness_zero_order_proof()
    right = default_minimal_harness_zero_order_proof()
    assert serialize_harness_proof_canonical(left) == serialize_harness_proof_canonical(right)
    assert compute_harness_proof_digest(left) == compute_harness_proof_digest(right)


def test_lifecycle_phase_not_zero_order_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase=PHASE_STATIC_PREFLIGHT,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert result["zero_order_lifecycle_eligibility"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_missing_pe26_assembly_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.pe26_assembly_proof, assembly_input_digest="")
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_zero_order_lifecycle_integration(bad)
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
    result = evaluate_zero_order_lifecycle_integration(bad)
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
    result = evaluate_zero_order_lifecycle_integration(bad)
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
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assembly_result_digest mismatch" in r for r in result["fail_reasons"])


def test_wrong_source_revision_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_zero_order_lifecycle_integration(
        integration_input,
        expected_source_revision="0" * 40,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_missing_harness_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = replace(integration_input.harness_zero_order_proof, harness_proof_digest="")
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("harness_proof_digest required" in r for r in result["fail_reasons"])


def test_wrong_harness_owner_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = replace(
        integration_input.harness_zero_order_proof,
        harness_owner="scripts/ops/wrong_harness.py",
    )
    bad_harness = replace(
        bad_harness,
        harness_proof_digest=compute_harness_proof_digest(bad_harness),
    )
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("harness_owner must be" in r for r in result["fail_reasons"])


def test_harness_request_count_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(**{"request_count": 1})
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("request_count must be 0" in r for r in result["fail_reasons"])


def test_harness_orders_created_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(orders_created=1)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_created must be 0" in r for r in result["fail_reasons"])


def test_harness_cancel_count_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(cancel_count=1)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("cancel_count must be 0" in r for r in result["fail_reasons"])


def test_harness_position_mutation_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(position_mutation_count=1)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("position_mutation_count must be 0" in r for r in result["fail_reasons"])


def test_harness_network_used_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(network_used=True)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_used must be false" in r for r in result["fail_reasons"])


def test_harness_credentials_used_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(credentials_used=True)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("credentials_used must be false" in r for r in result["fail_reasons"])


def test_harness_runtime_started_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(runtime_started=True)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("runtime_started must be false" in r for r in result["fail_reasons"])


def test_harness_adapter_called_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(adapter_called=True)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_called must be false" in r for r in result["fail_reasons"])


def test_harness_exchange_state_queried_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(exchange_state_queried=True)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("exchange_state_queried must be false" in r for r in result["fail_reasons"])


def test_plan_only_not_proven_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_harness = _harness_with(plan_only=False, zero_order_plan_only_proven=False)
    bad = replace(integration_input, harness_zero_order_proof=bad_harness)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("plan_only must be true" in r for r in result["fail_reasons"])
    assert any("zero_order_plan_only_proven must be true" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_zero_order_lifecycle_integration(
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
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"exchange_state_queried_override": True},
    ):
        result = evaluate_zero_order_lifecycle_integration(integration_input, **kwargs)
        assert result["integration_pass"] is False
        assert result["zero_order_lifecycle_eligibility"] is False


def test_unknown_lifecycle_state_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_zero_order_lifecycle_integration(
        integration_input,
        unknown_lifecycle_state="not_a_real_phase",
    )
    assert result["integration_pass"] is False
    assert any("unknown lifecycle state" in r for r in result["fail_reasons"])


def test_wrong_pe26_assembly_owner_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(integration_input.pe26_assembly_proof, assembly_owner="wrong.owner")
    bad = replace(integration_input, pe26_assembly_proof=bad_proof)
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assembly_owner must be" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_harness_owner_matches_pe12_zero_order_canonical_owner() -> None:
    assert HARNESS_OWNER == ARCHIVE_HARNESS_SCRIPT_REL_PATH
    assert HARNESS_OWNER == PHASE_CANONICAL_OWNERS[PHASE_ZERO_ORDER]
    assert PE26_ASSEMBLY_OWNER == PE26_CONTRACT_VERSION


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == "bounded_futures_testnet_zero_order_lifecycle_integration.v0"
    assert HARNESS_VERSION == "archive_futures_testnet_harness_v0"
    assert HARNESS_MODE_ZERO_ORDER == "zero_order_reachability_only"


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


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_zero_order_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_btc_placeholder_instrument_rejected() -> None:
    assembly = default_minimal_assembly_input(instrument="PF_XBTUSD")
    integration_input = default_minimal_integration_input(instrument="PF_XBTUSD")
    bad = replace(
        integration_input,
        pe26_assembly_input=assembly,
        pe26_assembly_proof=default_minimal_pe26_assembly_proof(assembly),
    )
    result = evaluate_zero_order_lifecycle_integration(bad)
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
    result = evaluate_zero_order_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def _harness_with(**overrides: object) -> HarnessZeroOrderProofBinding:
    base = default_minimal_harness_zero_order_proof()
    mutated = replace(base, **overrides)
    return replace(mutated, harness_proof_digest=compute_harness_proof_digest(mutated))
