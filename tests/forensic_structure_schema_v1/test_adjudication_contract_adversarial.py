"""Adversarial tests for the derived-only adjudication contract."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.adjudication_evaluator import (
    build_adjudication_contract,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_validation import (
    audit_adjudication_contract,
    run_adjudication_adversarial_suite,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes


def test_full_population_and_zero_positive_bindings() -> None:
    contract = build_adjudication_contract()
    assert contract.counts["OCCURRENCE_BINDING_CANDIDATE_COUNT"] == 244
    assert contract.counts["CANDIDATE_FAMILY_COUNT"] == 11
    assert contract.counts["COMPETING_CANDIDATE_SET_COUNT"] == 8
    assert contract.counts["COMPETING_CANDIDATE_MEMBER_COUNT"] == 18
    assert contract.counts["ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT"] == 6
    assert contract.counts["PROVEN_OCCURRENCE_IDENTITY_COUNT"] == 0
    assert contract.counts["PROVEN_PARENTAGE_COUNT"] == 0
    assert contract.counts["WINNER_SELECTED_COUNT"] == 0
    assert contract.counts["CURRENTNESS_ADJUDICATION_PERFORMED"] is False
    assert contract.counts["SUPERSESSION_ADJUDICATION_PERFORMED"] is False
    assert contract.counts["RESIDUAL_CLOSE_PERFORMED"] is False
    assert contract.authority == "NONE"
    assert contract.output_canonical is False
    assert all(row.authority == "NONE" for row in contract.candidate_results)
    assert all(row.output_canonical is False for row in contract.decision_records)
    assert all(not row.positive_evidence_ids for row in contract.decision_records)
    assert contract.residual_status["SW-R-002"] == "OPEN"
    assert contract.residual_status["SW-R-004"] == "OPEN"
    assert contract.residual_status["SW-R-009"] == "OPEN"


def test_competing_sets_keep_original_ambiguous_undercount_visible() -> None:
    contract = build_adjudication_contract()
    assert len(contract.competing_sets) == 8
    member_ids = [cid for row in contract.competing_sets for cid in row.member_candidate_ids]
    assert len(member_ids) == 18
    assert len(set(member_ids)) == 18
    for row in contract.competing_sets:
        assert row.duplicate_record is False
        assert row.identity_resolved is False
        assert row.resolution_status == "UNRESOLVED"
        assert row.member_candidate_ids == sorted(row.member_candidate_ids)
    ambiguous = [row for row in contract.candidate_results if row.original_ambiguous_binding]
    assert len(ambiguous) == 6
    competing_non_ambiguous = [
        row
        for row in contract.candidate_results
        if row.competing_set_id.presence == "present" and not row.original_ambiguous_binding
    ]
    assert len(competing_non_ambiguous) == 12
    for row in competing_non_ambiguous:
        assert row.occurrence_identity_outcome != "AMBIGUOUS_COMPETING"
    for row in ambiguous:
        assert row.occurrence_identity_outcome == "AMBIGUOUS_COMPETING"
    kinds = {row.competing_set_kind for row in contract.competing_sets}
    assert "CONFLICT_TRIANGLE_DOCUMENTARY" in kinds
    assert "OVERLAY_STRING_REUSE" in kinds
    assert "SIDECAR_CONSTRUCTED_STRING_REUSE" in kinds
    assert "CONFLICT_TRIANGLE_SIDECAR_CONSTRUCTED" in kinds


def test_negative_evidence_applicability_is_not_a_global_copy() -> None:
    contract = build_adjudication_contract()
    ni008 = [
        row for row in contract.evidence_records if row.evidence_reference.startswith("NI-008:")
    ]
    assert len(ni008) == 244
    assert all(row.applicable is False for row in ni008)
    ni006 = [
        row
        for row in contract.evidence_records
        if row.evidence_reference.startswith("NI-006:") and row.applicable
    ]
    assert len(ni006) == 87
    invented = [
        row
        for row in contract.evidence_records
        if row.record_class == "DISPOSITION_DISQUALIFIER"
        and row.evidence_reference == "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING"
        and row.applicable
    ]
    assert len(invented) == 6
    assert contract.counts["NEGATIVE_EVIDENCE_RECORD_COUNT"] == len(contract.evidence_records)
    assert all(row.polarity == "NEGATIVE" for row in contract.evidence_records)


def test_unexecuted_dimensions_stay_unadjudicated() -> None:
    contract = build_adjudication_contract()
    by_dim = {}
    for row in contract.decision_records:
        by_dim.setdefault(row.dimension, []).append(row)
    assert set(by_dim) == set(contract.dimension_model["unexecuted_dimensions"]).union(
        {"OCCURRENCE_IDENTITY"}
    )
    for dimension, rows in by_dim.items():
        assert len(rows) == 244
        if dimension == "OCCURRENCE_IDENTITY":
            assert all(row.dimension_executed is True for row in rows)
            assert all(row.outcome != "UNADJUDICATED" for row in rows)
            assert all(row.outcome != "PROVEN_OCCURRENCE_IDENTITY" for row in rows)
        else:
            assert all(row.dimension_executed is False for row in rows)
            assert all(row.outcome == "UNADJUDICATED" for row in rows)


def test_adversarial_suite_and_non_inference_audit() -> None:
    contract = build_adjudication_contract()
    audit = audit_adjudication_contract(contract)
    suite = run_adjudication_adversarial_suite(contract)
    assert audit["PROVEN_OCCURRENCE_IDENTITY_COUNT"] == 0
    assert all(suite.values())
    assert contract.non_inference_audit["NO_BIND_FROM_ALIAS_ONLY"] is True
    assert contract.non_inference_audit["NO_BIND_FROM_SHA_ONLY"] is True
    assert contract.non_inference_audit["NO_BIND_FROM_STRING_EQUALITY_ONLY"] is True
    assert contract.non_inference_audit["NO_BIND_FROM_ADJACENCY"] is True
    assert contract.non_inference_audit["NO_DEPENDENCY_FROM_MECHANICAL_ORDER"] is True
    assert contract.non_inference_audit["NO_CURRENTNESS_FROM_EPOCH"] is True
    assert contract.non_inference_audit["NO_SUPERSESSION_FROM_EPOCH"] is True
    assert contract.non_inference_audit["NO_WINNER_FROM_LATER_RECORD"] is True
    assert contract.non_inference_audit["NO_PARENTAGE_FROM_VIEW_HINT"] is True
    assert contract.non_inference_audit["NO_AUTHORITY_FROM_STRUCTURE"] is True
    assert contract.non_inference_audit["NO_RESIDUAL_CLOSE_FROM_ADJUDICATION"] is True
    assert contract.non_inference_audit["NO_CANONICALIZATION"] is True


def test_replay_idempotence_same_bytes() -> None:
    first = build_adjudication_contract()
    second = build_adjudication_contract()
    assert dumps_canonical_bytes(first.to_canonical()) == dumps_canonical_bytes(
        second.to_canonical()
    )
    assert first.counts["DECISION_RECORD_COUNT"] == 244 * 15
