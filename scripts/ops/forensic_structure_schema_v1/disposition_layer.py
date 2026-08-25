"""Additive derived binding-disposition layer for SW-R-002/004/009.

Does not replace relation envelopes, views, or sidecar facts.
Does not close residuals, bind occurrences, or adjudicate parentage.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    CLUSTER_RESIDUAL_IDS,
    CROSS_RESIDUAL_PREREQUISITES,
    DERIVED_T4_TSV_INDEX,
    DISPOSITION_AUTHORITY,
    DISPOSITION_LAYER_ID,
    DISPOSITION_TRANSFORMATION_VERSION,
    DOCUMENTARY_PARENT_HINT_PAIRS,
    ENDPOINT_DISPOSITION_RECORD_COUNT,
    EXPECTED_ORIENTATION,
    GUARD_GAP_IDS,
    MUST_REMAIN_OPEN_RESIDUAL_IDS,
    RELATION_DISPOSITION_RECORD_COUNT,
    SECTION_22_PAIR_TOKEN,
    SECTION_22_SIDECAR_ENDPOINT,
    SIDECAR_DEPENDENCY_SUBJECT,
    T4_DECLARED_TO_LAYER3_DERIVED_MAP,
    VIEW_PARENT_DISPOSITION_RECORD_COUNT,
    VIEW_UNRESOLVED_BOUNDARIES_ID,
)
from scripts.ops.forensic_structure_schema_v1.disposition_models import (
    DispositionLayer,
    DispositionRecord,
    SourceLocus,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guard_inventory import inventory_named_guards
from scripts.ops.forensic_structure_schema_v1.guards import GuardProgram
from scripts.ops.forensic_structure_schema_v1.id_spaces import classify_alias
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue
from scripts.ops.forensic_structure_schema_v1.navigation_views import (
    project_navigation_views,
)
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def relation_disposition_classes(relation_type: str) -> list[str]:
    """Multiclass, no silent dedup. Order is stable and type-specific."""
    if relation_type == "STRUCTURAL_ORDERED_BEFORE":
        return [
            "MECHANICAL_STRUCTURAL_RELATION_ONLY",
            "DOCUMENTARY_RELATION_ONLY",
            "NOT_A_SEMANTIC_GRAPH_EDGE",
            "SEMANTIC_STATUS_UNKNOWN",
        ]
    if relation_type == "PREFIX_EPOCH_SUCCEEDS":
        return [
            "MECHANICAL_STRUCTURAL_RELATION_ONLY",
            "NOT_A_SEMANTIC_GRAPH_EDGE",
            "SEMANTIC_STATUS_UNKNOWN",
        ]
    if relation_type == "WRAPPER_CONTAINS":
        return [
            "MECHANICAL_STRUCTURAL_RELATION_ONLY",
            "NOT_A_SEMANTIC_GRAPH_EDGE",
            "SEMANTIC_STATUS_UNKNOWN",
        ]
    if relation_type == "EXPLICIT_CONFLICT":
        return [
            "DOCUMENTARY_RELATION_ONLY",
            "EXPLICIT_TEXT_RECORD",
            "NOT_A_SEMANTIC_GRAPH_EDGE",
            "SEMANTIC_STATUS_UNKNOWN",
        ]
    if relation_type == "EXPLICIT_DEPENDENCY":
        return [
            "DOCUMENTARY_RELATION_ONLY",
            "EXPLICIT_TEXT_RECORD",
            "NOT_A_SEMANTIC_GRAPH_EDGE",
            "SEMANTIC_STATUS_UNKNOWN",
        ]
    _fail("SW-R-002", f"unclassified layer-3 relation_type {relation_type}")
    raise AssertionError("unreachable")


def endpoint_disposition_classes(
    *,
    relation_type: str,
    binding_kind: str,
    raw_value: str,
    unresolved_to_occurrence: bool,
) -> list[str]:
    classes: list[str] = []
    if raw_value == SECTION_22_SIDECAR_ENDPOINT:
        classes.extend(
            [
                "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING",
                "DOCUMENTARY_STRING_ONLY",
                "AMBIGUOUS_BINDING",
                "UNBOUND_NO_SUPPORTED_BINDING",
                "DO_NOT_BIND",
            ]
        )
        return classes
    if raw_value == SIDECAR_DEPENDENCY_SUBJECT:
        classes.extend(
            [
                "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING",
                "DOCUMENTARY_STRING_ONLY",
                "UNBOUND_NO_SUPPORTED_BINDING",
                "DO_NOT_BIND",
            ]
        )
        return classes
    if binding_kind == "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY":
        classes.extend(
            [
                "NAVIGATION_ALIAS_ONLY",
                "UNAMBIGUOUS_BINDING_CANDIDATE_NOT_AUTHORIZED",
                "UNBOUND_NO_SUPPORTED_BINDING",
                "DO_NOT_BIND",
            ]
        )
        return classes
    if binding_kind == "OVERLAY_REFERENCE":
        classes.extend(
            [
                "OVERLAY_REFERENCE_ONLY",
                "UNBOUND_NO_SUPPORTED_BINDING",
                "DO_NOT_BIND",
            ]
        )
        return classes
    if binding_kind == "LAYER1_OCCURRENCE_REFERENCE":
        if relation_type == "WRAPPER_CONTAINS":
            classes.extend(
                [
                    "LAYER1_MARKER_REFERENCE_ONLY",
                    "UNBOUND_NO_SUPPORTED_BINDING",
                    "DO_NOT_BIND",
                ]
            )
            return classes
        _fail("SW-R-004", f"unexpected layer1 endpoint for {relation_type}: {raw_value}")
    if binding_kind == "DOCUMENTARY_STRING_ENDPOINT":
        if relation_type == "EXPLICIT_CONFLICT":
            classes.extend(
                [
                    "DOCUMENTARY_STRING_ONLY",
                    "AMBIGUOUS_BINDING",
                    "UNBOUND_NO_SUPPORTED_BINDING",
                    "DO_NOT_BIND",
                ]
            )
            return classes
        classes.extend(
            [
                "DOCUMENTARY_STRING_ONLY",
                "UNAMBIGUOUS_BINDING_CANDIDATE_NOT_AUTHORIZED",
                "UNBOUND_NO_SUPPORTED_BINDING",
                "DO_NOT_BIND",
            ]
        )
        return classes
    _fail("SW-R-004", f"unclassified endpoint kind {binding_kind} value {raw_value}")
    raise AssertionError("unreachable")


def view_parent_disposition_classes(parents_field_status: str) -> list[str]:
    if parents_field_status == "DOCUMENTARY_UNADJUDICATED":
        return ["DOCUMENTARY_PARENT_HINT", "NOT_ADJUDICATED_PARENTAGE"]
    if parents_field_status in {"ABSENT", "NULL"}:
        return ["ABSENT_UNINTERPRETED", "NOT_ADJUDICATED_PARENTAGE"]
    _fail("SW-R-009", f"unclassified parents_field_status {parents_field_status}")
    raise AssertionError("unreachable")


def _id_space_for_endpoint(raw_value: str, binding_kind: str, binding_id_space: str) -> str:
    alias = classify_alias(raw_value)
    if alias is not None:
        return alias
    return binding_id_space


def _locus_from_occurrence(state: PipelineState, occurrence_id: str) -> SourceLocus | None:
    span = state.layer1_by_id.get(occurrence_id)
    if span is None:
        return None
    return SourceLocus(
        kind="BYTE_RANGE_EXACT",
        byte_start=span.byte_start,
        byte_end=span.byte_end,
        line_start=span.line_start,
        line_end=span.line_end,
        layer1_occurrence_id=span.occurrence_id,
        raw_excerpt=OptionalValue.absent(),
    )


def _locus_from_overlay(
    state: PipelineState, overlay_id: str, *, include_excerpt: bool
) -> SourceLocus | None:
    overlay = state.overlay_by_id.get(overlay_id)
    if overlay is None:
        return None
    start = overlay.payload.get("byte_start")
    end = overlay.payload.get("byte_end")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    excerpt = OptionalValue.absent()
    if include_excerpt and (end - start) <= 4096:
        excerpt = OptionalValue.present(state.source_bytes[start:end].decode("utf-8"))
    occ = overlay.payload.get("occurrence_id")
    line = overlay.payload.get("line")
    return SourceLocus(
        kind="BYTE_RANGE_EXACT",
        byte_start=start,
        byte_end=end,
        line_start=int(line) if isinstance(line, int) else None,
        line_end=int(line) if isinstance(line, int) else None,
        layer1_occurrence_id=str(occ) if isinstance(occ, str) else None,
        raw_excerpt=excerpt,
    )


def _parse_t4_tsv(state: PipelineState, overlay_id: str) -> list[str] | None:
    overlay = state.overlay_by_id.get(overlay_id)
    if overlay is None:
        return None
    start = overlay.payload.get("byte_start")
    end = overlay.payload.get("byte_end")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    raw = state.source_bytes[start:end].decode("utf-8")
    fields = raw.split("|")
    expected = int(overlay.payload.get("field_count") or 0)
    if expected and len(fields) != expected:
        _fail("G5", f"{overlay_id} TSV field_count {expected} != {len(fields)}")
    return fields


def _blocked_status(residual_ids: list[str]) -> str:
    if residual_ids:
        return "BLOCKED_BY_RESIDUAL"
    return "UNADJUDICATED"


def _common_extras() -> dict[str, Any]:
    return {
        "layer_id": DISPOSITION_LAYER_ID,
        "output_authority": DISPOSITION_AUTHORITY,
        "sw_r_002_status": "OPEN",
        "sw_r_004_status": "OPEN",
        "sw_r_009_status": "OPEN",
        "occurrence_binding_performed": False,
        "parentage_adjudication_performed": False,
        "winner_selected": False,
    }


def build_disposition_layer(state: PipelineState) -> DispositionLayer:
    if state.witness is None:
        _fail("DISPOSITION_LAYER", "pipeline witness missing")
    if state.witness.source_sha256 != BOUND_SOURCE_SHA256:
        _fail("SOURCE_SHA_DRIFT", "disposition layer refuses drifted source")
    if state.witness.sidecar_sha256 != BOUND_SIDECAR_SHA256:
        _fail("SIDECAR_SHA_DRIFT", "disposition layer refuses drifted sidecar")
    if not state.output_eligible:
        _fail("DISPOSITION_LAYER", "refusing layer: transformer output_eligible is false")

    orientation = _measure_orientation(state)
    for key, expected in EXPECTED_ORIENTATION.items():
        if orientation[key] != expected:
            _fail("DISPOSITION_LAYER", f"{key}={orientation[key]} != {expected}")

    relation_records: list[DispositionRecord] = []
    endpoint_records: list[DispositionRecord] = []
    guards = GuardProgram()
    t4_contains = 0
    for rec in state.overlays_by_class["t4_rel_row"]:
        if rec.payload.get("declared_relation_type") == "CONTAINS":
            t4_contains += 1
        mapped = rec.payload.get("layer3_mapped_type")
        declared = rec.payload.get("declared_relation_type")
        if mapped is not None and declared == mapped:
            from scripts.ops.forensic_structure_schema_v1.guards import (
                forbid_t4_directionality_identity_with_layer3_relation_type,
            )

            forbid_t4_directionality_identity_with_layer3_relation_type(str(declared), str(mapped))
        if mapped is not None and declared in T4_DECLARED_TO_LAYER3_DERIVED_MAP:
            expected_mapped = T4_DECLARED_TO_LAYER3_DERIVED_MAP[str(declared)]
            if mapped != expected_mapped:
                _fail("G3", f"{rec.overlay_id} derived map drift {declared}->{mapped}")
        if mapped is not None and "directionality" in rec.payload:
            _fail("G3", f"{rec.overlay_id} still carries source field name directionality")

    wrapper_count = 0
    for relation in state.relations:
        guards.check_relation(relation)
        guards.check_cluster_projection(relation, state)
        if relation.relation_type == "WRAPPER_CONTAINS":
            wrapper_count += 1
        relation_records.append(_relation_record(state, relation))
        endpoint_records.append(_endpoint_record(state, relation, "from"))
        endpoint_records.append(_endpoint_record(state, relation, "to"))

    if t4_contains == 0:
        _fail("G4", "T4 CONTAINS rows missing; fusion audit has no baseline")
    if wrapper_count != EXPECTED_ORIENTATION["WRAPPER_CONTAINS_COUNT"]:
        _fail("G4", "WRAPPER_CONTAINS count drifted")
    if t4_contains == wrapper_count:
        from scripts.ops.forensic_structure_schema_v1.guards import (
            forbid_t4_contains_fusion_with_wrapper_contains,
        )

        forbid_t4_contains_fusion_with_wrapper_contains(
            f"counts equal {t4_contains}; identity would be unfalsifiable"
        )

    views = project_navigation_views(state.sidecar["layer4_derived_views"])
    view_records = [_view_parent_record(state, view) for view in views]

    if len(relation_records) != RELATION_DISPOSITION_RECORD_COUNT:
        _fail("DISPOSITION_LAYER", "relation disposition count drifted")
    if len(endpoint_records) != ENDPOINT_DISPOSITION_RECORD_COUNT:
        _fail("DISPOSITION_LAYER", "endpoint disposition count drifted")
    if len(view_records) != VIEW_PARENT_DISPOSITION_RECORD_COUNT:
        _fail("DISPOSITION_LAYER", "view parent disposition count drifted")

    proven_occ = sum(
        1
        for rec in endpoint_records
        if rec.endpoint_dispositions is not None
        and "OCCURRENCE_BINDING_PROVEN" in rec.endpoint_dispositions
    )
    proven_parent = sum(
        1
        for rec in view_records
        if rec.parent_dispositions is not None and "PROVEN_PARENTAGE" in rec.parent_dispositions
    )
    if proven_occ != 0:
        _fail("SW-R-004", "OCCURRENCE_BINDING_PROVEN set without source proof")
    if proven_parent != 0:
        _fail("SW-R-009", "PROVEN_PARENTAGE set without source proof")

    winner = sum(1 for rel in state.relations if rel.winner_selected)
    residual_status = {residual_id: "OPEN" for residual_id in MUST_REMAIN_OPEN_RESIDUAL_IDS}
    residual_status.update({residual_id: "OPEN" for residual_id in CLUSTER_RESIDUAL_IDS})
    for rec in state.residuals:
        if rec.residual_id in residual_status and rec.status != "OPEN":
            _fail("STAGE_H", f"{rec.residual_id} closed by disposition layer")

    inventory = inventory_named_guards()
    gap_closure = {
        "G1": {
            "status": "CLOSED_BY_WIRING",
            "active_guard": "forbid_epoch_succession_currentness",
            "wrapper": "GuardProgram.assert_epoch_succession_not_currentness",
        },
        "G2": {
            "status": "CLOSED_BY_WIRING",
            "active_guard": "forbid_absent_view_parents_as_no_parent",
            "wrapper": "GuardProgram.assert_absent_parents_not_normalized",
        },
        "G3": {
            "status": "CLOSED_BY_WIRING",
            "active_guard": "forbid_t4_directionality_identity_with_layer3_relation_type",
            "note": "declared_relation_type is a derived rename of TSV directionality",
        },
        "G4": {
            "status": "CLOSED_BY_WIRING",
            "active_guard": "forbid_t4_contains_fusion_with_wrapper_contains",
            "t4_contains_count": t4_contains,
            "wrapper_contains_count": wrapper_count,
        },
        "G5": {
            "status": "CLOSED_BY_WIRING",
            "active_guard": "forbid_layer3_ordered_before_as_t4_src_target_pair",
            "projection": "REL_ALIAS -> subject_SRC_ALIAS",
        },
        "G6": {
            "status": "CLOSED_BY_WIRING",
            "active_guards": [
                "forbid_section_22_rewrite_as_source_identity",
                "forbid_sidecar_dependency_subject_as_source_identity",
            ],
        },
    }
    if tuple(gap_closure) != GUARD_GAP_IDS:
        _fail("DISPOSITION_LAYER", "guard gap id drift")

    counts = {
        "RELATION_DISPOSITION_RECORD_COUNT": len(relation_records),
        "ENDPOINT_DISPOSITION_RECORD_COUNT": len(endpoint_records),
        "VIEW_PARENT_DISPOSITION_RECORD_COUNT": len(view_records),
        "PROVEN_OCCURRENCE_BINDING_COUNT": proven_occ,
        "PROVEN_PARENTAGE_COUNT": proven_parent,
        "WINNER_SELECTED_COUNT": winner,
        "T4_CONTAINS_COUNT": t4_contains,
        "GUARD_GAP_BASELINE_COUNT": 6,
        "GUARD_GAP_REMAINING_COUNT": 0,
        "UNWIRED_GUARD_COUNT_BEFORE": 4,
        "UNWIRED_GUARD_COUNT_AFTER": sum(1 for row in inventory.values() if not row["CALLED"]),
    }
    return DispositionLayer(
        relation_records=relation_records,
        endpoint_records=endpoint_records,
        view_parent_records=view_records,
        counts=counts,
        guard_inventory=inventory,
        guard_gap_closure=gap_closure,
        residual_status=residual_status,
        orientation=orientation,
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
    )


def _measure_orientation(state: PipelineState) -> dict[str, int]:
    rels = state.relations
    views = state.sidecar["layer4_derived_views"]
    return {
        "LAYER3_RELATION_COUNT": len(rels),
        "STRUCTURAL_ORDERED_BEFORE_COUNT": sum(
            1 for r in rels if r.relation_type == "STRUCTURAL_ORDERED_BEFORE"
        ),
        "WRAPPER_CONTAINS_COUNT": sum(1 for r in rels if r.relation_type == "WRAPPER_CONTAINS"),
        "PREFIX_EPOCH_SUCCEEDS_COUNT": sum(
            1 for r in rels if r.relation_type == "PREFIX_EPOCH_SUCCEEDS"
        ),
        "EXPLICIT_DEPENDENCY_COUNT": sum(
            1 for r in rels if r.relation_type == "EXPLICIT_DEPENDENCY"
        ),
        "EXPLICIT_CONFLICT_COUNT": sum(1 for r in rels if r.relation_type == "EXPLICIT_CONFLICT"),
        "T4_LINE_COUNT": len(state.overlays_by_class["t4_rel_row"]),
        "VIEW_COUNT": len(views),
        "VIEW_PARENT_PRESENT_COUNT": sum(1 for v in views if "parents" in v),
        "VIEW_PARENT_ABSENT_COUNT": sum(1 for v in views if "parents" not in v),
        "WINNER_SELECTED_COUNT": sum(1 for r in rels if r.winner_selected),
    }


def _relation_record(state: PipelineState, relation: Any) -> DispositionRecord:
    rtype = relation.relation_type
    residuals = ["SW-R-002", *CROSS_RESIDUAL_PREREQUISITES["SW-R-002"]]
    dr_ids: list[str] = []
    if rtype == "WRAPPER_CONTAINS":
        dr_ids.append("DR-002")
        residuals = ["SW-R-002", "DR-002"]
    if rtype == "STRUCTURAL_ORDERED_BEFORE":
        residuals = ["SW-R-002", "SW-R-004"]
    if rtype == "EXPLICIT_DEPENDENCY":
        residuals = ["SW-R-002", "SW-R-004"]
    if rtype == "EXPLICIT_CONFLICT":
        residuals = ["SW-R-002", "SW-R-004"]
    if rtype == "PREFIX_EPOCH_SUCCEEDS":
        residuals = ["SW-R-002"]
    loci: list[SourceLocus] = []
    if relation.sidecar_overlay_id.presence == "present":
        locus = _locus_from_overlay(
            state, str(relation.sidecar_overlay_id.value), include_excerpt=True
        )
        if locus is not None:
            loci.append(locus)
    if relation.source_occurrence_id.presence == "present":
        locus = _locus_from_occurrence(state, str(relation.source_occurrence_id.value))
        if locus is not None:
            loci.append(locus)
    extras = _common_extras()
    extras.update(
        {
            "relation_id": relation.relation_id,
            "relation_type": rtype,
            "is_dependency": relation.is_dependency,
            "winner_selected": relation.winner_selected,
            "from_id_raw": relation.from_binding.value,
            "to_id_raw": relation.to_binding.value,
            "not_a_dependency": rtype != "EXPLICIT_DEPENDENCY",
            "not_semantic_graph_edge": True,
            "not_precedence_winner": True,
            "not_supersession": True,
            "not_currentness": True,
        }
    )
    if rtype == "STRUCTURAL_ORDERED_BEFORE" and relation.sidecar_overlay_id.presence == "present":
        fields = _parse_t4_tsv(state, str(relation.sidecar_overlay_id.value))
        overlay = state.overlay_by_id[str(relation.sidecar_overlay_id.value)]
        extras["t4_declared_relation_type"] = overlay.payload.get("declared_relation_type")
        extras["t4_layer3_mapped_type"] = overlay.payload.get("layer3_mapped_type")
        extras["t4_subject"] = overlay.payload.get("subject")
        extras["derived_field_mapping"] = {
            "source_field": "directionality",
            "sidecar_field": "declared_relation_type",
            "representation": "DERIVED_NOT_SOURCE_IDENTITY",
            "layer3_relation_type": rtype,
            "identity_with_layer3_relation_type": False,
        }
        if fields is not None:
            extras["derived_t4_tsv_directionality"] = {
                "presence": "present",
                "value": fields[DERIVED_T4_TSV_INDEX["directionality"]],
                "representation": "DERIVED_NOT_SOURCE_IDENTITY",
            }
            extras["derived_t4_tsv_target_ref"] = {
                "presence": "present",
                "value": fields[DERIVED_T4_TSV_INDEX["target_ref"]],
                "representation": "DERIVED_NOT_SOURCE_IDENTITY",
            }
            extras["layer3_projection"] = "REL_ALIAS_TO_SUBJECT_SRC_ALIAS"
            extras["layer3_not_t4_src_target_pair"] = True
    return DispositionRecord(
        derived_record_id=mint_transformation_local_id(
            kind="disp-relation",
            source_order=relation.source_order,
            sidecar_stable_suffix=relation.relation_id,
        ),
        record_class="RELATION_DISPOSITION",
        source_object_kind="layer3_relation",
        source_object_id=relation.relation_id,
        source_layer="layer3_relations",
        source_field=OptionalValue.present("relation_type"),
        raw_value=rtype,
        normalized_value=OptionalValue.absent(),
        id_space="RELATION_ID_SPACE",
        source_loci=loci,
        sidecar_locus={
            "collection": "layer3_relations",
            "relation_id": relation.relation_id,
            "source_order": relation.source_order,
        },
        epistemic_basis=relation.relation_epistemic_basis,
        adjudication_status=_blocked_status(residuals),
        unresolved=bool(
            relation.unresolved.presence == "present" and relation.unresolved.value is True
        ),
        relation_dispositions=relation_disposition_classes(rtype),
        endpoint_dispositions=None,
        parent_dispositions=None,
        governing_residual_ids=residuals,
        governing_dr_ids=dr_ids,
        guard_ids=["SW-R-002", "D1", "G1", "G3", "G4", "G5", "G6"],
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
        extras=extras,
        transformation_version=DISPOSITION_TRANSFORMATION_VERSION,
    )


def _endpoint_record(state: PipelineState, relation: Any, side: str) -> DispositionRecord:
    binding = relation.from_binding if side == "from" else relation.to_binding
    raw = str(binding.value)
    sidecar_constructed = raw in {SECTION_22_SIDECAR_ENDPOINT, SIDECAR_DEPENDENCY_SUBJECT}
    loci: list[SourceLocus] = []
    source_layer = "layer3_relations"
    source_field_name = "from_id" if side == "from" else "to_id"
    if sidecar_constructed:
        source_layer = "SIDECAR_CONSTRUCTED"
        # Do not invent a Source locus for sidecar-constructed strings.
        loci = []
    elif relation.sidecar_overlay_id.presence == "present" and side == "from":
        locus = _locus_from_overlay(
            state, str(relation.sidecar_overlay_id.value), include_excerpt=False
        )
        if locus is not None:
            loci.append(locus)
    elif (
        relation.relation_type == "WRAPPER_CONTAINS"
        and side == "to"
        and binding.kind == "LAYER1_OCCURRENCE_REFERENCE"
    ):
        locus = _locus_from_occurrence(state, raw)
        if locus is not None:
            loci.append(locus)
    residuals = ["SW-R-004", *CROSS_RESIDUAL_PREREQUISITES["SW-R-004"]]
    dr_ids = ["DR-003"]
    if relation.relation_type == "WRAPPER_CONTAINS" and side == "to":
        dr_ids.append("DR-002")
        residuals = ["SW-R-004", "DR-002"]
    normalized = OptionalValue.absent()
    if raw == SECTION_22_SIDECAR_ENDPOINT:
        normalized = OptionalValue.present(
            {
                "value": SECTION_22_PAIR_TOKEN,
                "representation": "DERIVED_NOT_SOURCE_IDENTITY",
                "rewrite": "SECTION_22_TO_SECTION_SIGN_22",
                "source_proven": False,
            }
        )
    extras = _common_extras()
    extras.update(
        {
            "relation_id": relation.relation_id,
            "side": side,
            "binding_kind": binding.kind,
            "unresolved_to_occurrence": binding.unresolved_to_occurrence,
            "occurrence_binding_proven": False,
            "sidecar_constructed_string": sidecar_constructed,
        }
    )
    return DispositionRecord(
        derived_record_id=mint_transformation_local_id(
            kind=f"disp-endpoint-{side}",
            source_order=relation.source_order,
            sidecar_stable_suffix=f"{relation.relation_id}-{raw}",
        ),
        record_class="ENDPOINT_DISPOSITION",
        source_object_kind="layer3_relation_endpoint",
        source_object_id=f"{relation.relation_id}:{side}",
        source_layer=source_layer,
        source_field=OptionalValue.present(source_field_name),
        raw_value=raw,
        normalized_value=normalized,
        id_space=_id_space_for_endpoint(raw, binding.kind, binding.id_space),
        source_loci=loci,
        sidecar_locus={
            "collection": "layer3_relations",
            "relation_id": relation.relation_id,
            "field": source_field_name,
            "source_order": relation.source_order,
        },
        epistemic_basis=relation.relation_epistemic_basis,
        adjudication_status=_blocked_status(residuals),
        unresolved=True,
        relation_dispositions=None,
        endpoint_dispositions=endpoint_disposition_classes(
            relation_type=relation.relation_type,
            binding_kind=binding.kind,
            raw_value=raw,
            unresolved_to_occurrence=binding.unresolved_to_occurrence,
        ),
        parent_dispositions=None,
        governing_residual_ids=residuals,
        governing_dr_ids=dr_ids,
        guard_ids=["SW-R-004", "SW-R-008", "G5", "G6"],
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
        extras=extras,
        transformation_version=DISPOSITION_TRANSFORMATION_VERSION,
    )


def _view_parent_record(state: PipelineState, view: dict[str, Any]) -> DispositionRecord:
    view_id = str(view["view_id"])
    status = str(view["parents_field_status"])
    original = view["original_view"]
    residuals = ["SW-R-009", *CROSS_RESIDUAL_PREREQUISITES["SW-R-009"]]
    dr_ids = ["DR-003", "DR-006"]
    pairs_field: dict[str, Any]
    raw_value: Any
    if status == "DOCUMENTARY_UNADJUDICATED":
        parents = original["parents"]
        raw_value = parents
        observed = tuple(sorted((str(k), str(v)) for k, v in parents.items()))
        expected = tuple(sorted(DOCUMENTARY_PARENT_HINT_PAIRS))
        if view_id == VIEW_UNRESOLVED_BOUNDARIES_ID and observed != expected:
            _fail("SW-R-009", "documentary parent hint pairs drifted")
        pair_rows = []
        for child, parent in DOCUMENTARY_PARENT_HINT_PAIRS:
            pair_rows.append(
                {
                    "child_raw": child,
                    "parent_raw": parent,
                    "parent_disposition": [
                        "DOCUMENTARY_PARENT_HINT",
                        "NOT_ADJUDICATED_PARENTAGE",
                    ],
                    "proven_parentage": False,
                    "h1_containment_is_not_parentage": True,
                    "src_region_containment_is_not_parentage": True,
                    "same_line_is_not_semantic_identity": True,
                    "child_endpoint_dispositions": [
                        "DOCUMENTARY_STRING_ONLY",
                        "UNBOUND_NO_SUPPORTED_BINDING",
                        "DO_NOT_BIND",
                    ],
                    "parent_endpoint_dispositions": [
                        "NAVIGATION_ALIAS_ONLY",
                        "UNAMBIGUOUS_BINDING_CANDIDATE_NOT_AUTHORIZED",
                        "UNBOUND_NO_SUPPORTED_BINDING",
                        "DO_NOT_BIND",
                    ],
                }
            )
        pairs_field = {"presence": "present", "value": pair_rows}
    elif status == "ABSENT":
        raw_value = {"presence": "absent"}
        pairs_field = {"presence": "absent"}
    else:
        raw_value = {"presence": "null", "value": None}
        pairs_field = {"presence": "null", "value": None}
    extras = _common_extras()
    extras.update(
        {
            "view_id": view_id,
            "parents_field_status": status,
            "parent_pairs": pairs_field,
            "parentage_adjudicated": False,
            "absent_is_not_no_parent": status == "ABSENT",
            "documentary_hint_is_not_proven_parentage": True,
        }
    )
    GuardProgram().assert_view_parents_not_parentage(view)
    return DispositionRecord(
        derived_record_id=mint_transformation_local_id(
            kind="disp-view-parent",
            source_order=int(view["source_order"]),
            sidecar_stable_suffix=view_id,
        ),
        record_class="VIEW_PARENT_DISPOSITION",
        source_object_kind="layer4_view",
        source_object_id=view_id,
        source_layer="layer4_derived_views",
        source_field=OptionalValue.present("parents")
        if status != "ABSENT"
        else OptionalValue.absent(),
        raw_value=raw_value,
        normalized_value=OptionalValue.absent(),
        id_space="VIEW_ID_SPACE",
        source_loci=[],
        sidecar_locus={
            "collection": "layer4_derived_views",
            "view_id": view_id,
            "source_order": view["source_order"],
        },
        epistemic_basis="STRUCTURAL_INFERENCE" if status == "ABSENT" else "EXPLICIT_TEXT",
        adjudication_status=_blocked_status(residuals),
        unresolved=True,
        relation_dispositions=None,
        endpoint_dispositions=None,
        parent_dispositions=view_parent_disposition_classes(status),
        governing_residual_ids=residuals,
        governing_dr_ids=dr_ids,
        guard_ids=["SW-R-009", "SW-R-005", "G2"],
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
        extras=extras,
        transformation_version=DISPOSITION_TRANSFORMATION_VERSION,
    )
