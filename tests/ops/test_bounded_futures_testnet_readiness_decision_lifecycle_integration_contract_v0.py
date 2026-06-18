"""Static + offline bounded Futures Testnet readiness-decision lifecycle integration (v0).

Docs/tests-only. No runtime, network, credentials, readiness decisions, or Testnet start.
PE-32 static PE-26..PE-31 chain + PE-25 operator-closure + blocker-register binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_CANONICAL_OWNERS,
    PHASE_READINESS_DECISION,
    PHASE_RECONCILIATION_REVIEW,
    PHASE_TINY_ORDER,
    PHASE_VALIDATE_ONLY,
    PHASE_PRIVATE_READONLY,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_pe25_integration_input,
)
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE26_CONTRACT_VERSION,
    default_minimal_assembly_input,
)
from src.ops.bounded_futures_testnet_private_readonly_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE28_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
    AUTHORITY_LIFT,
    BLOCKER_REGISTER_DOC_PATH,
    BLOCKER_REGISTER_OWNER,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    GLOBAL_READINESS_DECISION_LIFECYCLE_READINESS,
    LIFECYCLE_TRANSITION_EXECUTED,
    NETWORK_RUN_STARTED,
    OPERATIVE_BLOCKER_LIFT_EXECUTED,
    OPERATIVE_OPERATOR_CLOSURE_EXECUTED,
    OPERATIVE_OPERATOR_DECISION_CREATED,
    OPERATIVE_READINESS_DECISION_CREATED,
    PE25_INTEGRATION_OWNER,
    PE26_ASSEMBLY_OWNER,
    PE27_INTEGRATION_OWNER,
    PE28_INTEGRATION_OWNER,
    PE29_INTEGRATION_OWNER,
    PE30_INTEGRATION_OWNER,
    PE31_INTEGRATION_OWNER,
    READINESS_DECISION_MODE,
    READINESS_DECISION_OWNER,
    REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS,
    RUNTIME_STARTED,
    TESTNET_RUN_STARTED,
    BlockerRegisterSnapshotBinding,
    BlockerSnapshotEntry,
    Pe25OperatorClosureIntegrationProofBinding,
    Pe31ReconciliationReviewIntegrationProofBinding,
    ReadinessDecisionProofBinding,
    compute_blocker_register_snapshot_digest,
    compute_integration_input_digest,
    compute_integration_proof_digest,
    compute_lifecycle_matrix_digest,
    compute_readiness_decision_proof_digest,
    default_minimal_blocker_register_snapshot,
    default_minimal_integration_input,
    default_minimal_pe25_integration_proof,
    default_minimal_pe31_integration_proof,
    default_minimal_readiness_decision_proof,
    default_minimal_safety_snapshot,
    evaluate_readiness_decision_lifecycle_integration,
    serialize_integration_input_canonical,
    serialize_readiness_decision_proof_canonical,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE31_CONTRACT_VERSION,
    default_minimal_integration_input as default_minimal_pe31_integration_input,
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
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
)
from src.ops.bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge_contract_v0 import (
    CONTRACT_VERSION as PE39_CONTRACT_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0.py"
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
PE31_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0.py"
)
PE25_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py"
)
PE39_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge_contract_v0.py"
)
BLOCKER_REGISTER_MODULE = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
)
LIFECYCLE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_READINESS_DECISION_LIFECYCLE_INTEGRATION_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_READINESS_DECISION_LIFECYCLE_INTEGRATION_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
_PLACEHOLDER_DIGEST = "f" * 64


def _decision_proof_with(**kwargs: object) -> ReadinessDecisionProofBinding:
    base = default_minimal_readiness_decision_proof(
        pe25_closure_result_digest=_PLACEHOLDER_DIGEST,
        traceability_identity=_PLACEHOLDER_DIGEST,
    )
    updated = replace(base, **kwargs)
    if "readiness_decision_proof_digest" not in kwargs:
        updated = replace(
            updated,
            readiness_decision_proof_digest=compute_readiness_decision_proof_digest(updated),
        )
    return updated


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_READINESS_DECISION_LIFECYCLE_INTEGRATION_CONTRACT_V0=true"
        in INTEGRATION_MODULE.read_text(encoding="utf-8")
    )


def test_pe12_pe26_pe27_pe28_pe29_pe30_pe31_pe25_owners_referenced_not_duplicated() -> None:
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
        "bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0"
        in integration_text
    )
    assert (
        "bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge_contract_v0"
        in integration_text
    )
    assert "evaluate_phase_transition" not in integration_text
    assert "KrakenTestnetClient" not in integration_text
    assert "import subprocess" not in integration_text
    assert "open(" not in integration_text
    assert PE12_PACKAGE_MARKER in LIFECYCLE_MODULE.read_text(encoding="utf-8")
    assert PE26_MODULE.exists()
    assert PE27_MODULE.exists()
    assert PE28_MODULE.exists()
    assert PE29_MODULE.exists()
    assert PE30_MODULE.exists()
    assert PE31_MODULE.exists()
    assert PE25_MODULE.exists()
    assert PE39_MODULE.exists()
    assert BLOCKER_REGISTER_MODULE.exists()
    assert READINESS_DECISION_OWNER == PHASE_CANONICAL_OWNERS[PHASE_READINESS_DECISION]
    assert BLOCKER_REGISTER_OWNER == "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
    assert BLOCKER_REGISTER_DOC_PATH.endswith("MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md")


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert GLOBAL_READINESS_DECISION_LIFECYCLE_READINESS is False
    assert OPERATIVE_READINESS_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_DECISION_CREATED is False
    assert OPERATIVE_OPERATOR_CLOSURE_EXECUTED is False
    assert OPERATIVE_BLOCKER_LIFT_EXECUTED is False
    assert LIFECYCLE_TRANSITION_EXECUTED is False
    assert NETWORK_RUN_STARTED is False
    assert TESTNET_RUN_STARTED is False
    assert RUNTIME_STARTED is False
    assert AUTHORITY_LIFT is False


def test_valid_full_chain_passes() -> None:
    integration_input = default_minimal_integration_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_readiness_decision_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["readiness_decision_lifecycle_eligibility_for_separate_operator_review"] is True
    assert result["pe32_readiness_decision_lifecycle_static_integration_proven"] is True
    assert result["pe32_readiness_decision_lifecycle_bound"] is True
    assert result["pe39_admission_presentation_operator_closure_bridge_bound"] is True
    assert result["admission_presentation_lifecycle_bound"] is True
    assert result["pe25_operator_closure_bound"] is True
    assert result["pe34_handoff_bound"] is True
    assert result["pe35_staleness_revocation_recovery_bound"] is True
    assert result["pe36_admission_presentation_bound"] is True
    assert result["pe37_durable_traceability_bound"] is True
    assert result["pe12_readiness_decision_static_integration_proven"] is True
    assert result["static_pe12_lifecycle_chain_complete"] is True
    assert result["assigned_lifecycle_phase"] == PHASE_READINESS_DECISION
    assert result["fail_reasons"] == []


def test_valid_static_proof_remains_non_authorizing() -> None:
    result = evaluate_readiness_decision_lifecycle_integration(default_minimal_integration_input())
    assert result["integration_pass"] is True
    assert result["readiness_decision_lifecycle_eligibility_for_separate_operator_review"] is True
    assert result["contract_implementation_only"] is True
    assert result["authority_lift"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["global_blocker_lift_authorized"] is False
    assert result["preflight_lift_authorized"] is False
    assert result["ready_for_operator_arming"] is False
    assert result["readiness_decision_authorized"] is False
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
    assert result["global_readiness_decision_lifecycle_readiness"] is False
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
    left_result = evaluate_readiness_decision_lifecycle_integration(left)
    right_result = evaluate_readiness_decision_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] == right_result["integration_proof_digest"]
    assert left_result["integration_proof_digest"] == compute_integration_proof_digest(
        left,
        readiness_decision_lifecycle_eligibility_for_separate_operator_review=True,
    )


def test_readiness_decision_proof_digest_stability() -> None:
    left = default_minimal_readiness_decision_proof(
        pe25_closure_result_digest=_PLACEHOLDER_DIGEST,
        traceability_identity=_PLACEHOLDER_DIGEST,
    )
    right = default_minimal_readiness_decision_proof(
        pe25_closure_result_digest=_PLACEHOLDER_DIGEST,
        traceability_identity=_PLACEHOLDER_DIGEST,
    )
    assert serialize_readiness_decision_proof_canonical(left) == (
        serialize_readiness_decision_proof_canonical(right)
    )
    assert compute_readiness_decision_proof_digest(left) == (
        compute_readiness_decision_proof_digest(right)
    )


def test_lifecycle_phase_not_readiness_decision_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_matrix = replace(
        integration_input.lifecycle_matrix_proof,
        assigned_lifecycle_phase=PHASE_RECONCILIATION_REVIEW,
    )
    bad = replace(integration_input, lifecycle_matrix_proof=bad_matrix)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("assigned_lifecycle_phase must be" in r for r in result["fail_reasons"])


def test_skipped_lifecycle_sequence_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_before = replace(
        integration_input.lifecycle_state_before,
        assigned_lifecycle_phase=PHASE_TINY_ORDER,
    )
    bad = replace(integration_input, lifecycle_state_before=bad_before)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("lifecycle_state_before" in r for r in result["fail_reasons"])


def test_missing_pe31_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe31_reconciliation_review_integration_proof,
        integration_proof_digest="",
    )
    bad = replace(integration_input, pe31_reconciliation_review_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest required" in r for r in result["fail_reasons"])


def test_negative_pe31_integration_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe31_reconciliation_review_integration_proof,
        pe31_integration_pass=False,
        reconciliation_review_lifecycle_eligibility=False,
    )
    bad = replace(integration_input, pe31_reconciliation_review_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe31_integration_pass must be true" in r for r in result["fail_reasons"])


def test_wrong_pe31_integration_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe31_reconciliation_review_integration_proof,
        integration_proof_digest="0" * 64,
    )
    bad = replace(integration_input, pe31_reconciliation_review_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_missing_pe25_closure_result_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe25_operator_closure_integration_proof,
        closure_result_digest="",
    )
    bad = replace(integration_input, pe25_operator_closure_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("closure_result_digest required" in r for r in result["fail_reasons"])


def test_negative_pe25_integration_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe25_operator_closure_integration_proof,
        pe25_integration_pass=False,
        operator_closure_static_complete=False,
    )
    bad = replace(integration_input, pe25_operator_closure_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe25_integration_pass must be true" in r for r in result["fail_reasons"])


def test_wrong_pe25_closure_result_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe25_operator_closure_integration_proof,
        closure_result_digest="0" * 64,
    )
    bad = replace(integration_input, pe25_operator_closure_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("closure_result_digest mismatch" in r for r in result["fail_reasons"])


def test_blocker_register_owner_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.blocker_register_snapshot,
        blocker_register_owner="wrong.owner",
    )
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("blocker_register_owner must be" in r for r in result["fail_reasons"])


def test_blocker_register_digest_mismatch_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(
        integration_input.blocker_register_snapshot,
        blocker_register_digest="0" * 64,
    )
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("blocker_register_digest mismatch" in r for r in result["fail_reasons"])


def test_missing_blocker_snapshot_entries_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_snapshot = replace(integration_input.blocker_register_snapshot, entries=())
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("entries required" in r for r in result["fail_reasons"])


def test_incomplete_blocker_snapshot_fails() -> None:
    integration_input = default_minimal_integration_input()
    partial_entries = integration_input.blocker_register_snapshot.entries[:3]
    bad_snapshot = replace(
        integration_input.blocker_register_snapshot,
        entries=partial_entries,
    )
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("missing required blocker ids" in r for r in result["fail_reasons"])


def test_unknown_blocker_id_fails() -> None:
    integration_input = default_minimal_integration_input()
    entries = list(integration_input.blocker_register_snapshot.entries) + [
        BlockerSnapshotEntry(
            blocker_id="GLB-999",
            blocker_state="BLOCKED",
            state_verified=True,
            lift_authorized=False,
            lift_proof_digest="",
        )
    ]
    bad_snapshot = replace(integration_input.blocker_register_snapshot, entries=tuple(entries))
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("unknown blocker ids" in r for r in result["fail_reasons"])


def test_unverified_blocker_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    entries = list(integration_input.blocker_register_snapshot.entries)
    entries[0] = replace(entries[0], state_verified=False)
    bad_snapshot = replace(integration_input.blocker_register_snapshot, entries=tuple(entries))
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("state_verified must be true" in r for r in result["fail_reasons"])


def test_open_blocker_without_evidence_fails_via_closed_state() -> None:
    integration_input = default_minimal_integration_input()
    entries = list(integration_input.blocker_register_snapshot.entries)
    entries[0] = replace(entries[0], blocker_state="CLOSED")
    bad_snapshot = replace(integration_input.blocker_register_snapshot, entries=tuple(entries))
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "not allowed for eligibility" in r or "lifted state" in r for r in result["fail_reasons"]
    )


def test_claimed_blocker_lift_without_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    entries = list(integration_input.blocker_register_snapshot.entries)
    entries[0] = replace(entries[0], lift_authorized=True, lift_proof_digest="0" * 64)
    bad_snapshot = replace(
        integration_input.blocker_register_snapshot,
        entries=tuple(entries),
        global_blocker_lift_authorized=True,
    )
    bad = replace(integration_input, blocker_register_snapshot=bad_snapshot)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "lift_authorized must be false" in r or "global_blocker_lift_authorized" in r
        for r in result["fail_reasons"]
    )


def test_wrong_source_revision_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        expected_source_revision="0" * 40,
    )
    assert result["integration_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_dirty_source_state_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        dirty_source_state=True,
    )
    assert result["integration_pass"] is False
    assert any("dirty_source_state=true is not allowed" in r for r in result["fail_reasons"])


def test_loose_boolean_eligibility_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        loose_boolean_eligibility=True,
    )
    assert result["integration_pass"] is False
    assert any("loose_boolean_eligibility" in r for r in result["fail_reasons"])


def test_loose_authority_booleans_rejected() -> None:
    integration_input = default_minimal_integration_input()
    for kwargs in (
        {"readiness_decision_authorized": True},
        {"operator_decision_authorized": True},
        {"operator_closure_authorized": True},
        {"global_blocker_lift_authorized": True},
        {"preflight_lift_authorized": True},
        {"execution_authorized": True},
        {"live_authorized": True},
        {"zero_order_authorized": True},
        {"private_readonly_authorized": True},
        {"validate_only_authorized": True},
        {"tiny_order_authorized": True},
        {"reconciliation_authorized": True},
        {"evidence_acceptance_authorized": True},
        {"pilot_start_authorized": True},
        {"promotion_authorized": True},
        {"network_allowed": True},
        {"credentials_allowed": True},
        {"orders_allowed": True},
        {"runtime_started": True},
        {"adapter_called": True},
        {"exchange_api_called_override": True},
        {"account_state_queried_override": True},
        {"new_evidence_generation": True},
        {"existing_evidence_mutation": True},
        {"claimed_blocker_lift_without_proof": True},
        {"operator_name_implies_decision": True},
    ):
        result = evaluate_readiness_decision_lifecycle_integration(integration_input, **kwargs)
        assert result["integration_pass"] is False
        assert (
            result["readiness_decision_lifecycle_eligibility_for_separate_operator_review"] is False
        )


def test_operator_name_without_decision_proof_does_not_authorize() -> None:
    integration_input = default_minimal_integration_input(operator_name="Frank Rauter")
    result = evaluate_readiness_decision_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True
    assert result["readiness_decision_authorized"] is False
    assert result["operator_decision_authorized"] is False


def test_pe31_alone_does_not_create_readiness_decision() -> None:
    pe31_input = default_minimal_pe31_integration_input()
    pe31_result = evaluate_readiness_decision_lifecycle_integration(
        replace(
            default_minimal_integration_input(),
            pe31_reconciliation_review_integration_input=pe31_input,
            pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
                pe31_input
            ),
        )
    )
    assert pe31_result["readiness_decision_authorized"] is False


def test_unknown_lifecycle_state_rejected() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        unknown_lifecycle_state="not_a_real_phase",
    )
    assert result["integration_pass"] is False
    assert any("unknown lifecycle state" in r for r in result["fail_reasons"])


def test_network_used_true_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        readiness_decision_proof=_decision_proof_with(network_used=True),
    )
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("network_used must be false" in r for r in result["fail_reasons"])


def test_orders_created_gt_zero_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        readiness_decision_proof=_decision_proof_with(orders_created=1),
    )
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("orders_created must be 0" in r for r in result["fail_reasons"])


def test_lifecycle_matrix_digest_matches_pe12_canonical_identity() -> None:
    digest = compute_lifecycle_matrix_digest()
    assert len(digest) == 64
    integration_input = default_minimal_integration_input()
    assert integration_input.lifecycle_matrix_proof.lifecycle_matrix_digest == digest


def test_readiness_decision_owner_matches_pe12_canonical_owner() -> None:
    assert READINESS_DECISION_OWNER == PHASE_CANONICAL_OWNERS[PHASE_READINESS_DECISION]
    assert PE26_ASSEMBLY_OWNER == PE26_CONTRACT_VERSION
    assert PE27_INTEGRATION_OWNER == PE27_CONTRACT_VERSION
    assert PE28_INTEGRATION_OWNER == PE28_CONTRACT_VERSION
    assert PE29_INTEGRATION_OWNER == PE29_CONTRACT_VERSION
    assert PE30_INTEGRATION_OWNER == PE30_CONTRACT_VERSION
    assert PE31_INTEGRATION_OWNER == PE31_CONTRACT_VERSION
    assert PE25_INTEGRATION_OWNER == PE25_CONTRACT_VERSION


def test_contract_version_constants() -> None:
    assert CONTRACT_VERSION == (
        "bounded_futures_testnet_readiness_decision_lifecycle_integration.v0"
    )
    assert READINESS_DECISION_MODE == "static_readiness_decision_eligibility_proof_only"
    assert len(REQUIRED_BOUNDED_FUTURES_READINESS_BLOCKER_IDS) >= 10


def test_default_safety_snapshot_matches_required_invariants() -> None:
    snapshot = default_minimal_safety_snapshot()
    assert snapshot.preflight_remains_blocked is True
    assert snapshot.global_blocker_lift_authorized is False
    assert snapshot.preflight_lift_authorized is False
    assert snapshot.ready_for_operator_arming is False
    assert snapshot.readiness_decision_authorized is False
    assert snapshot.operator_decision_authorized is False
    assert snapshot.operator_closure_authorized is False
    assert snapshot.futures_only is True
    assert snapshot.bitcoin_direction_allowed is False


def test_generic_futures_instrument_passes() -> None:
    integration_input = default_minimal_integration_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_readiness_decision_lifecycle_integration(integration_input)
    assert result["integration_pass"] is True


def test_btc_placeholder_instrument_rejected() -> None:
    assembly = default_minimal_assembly_input(instrument="PF_XBTUSD")
    integration_input = default_minimal_integration_input()
    bad_pe30 = replace(
        integration_input.pe31_reconciliation_review_integration_input.pe30_tiny_order_integration_input,
        pe26_assembly_input=assembly,
        instrument="PF_XBTUSD",
    )
    bad_pe31 = replace(
        integration_input.pe31_reconciliation_review_integration_input,
        pe30_tiny_order_integration_input=bad_pe30,
        instrument="PF_XBTUSD",
    )
    bad = replace(
        integration_input,
        instrument="PF_XBTUSD",
        pe31_reconciliation_review_integration_input=bad_pe31,
        pe31_reconciliation_review_integration_proof=default_minimal_pe31_integration_proof(
            bad_pe31
        ),
    )
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("forbidden orientation" in r for r in result["fail_reasons"])


def test_input_mutation_changes_digest() -> None:
    left = default_minimal_integration_input()
    right = replace(left, integration_id="mutated-integration-id")
    assert compute_integration_input_digest(left) != compute_integration_input_digest(right)
    left_result = evaluate_readiness_decision_lifecycle_integration(left)
    right_result = evaluate_readiness_decision_lifecycle_integration(right)
    assert left_result["integration_proof_digest"] != right_result["integration_proof_digest"]


def test_embedded_lifecycle_phases_in_canonical_order() -> None:
    integration_input = default_minimal_integration_input()
    pe31 = integration_input.pe31_reconciliation_review_integration_input
    pe30 = pe31.pe30_tiny_order_integration_input
    assert (
        pe30.pe27_zero_order_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_ZERO_ORDER
    )
    assert (
        pe30.pe28_private_readonly_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_PRIVATE_READONLY
    )
    assert (
        pe30.pe29_validate_only_integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase
        == PHASE_VALIDATE_ONLY
    )
    assert pe30.lifecycle_matrix_proof.assigned_lifecycle_phase == PHASE_TINY_ORDER
    assert pe31.lifecycle_matrix_proof.assigned_lifecycle_phase == PHASE_RECONCILIATION_REVIEW
    assert integration_input.lifecycle_matrix_proof.assigned_lifecycle_phase == (
        PHASE_READINESS_DECISION
    )


def test_blocker_snapshot_digest_stable_for_default_fixture() -> None:
    left = default_minimal_blocker_register_snapshot()
    right = default_minimal_blocker_register_snapshot()
    assert compute_blocker_register_snapshot_digest(
        left
    ) == compute_blocker_register_snapshot_digest(right)


def test_missing_pe39_bridge_proof_digest_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        bridge_proof_digest="",
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bridge_proof_digest required" in r for r in result["fail_reasons"])


def test_missing_pe39_admission_presentation_lifecycle_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        admission_presentation_lifecycle_bound=False,
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any(
        "admission_presentation_lifecycle_bound must be True" in r for r in result["fail_reasons"]
    )


def test_missing_pe34_pe35_pe36_pe37_binding_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        pe37_durable_traceability_bound=False,
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe37_durable_traceability_bound must be True" in r for r in result["fail_reasons"])


def test_pe39_owner_identity_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe39_bridge_integration_proof,
        bridge_owner="wrong.owner.v0",
    )
    bad = replace(integration_input, pe39_bridge_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("bridge_owner must be" in r for r in result["fail_reasons"])


def test_pe39_proof_digest_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        expected_pe39_bridge_proof_digest="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("bridge_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_traceability_identity_drift_fails() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        expected_shared_pe37_traceability_identity="0" * 64,
    )
    assert result["integration_pass"] is False
    assert any("shared_pe37_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_closure_references_wrong_pe39_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad_proof = replace(
        integration_input.pe25_operator_closure_integration_proof,
        pe39_bridge_proof_digest="0" * 64,
    )
    bad = replace(integration_input, pe25_operator_closure_integration_proof=bad_proof)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe39_bridge_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_readiness_decision_references_wrong_closure_proof_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(
        integration_input,
        readiness_decision_proof=_decision_proof_with(pe25_closure_result_digest="0" * 64),
    )
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("pe25_closure_result_digest mismatch" in r for r in result["fail_reasons"])


def test_stale_handoff_fails() -> None:
    integration_input = default_minimal_integration_input()
    broken_pe35 = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_admission = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input,
        pe35_boundary_input=broken_pe35,
    )
    broken_bridge = replace(
        integration_input.pe39_bridge_integration_input,
        admission_presentation_integration_input=broken_admission,
    )
    bad = replace(integration_input, pe39_bridge_integration_input=broken_bridge)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False


def test_revoked_handoff_fails() -> None:
    integration_input = default_minimal_integration_input()
    broken_pe35 = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    broken_admission = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input,
        pe35_boundary_input=broken_pe35,
    )
    broken_bridge = replace(
        integration_input.pe39_bridge_integration_input,
        admission_presentation_integration_input=broken_admission,
    )
    bad = replace(integration_input, pe39_bridge_integration_input=broken_bridge)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False


def test_superseded_handoff_fails() -> None:
    integration_input = default_minimal_integration_input()
    broken_pe35 = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            integration_input.pe39_bridge_integration_input.admission_presentation_integration_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    broken_admission = replace(
        integration_input.pe39_bridge_integration_input.admission_presentation_integration_input,
        pe35_boundary_input=broken_pe35,
    )
    broken_bridge = replace(
        integration_input.pe39_bridge_integration_input,
        admission_presentation_integration_input=broken_admission,
    )
    bad = replace(integration_input, pe39_bridge_integration_input=broken_bridge)
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False


def test_empty_integration_id_fails() -> None:
    integration_input = default_minimal_integration_input()
    bad = replace(integration_input, integration_id="")
    result = evaluate_readiness_decision_lifecycle_integration(bad)
    assert result["integration_pass"] is False
    assert any("integration_id required" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    integration_input = default_minimal_integration_input()
    result = evaluate_readiness_decision_lifecycle_integration(
        integration_input,
        extra_fields={"unexpected_field": "value"},
    )
    assert result["integration_pass"] is False
    assert any("unknown extra field" in r for r in result["fail_reasons"])


def test_pe39_upstream_bridge_still_passes_independently() -> None:
    from src.ops.bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge_contract_v0 import (
        default_minimal_bridge_input,
        evaluate_admission_presentation_operator_closure_lifecycle_bridge,
    )

    bridge_input = default_minimal_bridge_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_admission_presentation_operator_closure_lifecycle_bridge(bridge_input)
    assert result["bridge_pass"] is True


def test_pe25_upstream_still_passes_independently() -> None:
    from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
        default_minimal_integration_input as default_minimal_pe25_input,
        evaluate_operator_closure_lifecycle_integration,
    )

    pe25_input = default_minimal_pe25_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    result = evaluate_operator_closure_lifecycle_integration(pe25_input)
    assert result["integration_pass"] is True


def test_pe39_canonical_owner_matches_expected() -> None:
    assert PE39_CONTRACT_VERSION == (
        "bounded_futures_testnet_admission_presentation_operator_closure_lifecycle_bridge.v0"
    )
