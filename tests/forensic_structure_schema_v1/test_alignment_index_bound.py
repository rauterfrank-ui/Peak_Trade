"""Bound-input tests for the full-corpus alignment index."""

from __future__ import annotations

import hashlib

import pytest

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_MUST_REMAIN_OPEN,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    EXPECTED_ENDPOINT_RECORD_COUNT,
    EXPECTED_LAYER3_RELATION_COUNT,
    EXPECTED_T4_CONTAINS_COUNT,
    EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT,
    EXPECTED_T4_LAYER3_MAPPED_PRESENT_COUNT,
    EXPECTED_T4_RECORD_COUNT,
    EXPECTED_VIEW_COUNT,
    NON_IDENTITY_STATEMENTS,
    OPEN_CLUSTER_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.alignment_index import build_alignment_index
from scripts.ops.forensic_structure_schema_v1.alignment_persist import persist_alignment_index
from scripts.ops.forensic_structure_schema_v1.alignment_validation import (
    assert_non_identity_preserved,
    audit_alignment_index,
    run_alignment_adversarial_suite,
)
from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes


pytestmark = pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")


def test_full_corpus_counts_and_negative_proofs() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    assert index.counts["T4_RECORD_COUNT"] == EXPECTED_T4_RECORD_COUNT == 7175
    assert index.counts["LAYER3_RELATION_COUNT"] == EXPECTED_LAYER3_RELATION_COUNT == 122
    assert index.counts["ENDPOINT_RECORD_COUNT"] == EXPECTED_ENDPOINT_RECORD_COUNT == 244
    assert index.counts["VIEW_COUNT"] == EXPECTED_VIEW_COUNT == 12
    assert index.counts["OCCURRENCE_BINDING_CANDIDATE_COUNT"] == 244
    assert index.counts["OCCURRENCE_BINDING_PROVEN_COUNT"] == 0
    assert index.counts["PROVEN_PARENTAGE_COUNT"] == 0
    assert index.counts["WINNER_SELECTED_COUNT"] == 0
    assert index.counts["T4_CONTAINS_COUNT"] == EXPECTED_T4_CONTAINS_COUNT
    assert index.counts["T4_LAYER3_MAPPED_PRESENT_COUNT"] == EXPECTED_T4_LAYER3_MAPPED_PRESENT_COUNT
    assert index.counts["T4_LAYER3_MAPPED_NULL_COUNT"] == EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT
    assert index.counts["T4_LAYER3_MAPPED_ABSENT_COUNT"] == 0
    assert index.counts["T4_TO_LAYER3_BACKFILL_COUNT"] == 0
    assert index.counts["SEMANTIC_BINDING_PERFORMED"] is False
    assert index.counts["CURRENTNESS_ADJUDICATION_PERFORMED"] is False
    assert index.counts["SUPERSESSION_ADJUDICATION_PERFORMED"] is False
    assert index.authority == "NONE"
    assert index.output_canonical is False
    assert index.semantic_binding_performed is False
    assert index.residual_close_performed is False
    assert index.cross_residual_edges
    assert len(index.non_identity_records) == len(NON_IDENTITY_STATEMENTS)


def test_open_residual_unknown_and_absent_preservation() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    for residual_id in (*OPEN_CLUSTER_RESIDUAL_IDS, *ALIGNMENT_MUST_REMAIN_OPEN):
        assert index.residual_status[residual_id] == "OPEN"
    absent_views = [rec for rec in index.view_records if rec.parents_field_state == "ABSENT"]
    assert len(absent_views) == 11
    for rec in absent_views:
        payload = rec.to_canonical()
        assert rec.proven_parentage is False
        assert "NO_PARENT" not in payload
        assert rec.documentary_parent_hints.presence == "absent"
        assert rec.epistemic_class != "FALSE"
    present = [rec for rec in index.view_records if rec.parents_field_state == "PRESENT"]
    assert len(present) == 1
    assert present[0].proven_parentage is False
    assert present[0].documentary_parent_hints.presence == "present"


