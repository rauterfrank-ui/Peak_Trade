"""Static + offline bounded Futures Testnet position/order reconciliation primary evidence integration (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
PE-21 static PE-12 reconciliation_review + PE-16 durable evidence binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration_contract_v0 import (
    AUTHORITY_LIFT,
    CLASSIFICATION_RECONCILED,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EXCHANGE_STATE_QUERIED,
    GLOBAL_RECONCILIATION_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_RECONCILIATION_EXECUTED,
    ORDER_STATE_QUERIED,
    PACKAGE_MARKER,
    POSITION_STATE_QUERIED,
    PRIMARY_EVIDENCE_PACKAGE_CREATED,
    PRIMARY_EVIDENCE_RUN_EXECUTED,
    PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION,
    ReconciliationPrimaryEvidenceIntegrationInput,
    ReconciliationStateBinding,
    AdapterLifecycleStateBinding,
    IntegrationSafetySnapshot,
    LifecycleMatrixProof,
    ManifestEntry,
    OrderRecord,
    OrderStateBinding,
    PositionStateBinding,
    PrimaryEvidenceBindingInput,
    REQUIRED_ARTIFACT_FILENAMES,
    TESTNET_RUN_STARTED,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_manifest_digest,
    compute_order_state_digest,
    compute_position_state_digest,
    compute_reconciliation_input_digest,
    default_minimal_integration_input,
    default_minimal_safety_snapshot,
    evaluate_position_order_reconciliation_primary_evidence_integration,
    evaluate_reconciliation_static,
    serialize_integration_input_canonical,
    validate_reconciliation_primary_evidence_integration_input,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_RECONCILIATION_REVIEW,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    FOLLOWUP_RUN_GATE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
    RECONCILIATION_OWNER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
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

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_POSITION_ORDER_RECONCILIATION_PRIMARY_EVIDENCE_INTEGRATION_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_POSITION_ORDER_RECONCILIATION_PRIMARY_EVIDENCE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
DURABLE_ARCHIVE_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in INTEGRATION_MODULE.read_text(encoding="utf-8")


def test_reconcile_and_primary_evidence_owners_referenced_not_duplicated() -> None:
    integration_text = INTEGRATION_MODULE.read_text(encoding="utf-8")
    assert "src.ops.recon.reconcile" in integration_text
    assert "scripts.ops.primary_evidence_retention_v0" in integration_text
    assert "bounded_futures_testnet_adapter_lifecycle_contract_v0" in integration_text
    assert RECONCILE_MODULE.exists()
    assert PRIMARY_EVIDENCE_MODULE.exists()
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert RECONCILIATION_OWNER == "src/ops/recon/reconcile.py"
    assert PRIMARY_EVIDENCE_OWNER == "scripts/ops/primary_evidence_retention_v0.py"


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATIVE_RECONCILIATION_EXECUTED is False
    assert PRIMARY_EVIDENCE_PACKAGE_CREATED is False
    assert PRIMARY_EVIDENCE_RUN_EXECUTED is False
    assert POSITION_STATE_QUERIED is False
    assert ORDER_STATE_QUERIED is False
    assert EXCHANGE_STATE_QUERIED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert AUTHORITY_LIFT is False
    assert GLOBAL_RECONCILIATION_READINESS is False


def test_deterministic_identical_inputs_same_payload_and_digest() -> None:
    left = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    right = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    assert serialize_integration_input_canonical(left) == serialize_integration_input_canonical(
        right
    )
    assert compute_integration_input_digest(left) == compute_integration_input_digest(right)
    left_result = evaluate_position_order_reconciliation_primary_evidence_integration(left)
    right_result = evaluate_position_order_reconciliation_primary_evidence_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]


def test_valid_position_order_lifecycle_reconciliation_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["reconciled"] is True
    assert result["reconciliation_classification"] == CLASSIFICATION_RECONCILED
    assert result["pe12_reconciliation_review_static_integration_proven"] is True
    assert result["integration_proof_digest"] == compute_integration_proof_digest(integration_input)
    assert result["fail_reasons"] == []


def test_valid_durable_primary_evidence_binding_passes() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    assert result["durable_primary_evidence_binding_proven"] is True
    binding = integration_input.primary_evidence_binding
    assert binding.manifest_verify_rc == 0
    assert set(binding.expected_artifact_filenames) == set(REQUIRED_ARTIFACT_FILENAMES)


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_position_order_reconciliation_primary_evidence_integration(
        default_minimal_integration_input()
    )
    assert result["integration_pass"] is True
    assert result["operative_reconciliation_executed"] is False
    assert result["primary_evidence_package_created"] is False
    assert result["primary_evidence_run_executed"] is False
    assert result["position_state_queried"] is False
    assert result["order_state_queried"] is False
    assert result["exchange_state_queried"] is False
    assert result["network_run_started"] is False
    assert result["testnet_run_started"] is False
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["global_reconciliation_readiness"] is False


def test_missing_position_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_position = replace(integration_input.position_state, snapshot_id="")
    bad = replace(integration_input, position_state=bad_position)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("position_state: snapshot_id required" in r for r in result["fail_reasons"])


def test_missing_order_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_order = replace(integration_input.order_state, snapshot_id="")
    bad = replace(integration_input, order_state=bad_order)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("order_state: snapshot_id required" in r for r in result["fail_reasons"])


def test_missing_lifecycle_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_lifecycle = replace(integration_input.adapter_lifecycle_state, state_id="")
    bad = replace(integration_input, adapter_lifecycle_state=bad_lifecycle)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_lifecycle_state: state_id required" in r for r in result["fail_reasons"])


def test_position_order_instrument_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_order = OrderRecord(
        order_id="offline-order-001",
        instrument="PF_SOLUSD",
        side="buy",
        quantity=1.0,
        status="open",
    )
    bad_order_state = OrderStateBinding(
        snapshot_id="order-snapshot-001",
        snapshot_digest="",
        orders=(bad_order,),
    )
    bad_order_state = replace(
        bad_order_state,
        snapshot_digest=compute_order_state_digest(bad_order_state),
    )
    bad = replace(integration_input, order_state=bad_order_state)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("instrument mismatch" in r for r in result["fail_reasons"])


def test_adapter_identity_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_lifecycle = replace(
        integration_input.adapter_lifecycle_state,
        adapter_id="other_adapter",
    )
    bad = replace(integration_input, adapter_lifecycle_state=bad_lifecycle)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("adapter_id mismatch" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(
        integration_input,
        expected_source_revision="0123456789abcdef0123456789abcdef0123456789",
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_incomplete_commit_sha_fails() -> None:
    integration_input = default_minimal_integration_input(source_revision="abc123")
    result = evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    assert result["integration_pass"] is False
    assert any("source_revision must be full 40-char" in r for r in result["fail_reasons"])


def test_unknown_contract_version_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_versions = replace(
        integration_input.contract_versions,
        integration="unknown.integration.v99",
    )
    bad = replace(integration_input, contract_versions=bad_versions)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("contract_versions: integration must be" in r for r in result["fail_reasons"])


def test_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_position = replace(integration_input.position_state, snapshot_digest="f" * 64)
    bad = replace(integration_input, position_state=bad_position)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("snapshot_digest mismatch" in r for r in result["fail_reasons"])


def test_duplicate_order_fails() -> None:
    integration_input = default_minimal_integration_input()
    order = integration_input.order_state.orders[0]
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_orders=(order, order),
        reconciled=True,
        classification=CLASSIFICATION_RECONCILED,
        duplicate_order_count=0,
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_orphaned_order_fails() -> None:
    integration_input = default_minimal_integration_input()
    extra = OrderRecord(
        order_id="orphan-001",
        instrument=GENERIC_FUTURES_INSTRUMENT,
        side="sell",
        quantity=2.0,
        status="open",
    )
    static = evaluate_reconciliation_static(
        expected_position=integration_input.position_state,
        observed_position=integration_input.position_state,
        expected_orders=integration_input.reconciliation_binding.expected_orders,
        observed_orders=(*integration_input.reconciliation_binding.expected_orders, extra),
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_orders=(*integration_input.reconciliation_binding.expected_orders, extra),
        input_digest=compute_reconciliation_input_digest(
            expected_position=integration_input.position_state,
            observed_position=integration_input.position_state,
            expected_orders=integration_input.reconciliation_binding.expected_orders,
            observed_orders=(*integration_input.reconciliation_binding.expected_orders, extra),
        ),
        result_digest=static["result_digest"],
        classification=static["classification"],
        reconciled=static["reconciled"],
        unresolved_count=static["unresolved_count"],
        mismatch_count=static["mismatch_count"],
        orphaned_order_count=static["orphaned_order_count"],
        duplicate_order_count=static["duplicate_order_count"],
        orphaned_position_count=static["orphaned_position_count"],
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("unresolved reconciliation" in r or "orphaned" in r for r in result["fail_reasons"])


def test_orphaned_position_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_observed = replace(integration_input.position_state, instrument="PF_SOLUSD")
    bad_observed = replace(
        bad_observed,
        snapshot_digest=compute_position_state_digest(bad_observed),
    )
    static = evaluate_reconciliation_static(
        expected_position=integration_input.position_state,
        observed_position=bad_observed,
        expected_orders=integration_input.reconciliation_binding.expected_orders,
        observed_orders=integration_input.reconciliation_binding.observed_orders,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_position=bad_observed,
        result_digest=static["result_digest"],
        classification=static["classification"],
        reconciled=static["reconciled"],
        unresolved_count=static["unresolved_count"],
        mismatch_count=static["mismatch_count"],
        orphaned_order_count=static["orphaned_order_count"],
        duplicate_order_count=static["duplicate_order_count"],
        orphaned_position_count=static["orphaned_position_count"],
        input_digest=compute_reconciliation_input_digest(
            expected_position=integration_input.position_state,
            observed_position=bad_observed,
            expected_orders=integration_input.reconciliation_binding.expected_orders,
            observed_orders=integration_input.reconciliation_binding.observed_orders,
        ),
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_contradictory_side_fails() -> None:
    integration_input = default_minimal_integration_input()
    order = integration_input.order_state.orders[0]
    bad_observed = replace(order, side="sell")
    static = evaluate_reconciliation_static(
        expected_position=integration_input.position_state,
        observed_position=integration_input.position_state,
        expected_orders=(order,),
        observed_orders=(bad_observed,),
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_orders=(bad_observed,),
        result_digest=static["result_digest"],
        classification=static["classification"],
        reconciled=static["reconciled"],
        unresolved_count=static["unresolved_count"],
        mismatch_count=static["mismatch_count"],
        orphaned_order_count=static["orphaned_order_count"],
        duplicate_order_count=static["duplicate_order_count"],
        orphaned_position_count=static["orphaned_position_count"],
        input_digest=compute_reconciliation_input_digest(
            expected_position=integration_input.position_state,
            observed_position=integration_input.position_state,
            expected_orders=(order,),
            observed_orders=(bad_observed,),
        ),
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_quantity_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    order = integration_input.order_state.orders[0]
    bad_observed = replace(order, quantity=99.0)
    static = evaluate_reconciliation_static(
        expected_position=integration_input.position_state,
        observed_position=integration_input.position_state,
        expected_orders=(order,),
        observed_orders=(bad_observed,),
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_orders=(bad_observed,),
        result_digest=static["result_digest"],
        classification=static["classification"],
        reconciled=static["reconciled"],
        unresolved_count=static["unresolved_count"],
        mismatch_count=static["mismatch_count"],
        orphaned_order_count=static["orphaned_order_count"],
        duplicate_order_count=static["duplicate_order_count"],
        orphaned_position_count=static["orphaned_position_count"],
        input_digest=compute_reconciliation_input_digest(
            expected_position=integration_input.position_state,
            observed_position=integration_input.position_state,
            expected_orders=(order,),
            observed_orders=(bad_observed,),
        ),
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_status_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    order = integration_input.order_state.orders[0]
    bad_observed = replace(order, status="closed")
    static = evaluate_reconciliation_static(
        expected_position=integration_input.position_state,
        observed_position=integration_input.position_state,
        expected_orders=(order,),
        observed_orders=(bad_observed,),
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    bad_recon = replace(
        integration_input.reconciliation_binding,
        observed_orders=(bad_observed,),
        result_digest=static["result_digest"],
        classification=static["classification"],
        reconciled=static["reconciled"],
        unresolved_count=static["unresolved_count"],
        mismatch_count=static["mismatch_count"],
        orphaned_order_count=static["orphaned_order_count"],
        duplicate_order_count=static["duplicate_order_count"],
        orphaned_position_count=static["orphaned_position_count"],
        input_digest=compute_reconciliation_input_digest(
            expected_position=integration_input.position_state,
            observed_position=integration_input.position_state,
            expected_orders=(order,),
            observed_orders=(bad_observed,),
        ),
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_unresolved_reconciliation_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_recon = replace(
        integration_input.reconciliation_binding,
        reconciled=False,
        classification="unresolved",
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False


def test_manipulated_reconciliation_classification_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_recon = replace(
        integration_input.reconciliation_binding,
        classification="reconciled",
        reconciled=True,
        result_digest="0" * 64,
    )
    bad = replace(integration_input, reconciliation_binding=bad_recon)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("result_digest mismatch" in r for r in result["fail_reasons"])


def test_boolean_reconciled_true_without_proof_chain_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_position_order_reconciliation_primary_evidence_integration(
        integration_input,
        reconciled_claim_without_proof_chain=True,
    )
    assert result["integration_pass"] is False
    assert result["pe12_reconciliation_review_static_integration_proven"] is False


def test_missing_primary_evidence_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        manifest_proof_identity="",
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_proof_identity required" in r for r in result["fail_reasons"])


def test_missing_required_artifact_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        expected_artifact_filenames=tuple(
            f for f in REQUIRED_ARTIFACT_FILENAMES if f != "PACKAGE_SUMMARY.md"
        ),
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("missing required artifact filenames" in r for r in result["fail_reasons"])


def test_manifest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        manifest_digest="0" * 64,
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_digest mismatch" in r for r in result["fail_reasons"])


def test_verify_rc_nonzero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(integration_input.primary_evidence_binding, manifest_verify_rc=1)
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("manifest_verify_rc must be 0" in r for r in result["fail_reasons"])


def test_tmp_only_evidence_target_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        durable_archive_root="/tmp/evidence",
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("/tmp" in r for r in result["fail_reasons"])


def test_traversal_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        archive_identity="../escape",
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("traversal" in r.lower() for r in result["fail_reasons"])


def test_root_escape_fails() -> None:
    integration_input = default_minimal_integration_input()
    entries = integration_input.primary_evidence_binding.manifest_entries
    bad_entries = tuple(
        ManifestEntry(digest=e.digest, relative_path="../escape.json") if i == 0 else e
        for i, e in enumerate(entries)
    )
    bad_binding = replace(
        integration_input.primary_evidence_binding,
        manifest_entries=bad_entries,
        manifest_digest=compute_manifest_digest(bad_entries),
        manifest_proof_identity=compute_manifest_digest(bad_entries),
    )
    bad = replace(integration_input, primary_evidence_binding=bad_binding)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("traversal" in r.lower() for r in result["fail_reasons"])


def test_safety_snapshot_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.safety_snapshot,
        followup_run_gate="AUTO_GO",
    )
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("followup_run_gate must be" in r for r in result["fail_reasons"])


def test_positive_network_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, network_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_execution_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, execution_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("execution_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_live_authority_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, live_authorized=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("live_authorized must be False" in r for r in result["fail_reasons"])


def test_positive_credential_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, credentials_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("credentials_allowed must be False" in r for r in result["fail_reasons"])


def test_positive_order_flag_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, orders_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_allowed must be False" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "instrument",
    ["BTC/EUR", "BTCUSDT", "PF_XBTUSD"],
)
def test_btc_xbt_spot_oriented_input_fails(instrument: str) -> None:
    integration_input = default_minimal_integration_input(instrument=instrument)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    assert result["integration_pass"] is False


def test_bitcoin_direction_allowed_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.safety_snapshot, bitcoin_direction_allowed=True)
    bad = replace(integration_input, safety_snapshot=bad_snapshot)
    result = evaluate_position_order_reconciliation_primary_evidence_integration(bad)
    assert result["integration_pass"] is False
    assert any("bitcoin_direction_allowed must be False" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_reconciliation_review_phase_required() -> None:
    integration_input = default_minimal_integration_input()
    assert (
        integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_RECONCILIATION_REVIEW
    )
    assert (
        integration_input.adapter_lifecycle_state.assigned_lifecycle_phase
        == PHASE_RECONCILIATION_REVIEW
    )


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_position_order_reconciliation_primary_evidence_integration.v0"
    )
    assert PE12_CONTRACT_VERSION == "bounded_futures_testnet_adapter_lifecycle.v0"
    assert PRIMARY_EVIDENCE_RETENTION_CONTRACT_VERSION == "primary_evidence_retention.v0"


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
    result = evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    assert result["integration_pass"] is True


def test_no_side_effects_from_evaluation() -> None:
    integration_input = default_minimal_integration_input()
    before = serialize_integration_input_canonical(integration_input)
    evaluate_position_order_reconciliation_primary_evidence_integration(integration_input)
    after = serialize_integration_input_canonical(integration_input)
    assert before == after
    assert validate_reconciliation_primary_evidence_integration_input(integration_input) == []
