"""Static + offline bounded Futures Testnet operator-review handoff boundary (v0).

Docs/tests-only. No runtime, network, credentials, operator review, or Testnet start.
PE-34 static PE-33/PE-19/PE-20/PE-25 handoff boundary binding only.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0 import (
    CONTRACT_VERSION as PE33_CONTRACT_VERSION,
    COHERENCE_OWNER as PE33_COHERENCE_OWNER,
    default_minimal_integration_input as default_minimal_pe33_integration_input,
    evaluate_cross_slice_proof_coherence_integration,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    CONTRACT_VERSION as PE25_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_operator_review_handoff_boundary_contract_v0 import (
    AUTHORITY_LIFT,
    CONTRACT_IMPLEMENTATION_ONLY,
    CONTRACT_VERSION,
    EXPECTED_OPERATOR_NAME,
    OPERATOR_CLOSURE_EXECUTED,
    OPERATOR_DECISION_SELECTED,
    OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED,
    OPERATOR_REVIEW_EXECUTED,
    Pe19UndecidedReviewInputBinding,
    Pe20UndecidedPackageEligibilityBinding,
    Pe25CrossSliceClosureBinding,
    Pe33CoherenceProofBinding,
    SECOND_ASSEMBLY_CREATED,
    SECOND_OPERATOR_REVIEW_SURFACE_CREATED,
    SECOND_READINESS_SURFACE_CREATED,
    compute_boundary_input_digest,
    compute_boundary_result_digest,
    default_minimal_handoff_boundary_input,
    evaluate_operator_review_handoff_boundary,
    serialize_boundary_input_canonical,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0 import (
    CONTRACT_VERSION as PE20_CONTRACT_VERSION,
    PACKAGE_SCHEMA_VERSION as PE20_PACKAGE_SCHEMA_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (
    CONTRACT_VERSION as PE19_CONTRACT_VERSION,
    DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    OperatorDecisionRecord,
    compute_review_input_digest,
    default_minimal_decision_record,
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
    / "bounded_futures_testnet_operator_review_handoff_boundary_contract_v0.py"
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

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_HANDOFF_BOUNDARY_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_HANDOFF_BOUNDARY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)

VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
ALT_COMMIT_SHA = "1234567890abcdef1234567890abcdef12345678"
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


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


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert (
        "BOUNDED_FUTURES_TESTNET_OPERATOR_REVIEW_HANDOFF_BOUNDARY_CONTRACT_V0=true"
        in BOUNDARY_MODULE.read_text(encoding="utf-8")
    )


def test_pe19_pe20_pe25_pe33_owners_referenced_not_duplicated() -> None:
    boundary_text = BOUNDARY_MODULE.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0" in (
        boundary_text
    )
    assert "bounded_futures_testnet_preflight_operator_review_proof_package_contract_v0" in (
        boundary_text
    )
    assert "bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0" in (
        boundary_text
    )
    assert "bounded_futures_testnet_cross_slice_proof_coherence_integration_contract_v0" in (
        boundary_text
    )
    assert "evaluate_operator_review(" not in boundary_text
    assert "from src.ops.bounded_futures_testnet_preflight_operator_review_reproducibility_contract_v0 import (\n    evaluate_operator_review" not in boundary_text
    assert "evaluate_operator_closure_lifecycle_integration" not in boundary_text
    assert "persist_operator_review_proof_package" not in boundary_text
    assert "import subprocess" not in boundary_text
    assert "open(" not in boundary_text
    assert PE19_MODULE.exists()
    assert PE20_MODULE.exists()
    assert PE25_MODULE.exists()
    assert PE33_MODULE.exists()


def test_global_safety_flags_remain_blocked() -> None:
    assert CONTRACT_IMPLEMENTATION_ONLY is True
    assert OPERATOR_REVIEW_EXECUTED is False
    assert OPERATOR_DECISION_SELECTED is False
    assert OPERATOR_PROOF_PACKAGE_OPERATIONALLY_ISSUED is False
    assert OPERATOR_CLOSURE_EXECUTED is False
    assert SECOND_ASSEMBLY_CREATED is False
    assert SECOND_READINESS_SURFACE_CREATED is False
    assert SECOND_OPERATOR_REVIEW_SURFACE_CREATED is False
    assert AUTHORITY_LIFT is False


def test_valid_canonical_handoff_passes() -> None:
    boundary_input = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    result = evaluate_operator_review_handoff_boundary(boundary_input)
    assert result["boundary_pass"] is True
    assert result["operator_review_handoff_boundary_satisfied"] is True
    assert result["pe34_operator_review_handoff_boundary_static_proven"] is True
    assert result["source_revision_coherent"] is True
    assert result["owner_identities_coherent"] is True
    assert result["proof_digests_coherent"] is True
    assert result["fail_reasons"] == []
    _assert_all_authorization_flags_false(result)


def test_valid_handoff_remains_non_authorizing() -> None:
    result = evaluate_operator_review_handoff_boundary(default_minimal_handoff_boundary_input())
    assert result["operator_review_handoff_boundary_satisfied"] is True
    assert result["operator_review_executed"] is False
    assert result["operator_decision_selected"] is False
    assert result["operator_proof_package_operationally_issued"] is False
    assert result["operator_closure_executed"] is False
    assert result["second_assembly_created"] is False
    assert result["second_readiness_surface_created"] is False
    assert result["second_operator_review_surface_created"] is False
    assert result["authority_lift"] is False
    _assert_all_authorization_flags_false(result)


def test_missing_pe33_coherence_proof_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken = replace(
        boundary_input,
        pe33_coherence_proof=Pe33CoherenceProofBinding(
            coherence_owner="",
            source_revision="",
            integration_input_digest="",
            integration_proof_digest="",
            cross_slice_proof_coherence_for_separate_operator_review=False,
            static_pe12_lifecycle_chain_complete=False,
            integration_pass=False,
        ),
    )
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert result["operator_review_handoff_boundary_satisfied"] is False


def test_pe33_negative_coherence_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_proof = replace(
        boundary_input.pe33_coherence_proof,
        cross_slice_proof_coherence_for_separate_operator_review=False,
    )
    broken = replace(boundary_input, pe33_coherence_proof=broken_proof)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("cross_slice_proof_coherence" in reason for reason in result["fail_reasons"])


def test_wrong_pe33_owner_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_proof = replace(
        boundary_input.pe33_coherence_proof,
        coherence_owner="wrong.pe33.owner",
    )
    broken = replace(boundary_input, pe33_coherence_proof=broken_proof)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("coherence_owner" in reason for reason in result["fail_reasons"])


def test_pe33_digest_mismatch_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_proof = replace(
        boundary_input.pe33_coherence_proof,
        integration_proof_digest="0" * 64,
    )
    broken = replace(boundary_input, pe33_coherence_proof=broken_proof)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("integration_proof_digest mismatch" in reason for reason in result["fail_reasons"])


def test_missing_pe19_review_input_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe19 = replace(
        boundary_input.pe19_undecided_review_input,
        review_input_owner="",
        pe33_integration_proof_digest="",
    )
    broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False


def test_wrong_pe19_owner_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe19 = replace(
        boundary_input.pe19_undecided_review_input,
        review_input_owner="wrong.pe19.owner",
    )
    broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("review_input_owner" in reason for reason in result["fail_reasons"])


def test_pe19_wrong_pe33_digest_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe19 = replace(
        boundary_input.pe19_undecided_review_input,
        pe33_integration_proof_digest="1" * 64,
    )
    broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any(
        "pe33_integration_proof_digest mismatch" in reason for reason in result["fail_reasons"]
    )


def test_pe19_wrong_source_revision_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    broken_pe19 = replace(
        boundary_input.pe19_undecided_review_input,
        source_revision=ALT_COMMIT_SHA,
    )
    broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("source_revision mismatch" in reason for reason in result["fail_reasons"])


def test_selected_operator_decision_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        selected_decision=DECISION_APPROVE_FOR_SEPARATE_NEXT_PHASE_REVIEW,
    )
    assert result["boundary_pass"] is False
    assert any("selected_decision" in reason for reason in result["fail_reasons"])


def test_default_approve_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(boundary_input, default_approve=True)
    assert result["boundary_pass"] is False
    assert any("default_approve" in reason for reason in result["fail_reasons"])


def test_implicit_approve_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(boundary_input, implicit_approve=True)
    assert result["boundary_pass"] is False
    assert any("implicit_approve" in reason for reason in result["fail_reasons"])


def test_unknown_decision_state_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        unknown_decision_state="approve",
    )
    assert result["boundary_pass"] is False
    assert any("unknown decision state" in reason for reason in result["fail_reasons"])


def test_operator_name_alone_does_not_execute_review_or_decision() -> None:
    boundary_input = default_minimal_handoff_boundary_input(
        operator_name_legibility=EXPECTED_OPERATOR_NAME,
    )
    result = evaluate_operator_review_handoff_boundary(boundary_input)
    assert result["operator_review_handoff_boundary_satisfied"] is True
    assert result["operator_review_executed"] is False
    assert result["operator_decision_selected"] is False


def test_operator_name_wrong_legibility_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input(
        operator_name_legibility="Wrong Operator"
    )
    result = evaluate_operator_review_handoff_boundary(boundary_input)
    assert result["boundary_pass"] is False
    assert any("operator_name_legibility" in reason for reason in result["fail_reasons"])


def test_missing_pe20_binding_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe20_undecided_package_eligibility,
        package_owner="",
        review_input_digest="",
    )
    broken = replace(boundary_input, pe20_undecided_package_eligibility=broken_pe20)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False


def test_decided_pe20_package_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe20_undecided_package_eligibility,
        operative_decision_issued=True,
        decision_record_digest="d" * 64,
    )
    broken = replace(boundary_input, pe20_undecided_package_eligibility=broken_pe20)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any(
        "operative_decision_issued" in reason or "decision_record_digest" in reason
        for reason in result["fail_reasons"]
    )


def test_wrong_pe20_owner_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe20_undecided_package_eligibility,
        package_owner="wrong.pe20.owner",
    )
    broken = replace(boundary_input, pe20_undecided_package_eligibility=broken_pe20)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("package_owner" in reason for reason in result["fail_reasons"])


def test_pe20_review_input_digest_mismatch_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe20 = replace(
        boundary_input.pe20_undecided_package_eligibility,
        review_input_digest="0" * 64,
    )
    broken = replace(boundary_input, pe20_undecided_package_eligibility=broken_pe20)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("review_input_digest mismatch" in reason for reason in result["fail_reasons"])


def test_missing_pe25_binding_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe25 = replace(
        boundary_input.pe25_cross_slice_closure,
        closure_owner="",
        closure_result_digest="",
        pe33_pe25_slot_digest="",
    )
    broken = replace(boundary_input, pe25_cross_slice_closure=broken_pe25)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False


def test_pe25_operative_closure_interpretation_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe25 = replace(
        boundary_input.pe25_cross_slice_closure,
        operative_operator_closure_executed=True,
    )
    broken = replace(boundary_input, pe25_cross_slice_closure=broken_pe25)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("operative_operator_closure_executed" in reason for reason in result["fail_reasons"])


def test_pe25_digest_mismatch_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe25 = replace(
        boundary_input.pe25_cross_slice_closure,
        pe33_pe25_slot_digest="0" * 64,
        closure_result_digest="0" * 64,
    )
    broken = replace(boundary_input, pe25_cross_slice_closure=broken_pe25)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("pe33_pe25_slot_digest mismatch" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize(
    ("field", "alt_revision"),
    [
        ("source_revision", ALT_COMMIT_SHA),
        ("pe19_undecided_review_input", None),
        ("pe20_undecided_package_eligibility", None),
        ("pe25_cross_slice_closure", None),
        ("pe33_coherence_proof", None),
    ],
)
def test_source_revision_mismatch_across_bindings_fails_closed(
    field: str,
    alt_revision: str | None,
) -> None:
    boundary_input = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    if field == "source_revision":
        broken = replace(boundary_input, source_revision=ALT_COMMIT_SHA)
    elif field == "pe19_undecided_review_input":
        broken_pe19 = replace(
            boundary_input.pe19_undecided_review_input,
            source_revision=ALT_COMMIT_SHA,
        )
        broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    elif field == "pe20_undecided_package_eligibility":
        broken_pe20 = replace(
            boundary_input.pe20_undecided_package_eligibility,
            source_revision=ALT_COMMIT_SHA,
        )
        broken = replace(boundary_input, pe20_undecided_package_eligibility=broken_pe20)
    elif field == "pe25_cross_slice_closure":
        broken_pe25 = replace(
            boundary_input.pe25_cross_slice_closure,
            source_revision=ALT_COMMIT_SHA,
        )
        broken = replace(boundary_input, pe25_cross_slice_closure=broken_pe25)
    else:
        broken_proof = replace(
            boundary_input.pe33_coherence_proof,
            source_revision=ALT_COMMIT_SHA,
        )
        broken = replace(boundary_input, pe33_coherence_proof=broken_proof)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("source_revision mismatch" in reason for reason in result["fail_reasons"])


@pytest.mark.parametrize("bad_revision", ["", "abc", "A" * 40, "g" * 40])
def test_invalid_source_revision_fails_closed(bad_revision: str) -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken = replace(boundary_input, source_revision=bad_revision)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False
    assert any("source_revision" in reason for reason in result["fail_reasons"])


def test_owner_alias_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    broken_pe19 = replace(
        boundary_input.pe19_undecided_review_input,
        review_input_owner=f"{PE19_CONTRACT_VERSION}_alias",
    )
    broken = replace(boundary_input, pe19_undecided_review_input=broken_pe19)
    result = evaluate_operator_review_handoff_boundary(broken)
    assert result["boundary_pass"] is False


def test_loose_boolean_eligibility_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        loose_boolean_eligibility=True,
    )
    assert result["boundary_pass"] is False
    assert result["operator_review_handoff_boundary_satisfied"] is False
    assert any("loose boolean eligibility" in reason for reason in result["fail_reasons"])


def test_extra_proof_slots_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        extra_proof_slots=("pe99",),
    )
    assert result["boundary_pass"] is False
    assert any("unknown extra proof slots" in reason for reason in result["fail_reasons"])


def test_extra_decision_fields_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        extra_decision_fields=("decision",),
    )
    assert result["boundary_pass"] is False
    assert any("unknown extra decision fields" in reason for reason in result["fail_reasons"])


def test_operative_decision_issued_flag_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        operative_decision_issued=True,
    )
    assert result["boundary_pass"] is False


def test_operative_closure_executed_flag_fails_closed() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    result = evaluate_operator_review_handoff_boundary(
        boundary_input,
        operative_closure_executed=True,
    )
    assert result["boundary_pass"] is False


def test_digest_stability_identical_inputs() -> None:
    first = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    second = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    assert compute_boundary_input_digest(first) == compute_boundary_input_digest(second)
    first_result = evaluate_operator_review_handoff_boundary(first)
    second_result = evaluate_operator_review_handoff_boundary(second)
    assert first_result["boundary_result_digest"] == second_result["boundary_result_digest"]


def test_canonical_serialization_order_irrelevant() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    canonical = serialize_boundary_input_canonical(boundary_input)
    parsed = __import__("json").loads(canonical)
    shuffled = __import__("json").dumps(parsed, sort_keys=True, separators=(",", ":"))
    assert canonical == shuffled
    assert (
        compute_boundary_input_digest(boundary_input)
        == __import__("hashlib").sha256(shuffled.encode("utf-8")).hexdigest()
    )


def test_relevant_input_mutation_changes_digest() -> None:
    baseline = default_minimal_handoff_boundary_input(source_revision=VALID_COMMIT_SHA)
    baseline_digest = compute_boundary_input_digest(baseline)
    mutated = replace(
        baseline,
        handoff_id="operator-review-handoff-boundary-mutated",
    )
    assert compute_boundary_input_digest(mutated) != baseline_digest
    baseline_result = evaluate_operator_review_handoff_boundary(baseline)
    mutated_result = evaluate_operator_review_handoff_boundary(mutated)
    assert baseline_result["boundary_result_digest"] != mutated_result["boundary_result_digest"]


def test_pe19_decision_record_not_part_of_handoff_input() -> None:
    """PE-19 decision records are out of scope; handoff binds undecided review input only."""
    review_input = default_minimal_operator_review_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest="a" * 64,
        input_capture_digest="b" * 64,
        replay_manifest_digest="c" * 64,
        archive_identity="d" * 64,
        archive_manifest_digest="e" * 64,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
        source_state_digest="f" * 64,
    )
    _ = default_minimal_decision_record(
        source_revision=VALID_COMMIT_SHA,
        review_input_digest=compute_review_input_digest(review_input),
    )
    boundary_input = default_minimal_handoff_boundary_input(
        source_revision=VALID_COMMIT_SHA,
        review_input=review_input,
    )
    result = evaluate_operator_review_handoff_boundary(boundary_input)
    assert result["operator_review_handoff_boundary_satisfied"] is True
    assert result["operator_decision_selected"] is False


def test_no_file_archive_environment_git_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file/archive/environment access not allowed in PE-34 tests")

    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)
    # evaluate must not touch filesystem
    result = evaluate_operator_review_handoff_boundary(default_minimal_handoff_boundary_input())
    assert result["operator_review_handoff_boundary_satisfied"] is True


def test_no_positive_btc_xbt_spot_fixtures() -> None:
    boundary_input = default_minimal_handoff_boundary_input(instrument=GENERIC_FUTURES_INSTRUMENT)
    assert boundary_input.instrument == GENERIC_FUTURES_INSTRUMENT
    assert "XBT" not in boundary_input.instrument
    assert "BTC" not in boundary_input.instrument
    result = evaluate_operator_review_handoff_boundary(boundary_input)
    assert result["operator_review_handoff_boundary_satisfied"] is True


def test_canonical_owners_match_expected() -> None:
    boundary_input = default_minimal_handoff_boundary_input()
    assert boundary_input.pe33_coherence_proof.coherence_owner == PE33_COHERENCE_OWNER
    assert boundary_input.pe19_undecided_review_input.review_input_owner == PE19_CONTRACT_VERSION
    assert boundary_input.pe20_undecided_package_eligibility.package_owner == PE20_CONTRACT_VERSION
    assert boundary_input.pe25_cross_slice_closure.closure_owner == PE25_CONTRACT_VERSION
    assert (
        boundary_input.contract_versions.pe33_cross_slice_proof_coherence == PE33_CONTRACT_VERSION
    )


def test_boundary_result_digest_only_when_pass() -> None:
    valid = default_minimal_handoff_boundary_input()
    valid_result = evaluate_operator_review_handoff_boundary(valid)
    assert valid_result["boundary_result_digest"] is not None
    assert valid_result["boundary_result_digest"] == compute_boundary_result_digest(
        valid,
        operator_review_handoff_boundary_satisfied=True,
    )

    broken = replace(
        valid,
        pe33_coherence_proof=replace(
            valid.pe33_coherence_proof,
            integration_proof_digest="0" * 64,
        ),
    )
    broken_result = evaluate_operator_review_handoff_boundary(broken)
    assert broken_result["boundary_result_digest"] is None
