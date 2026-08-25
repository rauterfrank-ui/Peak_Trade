"""Bound-input tests for the additive SW-R-002/004/009 disposition layer."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    DR_RESIDUAL_IDS,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    DOCUMENTARY_PARENT_HINT_PAIRS,
    ENDPOINT_DISPOSITION_RECORD_COUNT,
    EXPECTED_ORIENTATION,
    RELATION_DISPOSITION_RECORD_COUNT,
    SECTION_22_SIDECAR_ENDPOINT,
    SIDECAR_DEPENDENCY_SUBJECT,
    VIEW_PARENT_DISPOSITION_RECORD_COUNT,
    VIEW_UNRESOLVED_BOUNDARIES_ID,
)
from scripts.ops.forensic_structure_schema_v1.disposition_layer import build_disposition_layer
from scripts.ops.forensic_structure_schema_v1.disposition_persist import (
    persist_binding_disposition,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes


pytestmark = pytest.mark.skipif(not bound_inputs_available(), reason="bound forensic inputs absent")


def test_orientation_counts_match_adjudicated_baseline() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    assert layer.orientation == EXPECTED_ORIENTATION
    assert layer.orientation["LAYER3_RELATION_COUNT"] == 122
    assert layer.orientation["STRUCTURAL_ORDERED_BEFORE_COUNT"] == 87
    assert layer.orientation["WRAPPER_CONTAINS_COUNT"] == 23
    assert layer.orientation["PREFIX_EPOCH_SUCCEEDS_COUNT"] == 5
    assert layer.orientation["EXPLICIT_DEPENDENCY_COUNT"] == 4
    assert layer.orientation["EXPLICIT_CONFLICT_COUNT"] == 3
    assert layer.orientation["T4_LINE_COUNT"] == 7175
    assert layer.orientation["VIEW_COUNT"] == 12
    assert layer.orientation["VIEW_PARENT_PRESENT_COUNT"] == 1
    assert layer.orientation["VIEW_PARENT_ABSENT_COUNT"] == 11
    assert layer.orientation["WINNER_SELECTED_COUNT"] == 0


def test_disposition_counts_and_negative_proofs() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    assert len(layer.relation_records) == RELATION_DISPOSITION_RECORD_COUNT == 122
    assert len(layer.endpoint_records) == ENDPOINT_DISPOSITION_RECORD_COUNT == 244
    assert len(layer.view_parent_records) == VIEW_PARENT_DISPOSITION_RECORD_COUNT == 12
    assert layer.counts["PROVEN_OCCURRENCE_BINDING_COUNT"] == 0
    assert layer.counts["PROVEN_PARENTAGE_COUNT"] == 0
    assert layer.counts["WINNER_SELECTED_COUNT"] == 0
    assert layer.counts["GUARD_GAP_REMAINING_COUNT"] == 0
    assert layer.counts["UNWIRED_GUARD_COUNT_AFTER"] == 0
    assert layer.authority == "NONE"
    assert layer.output_canonical is False
    assert layer.semantic_binding_performed is False
    assert layer.residual_close_performed is False


def test_cluster_residuals_remain_open() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    for residual_id in ("SW-R-002", "SW-R-004", "SW-R-009"):
        assert layer.residual_status[residual_id] == "OPEN"
    for residual_id in ("SW-R-005", "SW-R-008", "SW-R-015", "DR-002", "DR-003", "DR-006"):
        assert layer.residual_status[residual_id] == "OPEN"
    open_ids = {r.residual_id for r in result.state.residuals if r.status == "OPEN"}
    assert open_ids == set(SW_RESIDUAL_IDS + DR_RESIDUAL_IDS)


def test_structural_ordered_before_projection_is_rel_to_subject() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    sob = [rec for rec in layer.relation_records if rec.raw_value == "STRUCTURAL_ORDERED_BEFORE"]
    assert len(sob) == 87
    for rec in sob:
        assert rec.relation_dispositions is not None
        assert "MECHANICAL_STRUCTURAL_RELATION_ONLY" in rec.relation_dispositions
        assert "DOCUMENTARY_RELATION_ONLY" in rec.relation_dispositions
        assert "NOT_A_SEMANTIC_GRAPH_EDGE" in rec.relation_dispositions
        extras = rec.extras
        assert extras["layer3_projection"] == "REL_ALIAS_TO_SUBJECT_SRC_ALIAS"
        assert extras["layer3_not_t4_src_target_pair"] is True
        assert extras["derived_field_mapping"]["identity_with_layer3_relation_type"] is False
        assert extras["from_id_raw"].startswith("REL-")
        assert extras["to_id_raw"].startswith("SRC-")
        assert extras["t4_subject"] == extras["to_id_raw"]
        assert extras["derived_t4_tsv_target_ref"]["value"] != extras["to_id_raw"]
        assert extras["t4_declared_relation_type"] == "ORDERED_BEFORE"
        assert extras["t4_declared_relation_type"] != rec.raw_value
        assert rec.adjudication_status == "BLOCKED_BY_RESIDUAL"
        assert rec.canonical is False


def test_prefix_epoch_does_not_imply_currentness() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    epochs = [rec for rec in layer.relation_records if rec.raw_value == "PREFIX_EPOCH_SUCCEEDS"]
    assert len(epochs) == 5
    for rec in epochs:
        assert rec.extras["not_currentness"] is True
        assert rec.extras["not_supersession"] is True
        assert rec.extras["winner_selected"] is False
        assert rec.extras["is_dependency"] is False


def test_wrapper_to_id_is_begin_marker_not_body() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    wrappers = [rec for rec in layer.relation_records if rec.raw_value == "WRAPPER_CONTAINS"]
    assert len(wrappers) == 23
    for rec in wrappers:
        rel = result.state.relation_by_id[rec.source_object_id]
        overlay = result.state.overlay_by_id[str(rel.from_binding.value)]
        assert rel.to_binding.value == overlay.payload["begin_occurrence_id"]
        assert rel.to_binding.value != overlay.payload["end_occurrence_id"]
        assert "DR-002" in rec.governing_dr_ids


def test_t4_contains_not_fused_with_wrapper() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    assert layer.counts["T4_CONTAINS_COUNT"] == 2613
    assert layer.counts["T4_CONTAINS_COUNT"] != layer.orientation["WRAPPER_CONTAINS_COUNT"]
    assert all(rec.raw_value != "CONTAINS" for rec in layer.relation_records)


def test_conflict_and_dependency_endpoints_unbound() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    section22 = [
        rec for rec in layer.endpoint_records if rec.raw_value == SECTION_22_SIDECAR_ENDPOINT
    ]
    assert len(section22) == 2
    for rec in section22:
        assert rec.source_layer == "SIDECAR_CONSTRUCTED"
        assert rec.source_loci == []
        assert rec.endpoint_dispositions is not None
        assert "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in rec.endpoint_dispositions
        assert rec.normalized_value.presence == "present"
        assert rec.normalized_value.value["source_proven"] is False
    subjects = [
        rec for rec in layer.endpoint_records if rec.raw_value == SIDECAR_DEPENDENCY_SUBJECT
    ]
    assert len(subjects) == 4
    for rec in subjects:
        assert rec.source_layer == "SIDECAR_CONSTRUCTED"
        assert rec.source_loci == []
        assert rec.endpoint_dispositions is not None
        assert "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in rec.endpoint_dispositions
    aliases = [
        rec
        for rec in layer.endpoint_records
        if rec.endpoint_dispositions is not None
        and "NAVIGATION_ALIAS_ONLY" in rec.endpoint_dispositions
    ]
    assert aliases
    assert all(rec.unresolved is True for rec in layer.endpoint_records)
    assert all(
        rec.endpoint_dispositions is None
        or "OCCURRENCE_BINDING_PROVEN" not in rec.endpoint_dispositions
        for rec in layer.endpoint_records
    )


def test_view_parents_documentary_not_proven() -> None:
    result = run_bound_transformer()
    layer = build_disposition_layer(result.state)
    present = [
        rec
        for rec in layer.view_parent_records
        if rec.source_object_id == VIEW_UNRESOLVED_BOUNDARIES_ID
    ]
    assert len(present) == 1
    rec = present[0]
    assert rec.parent_dispositions is not None
    assert "DOCUMENTARY_PARENT_HINT" in rec.parent_dispositions
    assert "NOT_ADJUDICATED_PARENTAGE" in rec.parent_dispositions
    assert "PROVEN_PARENTAGE" not in rec.parent_dispositions
    pairs = rec.extras["parent_pairs"]["value"]
    observed = [(row["child_raw"], row["parent_raw"]) for row in pairs]
    assert observed == list(DOCUMENTARY_PARENT_HINT_PAIRS)
    absent = [
        rec
        for rec in layer.view_parent_records
        if rec.source_object_id != VIEW_UNRESOLVED_BOUNDARIES_ID
    ]
    assert len(absent) == 11
    for rec in absent:
        assert rec.extras["parents_field_status"] == "ABSENT"
        assert rec.extras["parent_pairs"]["presence"] == "absent"
        assert rec.extras["absent_is_not_no_parent"] is True
        assert "parent_count" not in rec.extras
        assert rec.parent_dispositions is not None
        assert "ABSENT_UNINTERPRETED" in rec.parent_dispositions
        assert "PROVEN_PARENTAGE" not in rec.parent_dispositions


def test_determinism_and_source_sidecar_unmutated(tmp_path) -> None:
    cached = run_bound_transformer()
    first = persist_binding_disposition(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "a",
        result=cached,
    )
    second = persist_binding_disposition(
        source_path=BOUND_SOURCE,
        sidecar_path=BOUND_SIDECAR,
        reports_dir=tmp_path / "b",
        result=cached,
    )
    assert first.layer_sha256 == second.layer_sha256
    assert dumps_canonical_bytes(first.layer.to_canonical()) == dumps_canonical_bytes(
        second.layer.to_canonical()
    )
    assert first.manifest["generated_from_source_sha256"] == BOUND_SOURCE_SHA256
    assert first.manifest["generated_from_sidecar_sha256"] == BOUND_SIDECAR_SHA256
    assert cached.state.source_sha256_after == BOUND_SOURCE_SHA256
    assert cached.state.sidecar_sha256_after == BOUND_SIDECAR_SHA256
    assert cached.state.losslessness_audit is not None
    assert cached.state.losslessness_audit.source_mutated is False
    assert cached.state.losslessness_audit.sidecar_mutated is False


def test_existing_transformer_still_eligible_and_non_canonical() -> None:
    result = run_bound_transformer()
    assert result.output_eligible is True
    assert result.output_role == "TEST_ARTIFACT_ONLY"
    assert result.payload["output_not_canonical"] is True
    assert result.payload["residuals_auto_closed"] is False