def test_t4_unmapped_rows_are_null_not_backfilled() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    unmapped = [rec for rec in index.t4_records if rec.layer3_mapped_type.presence == "null"]
    assert len(unmapped) == 7088
    assert all(rec.layer3_semantic_backfill_performed is False for rec in unmapped)
    mapped = [rec for rec in index.t4_records if rec.layer3_mapped_type.presence == "present"]
    assert len(mapped) == 87
    assert all(rec.layer3_mapped_type.value == "STRUCTURAL_ORDERED_BEFORE" for rec in mapped)
    for rec in mapped:
        assert rec.sidecar_declared_relation_type.value != rec.layer3_mapped_type.value
        assert rec.t4_flags["tsv_declared_identity"] is False


def test_candidates_never_proven_and_section22_has_no_source_locus() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    assert all(rec.occurrence_binding_proven is False for rec in index.endpoint_records)
    assert all(rec.unresolved_to_occurrence is True for rec in index.endpoint_records)
    section22 = [rec for rec in index.endpoint_records if rec.endpoint_string == "§22"]
    assert section22
    assert all(rec.source_locus_availability == "ABSENT" for rec in section22)
    assert all(rec.source_loci == [] for rec in section22)


def test_cross_residual_edges_are_not_close_order() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    assert all(edge.close_order is False for edge in index.cross_residual_edges)
    assert all(edge.evidence_class for edge in index.cross_residual_edges)
    prereq = [
        edge
        for edge in index.cross_residual_edges
        if edge.provenance_class == "PR_6063_CROSS_RESIDUAL_PREREQUISITES"
    ]
    assert prereq
    assert all(edge.epistemic_state == "rejected" for edge in prereq)


def test_adversarial_suite_and_audits_pass() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    audit = audit_alignment_index(index)
    cases = run_alignment_adversarial_suite(index, state=result.state)
    assert_non_identity_preserved(index)
    assert audit["OPEN_RESIDUAL_PRESERVATION"] is True
    assert len(cases) == 30
    assert all(cases.values())


def test_determinism_idempotence_and_immutability(tmp_path) -> None:
    cached = run_bound_transformer()
    before_src = hashlib.sha256(BOUND_SOURCE.read_bytes()).hexdigest()
    before_sid = hashlib.sha256(BOUND_SIDECAR.read_bytes()).hexdigest()
    first = persist_alignment_index(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "a",
        dataset_dir=tmp_path / "a_data",
        result=cached,
    )
    second = persist_alignment_index(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "b",
        dataset_dir=tmp_path / "b_data",
        result=cached,
    )
    third = persist_alignment_index(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "a",
        dataset_dir=tmp_path / "a_data",
        result=cached,
    )
    assert first.index_sha256 == second.index_sha256 == third.index_sha256
    assert first.shard_sha256s == second.shard_sha256s == third.shard_sha256s
    assert dumps_canonical_bytes(first.index.to_canonical()) == dumps_canonical_bytes(
        second.index.to_canonical()
    )
    after_src = hashlib.sha256(BOUND_SOURCE.read_bytes()).hexdigest()
    after_sid = hashlib.sha256(BOUND_SIDECAR.read_bytes()).hexdigest()
    assert before_src == after_src == BOUND_SOURCE_SHA256
    assert before_sid == after_sid == BOUND_SIDECAR_SHA256
    assert first.immutability_report["source_mutated"] is False
    assert first.immutability_report["sidecar_mutated"] is False
    assert first.immutability_report["a_l_inputs_mutated"] is False
    assert first.immutability_report["disposition_inputs_mutated"] is False
    assert cached.state.losslessness_audit is not None
    assert cached.state.losslessness_audit.source_mutated is False
    assert cached.state.losslessness_audit.sidecar_mutated is False


def test_existing_transformer_and_disposition_remain_non_canonical() -> None:
    result = run_bound_transformer()
    index = build_alignment_index(result.state)
    assert result.output_eligible is True
    assert result.payload["output_not_canonical"] is True
    assert result.payload["residuals_auto_closed"] is False
    assert index.output_canonical is False
    assert index.authority == "NONE"
