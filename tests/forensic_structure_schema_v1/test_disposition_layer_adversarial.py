"""Adversarial unit tests for the additive binding-disposition layer."""

from __future__ import annotations

import pytest

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_NAVIGATION_VIEW_COUNT,
    VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
)
from scripts.ops.forensic_structure_schema_v1.disposition_layer import (
    endpoint_disposition_classes,
    relation_disposition_classes,
    view_parent_disposition_classes,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guard_inventory import inventory_named_guards
from scripts.ops.forensic_structure_schema_v1.guards import (
    GuardProgram,
    forbid_epoch_succession_currentness,
    forbid_t4_contains_fusion_with_wrapper_contains,
    forbid_t4_directionality_identity_with_layer3_relation_type,
    forbid_layer3_ordered_before_as_t4_src_target_pair,
    forbid_section_22_rewrite_as_source_identity,
    forbid_sidecar_dependency_subject_as_source_identity,
)
from scripts.ops.forensic_structure_schema_v1.models import Binding, OptionalValue, RelationEnvelope
from scripts.ops.forensic_structure_schema_v1.navigation_views import project_navigation_views


def _view(view_id: str, extra: dict | None = None) -> dict:
    payload = {
        "view_id": view_id,
        "view_role": VIEW_ROLE_NAVIGATION_OR_ANALYSIS_ONLY,
        "target_authority": "NONE",
        "sidecar_authority": "NONE",
        "member_ids": [],
        "member_kind": "demo",
        "does_not_replace_raw_spans": True,
    }
    if extra:
        payload.update(extra)
    return payload


def _relation(**overrides: object) -> RelationEnvelope:
    payload = dict(
        transformation_local_id="tlid-relation-000000-demo",
        relation_id="rel_demo",
        relation_type="PREFIX_EPOCH_SUCCEEDS",
        relation_provenance="STRUCTURAL_DERIVATION",
        from_binding=Binding(
            kind="OVERLAY_REFERENCE",
            value="append_epoch-aaa",
            id_space="OVERLAY_ID_SPACE_PARTITIONED_BY_CLASS",
        ),
        to_binding=Binding(
            kind="OVERLAY_REFERENCE",
            value="append_epoch-bbb",
            id_space="OVERLAY_ID_SPACE_PARTITIONED_BY_CLASS",
        ),
        relation_epistemic_basis="STRUCTURAL_INFERENCE",
        is_dependency=False,
        unresolved=OptionalValue.present(False),
        winner_selected=False,
        source_occurrence_id=OptionalValue.absent(),
        sidecar_overlay_id=OptionalValue.absent(),
        end_occurrence_id=OptionalValue.absent(),
    )
    payload.update(overrides)
    return RelationEnvelope(**payload)  # type: ignore[arg-type]


def test_structural_ordered_before_is_mechanical_and_documentary_not_edge() -> None:
    classes = relation_disposition_classes("STRUCTURAL_ORDERED_BEFORE")
    assert classes.count("MECHANICAL_STRUCTURAL_RELATION_ONLY") == 1
    assert classes.count("DOCUMENTARY_RELATION_ONLY") == 1
    assert classes.count("NOT_A_SEMANTIC_GRAPH_EDGE") == 1
    assert "OCCURRENCE_BINDING_PROVEN" not in classes
    assert classes == [
        "MECHANICAL_STRUCTURAL_RELATION_ONLY",
        "DOCUMENTARY_RELATION_ONLY",
        "NOT_A_SEMANTIC_GRAPH_EDGE",
        "SEMANTIC_STATUS_UNKNOWN",
    ]


def test_source_order_does_not_become_dependency_or_precedence() -> None:
    classes = relation_disposition_classes("STRUCTURAL_ORDERED_BEFORE")
    assert "DEPENDENCY" not in classes
    assert "PRECEDENCE" not in "".join(classes)


def test_epoch_succession_is_mechanical_only() -> None:
    classes = relation_disposition_classes("PREFIX_EPOCH_SUCCEEDS")
    assert classes[0] == "MECHANICAL_STRUCTURAL_RELATION_ONLY"
    assert "NOT_A_SEMANTIC_GRAPH_EDGE" in classes


def test_epoch_succession_currentness_guard_fires() -> None:
    rel = _relation(currentness_status="CURRENT")
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_epoch_succession_not_currentness(rel)
    assert exc.value.rule == "D13"


def test_epoch_succession_supersession_and_winner_guards_fire() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_epoch_succession_not_currentness(_relation(supersession="SUPERSEDED"))
    assert exc.value.rule == "D13"
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_epoch_succession_not_currentness(_relation(winner_selected=True))
    assert exc.value.rule == "D13"
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_epoch_succession_not_currentness(_relation(is_dependency=True))
    assert exc.value.rule == "D13"
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().check_relation(_relation(is_dependency=True))
    assert exc.value.rule == "D1"


def test_epoch_succession_unpromoted_does_not_fire() -> None:
    GuardProgram().assert_epoch_succession_not_currentness(_relation())


def test_alias_equality_does_not_bind_occurrence() -> None:
    binding = Binding(
        kind="EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
        value="REL-000001",
        id_space="T4_REL_ALIAS_SPACE",
        unresolved_to_occurrence=True,
    )
    GuardProgram().assert_endpoint_not_occurrence_bound(binding)
    bound = Binding(
        kind="EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
        value="REL-000001",
        id_space="T4_REL_ALIAS_SPACE",
        unresolved_to_occurrence=False,
    )
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_endpoint_not_occurrence_bound(bound)
    assert exc.value.rule == "SW-R-004"


def test_documentary_string_auto_resolution_forbidden() -> None:
    bound = Binding(
        kind="DOCUMENTARY_STRING_ENDPOINT",
        value="Z2AR",
        id_space="DOCUMENTARY_STRING_ENDPOINT_SPACE",
        unresolved_to_occurrence=False,
    )
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_endpoint_not_occurrence_bound(bound)
    assert exc.value.rule == "SW-R-004"


def test_occurrence_binding_proven_not_emitted_for_known_classes() -> None:
    samples = [
        ("STRUCTURAL_ORDERED_BEFORE", "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY", "REL-000001", True),
        ("WRAPPER_CONTAINS", "LAYER1_OCCURRENCE_REFERENCE", "occ-aaa", True),
        ("PREFIX_EPOCH_SUCCEEDS", "OVERLAY_REFERENCE", "append_epoch-aaa", False),
        ("EXPLICIT_CONFLICT", "DOCUMENTARY_STRING_ENDPOINT", "Z2AR", True),
        ("EXPLICIT_CONFLICT", "DOCUMENTARY_STRING_ENDPOINT", "§22", True),
        (
            "EXPLICIT_DEPENDENCY",
            "DOCUMENTARY_STRING_ENDPOINT",
            "Z2AR_SUI_POSITION_VALUE_ALGEBRA_RECORD",
            True,
        ),
    ]
    for relation_type, kind, raw, unresolved in samples:
        classes = endpoint_disposition_classes(
            relation_type=relation_type,
            binding_kind=kind,
            raw_value=raw,
            unresolved_to_occurrence=unresolved,
        )
        assert "OCCURRENCE_BINDING_PROVEN" not in classes


def test_section_22_rewrite_is_sidecar_constructed_not_source_identity() -> None:
    classes = endpoint_disposition_classes(
        relation_type="EXPLICIT_CONFLICT",
        binding_kind="DOCUMENTARY_STRING_ENDPOINT",
        raw_value="§22",
        unresolved_to_occurrence=True,
    )
    assert "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in classes
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_section_22_rewrite_as_source_identity("§22")
    assert exc.value.rule == "G6"


def test_sidecar_dependency_subject_not_source_identity() -> None:
    classes = endpoint_disposition_classes(
        relation_type="EXPLICIT_DEPENDENCY",
        binding_kind="DOCUMENTARY_STRING_ENDPOINT",
        raw_value="Z2AR_SUI_POSITION_VALUE_ALGEBRA_RECORD",
        unresolved_to_occurrence=True,
    )
    assert "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in classes
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_sidecar_dependency_subject_as_source_identity(
            "Z2AR_SUI_POSITION_VALUE_ALGEBRA_RECORD"
        )
    assert exc.value.rule == "G6"


def test_directionality_is_not_relation_type_identity() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_t4_directionality_identity_with_layer3_relation_type(
            "ORDERED_BEFORE", "ORDERED_BEFORE"
        )
    assert exc.value.rule == "G3"
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_t4_directionality_identity_with_layer3_relation_type(
            "STRUCTURAL_ORDERED_BEFORE", "STRUCTURAL_ORDERED_BEFORE"
        )
    assert exc.value.rule == "G3"


def test_t4_contains_not_wrapper_contains() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_t4_contains_fusion_with_wrapper_contains("identity claimed")
    assert exc.value.rule == "G4"


def test_layer3_not_t4_src_target_pair() -> None:
    with pytest.raises(TransformationContractViolation) as exc:
        forbid_layer3_ordered_before_as_t4_src_target_pair("SRC-000001 -> SRC-000002")
    assert exc.value.rule == "G5"


def test_absent_parents_not_normalized_to_no_parent() -> None:
    views = [_view(f"view_{i:02d}") for i in range(EXPECTED_NAVIGATION_VIEW_COUNT)]
    retained = project_navigation_views(views)
    absent = retained[1]
    assert absent["parents_field_status"] == "ABSENT"
    assert "parent_count" not in absent
    assert "has_parent" not in absent
    assert "root" not in absent
    assert absent.get("parents") is None
    mutated = dict(absent)
    mutated["parent_count"] = 0
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_absent_parents_not_normalized(mutated)
    assert exc.value.rule == "G2"
    mutated = dict(absent)
    mutated["parents"] = {}
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_absent_parents_not_normalized(mutated)
    assert exc.value.rule == "G2"
    mutated = dict(absent)
    mutated["root"] = True
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_absent_parents_not_normalized(mutated)
    assert exc.value.rule == "G2"


def test_json_null_parents_distinct_from_absent() -> None:
    views = [_view(f"view_{i:02d}") for i in range(EXPECTED_NAVIGATION_VIEW_COUNT)]
    views[0]["parents"] = None
    retained = project_navigation_views(views)
    assert retained[0]["parents_field_status"] == "NULL"
    assert retained[1]["parents_field_status"] == "ABSENT"


def test_view_parents_not_adjudicated_parentage() -> None:
    views = [_view(f"view_{i:02d}") for i in range(EXPECTED_NAVIGATION_VIEW_COUNT)]
    views[0]["parents"] = {"U16612": "SRC-000048"}
    retained = project_navigation_views(views)
    first = retained[0]
    assert first["parentage_adjudicated"] is False
    assert first["sw_r_009_status"] == "OPEN"
    assert view_parent_disposition_classes("DOCUMENTARY_UNADJUDICATED") == [
        "DOCUMENTARY_PARENT_HINT",
        "NOT_ADJUDICATED_PARENTAGE",
    ]
    assert "PROVEN_PARENTAGE" not in view_parent_disposition_classes("DOCUMENTARY_UNADJUDICATED")
    mutated = dict(first)
    mutated["parentage_adjudicated"] = True
    with pytest.raises(TransformationContractViolation) as exc:
        GuardProgram().assert_view_parents_not_parentage(mutated)
    assert exc.value.rule == "SW-R-009"


def test_wrapper_containment_not_semantic_parentage() -> None:
    classes = relation_disposition_classes("WRAPPER_CONTAINS")
    assert "MECHANICAL_STRUCTURAL_RELATION_ONLY" in classes
    assert "NOT_A_SEMANTIC_GRAPH_EDGE" in classes
    ep = endpoint_disposition_classes(
        relation_type="WRAPPER_CONTAINS",
        binding_kind="LAYER1_OCCURRENCE_REFERENCE",
        raw_value="occ-begin",
        unresolved_to_occurrence=False,
    )
    assert "LAYER1_MARKER_REFERENCE_ONLY" in ep
    assert "OCCURRENCE_BINDING_PROVEN" not in ep


def test_identical_occ_syntax_does_not_unify_id_spaces() -> None:
    marker = endpoint_disposition_classes(
        relation_type="WRAPPER_CONTAINS",
        binding_kind="LAYER1_OCCURRENCE_REFERENCE",
        raw_value="occ-deadbeef",
        unresolved_to_occurrence=False,
    )
    assert "LAYER1_MARKER_REFERENCE_ONLY" in marker


def test_missing_classification_is_not_negative_fact() -> None:
    absent = view_parent_disposition_classes("ABSENT")
    assert absent == ["ABSENT_UNINTERPRETED", "NOT_ADJUDICATED_PARENTAGE"]
    assert "NO_PARENT" not in absent
    assert "CHILDLESS" not in absent


def test_git_tracked_and_eligible_tokens_are_not_authority() -> None:
    forbid_epoch_succession_currentness
    inventory = inventory_named_guards()
    for name in (
        "forbid_epoch_succession_currentness",
        "forbid_alias_occurrence_bind",
        "forbid_documentary_string_auto_resolution",
        "forbid_view_parents_parentage",
    ):
        row = inventory[name]
        assert row["DEFINED"] is True
        assert row["CALLED"] is True
        assert row["REACHABLE"] is True
        assert row["COVERED_BY_ACTIVE_EQUIVALENT"] is True
        assert row["CALL_SITES"]
