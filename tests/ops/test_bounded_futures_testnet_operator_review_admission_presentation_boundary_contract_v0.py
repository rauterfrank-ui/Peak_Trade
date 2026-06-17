"""Static + offline bounded Futures Testnet operator review admission/presentation boundary (v0).

Docs/tests-only. No runtime, network, credentials, operator review, queue, UI, or Testnet start.
PE-36 admission/presentation guard over PE-35-validated handoff only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    BOUNDARY_OWNER as PE35_BOUNDARY_OWNER,
    CONTRACT_VERSION as PE35_CONTRACT_VERSION,
    HANDOFF_STATE_CURRENT,
    HANDOFF_STATE_RECOVERED,
    HANDOFF_STATE_RECOVERY_REQUIRED,
    HANDOFF_STATE_REVOKED,
    HANDOFF_STATE_STALE,
    HANDOFF_STATE_SUPERSEDED,
    CanonicalCurrentBindings,
    HandoffLifecycleMetadata,
    HandoffStalenessRevocationRecoveryBoundaryInput,
    RecoveryProofBinding,
    RevocationProofBinding,
    compute_boundary_input_digest as compute_pe35_boundary_input_digest,
    compute_boundary_result_digest as compute_pe35_boundary_result_digest,
    default_minimal_boundary_input as default_minimal_pe35_boundary_input,
    evaluate_handoff_staleness_revocation_recovery_boundary,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
    AUTHORITY_LIFT,
    BOUNDARY_OWNER,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    PRESENTATION_FIELD_ALLOWLIST,
    PRESENTATION_RENDERED,
    REVIEW_QUEUE_CREATED,
    REVIEW_QUEUE_ENTRY_CREATED,
    SECOND_ASSEMBLY_CREATED,
    SECOND_HANDOFF_SURFACE_CREATED,
    SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
    SECOND_PRESENTATION_SURFACE_CREATED,
    SECOND_READINESS_SURFACE_CREATED,
    UI_SURFACE_CREATED,
    OperatorReviewAdmissionPresentationBoundaryInput,
    Pe35BoundaryProofBinding,
    compute_boundary_input_digest,
    compute_boundary_result_digest,
    compute_presentation_projection_digest,
    default_minimal_boundary_input,
    default_minimal_pe35_proof_binding,
    evaluate_operator_review_admission_presentation_boundary,
    serialize_boundary_input_canonical,
    serialize_presentation_projection_canonical,
    validate_presentation_projection_dict,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    ALLOWED_LATER_DECISIONS,
    compute_boundary_input_digest as compute_pe34_boundary_input_digest,
    default_minimal_handoff_boundary_input,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    EXPECTED_OPERATOR_NAME,
    compute_review_input_digest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0.py"
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
PE35_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0.py"
)

TEST_PACKAGE_MARKER = (
    "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_BOUNDARY_GUARD_V0=true"
)
_CLASS4_SCOPED_EXCEPTION_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_BOUNDARY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"

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
) -> OperatorReviewAdmissionPresentationBoundaryInput:
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
        "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_ADMISSION_PRESENTATION_BOUNDARY_CONTRACT_V0=true"
        in BOUNDARY_MODULE.read_text(encoding="utf-8")
    )


def test_pe19_pe20_pe25_pe33_pe34_pe35_owners_referenced_not_duplicated() -> None:
    boundary_text = BOUNDARY_MODULE.read_text(encoding="utf-8")
    assert (
        "bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0"
        in boundary_text
    )
    assert "evaluate_handoff_staleness_revocation_recovery_boundary" in boundary_text
    assert "evaluate_operator_review(" not in boundary_text
    assert "persist_operator_review_proof_package" not in boundary_text
    assert "import subprocess" not in boundary_text
    assert "REVIEW_QUEUE_CREATED = False" in boundary_text
    assert "UI_SURFACE_CREATED = False" in boundary_text
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE25_MODULE.exists()
    assert PE33_MODULE.exists()
    assert PE34_MODULE.exists()
    assert PE35_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert SECOND_ASSEMBLY_CREATED is False
    assert SECOND_READINESS_SURFACE_CREATED is False
    assert SECOND_OPERATOR_REVIEW_SURFACE_CREATED is False
    assert SECOND_HANDOFF_SURFACE_CREATED is False
    assert SECOND_PRESENTATION_SURFACE_CREATED is False
    assert REVIEW_QUEUE_CREATED is False
    assert REVIEW_QUEUE_ENTRY_CREATED is False
    assert UI_SURFACE_CREATED is False
    assert PRESENTATION_RENDERED is False
    assert AUTHORITY_LIFT is False


def test_valid_pe35_proof_yields_non_authorizing_projection() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    assert result["boundary_pass"] is True
    assert result["operator_review_admission_presentation_boundary_satisfied"] is True
    assert result["presentation_fields_allowlisted"] is True
    assert result["secret_fields_present"] is False
    assert result["decision_preselected"] is False
    assert result["presentation_projection"] is not None
    assert result["presentation_projection_digest"] is not None
    projection = result["presentation_projection"]
    assert projection.non_authorizing is True
    assert projection.presentation_status == "read_only_non_authorizing"
    assert tuple(projection.allowed_later_decisions) == tuple(sorted(ALLOWED_LATER_DECISIONS))
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_missing_pe35_proof_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        boundary_input_digest="",
        boundary_result_digest=None,
        handoff_staleness_revocation_recovery_boundary_satisfied=False,
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["operator_review_admission_presentation_boundary_satisfied"] is False


def test_negative_pe35_proof_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_wrong_pe35_owner_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        boundary_owner="wrong.owner.alias.v0",
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("boundary_owner" in r for r in result["fail_reasons"])


def test_wrong_pe35_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        boundary_input_digest="0" * 64,
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("boundary_input_digest mismatch" in r for r in result["fail_reasons"])


@pytest.mark.parametrize(
    "lifecycle_state",
    [
        HANDOFF_STATE_STALE,
        HANDOFF_STATE_SUPERSEDED,
        HANDOFF_STATE_REVOKED,
        HANDOFF_STATE_RECOVERY_REQUIRED,
    ],
)
def test_non_current_handoff_states_fail_closed(lifecycle_state: str) -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=lifecycle_state,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["operator_review_admission_presentation_boundary_satisfied"] is False


def test_recovered_without_recovery_proof_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_RECOVERED,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_wrong_pe34_handoff_digest_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe35_boundary_input,
        canonical_current=replace(
            boundary_input.pe35_boundary_input.canonical_current,
            pe34_handoff_digest="1" * 64,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_source_revision_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        source_revision=ALT_COMMIT_SHA,
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_pe33_digest_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe35 = replace(
        boundary_input.pe35_boundary_input,
        canonical_current=replace(
            boundary_input.pe35_boundary_input.canonical_current,
            pe33_integration_proof_digest="2" * 64,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_pe19_digest_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe19 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff.pe19_undecided_review_input,
        pe33_integration_proof_digest="3" * 64,
    )
    broken_pe34 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff,
        pe19_undecided_review_input=broken_pe19,
    )
    broken_pe35 = replace(boundary_input.pe35_boundary_input, pe34_handoff=broken_pe34)
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_pe20_digest_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff.pe20_undecided_package_eligibility,
        review_input_digest="4" * 64,
    )
    broken_pe34 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff,
        pe20_undecided_package_eligibility=broken_pe20,
    )
    broken_pe35 = replace(boundary_input.pe35_boundary_input, pe34_handoff=broken_pe34)
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_pe25_digest_mismatch_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_pe25 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff.pe25_cross_slice_closure,
        closure_result_digest="5" * 64,
    )
    broken_pe34 = replace(
        boundary_input.pe35_boundary_input.pe34_handoff,
        pe25_cross_slice_closure=broken_pe25,
    )
    broken_pe35 = replace(boundary_input.pe35_boundary_input, pe34_handoff=broken_pe34)
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_missing_presentation_field_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    projection = result["presentation_projection"]
    assert projection is not None
    projection_dict = {
        k: v for k, v in __import__("dataclasses").asdict(projection).items() if k != "handoff_id"
    }
    fail_reasons = validate_presentation_projection_dict(projection_dict)
    assert any("missing required fields" in r for r in fail_reasons)


def test_unknown_presentation_field_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    projection = result["presentation_projection"]
    assert projection is not None
    projection_dict = __import__("dataclasses").asdict(projection)
    projection_dict["extra_unknown_field"] = "not_allowed"
    fail_reasons = validate_presentation_projection_dict(projection_dict)
    assert any("unknown fields" in r for r in fail_reasons)


def test_owner_alias_fails_closed() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        boundary_owner=PE35_CONTRACT_VERSION + ".alias",
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


@pytest.mark.parametrize(
    "forbidden_key,forbidden_value",
    [
        ("api_key", "placeholder-not-real"),
        ("secret_token", "placeholder-not-real"),
        ("account_balance", "100.00"),
        ("position_state", "open"),
        ("order_state", "pending"),
        ("authorization_header", "Bearer placeholder"),
        ("runtime_command", "start_testnet"),
    ],
)
def test_forbidden_presentation_fields_fail_closed(
    forbidden_key: str,
    forbidden_value: str,
) -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        injected_presentation_overrides={forbidden_key: forbidden_value},
    )
    assert result["boundary_pass"] is False
    assert result["secret_fields_present"] is False


def test_preselected_decision_fails_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        selected_decision="approve_for_separate_next_phase_review",
    )
    assert result["boundary_pass"] is False
    assert result["decision_preselected"] is False


def test_default_approve_fails_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        default_approve=True,
    )
    assert result["boundary_pass"] is False


def test_implicit_approve_fails_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        implicit_approve=True,
    )
    assert result["boundary_pass"] is False


def test_loose_admitted_flag_fails_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        loose_admitted_flag=True,
    )
    assert result["boundary_pass"] is False


def test_loose_presentable_flag_fails_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        loose_presentable_flag=True,
    )
    assert result["boundary_pass"] is False


def test_extra_presentation_fields_fail_closed() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(
        _valid_boundary_input(),
        extra_presentation_fields=("unexpected_field",),
    )
    assert result["boundary_pass"] is False


def test_operator_name_alone_is_not_decision() -> None:
    boundary_input = default_minimal_boundary_input(
        operator_name_legibility=EXPECTED_OPERATOR_NAME,
    )
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    assert result["operator_review_admission_presentation_boundary_satisfied"] is True
    assert result["operator_decision_selected"] is False
    assert result["decision_preselected"] is False
    projection = result["presentation_projection"]
    assert projection is not None
    assert projection.operator_name_legibility == EXPECTED_OPERATOR_NAME


def test_allowed_decision_enumeration_is_presentation_only() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(_valid_boundary_input())
    projection = result["presentation_projection"]
    assert projection is not None
    assert set(projection.allowed_later_decisions) == ALLOWED_LATER_DECISIONS
    assert result["operator_decision_selected"] is False


def test_admitted_does_not_replace_proof_binding() -> None:
    boundary_input = _valid_boundary_input()
    broken_proof = replace(
        boundary_input.pe35_proof,
        handoff_staleness_revocation_recovery_boundary_satisfied=True,
        boundary_result_digest="f" * 64,
    )
    broken = replace(boundary_input, pe35_proof=broken_proof)
    result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert result["boundary_pass"] is False


def test_valid_recovery_with_new_digests_can_pass_when_current() -> None:
    baseline_pe35 = default_minimal_pe35_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        review_identity=REVIEW_IDENTITY,
    )
    old_digest = compute_pe34_boundary_input_digest(baseline_pe35.pe34_handoff)
    new_pe34 = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        handoff_id="recovered-handoff-pe36",
    )
    new_digest = compute_pe34_boundary_input_digest(new_pe34)
    evidence = new_pe34.pe19_undecided_review_input.review_input.evidence_chain
    recovery = RecoveryProofBinding(
        recovery_owner=PE35_CONTRACT_VERSION,
        source_revision=VALID_COMMIT_SHA,
        invalidated_predecessor_handoff_digest=old_digest,
        invalidation_reason="revoked",
        new_handoff_digest=new_digest,
        new_pe33_integration_proof_digest=new_pe34.pe33_coherence_proof.integration_proof_digest,
        new_pe19_review_input_digest=compute_review_input_digest(
            new_pe34.pe19_undecided_review_input.review_input
        ),
        new_pe20_review_input_digest=new_pe34.pe20_undecided_package_eligibility.review_input_digest,
        new_pe25_closure_result_digest=new_pe34.pe25_cross_slice_closure.closure_result_digest,
        recovery_generation=1,
    )
    pe35_input = HandoffStalenessRevocationRecoveryBoundaryInput(
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
                revocation_owner=PE35_CONTRACT_VERSION,
                source_revision=VALID_COMMIT_SHA,
                target_handoff_digest=old_digest,
                revocation_reason="revoked",
            ),
        ),
        recovery_proof=recovery,
    )
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(pe35_input)
    assert pe35_result["handoff_staleness_revocation_recovery_boundary_satisfied"] is True
    boundary_input = OperatorReviewAdmissionPresentationBoundaryInput(
        pe35_boundary_input=pe35_input,
        pe35_proof=Pe35BoundaryProofBinding(
            boundary_owner=PE35_BOUNDARY_OWNER,
            source_revision=VALID_COMMIT_SHA,
            boundary_input_digest=compute_pe35_boundary_input_digest(pe35_input),
            boundary_result_digest=pe35_result["boundary_result_digest"],
            handoff_staleness_revocation_recovery_boundary_satisfied=True,
        ),
        operator_name_legibility=EXPECTED_OPERATOR_NAME,
    )
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    assert result["operator_review_admission_presentation_boundary_satisfied"] is True


def test_digest_stability_identical_inputs() -> None:
    first = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    second = _valid_boundary_input(source_revision=VALID_COMMIT_SHA)
    assert compute_boundary_input_digest(first) == compute_boundary_input_digest(second)
    first_result = evaluate_operator_review_admission_presentation_boundary(first)
    second_result = evaluate_operator_review_admission_presentation_boundary(second)
    assert (
        first_result["presentation_projection_digest"]
        == second_result["presentation_projection_digest"]
    )
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
    broken_pe35 = replace(
        baseline.pe35_boundary_input,
        lifecycle_metadata=replace(
            baseline.pe35_boundary_input.lifecycle_metadata,
            review_identity="mutated-review-identity",
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    mutated = replace(
        baseline,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    assert compute_boundary_input_digest(mutated) != baseline_digest


def test_projection_immutable_and_deterministic() -> None:
    result = evaluate_operator_review_admission_presentation_boundary(_valid_boundary_input())
    projection = result["presentation_projection"]
    assert projection is not None
    first_digest = compute_presentation_projection_digest(projection)
    second_digest = compute_presentation_projection_digest(projection)
    assert first_digest == second_digest
    serialized = serialize_presentation_projection_canonical(projection)
    reparsed = __import__("json").loads(serialized)
    reserialized = __import__("json").dumps(reparsed, sort_keys=True, separators=(",", ":"))
    assert serialized == reserialized


def test_presentation_field_allowlist_closed() -> None:
    assert len(PRESENTATION_FIELD_ALLOWLIST) >= 20


def test_no_file_archive_environment_git_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in PE-36 tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    result = evaluate_operator_review_admission_presentation_boundary(_valid_boundary_input())
    assert result["operator_review_admission_presentation_boundary_satisfied"] is True


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    boundary_input = default_minimal_boundary_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    assert boundary_input.pe35_boundary_input.pe34_handoff.instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in boundary_input.pe35_boundary_input.pe34_handoff.instrument
    assert "BTC" not in boundary_input.pe35_boundary_input.pe34_handoff.instrument
    result = evaluate_operator_review_admission_presentation_boundary(boundary_input)
    assert result["operator_review_admission_presentation_boundary_satisfied"] is True


def test_boundary_result_digest_only_when_satisfied() -> None:
    valid = _valid_boundary_input()
    valid_result = evaluate_operator_review_admission_presentation_boundary(valid)
    assert valid_result["boundary_result_digest"] is not None
    assert valid_result["presentation_projection_digest"] is not None
    assert valid_result["boundary_result_digest"] == compute_boundary_result_digest(
        valid,
        operator_review_admission_presentation_boundary_satisfied=True,
        presentation_projection_digest=valid_result["presentation_projection_digest"],
    )

    broken_pe35 = replace(
        valid.pe35_boundary_input,
        lifecycle_metadata=replace(
            valid.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken = replace(
        valid,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_proof,
    )
    broken_result = evaluate_operator_review_admission_presentation_boundary(broken)
    assert broken_result["boundary_result_digest"] is None


def test_pe35_owner_constants_coherent() -> None:
    boundary_input = _valid_boundary_input()
    assert boundary_input.pe35_proof.boundary_owner == PE35_BOUNDARY_OWNER
    assert BOUNDARY_OWNER == CONTRACT_VERSION
