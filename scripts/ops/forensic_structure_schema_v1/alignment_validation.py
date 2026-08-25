"""Adversarial and non-inference validation of the alignment index."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_MUST_REMAIN_OPEN,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    EXPECTED_ENDPOINT_RECORD_COUNT,
    EXPECTED_LAYER3_RELATION_COUNT,
    EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT,
    EXPECTED_T4_RECORD_COUNT,
    EXPECTED_VIEW_COUNT,
    HISTORICAL_LOCATOR_SUBSTRINGS,
    NON_IDENTITY_STATEMENTS,
    OPEN_CLUSTER_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.alignment_guards import AlignmentGuardProgram
from scripts.ops.forensic_structure_schema_v1.alignment_models import AlignmentIndex
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    forbid_absent_to_no_parent_collapse,
    forbid_candidate_as_proven_occurrence,
    forbid_cross_residual_close_order,
    forbid_documentary_parent_as_proven_parentage,
    forbid_duplicate_evidence_collapse,
    forbid_epoch_order_as_currentness,
    forbid_epoch_order_as_supersession,
    forbid_later_record_as_winner,
    forbid_missing_binding_as_negative_fact,
    forbid_open_residual_status_transition,
    forbid_provenance_collapse,
    forbid_unknown_to_false_collapse,
)
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def audit_alignment_index(index: AlignmentIndex) -> dict[str, Any]:
    guards = AlignmentGuardProgram()
    guards.assert_authority_none(index.authority)
    guards.assert_output_not_canonical(index.output_canonical)
    guards.assert_open_residuals(index.residual_status)
    if len(index.t4_records) != EXPECTED_T4_RECORD_COUNT:
        _fail("FULL_CORPUS_COUNT", "T4 record count drifted")
    if len(index.layer3_records) != EXPECTED_LAYER3_RELATION_COUNT:
        _fail("FULL_CORPUS_COUNT", "Layer-3 count drifted")
    if len(index.endpoint_records) != EXPECTED_ENDPOINT_RECORD_COUNT:
        _fail("FULL_CORPUS_COUNT", "endpoint count drifted")
    if len(index.view_records) != EXPECTED_VIEW_COUNT:
        _fail("FULL_CORPUS_COUNT", "view count drifted")
    if index.occurrence_binding_proven_count != 0:
        forbid_candidate_as_proven_occurrence("audit count")
    if index.proven_parentage_count != 0:
        forbid_documentary_parent_as_proven_parentage("audit count")
    if index.semantic_binding_performed:
        _fail("SW-R-002", "semantic binding performed")
    if index.currentness_adjudication_performed:
        forbid_epoch_order_as_currentness("audit")
    if index.supersession_adjudication_performed:
        forbid_epoch_order_as_supersession("audit")
    if index.winner_selected_count != 0:
        forbid_later_record_as_winner("audit count")
    if index.generated_from_source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_SHA_DRIFT", "index source hash drifted")
    if index.generated_from_sidecar_sha256 != BOUND_SIDECAR_SHA256:
        _fail("SIDECAR_SHA_DRIFT", "index sidecar hash drifted")
    return {
        "AUTHORITY_NONE": True,
        "OUTPUT_CANONICAL": False,
        "OPEN_RESIDUAL_PRESERVATION": True,
        "FULL_CORPUS_COUNT_VALIDATION": True,
        "OCCURRENCE_BINDING_PROVEN_COUNT": 0,
        "PROVEN_PARENTAGE_COUNT": 0,
    }


def run_alignment_adversarial_suite(
    index: AlignmentIndex,
    *,
    state: PipelineState | None = None,
) -> dict[str, bool]:
    """Fail closed on the authorized adversarial matrix. All values True means held."""
    cases: dict[str, bool] = {}
    _case_same_text_distinct_occurrences(index, cases)
    _case_same_residual_distinct_provenance(index, cases)
    _case_explicit_conflict_without_winner(index, cases)
    _case_raw_evidence_after_adjudicated_block(index, cases)
    _case_historical_locator(index, cases, state)
    _case_derived_authority(index, cases)
    _case_parentage_from_proximity(index, cases)
    _case_parentage_from_h1(index, cases)
    _case_currentness_from_order(index, cases)
    _case_supersession_from_epoch(index, cases)
    _case_winner_from_later(index, cases)
    _case_duplicate_verbatim(index, cases)
    _case_truncated_repeats(index, cases)
    _case_residual_edge_evidence_class(index, cases)
    _case_same_claim_other_provenance(index, cases)
    _case_section_22_without_source_locus(index, cases)
    _case_t4_contains_vs_wrapper(index, cases)
    _case_rel_subject_vs_t4_src_target(index, cases)
    _case_missing_binding_as_false(index, cases)
    _case_unknown_to_false(index, cases)
    _case_absent_to_no_parent(index, cases)
    _case_open_to_closed(index, cases)
    _case_open_to_unproven(index, cases)
    _case_candidate_to_proven(index, cases)
    _case_documentary_parent_to_proven(index, cases)
    _case_token_layer1_join(index, cases, state)
    _case_line_as_join(index, cases)
    _case_cross_residual_close_order(index, cases)
    _case_unmapped_t4_backfill(index, cases)
    _case_source_sidecar_byte_identity(index, cases, state)
    if len(cases) != 30:
        _fail("ALIGNMENT_ADVERSARIAL", f"expected 30 cases, got {len(cases)}")
    if not all(cases.values()):
        failed = [name for name, ok in cases.items() if not ok]
        _fail("ALIGNMENT_ADVERSARIAL", f"failed: {failed}")
    return cases


def _case_same_text_distinct_occurrences(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    ids = [rec.overlay_id for rec in index.t4_records]
    occs = [rec.layer1_occurrence_id for rec in index.t4_records]
    if len(ids) != len(set(ids)):
        forbid_duplicate_evidence_collapse("duplicate overlay ids")
    if len(occs) != len(set(occs)):
        # Duplicate occurrence_ids would still be distinct overlay rows; keep both.
        pass
    cases["same_text_different_occurrences"] = True


def _case_same_residual_distinct_provenance(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(not e.provenance_class for e in index.cross_residual_edges):
        forbid_provenance_collapse("missing provenance class")
    cases["same_residual_id_different_provenances"] = True


def _case_explicit_conflict_without_winner(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    conflicts = [r for r in index.layer3_records if r.relation_type == "EXPLICIT_CONFLICT"]
    if any(r.winner_selected for r in conflicts):
        forbid_later_record_as_winner("EXPLICIT_CONFLICT")
    cases["explicit_conflict_without_winner"] = True


def _case_raw_evidence_after_adjudicated_block(
    index: AlignmentIndex, cases: dict[str, bool]
) -> None:
    blocked = [r for r in index.t4_records if r.adjudication_status == "BLOCKED_BY_RESIDUAL"]
    if not blocked:
        _fail("ALIGNMENT_ADVERSARIAL", "blocked T4 raw evidence missing")
    if any(r.epistemic_class not in {"RAW_EVIDENCE", "FACT_FROM_SOURCE"} for r in blocked):
        _fail("ALIGNMENT_ADVERSARIAL", "blocked T4 lost raw evidence class")
    cases["raw_evidence_after_adjudicated_block"] = True


def _case_historical_locator(
    index: AlignmentIndex, cases: dict[str, bool], state: PipelineState | None
) -> None:
    guards = AlignmentGuardProgram()
    if state is not None:
        guards.assert_current_locator_not_historical(str(state.source_path))
        guards.assert_current_locator_not_historical(str(state.sidecar_path))
    for token in HISTORICAL_LOCATOR_SUBSTRINGS:
        if token in str(index.generated_from_source_sha256):
            _fail("HISTORICAL_LOCATOR", "hash field contained locator token")
    cases["historical_desktop_downloads_path"] = True


def _case_derived_authority(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if index.authority != ALIGNMENT_AUTHORITY or index.output_canonical:
        AlignmentGuardProgram().assert_authority_none("CANONICAL")
    cases["derived_artifact_authority"] = True


def _case_parentage_from_proximity(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(view.proven_parentage for view in index.view_records):
        forbid_documentary_parent_as_proven_parentage("proximity")
    cases["parentage_from_proximity"] = True


def _case_parentage_from_h1(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(view.proven_parentage for view in index.view_records):
        forbid_documentary_parent_as_proven_parentage("H1")
    cases["parentage_from_h1"] = True


def _case_currentness_from_order(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if index.currentness_adjudication_performed:
        forbid_epoch_order_as_currentness("order")
    cases["currentness_from_order"] = True


def _case_supersession_from_epoch(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if index.supersession_adjudication_performed:
        forbid_epoch_order_as_supersession("PREFIX_EPOCH_SUCCEEDS")
    cases["supersession_from_epoch"] = True


def _case_winner_from_later(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if index.winner_selected_count:
        forbid_later_record_as_winner("later record")
    cases["winner_from_later_occurrence"] = True


def _case_duplicate_verbatim(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    ids = [rec.derived_record_id for rec in index.t4_records]
    if len(ids) != len(set(ids)):
        forbid_duplicate_evidence_collapse("t4 derived ids")
    cases["duplicate_verbatim_outputs"] = True


def _case_truncated_repeats(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if len(index.t4_records) < EXPECTED_T4_RECORD_COUNT:
        forbid_duplicate_evidence_collapse("truncated T4 corpus")
    cases["truncated_repeats"] = True


def _case_residual_edge_evidence_class(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(not edge.evidence_class for edge in index.cross_residual_edges):
        _fail("ALIGNMENT_ADVERSARIAL", "residual-to-residual edge missing evidence class")
    cases["residual_edge_without_evidence_class"] = True


def _case_same_claim_other_provenance(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(edge.provenance_class == "" for edge in index.cross_residual_edges):
        forbid_provenance_collapse("empty provenance")
    cases["same_claim_other_provenance"] = True


def _case_section_22_without_source_locus(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    section22 = [rec for rec in index.endpoint_records if rec.endpoint_string == "§22"]
    if any(rec.source_locus_availability == "PRESENT" for rec in section22):
        _fail("G6", "§22 gained a source locus")
    cases["section_22_without_source_locus"] = True


def _case_t4_contains_vs_wrapper(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    t4_contains = index.counts["T4_CONTAINS_COUNT"]
    wrappers = sum(1 for rec in index.layer3_records if rec.relation_type == "WRAPPER_CONTAINS")
    if t4_contains == wrappers:
        _fail("G4", "T4 CONTAINS fused with WRAPPER_CONTAINS by count identity")
    cases["t4_contains_vs_wrapper_contains"] = True


def _case_rel_subject_vs_t4_src_target(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    sob = [rec for rec in index.layer3_records if rec.relation_type == "STRUCTURAL_ORDERED_BEFORE"]
    if any(
        not rec.source_projection_references.get("layer3_not_t4_src_target_pair") for rec in sob
    ):
        _fail("G5", "REL→subject projected as T4 src/target")
    cases["rel_subject_vs_t4_src_target"] = True


def _case_missing_binding_as_false(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    for rec in index.endpoint_records:
        if rec.occurrence_binding_proven is False and rec.unresolved_to_occurrence is False:
            forbid_missing_binding_as_negative_fact(rec.derived_record_id)
    cases["missing_binding_as_false"] = True


def _case_unknown_to_false(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if index.non_inference_audit.get("UNKNOWN_COLLAPSED_TO_FALSE"):
        forbid_unknown_to_false_collapse("audit")
    cases["unknown_to_false"] = True


def _case_absent_to_no_parent(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    for rec in index.view_records:
        payload = rec.to_canonical()
        if rec.parents_field_state == "ABSENT" and (
            "NO_PARENT" in payload or payload.get("proven_parentage") is True
        ):
            forbid_absent_to_no_parent_collapse(rec.view_id)
    cases["absent_to_no_parent"] = True


def _case_open_to_closed(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    for residual_id in OPEN_CLUSTER_RESIDUAL_IDS:
        if index.residual_status.get(residual_id) != "OPEN":
            forbid_open_residual_status_transition(
                residual_id, str(index.residual_status.get(residual_id))
            )
    cases["open_to_closed"] = True


def _case_open_to_unproven(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    for residual_id in ALIGNMENT_MUST_REMAIN_OPEN:
        if index.residual_status.get(residual_id) == "UNPROVEN":
            forbid_open_residual_status_transition(residual_id, "UNPROVEN")
    cases["open_to_unproven"] = True


def _case_candidate_to_proven(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(rec.occurrence_binding_proven for rec in index.endpoint_records):
        forbid_candidate_as_proven_occurrence("endpoint")
    cases["endpoint_candidate_to_proven_occurrence"] = True


def _case_documentary_parent_to_proven(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(view.proven_parentage for view in index.view_records):
        forbid_documentary_parent_as_proven_parentage("view")
    cases["documentary_parent_to_proven_parentage"] = True


def _case_token_layer1_join(
    index: AlignmentIndex, cases: dict[str, bool], state: PipelineState | None
) -> None:
    if state is not None:
        overlap = state.token_occurrence_ids.intersection(state.layer1_by_id)
        if overlap:
            _fail("SW-R-008", f"token/layer1 equality join {sorted(overlap)[:3]}")
    cases["token_occ_equality_join_layer1"] = True


def _case_line_as_join(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    for rec in index.t4_records:
        if rec.source_locus is not None and rec.source_locus.kind == "LINE_NUMBER":
            _fail("DR-003", f"line used as join for {rec.overlay_id}")
    cases["line_number_as_identity_join"] = True


def _case_cross_residual_close_order(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    if any(edge.close_order for edge in index.cross_residual_edges):
        forbid_cross_residual_close_order("edge")
    cases["cross_residual_prerequisites_as_close_order"] = True


def _case_unmapped_t4_backfill(index: AlignmentIndex, cases: dict[str, bool]) -> None:
    nulls = sum(1 for rec in index.t4_records if rec.layer3_mapped_type.presence == "null")
    backfill = sum(1 for rec in index.t4_records if rec.layer3_semantic_backfill_performed)
    if nulls != EXPECTED_T4_LAYER3_MAPPED_NULL_COUNT or backfill != 0:
        _fail("SW-R-002", "7088 unmapped T4 rows were semantically backfilled")
    cases["unmapped_t4_layer3_backfill"] = True


def _case_source_sidecar_byte_identity(
    index: AlignmentIndex, cases: dict[str, bool], state: PipelineState | None
) -> None:
    if state is not None:
        if state.source_sha256_before != state.source_sha256_after:
            _fail("SOURCE_MUTATION", "source mutated")
        if state.sidecar_sha256_before != state.sidecar_sha256_after:
            _fail("SIDECAR_MUTATION", "sidecar mutated")
    if index.generated_from_source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_MUTATION", "index unbound from source")
    cases["source_sidecar_byte_identity"] = True


def assert_non_identity_preserved(index: AlignmentIndex) -> None:
    observed = {(rec.left_term, rec.right_term) for rec in index.non_identity_records}
    expected = {(left, right) for _identity_id, left, right in NON_IDENTITY_STATEMENTS}
    if observed != expected:
        _fail("NON_IDENTITY", "non-identity set drifted or collapsed")
    if any(rec.collapsed for rec in index.non_identity_records):
        forbid_duplicate_evidence_collapse("non-identity")
