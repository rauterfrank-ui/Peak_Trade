"""Static + offline bounded Futures Testnet handoff staleness/revocation/recovery boundary (v0).

Docs/tests-only. No runtime, network, credentials, operator review, or Testnet start.
PE-35 negative guard over PE-34 handoff boundary only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    HANDOFF_STATE_CURRENT,
    HANDOFF_STATE_RECOVERED,
    HANDOFF_STATE_RECOVERY_REQUIRED,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
    INVALIDATION_REASON_REVOKED,
    INVALIDATION_REASON_STALE,
    INVALIDATION_REASON_SUPERSEDED,
    CanonicalCurrentBindings,
    HandoffLifecycleMetadata,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    RecoveryProofBinding,
    REVOCATION_EXECUTED,
    RECOVERY_EXECUTED,
    RevocationProofBinding,
    SECOND_ASSEMBLY_CREATED,
    SECOND_HANDOFF_SURFACE_CREATED,
    SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
    SECOND_READINESS_SURFACE_CREATED,
    SupersessionLink,
    compute_boundary_input_digest,
    compute_boundary_result_digest,
    default_minimal_boundary_input,
    evaluate_handoff_staleness_revocation_recovery_boundary,
    serialize_boundary_input_canonical,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    CONTRACT_VERSION as PE34_CONTRACT_VERSION,
    Pe20UndecidedPackageEligibilityBinding,
    Pe25CrossSliceClosureBinding,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
    default_minimal_handoff_boundary_input,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    compute_review_input_digest,
    default_minimal_operator_review_input,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE = (
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
PE25_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0.py"
)
PE33_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0.py"
)
PE34_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_HANDOFF_STALENESS_REVOCATION_RECOVERY_BOUNDARY_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_HANDOFF_STALENESS_REVOCATION_RECOVERY_BOUNDARY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
REVIEW_IDENTITY = "glb-016-bounded-futures-testnet-operator-review"


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
    assert result["zero_order_authorized"] is False
    assert result["private_readonly_authorized"] is False
    assert result["validate_only_authorized"] is False
    assert result["tiny_order_authorized"] is False
    assert result["reconciliation_authorized"] is False
    assert result["evidence_acceptance_authorized"] is False
    assert result["pilot_start_authorized"] is False
    assert result["promotion_authorized"] is False
    assert result["live_authorized"] is False
    assert result["network_used"] is False
    assert result["credentials_used"] is False
    assert result["exchange_api_called"] is False
    assert result["exchange_request_count"] == 0
    assert result["orders_created"] == 0
    assert result["orders_cancelled"] == 0
    assert result["orders_amended"] == 0
    assert result["positions_changed"] == 0
    assert result["adapter_called"] is False
    assert result["testnet_started"] is False
    assert result["runtime_started"] is False
    assert result["harness_started"] is False
    assert result["subprocess_started"] is False
    assert result["account_state_queried"] is False


def _valid_boundary_input(
    source_revision: str = VALID_COMMIT_SHA,
) -> HandoffStalenessRevocationRecoveryBoundaryInput:
    return default_minimal_boundary_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
        review_identity=REVIEW_IDENTITY,
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_HANDOFF_STALENESS_REVOCATION_RECOVERY_BOUNDARY_CONTRACT_V0=true"
        in BOUNDARY_MODULE.read_text(encoding="utf-8")
    )


def test_pe19_pe20_pe25_pe33_pe34_owners_referenced_not_duplicated() -> None:
    boundary_text = BOUNDARY_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0" in boundary_text
    assert "evaluate_operator_review_handoff_boundary" in boundary_text
    assert "evaluate_operator_review(" not in boundary_text
    assert "evaluate_operator_closure_lifecycle_integration" not in boundary_text
    assert "persist_operator_review_proof_package" not in boundary_text
    assert "import subprocess" not in boundary_text
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE25_MODULE.exists()
    assert PE33_MODULE.exists()
    assert PE34_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert REVOCATION_EXECUTED is False
    assert RECOVERY_EXECUTED is False
    assert SECOND_ASSEMBLY_CREATED is False
    assert SECOND_READINESS_SURFACE_CREATED is False
    assert SECOND_OPERATOR_REVIEW_SURFACE_CREATED is False
    assert SECOND_HANDOFF_SURFACE_CREATED is False
    assert AUTHORITY_LIFT is False


def test_valid_current_handoff_passes() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_handoff_staleness_revocation_recovery_boundary(boundary_input)
    assert result["boundary_pass"] is True
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True
    assert result["handoff_current"] is True
    assert result["handoff_stale"] is False
    assert result["handoff_superseded"] is False
    assert result["handoff_revoked"] is False
    assert result["recovery_required"] is False
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_missing_pe34_handoff_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe34 = replace(
        boundary_input.pe34_handoff,
        handoff_id="",
        adapter_id="",
    )
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is False


def test_negative_pe34_handoff_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe34_handoff.pe33_coherence_proof,
        integration_pass=False,
    )
    broken_pe34 = replace(boundary_input.pe34_handoff, pe33_coherence_proof=broken_proof)
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_wrong_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_canonical = replace(
        boundary_input.canonical_current,
        pe34_handoff_digest="0" * 64,
    )
    broken = replace(boundary_input, canonical_current=broken_canonical)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("pe34_handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_old_source_revision_fails_closed() -> None:
    boundary_input = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    broken_pe34 = replace(boundary_input.pe34_handoff, source_revision=ALT_COMMIT_SHA)
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("source_revision" in r for r in result["fail_reasons"])


def test_divergent_source_revision_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_canonical = replace(
        boundary_input.canonical_current,
        source_revision=ALT_COMMIT_SHA,
    )
    broken = replace(boundary_input, canonical_current=broken_canonical)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


@pytest.mark.parametrize("bad_revision", ["", "abc", "A" * 40, "g" * 40])
def test_invalid_source_revision_fails_closed(bad_revision: str) -> None:
    boundary_input = _valid_boundary_input()
    broken_canonical = replace(
        boundary_input.canonical_current,
        source_revision=bad_revision,
    )
    broken = replace(boundary_input, canonical_current=broken_canonical)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_stale_pe33_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_canonical = replace(
        boundary_input.canonical_current,
        pe33_integration_proof_digest="1" * 64,
    )
    broken = replace(boundary_input, canonical_current=broken_canonical)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("pe33_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_changed_pe19_without_new_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    new_review = default_minimal_operator_review_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest="9" * 64,
        input_capture_digest="b" * 64,
        replay_manifest_digest="c" * 64,
        archive_identity="d" * 64,
        archive_manifest_digest="e" * 64,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
        source_state_digest="f" * 64,
    )
    broken_pe19 = replace(
        boundary_input.pe34_handoff.pe19_undecided_review_input,
        review_input=new_review,
    )
    broken_pe34 = replace(boundary_input.pe34_handoff, pe19_undecided_review_input=broken_pe19)
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("handoff_digest mismatch" in r for r in result["fail_reasons"])


def test_changed_pe20_without_new_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe34_handoff.pe20_undecided_package_eligibility,
        review_input_digest="0" * 64,
    )
    broken_pe34 = replace(
        boundary_input.pe34_handoff,
        pe20_undecided_package_eligibility=broken_pe20,
    )
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_changed_pe25_without_new_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe25 = replace(
        boundary_input.pe34_handoff.pe25_cross_slice_closure,
        closure_result_digest="0" * 64,
        pe33_pe25_slot_digest="0" * 64,
    )
    broken_pe34 = replace(boundary_input.pe34_handoff, pe25_cross_slice_closure=broken_pe25)
    broken = replace(boundary_input, pe34_handoff=broken_pe34)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_explicit_stale_state_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_lifecycle = replace(
        boundary_input.lifecycle_metadata,
        lifecycle_state=HANDOFF_STATE_STALE,
    )
    broken = replace(boundary_input, lifecycle_metadata=broken_lifecycle)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["handoff_stale"] is True


def test_superseded_state_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_lifecycle = replace(
        boundary_input.lifecycle_metadata,
        lifecycle_state=HANDOFF_STATE_SUPERSEDED,
    )
    broken = replace(boundary_input, lifecycle_metadata=broken_lifecycle)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["handoff_superseded"] is True


def test_predecessor_supersession_link_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    pe19_digest = compute_review_input_digest(
        boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
    )
    link = SupersessionLink(
        supersession_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
        predecessor_review_input_digest=pe19_digest,
        successor_review_input_digest="a" * 64,
        predecessor_handoff_digest=pe34_digest,
        successor_handoff_digest="b" * 64,
        generation=1,
    )
    broken = replace(boundary_input, supersession_links=(link,))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("superseded" in r for r in result["fail_reasons"])


def test_self_supersession_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    pe19_digest = compute_review_input_digest(
        boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
    )
    link = SupersessionLink(
        supersession_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
        predecessor_review_input_digest=pe19_digest,
        successor_review_input_digest=pe19_digest,
        predecessor_handoff_digest=pe34_digest,
        successor_handoff_digest=pe34_digest,
        generation=1,
    )
    broken = replace(boundary_input, supersession_links=(link,))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("self-supersession" in r for r in result["fail_reasons"])


def test_cyclic_supersession_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    link_ab = SupersessionLink(
        supersession_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
        predecessor_review_input_digest="a" * 64,
        successor_review_input_digest="b" * 64,
        predecessor_handoff_digest="a" * 64,
        successor_handoff_digest="b" * 64,
        generation=1,
    )
    link_bc = SupersessionLink(
        supersession_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
        predecessor_review_input_digest="b" * 64,
        successor_review_input_digest="c" * 64,
        predecessor_handoff_digest="b" * 64,
        successor_handoff_digest="c" * 64,
        generation=2,
    )
    link_ca = SupersessionLink(
        supersession_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
        predecessor_review_input_digest="c" * 64,
        successor_review_input_digest="a" * 64,
        predecessor_handoff_digest="c" * 64,
        successor_handoff_digest="a" * 64,
        generation=3,
    )
    broken = replace(boundary_input, supersession_links=(link_ab, link_bc, link_ca))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("cycle" in r for r in result["fail_reasons"])


def test_multiple_active_successors_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken = replace(
        boundary_input,
        active_successor_handoff_digests=("a" * 64, "b" * 64),
    )
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("active successor" in r for r in result["fail_reasons"])


def test_revoked_state_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_lifecycle = replace(
        boundary_input.lifecycle_metadata,
        lifecycle_state=HANDOFF_STATE_REVOKED,
    )
    broken = replace(boundary_input, lifecycle_metadata=broken_lifecycle)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["handoff_revoked"] is True


def test_revocation_for_current_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    revocation = RevocationProofBinding(
        revocation_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        target_handoff_digest=pe34_digest,
        revocation_reason=INVALIDATION_REASON_REVOKED,
    )
    broken = replace(boundary_input, revocation_proofs=(revocation,))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["handoff_revoked"] is True


def test_revocation_for_wrong_digest_is_ignored() -> None:
    boundary_input = _valid_boundary_input()
    revocation = RevocationProofBinding(
        revocation_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        target_handoff_digest="f" * 64,
        revocation_reason=INVALIDATION_REASON_REVOKED,
    )
    broken = replace(boundary_input, revocation_proofs=(revocation,))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True


def test_contradictory_revocation_states_fail_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    rev1 = RevocationProofBinding(
        revocation_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        target_handoff_digest=pe34_digest,
        revocation_reason=INVALIDATION_REASON_REVOKED,
    )
    rev2 = RevocationProofBinding(
        revocation_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        target_handoff_digest=pe34_digest,
        revocation_reason=INVALIDATION_REASON_STALE,
    )
    broken = replace(boundary_input, revocation_proofs=(rev1, rev2))
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_clearing_revocation_flag_without_recovery_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_handoff_staleness_revocation_recovery_boundary(
        boundary_input,
        revoked_flag_cleared=True,
    )
    assert result["boundary_pass"] is False


def test_loose_recovered_flag_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_handoff_staleness_revocation_recovery_boundary(
        boundary_input,
        loose_recovered_flag=True,
    )
    assert result["boundary_pass"] is False


def test_recovered_state_without_proof_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_lifecycle = replace(
        boundary_input.lifecycle_metadata,
        lifecycle_state=HANDOFF_STATE_RECOVERED,
    )
    broken = replace(boundary_input, lifecycle_metadata=broken_lifecycle)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_recovery_without_new_pe33_proof_fails_closed() -> None:
    boundary_input = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    new_pe34 = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        handoff_id="recovered-handoff-001",
    )
    new_digest = compute_pe34_boundary_input_digest(new_pe34)
    old_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    pe19_digest = compute_review_input_digest(new_pe34.pe19_undecided_review_input.review_input)
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest=old_digest,
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=new_digest,
        new_pe33_integration_proof_digest="0" * 64,
        new_pe19_review_input_digest=pe19_digest,
        new_pe20_review_input_digest=new_pe34.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=new_pe34.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    rebuilt = replace(
        boundary_input,
        pe34_handoff=new_pe34,
        canonical_current=CanonicalCurrentBindings(
            source_revision=VALID_COMMIT_SHA,
            pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
            pe34_handoff_digest=new_digest,
            replay_manifest_digest=new_pe34.pe19_undecided_review_input.review_input.evidence_chain.replay_manifest_digest,
            archive_manifest_digest=new_pe34.pe19_undecided_review_input.review_input.evidence_chain.archive_manifest_digest,
        ),
        lifecycle_metadata=HandoffLifecycleMetadata(
            lifecycle_state=HANDOFF_STATE_CURRENT,
            handoff_digest=new_digest,
            review_identity=REVIEW_IDENTITY,
            generation=1,
        ),
        recovery_proof=recovery,
    )
    result = evaluate_handoff_staleness_revocation_recovery_boundary(rebuilt)
    assert result["boundary_pass"] is False
    assert any("new_pe33_integration_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_recovery_with_old_pe34_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    pe33_digest = boundary_input.pe34_handoff.pe33_coherence_proof.integration_proof_digest
    pe19_digest = compute_review_input_digest(
        boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
    )
    pe20_digest = boundary_input.pe34_handoff.pe20_undecided_package_eligibility.review_input_digest
    pe25_digest = boundary_input.pe34_handoff.pe25_cross_slice_closure.closure_result_digest
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest="e" * 64,
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=pe34_digest,
        new_pe33_integration_proof_digest=pe33_digest,
        new_pe19_review_input_digest=pe19_digest,
        new_pe20_review_input_digest=pe20_digest,
        new_pe25_closure_result_digest=pe25_digest,
        recovery_generation=1,
    )
    broken = replace(boundary_input, recovery_proof=recovery)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_recovery_without_predecessor_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest="",
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=pe34_digest,
        new_pe33_integration_proof_digest=boundary_input.pe34_handoff.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=boundary_input.pe34_handoff.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=boundary_input.pe34_handoff.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    broken = replace(boundary_input, recovery_proof=recovery)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_recovery_with_wrong_predecessor_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    new_pe34 = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        handoff_id="recovered-handoff-002",
    )
    new_digest = compute_pe34_boundary_input_digest(new_pe34)
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest="d" * 64,
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=new_digest,
        new_pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            new_pe34.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=new_pe34.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=new_pe34.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    rebuilt = replace(
        boundary_input,
        pe34_handoff=new_pe34,
        canonical_current=replace(
            boundary_input.canonical_current,
            pe34_handoff_digest=new_digest,
            pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
        ),
        lifecycle_metadata=replace(
            boundary_input.lifecycle_metadata,
            handoff_digest=new_digest,
            generation=1,
        ),
        recovery_proof=recovery,
    )
    result = evaluate_handoff_staleness_revocation_recovery_boundary(rebuilt)
    assert result["boundary_pass"] is False
    assert any(
        "invalidated_predecessor_handoff_digest not evidenced" in r for r in result["fail_reasons"]
    )


def test_recovery_with_inconsistent_pe20_binding_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    new_pe34 = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        handoff_id="recovered-handoff-003",
    )
    new_digest = compute_pe34_boundary_input_digest(new_pe34)
    old_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest=old_digest,
        invalidation_reason=INVALIDATION_REASON_SUPERSEDED,
        new_handoff_digest=new_digest,
        new_pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            new_pe34.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest="0" * 64,
        new_pe25_closure_result_digest=new_pe34.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    rebuilt = replace(
        boundary_input,
        pe34_handoff=new_pe34,
        canonical_current=CanonicalCurrentBindings(
            source_revision=VALID_COMMIT_SHA,
            pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
            pe34_handoff_digest=new_digest,
        ),
        lifecycle_metadata=HandoffLifecycleMetadata(
            lifecycle_state=HANDOFF_STATE_CURRENT,
            handoff_digest=new_digest,
            review_identity=REVIEW_IDENTITY,
            generation=1,
        ),
        revocation_proofs=(
            RevocationProofBinding(
                revocation_owner=CONTRACT_VERSION,
                source_revision=VALID_COMMIT_SHA,
                target_handoff_digest=old_digest,
                revocation_reason=INVALIDATION_REASON_SUPERSEDED,
            ),
        ),
        recovery_proof=recovery,
    )
    result = evaluate_handoff_staleness_revocation_recovery_boundary(rebuilt)
    assert result["boundary_pass"] is False


def test_recovery_cycle_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    pe34_digest = compute_pe34_boundary_input_digest(boundary_input.pe34_handoff)
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest=pe34_digest,
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=pe34_digest,
        new_pe33_integration_proof_digest=boundary_input.pe34_handoff.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=boundary_input.pe34_handoff.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=boundary_input.pe34_handoff.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    broken = replace(boundary_input, recovery_proof=recovery)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("recovery cycle" in r for r in result["fail_reasons"])


def test_unknown_invalidation_reason_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest="e" * 64,
        invalidation_reason="unknown_reason",
        new_handoff_digest=compute_pe34_boundary_input_digest(boundary_input.pe34_handoff),
        new_pe33_integration_proof_digest=boundary_input.pe34_handoff.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            boundary_input.pe34_handoff.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=boundary_input.pe34_handoff.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=boundary_input.pe34_handoff.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    broken = replace(boundary_input, recovery_proof=recovery)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False


def test_manifest_digest_drift_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_canonical = replace(
        boundary_input.canonical_current,
        replay_manifest_digest="0" * 64,
    )
    broken = replace(boundary_input, canonical_current=broken_canonical)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("replay_manifest_digest mismatch" in r for r in result["fail_reasons"])


def test_recovery_required_state_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_lifecycle = replace(
        boundary_input.lifecycle_metadata,
        lifecycle_state=HANDOFF_STATE_RECOVERY_REQUIRED,
    )
    broken = replace(boundary_input, lifecycle_metadata=broken_lifecycle)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["recovery_required"] is True


def test_valid_recovery_passes() -> None:
    baseline = _valid_boundary_input()
    old_digest = compute_pe34_boundary_input_digest(baseline.pe34_handoff)
    new_pe34 = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        handoff_id="recovered-handoff-valid",
    )
    new_digest = compute_pe34_boundary_input_digest(new_pe34)
    evidence = new_pe34.pe19_undecided_review_input.review_input.evidence_chain
    recovery = RecoveryProofBinding(
        recovery_owner=CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest=old_digest,
        invalidation_reason=INVALIDATION_REASON_REVOKED,
        new_handoff_digest=new_digest,
        new_pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            new_pe34.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=new_pe34.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=new_pe34.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    rebuilt = HandoffStalenessRevocationRecoveryBoundaryInput(
        pe34_handoff=new_pe34,
        canonical_current=CanonicalCurrentBindings(
            source_revision=VALID_COMMIT_SHA,
            pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
            pe34_handoff_digest=new_digest,
            replay_manifest_digest=evidence.replay_manifest_digest,
            archive_manifest_digest=evidence.archive_manifest_digest,
        ),
        lifecycle_metadata=HandoffLifecycleMetadata(
            lifecycle_state=HANDOFF_STATE_CURRENT,
            handoff_digest=new_digest,
            review_identity=REVIEW_IDENTITY,
            generation=1,
        ),
        revocation_proofs=(
            RevocationProofBinding(
                revocation_owner=CONTRACT_VERSION,
                source_revision=VALID_COMMIT_SHA,
                target_handoff_digest=old_digest,
                revocation_reason=INVALIDATION_REASON_REVOKED,
            ),
        ),
        recovery_proof=recovery,
    )
    result = evaluate_handoff_staleness_revocation_recovery_boundary(rebuilt)
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True
    assert result["recovery_proof_valid"] is True
    _assert_all_authorization_flags_false(result)


def test_digest_stability_identical_inputs() -> None:
    first = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    second = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    assert compute_boundary_input_digest(first) == compute_boundary_input_digest(second)
    first_result = evaluate_handoff_staleness_revocation_recovery_boundary(first)
    second_result = evaluate_handoff_staleness_revocation_recovery_boundary(second)
    assert first_result["boundary_result_digest"] == second_result["boundary_result_digest"]


def test_canonical_serialization_order_irrelevant() -> None:
    boundary_input = _valid_boundary_input()
    canonical = serialize_boundary_input_canonical(boundary_input)
    parsed = __import__("json").loads(canonical)
    shuffled = __import__("json").dumps(parsed, sort_keys=True, separators=(",", ":"))
    assert canonical == shuffled


def test_relevant_input_mutation_changes_digest() -> None:
    baseline = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    baseline_digest = compute_boundary_input_digest(baseline)
    broken_lifecycle = replace(
        baseline.lifecycle_metadata,
        review_identity="mutated-review-identity",
    )
    mutated = replace(baseline, lifecycle_metadata=broken_lifecycle)
    assert compute_boundary_input_digest(mutated) != baseline_digest


def test_no_file_archive_environment_git_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in PE-35 tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    result = evaluate_handoff_staleness_revocation_recovery_boundary(_valid_boundary_input())
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    boundary_input = default_minimal_boundary_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    assert boundary_input.pe34_handoff.instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in boundary_input.pe34_handoff.instrument
    assert "BTC" not in boundary_input.pe34_handoff.instrument
    result = evaluate_handoff_staleness_revocation_recovery_boundary(boundary_input)
    assert result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True


def test_pe34_owner_reused_not_duplicated() -> None:
    boundary_input = _valid_boundary_input()
    assert boundary_input.pe34_handoff.contract_versions.integration == PE34_CONTRACT_VERSION


def test_boundary_result_digest_only_when_satisfied() -> None:
    valid = _valid_boundary_input()
    valid_result = evaluate_handoff_staleness_revocation_recovery_boundary(valid)
    assert valid_result["boundary_result_digest"] is not None
    assert valid_result["boundary_result_digest"] == compute_boundary_result_digest(
        valid,
        handoff_staleness_revocation_recovery_boundary_satisfied=True,
    )

    broken = replace(
        valid,
        lifecycle_metadata=replace(valid.lifecycle_metadata, lifecycle_state=HANDOFF_STATE_STALE),
    )
    broken_result = evaluate_handoff_staleness_revocation_recovery_boundary(broken)
    assert broken_result["boundary_result_digest"] is None


def test_implicit_reactivation_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_handoff_staleness_revocation_recovery_boundary(
        boundary_input,
        implicit_reactivation=True,
    )
    assert result["boundary_pass"] is False
