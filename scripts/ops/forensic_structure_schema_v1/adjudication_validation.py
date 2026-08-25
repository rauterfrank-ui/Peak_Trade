"""Adversarial and non-inference validation of the adjudication contract."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_MUST_REMAIN_OPEN,
    ADJUDICATION_OPEN_CLUSTER,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    EXPECTED_CANDIDATE_COUNT,
    EXPECTED_CANDIDATE_FAMILY_COUNT,
    EXPECTED_COMPETING_MEMBER_COUNT,
    EXPECTED_COMPETING_SET_COUNT,
    EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT,
    SECTION_22_SIDECAR_ENDPOINT,
    SIDECAR_DEPENDENCY_SUBJECT,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_guards import AdjudicationGuardProgram
from scripts.ops.forensic_structure_schema_v1.adjudication_models import AdjudicationContract
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def audit_adjudication_contract(contract: AdjudicationContract) -> dict[str, Any]:
    guards = AdjudicationGuardProgram()
    guards.assert_authority_none(contract.authority)
    guards.assert_output_not_canonical(contract.output_canonical)
    guards.assert_no_proven_occurrence(
        count=contract.proven_occurrence_identity_count,
        detail="audit",
    )
    guards.assert_no_parentage(
        performed=False,
        count=contract.proven_parentage_count,
        detail="audit",
    )
    guards.assert_no_currentness(
        performed=contract.currentness_adjudication_performed,
        detail="audit",
    )
    guards.assert_no_supersession(
        performed=contract.supersession_adjudication_performed,
        detail="audit",
    )
    guards.assert_no_winner(count=contract.winner_selected_count, detail="audit")
    guards.assert_no_residual_close(
        performed=contract.residual_close_performed,
        residual_status=contract.residual_status,
    )
    if len(contract.candidate_results) != EXPECTED_CANDIDATE_COUNT:
        _fail("CANDIDATE_POPULATION", "audit candidate count drifted")
    if len(contract.competing_sets) != EXPECTED_COMPETING_SET_COUNT:
        _fail("COMPETING_SET", "audit competing set count drifted")
    if contract.generated_from_source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_SHA_DRIFT", "contract source hash drifted")
    if contract.generated_from_sidecar_sha256 != BOUND_SIDECAR_SHA256:
        _fail("SIDECAR_SHA_DRIFT", "contract sidecar hash drifted")
    for residual_id in (*ADJUDICATION_OPEN_CLUSTER, *ADJUDICATION_MUST_REMAIN_OPEN):
        if contract.residual_status.get(residual_id) != "OPEN":
            _fail("STAGE_H", f"{residual_id} not OPEN")
    return {
        "AUTHORITY_NONE": True,
        "CANDIDATE_FAMILY_COUNT": contract.counts["CANDIDATE_FAMILY_COUNT"],
        "FULL_CANDIDATE_INVENTORY_COMPLETE": True,
        "OUTPUT_CANONICAL": False,
        "PROVEN_OCCURRENCE_IDENTITY_COUNT": 0,
        "RESIDUAL_CLOSE_PERFORMED": False,
    }


def run_adjudication_adversarial_suite(contract: AdjudicationContract) -> dict[str, bool]:
    cases: dict[str, bool] = {}
    _case_f1_rel_alias(contract, cases)
    _case_f2_src_alias(contract, cases)
    _case_f3_layer1_marker(contract, cases)
    _case_f5_f6_epoch(contract, cases)
    _case_f7_sidecar_constructed(contract, cases)
    _case_f9_f11_conflict_triangle(contract, cases)
    _case_adjacency(contract, cases)
    _case_residual_co_tag(contract, cases)
    _case_no_positive_identity(contract, cases)
    _case_hashes_bound(contract, cases)
    _case_absent_unknown_false(contract, cases)
    return cases


def _case_f1_rel_alias(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    rels = [row for row in contract.candidate_results if row.candidate_family == "T4_REL_ALIAS"]
    if len(rels) != 87:
        _fail("F1", f"REL family count {len(rels)}")
    for row in rels:
        if row.occurrence_identity_outcome == "PROVEN_OCCURRENCE_IDENTITY":
            _fail("F1", "REL alias proven")
        if row.occurrence_identity_outcome != "NAVIGATION_LINK_ONLY":
            _fail("F1", f"REL outcome {row.occurrence_identity_outcome}")
        if row.source_locus_availability != "PRESENT":
            _fail("F1", "REL locus expected PRESENT")
    cases["F1_REL_ALIAS_NOT_OCCURRENCE"] = True


def _case_f2_src_alias(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    srcs = [row for row in contract.candidate_results if row.candidate_family == "T3_SRC_ALIAS"]
    if len(srcs) != 87:
        _fail("F2", f"SRC family count {len(srcs)}")
    for row in srcs:
        if row.source_locus_availability != "ABSENT":
            _fail("F2", "SRC locus expected ABSENT")
        if row.occurrence_identity_outcome == "PROVEN_OCCURRENCE_IDENTITY":
            _fail("F2", "SRC alias proven from T4 co-existence")
        if row.occurrence_identity_outcome != "NAVIGATION_LINK_ONLY":
            _fail("F2", f"SRC outcome {row.occurrence_identity_outcome}")
    cases["F2_SRC_ALIAS_NOT_BOUND_FROM_T4"] = True


def _case_f3_layer1_marker(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    markers = [
        row for row in contract.candidate_results if row.candidate_family == "LAYER1_OCCURRENCE"
    ]
    if len(markers) != 23:
        _fail("F3", f"LAYER1 family count {len(markers)}")
    for row in markers:
        if row.endpoint_string.startswith("occ-") is False:
            _fail("F3", "expected occ- endpoint")
        if row.occurrence_identity_outcome == "PROVEN_OCCURRENCE_IDENTITY":
            _fail("F3", "exact string match proven")
        if row.occurrence_identity_outcome != "NOT_BINDABLE_AS_OCCURRENCE":
            _fail("F3", f"marker outcome {row.occurrence_identity_outcome}")
        if "LAYER1_MARKER_REFERENCE_ONLY" not in row.original_dispositions:
            _fail("F3", "marker disposition lost")
    cases["F3_EXACT_STRING_MATCH_NOT_PROVEN"] = True


def _case_f5_f6_epoch(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    epochs = [
        row
        for row in contract.candidate_results
        if row.candidate_family in {"OVERLAY_APPEND_EPOCH_REUSED", "OVERLAY_APPEND_EPOCH_UNIQUE"}
    ]
    if len(epochs) != 10:
        _fail("F5", f"epoch candidate count {len(epochs)}")
    currentness = [
        row
        for row in contract.decision_records
        if row.dimension == "CURRENTNESS" and row.outcome != "UNADJUDICATED"
    ]
    supersession = [
        row
        for row in contract.decision_records
        if row.dimension == "SUPERSESSION" and row.outcome != "UNADJUDICATED"
    ]
    if currentness or supersession:
        _fail("F5", "epoch currentness/supersession executed")
    if contract.currentness_adjudication_performed or contract.supersession_adjudication_performed:
        _fail("F5", "epoch adjudication flags set")
    cases["F5_F6_EPOCH_NOT_CURRENTNESS_OR_SUPERSESSION"] = True


def _case_f7_sidecar_constructed(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    rows = [
        row
        for row in contract.candidate_results
        if row.endpoint_string == SIDECAR_DEPENDENCY_SUBJECT
    ]
    if len(rows) != 4:
        _fail("F7", f"Z2AR_SUI count {len(rows)}")
    for row in rows:
        if row.occurrence_identity_outcome == "PROVEN_OCCURRENCE_IDENTITY":
            _fail("F7", "sidecar constructed proven")
        if row.occurrence_identity_outcome != "NOT_BINDABLE_AS_OCCURRENCE":
            _fail("F7", f"sidecar outcome {row.occurrence_identity_outcome}")
        if "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" not in row.original_dispositions:
            _fail("F7", "invented disposition lost")
        if row.original_ambiguous_binding:
            _fail("F7", "Z2AR_SUI silently marked AMBIGUOUS_BINDING")
    cases["F7_SIDECAR_CONSTRUCTED_NOT_OCCURRENCE"] = True


def _case_f9_f11_conflict_triangle(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    triangle_strings = {"Z2AR", "Z2AP", SECTION_22_SIDECAR_ENDPOINT}
    triangle = [
        row for row in contract.candidate_results if row.endpoint_string in triangle_strings
    ]
    if len(triangle) != 6:
        _fail("F9", f"conflict triangle count {len(triangle)}")
    winners = [row for row in contract.decision_records if row.dimension == "WINNER_SELECTION"]
    if any(row.outcome != "UNADJUDICATED" for row in winners):
        _fail("F9", "winner selection executed")
    if contract.winner_selected_count != 0:
        _fail("F9", "winner selected")
    kinds = {row.competing_set_kind for row in contract.competing_sets}
    if "CONFLICT_TRIANGLE_DOCUMENTARY" not in kinds:
        _fail("F9", "conflict triangle kind missing")
    if "CONFLICT_TRIANGLE_SIDECAR_CONSTRUCTED" not in kinds:
        _fail("F9", "section22 competing kind missing")
    if "OVERLAY_STRING_REUSE" not in kinds:
        _fail("F9", "epoch reuse kind missing")
    if "SIDECAR_CONSTRUCTED_STRING_REUSE" not in kinds:
        _fail("F9", "Z2AR_SUI reuse kind missing")
    cases["F9_F11_CONFLICT_TRIANGLE_NO_WINNER"] = True


def _case_adjacency(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    deps = [row for row in contract.decision_records if row.dimension == "DEPENDENCY"]
    if any(row.outcome != "UNADJUDICATED" for row in deps):
        _fail("ADJACENCY", "dependency inferred from mechanical order")
    if contract.non_inference_audit["NO_BIND_FROM_ADJACENCY"] is not True:
        _fail("ADJACENCY", "adjacency audit false")
    cases["ADJACENCY_87_NOT_DEPENDENCY"] = True


def _case_residual_co_tag(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    if contract.residual_status["SW-R-004"] != "OPEN":
        _fail("SW-R-004", "residual mutated")
    if contract.residual_close_performed:
        _fail("SW-R-004", "residual close performed")
    cases["RESIDUAL_CO_TAG_NOT_CLOSURE"] = True


def _case_no_positive_identity(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    if any(row.positive_evidence_ids for row in contract.decision_records):
        _fail("POSITIVE_EVIDENCE", "positive evidence present")
    if any(row.occurrence_binding_proven for row in contract.candidate_results):
        _fail("SW-R-004", "occurrence_binding_proven flipped")
    cases["NO_POSITIVE_OCCURRENCE_IDENTITY"] = True


def _case_hashes_bound(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    if contract.generated_from_source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_SHA_DRIFT", "hash unbound")
    if contract.generated_from_sidecar_sha256 != BOUND_SIDECAR_SHA256:
        _fail("SIDECAR_SHA_DRIFT", "hash unbound")
    cases["SOURCE_SIDECAR_HASHES_BOUND"] = True


def _case_absent_unknown_false(contract: AdjudicationContract, cases: dict[str, bool]) -> None:
    absents = [
        row for row in contract.candidate_results if row.source_locus_availability == "ABSENT"
    ]
    presents = [
        row for row in contract.candidate_results if row.source_locus_availability == "PRESENT"
    ]
    if not absents or not presents:
        _fail("DR-006", "ABSENT/PRESENT collapsed")
    competing_absent_sets = [
        row for row in contract.competing_sets if row.identity_resolved is True
    ]
    if competing_absent_sets:
        _fail("DR-006", "identity_resolved collapsed from absent proof")
    false_as_absent = [
        row
        for row in contract.evidence_records
        if row.locus_availability not in {"PRESENT", "ABSENT"}
    ]
    if false_as_absent:
        _fail("DR-006", "locus_availability used FALSE/UNKNOWN encoding")
    cases["ABSENT_UNKNOWN_FALSE_PRESERVED"] = True


def assert_population_invariants(contract: AdjudicationContract) -> None:
    if contract.counts["OCCURRENCE_BINDING_CANDIDATE_COUNT"] != EXPECTED_CANDIDATE_COUNT:
        _fail("CANDIDATE_POPULATION", "count drifted")
    if contract.counts["CANDIDATE_FAMILY_COUNT"] != EXPECTED_CANDIDATE_FAMILY_COUNT:
        _fail("CANDIDATE_FAMILY", "family count drifted")
    if contract.counts["COMPETING_CANDIDATE_SET_COUNT"] != EXPECTED_COMPETING_SET_COUNT:
        _fail("COMPETING_SET", "set count drifted")
    if contract.counts["COMPETING_CANDIDATE_MEMBER_COUNT"] != EXPECTED_COMPETING_MEMBER_COUNT:
        _fail("COMPETING_SET", "member count drifted")
    if (
        contract.counts["ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT"]
        != EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT
    ):
        _fail("AMBIGUOUS_UNDERCOUNT", "ambiguous count drifted")
    if contract.authority != ADJUDICATION_AUTHORITY:
        _fail("C9", "authority drifted")
