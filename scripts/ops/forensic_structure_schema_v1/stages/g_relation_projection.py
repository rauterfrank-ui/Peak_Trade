"""Stage G — Relation Projection. Endpoints are annotated, not resolved into occurrences."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import EXPECTED_SOURCE_SHA256
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import ORDERING_RELATION_TYPES
from scripts.ops.forensic_structure_schema_v1.joins import classify_endpoint
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue, RelationEnvelope
from scripts.ops.forensic_structure_schema_v1.state import PipelineState

_BASIS_MAP = {
    "STRUCTURAL_INFERENCE": "STRUCTURAL_DERIVATION",
    "PRIOR_ADJUDICATION_REFERENCE": "PRIOR_ADJUDICATION_REFERENCE",
    "EXPLICIT_TEXT": "EXPLICIT_TEXT_RELATION",
}


def run_stage_g(state: PipelineState) -> None:
    if state.guards is None:
        raise TransformationContractViolation("STAGE_G", "GuardProgram missing")
    overlay_ids = set(state.overlay_by_id)
    layer1_ids = set(state.layer1_by_id)
    relations: list[RelationEnvelope] = []
    by_id: dict[str, RelationEnvelope] = {}
    for index, raw in enumerate(state.sidecar["layer3_relations"]):
        relation_id = str(raw["relation_id"])
        relation_type = str(raw["relation_type"])
        is_dependency = bool(raw["is_dependency"])
        winner_selected = bool(raw["winner_selected"])
        if raw.get("sidecar_authority") != "NONE" or raw.get("target_authority") != "NONE":
            raise TransformationContractViolation(
                "C9",
                f"{relation_id} authority is not NONE",
            )
        if relation_type in ORDERING_RELATION_TYPES and is_dependency:
            raise TransformationContractViolation(
                "D1",
                f"{relation_id} ordering type has is_dependency=true",
            )
        if relation_type == "EXPLICIT_CONFLICT" and winner_selected:
            raise TransformationContractViolation(
                "C5",
                f"{relation_id} winner_selected=true",
            )
        from_binding = classify_endpoint(
            str(raw["from_id"]),
            overlay_ids=overlay_ids,
            layer1_ids=layer1_ids,
            alias_maps=state.alias_to_overlay_id,
        )
        to_binding = classify_endpoint(
            str(raw["to_id"]),
            overlay_ids=overlay_ids,
            layer1_ids=layer1_ids,
            alias_maps=state.alias_to_overlay_id,
        )
        if from_binding.kind == "LAYER1_OCCURRENCE_REFERENCE":
            if str(raw["from_id"]) in state.token_occurrence_ids:
                raise TransformationContractViolation(
                    "SW-R-008",
                    f"{relation_id} from_id used token occ as layer1",
                )
        if to_binding.kind == "LAYER1_OCCURRENCE_REFERENCE":
            if str(raw["to_id"]) in state.token_occurrence_ids:
                raise TransformationContractViolation(
                    "SW-R-008",
                    f"{relation_id} to_id used token occ as layer1",
                )
        basis = str(raw.get("epistemic_basis") or "UNKNOWN")
        envelope = RelationEnvelope(
            transformation_local_id=mint_transformation_local_id(
                kind="relation",
                source_order=index,
                sidecar_stable_suffix=relation_id,
            ),
            relation_id=relation_id,
            relation_type=relation_type,
            relation_provenance=_BASIS_MAP.get(basis, "UNKNOWN"),
            from_binding=from_binding,
            to_binding=to_binding,
            relation_epistemic_basis=basis,
            is_dependency=is_dependency,
            unresolved=OptionalValue.from_mapping(raw, "unresolved"),
            winner_selected=winner_selected,
            source_occurrence_id=OptionalValue.from_mapping(raw, "source_occurrence_id"),
            sidecar_overlay_id=OptionalValue.from_mapping(raw, "t4_rel_overlay_id"),
            end_occurrence_id=OptionalValue.from_mapping(raw, "end_occurrence_id"),
            source_sha256=EXPECTED_SOURCE_SHA256,
            source_order=index,
            pointer_adjudication_performed=OptionalValue.from_mapping(
                raw, "pointer_adjudication_performed"
            ),
            repo_z2cf_imported_as_resolution=OptionalValue.from_mapping(
                raw, "repo_z2cf_imported_as_resolution"
            ),
            not_invented_gate_edge=OptionalValue.from_mapping(raw, "not_invented_gate_edge"),
            pair=OptionalValue.from_mapping(raw, "pair"),
            explicit_source_note=OptionalValue.from_mapping(raw, "explicit_source_note"),
        )
        if envelope.source_occurrence_id.presence == "present":
            occ = str(envelope.source_occurrence_id.value)
            if occ not in layer1_ids:
                raise TransformationContractViolation(
                    "LAYER1_OCCURRENCE_REFERENCE",
                    f"{relation_id} source_occurrence_id {occ} not in LAYER1",
                )
        if envelope.sidecar_overlay_id.presence == "present":
            oid = str(envelope.sidecar_overlay_id.value)
            if oid not in overlay_ids:
                raise TransformationContractViolation(
                    "OVERLAY_REFERENCE",
                    f"{relation_id} t4_rel_overlay_id {oid} unknown",
                )
        if envelope.end_occurrence_id.presence == "present":
            occ = str(envelope.end_occurrence_id.value)
            if occ not in layer1_ids:
                raise TransformationContractViolation(
                    "LAYER1_OCCURRENCE_REFERENCE",
                    f"{relation_id} end_occurrence_id {occ} not in LAYER1",
                )
        if relation_type == "EXPLICIT_DEPENDENCY":
            envelope.gate_membership = "UNKNOWN"
            if not is_dependency:
                raise TransformationContractViolation(
                    "STAGE_G",
                    f"{relation_id} EXPLICIT_DEPENDENCY is_dependency=false",
                )
        state.guards.check_relation(envelope)
        state.guards.check_cluster_projection(envelope, state)
        relations.append(envelope)
        by_id[relation_id] = envelope

    state.relations = relations
    state.relation_by_id = by_id
    state.stages_completed.append("G_RELATION_PROJECTION")
