"""Static + offline bounded Futures Testnet adapter capability lifecycle integration (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
GLB-012/013 static PE-8/9/10/11-to-PE-12 binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLB012_013_GLOBAL_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_ADAPTER_VALIDATION_EXECUTED,
    PACKAGE_MARKER,
    PE10_CONTRACT_VERSION,
    PE11_CONTRACT_VERSION,
    PE8_CONTRACT_VERSION,
    PE9_CONTRACT_VERSION,
    TESTNET_RUN_STARTED,
    CapabilityLifecycleIntegrationInput,
    CapabilityProofBinding,
    CapabilityProofsInput,
    ContractVersionsInput,
    IntegrationSafetySnapshot,
    LifecycleMatrixProof,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_okx_europe_adapter_lifecycle_slot_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_capability_lifecycle_integration,
    serialize_integration_input_canonical,
    serialize_integration_proof_canonical,
    validate_capability_lifecycle_integration_input,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_venue_binding_v0 import (
    OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
    VENUE_OKX_EUROPE,
)
from src.ops.okx_europe_adapter_lifecycle_contract_v0 import (
    CONTRACT_VERSION as OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION,
    PACKAGE_MARKER as OKX_EUROPE_LIFECYCLE_PACKAGE_MARKER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.py"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)
ADAPTER_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_contract_v0.py"
HARNESS_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_harness_contract_v0.py"
RUNTIME_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_runtime_harness_contract_v0.py"
)
PRIVATE_READONLY_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_private_readonly_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_ADAPTER_CAPABILITY_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in INTEGRATION_MODULE.read_text(encoding="utf-8")


def test_pe8_through_pe12_owners_referenced_not_duplicated() -> None:
    lifecycle_text = LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE12_PACKAGE_MARKER in lifecycle_text
    assert "bounded_futures_testnet_adapter_contract_v0" in lifecycle_text
    assert "bounded_futures_testnet_harness_contract_v0" in lifecycle_text
    assert "bounded_futures_testnet_runtime_harness_contract_v0" in lifecycle_text
    assert "bounded_futures_private_readonly_contract_v0" in lifecycle_text
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert "evaluate_pe_contract_composition" not in integration_text
    assert ADAPTER_MODULE.exists()
    assert HARNESS_MODULE.exists()
    assert RUNTIME_MODULE.exists()
    assert PRIVATE_READONLY_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_ADAPTER_VALIDATION_EXECUTED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert GLB012_013_GLOBAL_READINESS is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_capability_lifecycle_integration(left)
    right_result = evaluate_capability_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]


def test_valid_pe8_to_pe12_binding_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_capability_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["glb012_013_static_integration_proven"] is True
    assert result["integration_proof_digest"] == compute_integration_proof_digest(integration_input)
    assert result["fail_reasons"] == []
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["zero_order_authorized"] is False
    assert result["authority_lift"] is False
    assert result["glb012_013_global_readiness"] is False


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_capability_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["operative_adapter_validation_executed"] is False
    assert result["lifecycle_transition_executed"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["contract_implementation_only"] is True


def test_missing_capability_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proofs = CapabilityProofsInput(
        pe8_adapter_capability=CapabilityProofBinding(
            proof_digest="",
            proof_pass=True,
            adapter_id=integration_input.adapter_id,
            contract_version=PE8_CONTRACT_VERSION,
        ),
        pe9_capability_validation=integration_input.capability_proofs.pe9_capability_validation,
        pe10_execution_boundary=integration_input.capability_proofs.pe10_execution_boundary,
        pe11_lifecycle_safety_binding=integration_input.capability_proofs.pe11_lifecycle_safety_binding,
    )
    bad = replace(integration_input, capability_proofs=bad_proofs)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe8_adapter_capability: proof_digest required" in r for r in result["fail_reasons"])


def test_missing_lifecycle_matrix_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = LifecycleMatrixProof(
        pe12_contract_version=PE12_CONTRACT_VERSION,
        lifecycle_matrix_digest="",
        assigned_lifecycle_phase=PHASE_STATIC_PREFLIGHT,
        lifecycle_state_digest="e" * 64,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_matrix_digest required" in r for r in result["fail_reasons"])


def test_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        lifecycle_matrix_digest="f" * 64,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_matrix_digest mismatch" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_capability_lifecycle_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_incomplete_commit_sha_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision="abc123")
    result = evaluate_capability_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("source_revision must be full 40-char" in r for r in result["fail_reasons"])


def test_unknown_contract_version_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_versions = replace(
        integration_input.contract_versions,
        integration="unknown.integration.v99",
    )
    bad = replace(integration_input, contract_versions=bad_versions)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("contract_versions: integration must be" in r for r in result["fail_reasons"])


def test_adapter_identity_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe8 = replace(
        integration_input.capability_proofs.pe8_adapter_capability,
        adapter_id="other_adapter",
    )
    bad_proofs = replace(
        integration_input.capability_proofs,
        pe8_adapter_capability=bad_pe8,
    )
    bad = replace(integration_input, capability_proofs=bad_proofs)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_id mismatch" in r for r in result["fail_reasons"])


def test_capability_lifecycle_contradiction_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe9 = replace(
        integration_input.capability_proofs.pe9_capability_validation,
        proof_pass=False,
    )
    bad_proofs = replace(
        integration_input.capability_proofs,
        pe9_capability_validation=bad_pe9,
    )
    bad = replace(integration_input, capability_proofs=bad_proofs)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("proof_pass must be true" in r for r in result["fail_reasons"])


def test_unsupported_lifecycle_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase="unsupported_phase",
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("unsupported lifecycle phase" in r for r in result["fail_reasons"])


def test_positive_network_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, network_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_execution_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, execution_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("execution_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_live_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, live_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("live_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_credential_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, credentials_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("credentials_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_order_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, orders_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_allowed must be False" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "instrument",
    ["BTC/EUR", "BTCUSDT", "PF_XBTUSD"],
)
def test_btc_xbt_spot_oriented_input_fails(instrument: str) -> None:
    integration_input = default_minimal_integration_input(instrument=instrument)
    result = evaluate_capability_lifecycle_integration(integration_input)
    assert result["integration_pass"] is False


def test_bitcoin_direction_allowed_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, bitcoin_direction_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bitcoin_direction_allowed must be False" in r for r in result["fail_reasons"])


def test_safety_snapshot_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.safety_snapshot,
        followup_run_gate="AUTO_GO",
    )
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("followup_run_gate must be" in r for r in result["fail_reasons"])


def test_boolean_true_without_full_proof_chain_insufficient() -> None:
    integration_input = default_minimal_integration_input()
    bad_pe10 = replace(
        integration_input.capability_proofs.pe10_execution_boundary,
        proof_pass=False,
    )
    bad_proofs = replace(
        integration_input.capability_proofs,
        pe10_execution_boundary=bad_pe10,
    )
    bad = replace(integration_input, capability_proofs=bad_proofs)
    assert validate_capability_lifecycle_integration_input(bad)
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["glb012_013_static_integration_proven"] is False


def test_lifecycle_state_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_capability_lifecycle_integration(
        integration_input,
        expected_lifecycle_state_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("lifecycle_state_digest mismatch" in r for r in result["fail_reasons"])


def test_capability_proof_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_capability_lifecycle_integration(
        integration_input,
        expected_capability_proof_digests={"pe8_adapter_capability": "0" * 64},
    )
    assert result["integration_pass"] is False
    assert any("proof_digest mismatch" in r for r in result["fail_reasons"])


def test_zero_order_phase_requires_all_capability_proofs() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase=PHASE_ZERO_ORDER,
    )
    bad_pe11 = replace(
        integration_input.capability_proofs.pe11_lifecycle_safety_binding,
        proof_pass=False,
    )
    bad_proofs = replace(
        integration_input.capability_proofs,
        pe11_lifecycle_safety_binding=bad_pe11,
    )
    bad = replace(
        integration_input,
        lifecycle_matrix_proof=bad_matrix,
        capability_proofs=bad_proofs,
    )
    result = evaluate_capability_lifecycle_integration(bad)
    assert result["integration_pass"] is False


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_adapter_capability_lifecycle_integration.v0"
    )
    assert PE8_CONTRACT_VERSION == "bounded_futures_testnet_adapter.v0"
    assert PE9_CONTRACT_VERSION == "bounded_futures_testnet_harness.v0"
    assert PE10_CONTRACT_VERSION == "bounded_futures_testnet_runtime_harness.v0"
    assert PE11_CONTRACT_VERSION == "bounded_futures_private_readonly.v0"


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
    result = evaluate_capability_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_okx_europe_adapter_lifecycle_slot_digest_deterministic() -> None:
    left = compute_okx_europe_adapter_lifecycle_slot_digest()
    right = compute_okx_europe_adapter_lifecycle_slot_digest()
    assert left == right
    assert len(left) == 64
    assert left.islower()


def test_okx_europe_adapter_lifecycle_slot_digest_version_coherence() -> None:
    import hashlib
    import json

    expected = hashlib.sha256(
        json.dumps(
            {
                "hash_algorithm": "sha256",
                "okx_europe_lifecycle_contract_version": OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION,
                "okx_europe_lifecycle_package_marker": OKX_EUROPE_LIFECYCLE_PACKAGE_MARKER,
                "venue": VENUE_OKX_EUROPE,
                "venue_binding_lifecycle_contract_version": OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert compute_okx_europe_adapter_lifecycle_slot_digest() == expected
    assert OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION == OKX_EUROPE_ADAPTER_LIFECYCLE_CONTRACT_VERSION


def test_okx_europe_adapter_lifecycle_slot_digest_changes_on_version_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = compute_okx_europe_adapter_lifecycle_slot_digest()
    monkeypatch.setattr(
        "src.ops.bounded_futures_testnet_adapter_capability_lifecycle_integration_contract_v0.OKX_EUROPE_LIFECYCLE_CONTRACT_VERSION",
        "okx_europe_adapter_lifecycle.v0.drift",
    )
    drifted = compute_okx_europe_adapter_lifecycle_slot_digest()
    assert drifted != baseline


def test_pe12_lifecycle_matrix_digest_unaffected_by_okx_slot_digest() -> None:
    before = compute_lifecycle_matrix_digest()
    compute_okx_europe_adapter_lifecycle_slot_digest()
    after = compute_lifecycle_matrix_digest()
    assert before == after


def test_okx_europe_slot_digest_does_not_authorize_runtime() -> None:
    compute_okx_europe_adapter_lifecycle_slot_digest()
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_ADAPTER_VALIDATION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert GLB012_013_GLOBAL_READINESS is False
