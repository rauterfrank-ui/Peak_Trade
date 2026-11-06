"""Derived binding-candidate alignment records. Authority remains NONE."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_GENERATOR_ID,
    ALIGNMENT_LAYER_ID,
    ALIGNMENT_OUTPUT_ROLE,
    ALIGNMENT_TRANSFORMATION_VERSION,
)
from scripts.ops.forensic_structure_schema_v1.disposition_models import SourceLocus
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue


@dataclass
class T4OverlayRecord:
    derived_record_id: str
    overlay_id: str
    source_order: int
    sidecar_index: int
    layer1_occurrence_id: str
    source_src_id: OptionalValue
    target_ref: OptionalValue
    tsv_directionality: OptionalValue
    sidecar_declared_relation_type: OptionalValue
    layer3_mapped_type: OptionalValue
    byte_start: int
    byte_end: int
    line: OptionalValue
    t4_family: OptionalValue
    overlay_kind: OptionalValue
    field_count: OptionalValue
    content_hash_sha256: OptionalValue
    source_identifier_alias: OptionalValue
    sidecar_subject: OptionalValue
    is_dependency: bool
    t4_flags: dict[str, Any]
    adjudication_status: str
    provenance_type: str
    epistemic_class: str
    residual_ids: list[str]
    source_locus: SourceLocus | None
    source_sha256: str
    sidecar_sha256: str
    layer3_semantic_backfill_performed: bool = False
    occurrence_binding_proven: bool = False
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "adjudication_status": self.adjudication_status,
            "authority": self.authority,
            "byte_end": self.byte_end,
            "byte_start": self.byte_start,
            "content_hash_sha256": self.content_hash_sha256.to_canonical(),
            "derived_record_id": self.derived_record_id,
            "epistemic_class": self.epistemic_class,
            "field_count": self.field_count.to_canonical(),
            "is_dependency": self.is_dependency,
            "layer1_occurrence_id": self.layer1_occurrence_id,
            "layer3_mapped_type": self.layer3_mapped_type.to_canonical(),
            "layer3_semantic_backfill_performed": self.layer3_semantic_backfill_performed,
            "line": self.line.to_canonical(),
            "occurrence_binding_proven": self.occurrence_binding_proven,
            "output_canonical": self.output_canonical,
            "overlay_id": self.overlay_id,
            "overlay_kind": self.overlay_kind.to_canonical(),
            "provenance_type": self.provenance_type,
            "record_class": "T4_OVERLAY_RECORD",
            "residual_ids": list(self.residual_ids),
            "sidecar_declared_relation_type": self.sidecar_declared_relation_type.to_canonical(),
            "sidecar_index": self.sidecar_index,
            "sidecar_sha256": self.sidecar_sha256,
            "sidecar_subject": self.sidecar_subject.to_canonical(),
            "source_identifier_alias": self.source_identifier_alias.to_canonical(),
            "source_locus": None if self.source_locus is None else self.source_locus.to_canonical(),
            "source_order": self.source_order,
            "source_sha256": self.source_sha256,
            "source_src_id": self.source_src_id.to_canonical(),
            "t4_family": self.t4_family.to_canonical(),
            "t4_flags": dict(self.t4_flags),
            "target_ref": self.target_ref.to_canonical(),
            "tsv_directionality": self.tsv_directionality.to_canonical(),
        }


@dataclass
class Layer3RelationRecord:
    derived_record_id: str
    relation_id: str
    relation_type: str
    from_id: str
    to_id: str
    source_order: int
    source_projection_references: dict[str, Any]
    existing_disposition: list[str]
    semantic_status: str
    endpoint_record_ids: list[str]
    residual_ids: list[str]
    provenance_type: str
    evidence_class: str
    epistemic_class: str
    source_sha256: str
    sidecar_sha256: str
    winner_selected: bool = False
    is_dependency: bool = False
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False
    semantic_binding_performed: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "derived_record_id": self.derived_record_id,
            "endpoint_record_ids": list(self.endpoint_record_ids),
            "epistemic_class": self.epistemic_class,
            "evidence_class": self.evidence_class,
            "existing_disposition": list(self.existing_disposition),
            "from_id": self.from_id,
            "is_dependency": self.is_dependency,
            "output_canonical": self.output_canonical,
            "provenance_type": self.provenance_type,
            "record_class": "LAYER3_RELATION_RECORD",
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "residual_ids": list(self.residual_ids),
            "semantic_binding_performed": self.semantic_binding_performed,
            "semantic_status": self.semantic_status,
            "sidecar_sha256": self.sidecar_sha256,
            "source_order": self.source_order,
            "source_projection_references": dict(self.source_projection_references),
            "source_sha256": self.source_sha256,
            "to_id": self.to_id,
            "winner_selected": self.winner_selected,
        }


@dataclass
class EndpointBindingCandidateRecord:
    derived_record_id: str
    endpoint_string: str
    endpoint_side: str
    endpoint_class: str
    relation_id: str
    alias_navigation_references: dict[str, Any]
    possible_structural_candidates: list[dict[str, Any]]
    source_locus_availability: str
    source_loci: list[SourceLocus]
    candidate_state: str
    unresolved_to_occurrence: bool
    occurrence_binding_proven: bool
    provenance_type: str
    evidence_class: str
    reason: str
    residual_ids: list[str]
    existing_disposition: list[str]
    source_sha256: str
    sidecar_sha256: str
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "alias_navigation_references": dict(self.alias_navigation_references),
            "authority": self.authority,
            "candidate_state": self.candidate_state,
            "derived_record_id": self.derived_record_id,
            "endpoint_class": self.endpoint_class,
            "endpoint_side": self.endpoint_side,
            "endpoint_string": self.endpoint_string,
            "epistemic_note": "CANDIDATE_IS_NEVER_PROVEN",
            "evidence_class": self.evidence_class,
            "existing_disposition": list(self.existing_disposition),
            "occurrence_binding_proven": self.occurrence_binding_proven,
            "output_canonical": self.output_canonical,
            "possible_structural_candidates": list(self.possible_structural_candidates),
            "provenance_type": self.provenance_type,
            "reason": self.reason,
            "record_class": "ENDPOINT_BINDING_CANDIDATE_RECORD",
            "relation_id": self.relation_id,
            "residual_ids": list(self.residual_ids),
            "sidecar_sha256": self.sidecar_sha256,
            "source_loci": [locus.to_canonical() for locus in self.source_loci],
            "source_locus_availability": self.source_locus_availability,
            "source_sha256": self.source_sha256,
            "unresolved_to_occurrence": self.unresolved_to_occurrence,
        }


@dataclass
class ViewRecord:
    derived_record_id: str
    view_id: str
    view_class: str
    source_order: int
    parents_field_state: str
    documentary_parent_hints: OptionalValue
    candidate_parent_relationships: OptionalValue
    proven_parentage: bool
    residual_ids: list[str]
    existing_disposition: list[str]
    provenance_type: str
    epistemic_class: str
    source_sha256: str
    sidecar_sha256: str
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "candidate_parent_relationships": self.candidate_parent_relationships.to_canonical(),
            "derived_record_id": self.derived_record_id,
            "documentary_parent_hints": self.documentary_parent_hints.to_canonical(),
            "epistemic_class": self.epistemic_class,
            "existing_disposition": list(self.existing_disposition),
            "output_canonical": self.output_canonical,
            "parents_field_state": self.parents_field_state,
            "proven_parentage": self.proven_parentage,
            "provenance_type": self.provenance_type,
            "record_class": "VIEW_RECORD",
            "residual_ids": list(self.residual_ids),
            "sidecar_sha256": self.sidecar_sha256,
            "source_order": self.source_order,
            "source_sha256": self.source_sha256,
            "view_class": self.view_class,
            "view_id": self.view_id,
        }


@dataclass
class CrossResidualEvidenceEdge:
    derived_record_id: str
    edge_id: str
    source_object: str
    target_object: str
    edge_class: str
    evidence_class: str
    provenance_class: str
    epistemic_state: str
    close_order: bool
    residual_ids: list[str]
    source_order: int
    source_sha256: str
    sidecar_sha256: str
    note: str = ""
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "close_order": self.close_order,
            "derived_record_id": self.derived_record_id,
            "edge_class": self.edge_class,
            "edge_id": self.edge_id,
            "epistemic_state": self.epistemic_state,
            "evidence_class": self.evidence_class,
            "note": self.note,
            "output_canonical": self.output_canonical,
            "provenance_class": self.provenance_class,
            "record_class": "CROSS_RESIDUAL_EVIDENCE_EDGE",
            "residual_ids": list(self.residual_ids),
            "sidecar_sha256": self.sidecar_sha256,
            "source_object": self.source_object,
            "source_order": self.source_order,
            "source_sha256": self.source_sha256,
            "target_object": self.target_object,
        }


@dataclass
class NonIdentityRecord:
    derived_record_id: str
    identity_id: str
    left_term: str
    right_term: str
    statement: str
    source_order: int
    epistemic_class: str
    provenance_type: str
    residual_ids: list[str]
    source_sha256: str
    sidecar_sha256: str
    collapsed: bool = False
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "collapsed": self.collapsed,
            "derived_record_id": self.derived_record_id,
            "epistemic_class": self.epistemic_class,
            "identity_id": self.identity_id,
            "left_term": self.left_term,
            "output_canonical": self.output_canonical,
            "provenance_type": self.provenance_type,
            "record_class": "NON_IDENTITY_RECORD",
            "residual_ids": list(self.residual_ids),
            "right_term": self.right_term,
            "sidecar_sha256": self.sidecar_sha256,
            "source_order": self.source_order,
            "source_sha256": self.source_sha256,
            "statement": self.statement,
        }


@dataclass
class AlignmentIndex:
    t4_records: list[T4OverlayRecord]
    layer3_records: list[Layer3RelationRecord]
    endpoint_records: list[EndpointBindingCandidateRecord]
    view_records: list[ViewRecord]
    cross_residual_edges: list[CrossResidualEvidenceEdge]
    non_identity_records: list[NonIdentityRecord]
    counts: dict[str, Any]
    residual_status: dict[str, str]
    non_inference_audit: dict[str, Any]
    non_identity_audit: dict[str, Any]
    evidence_edge_report: dict[str, Any]
    generated_from_source_sha256: str
    generated_from_sidecar_sha256: str
    a_l_input_hashes: dict[str, str]
    disposition_input_hashes: dict[str, str]
    layer_id: str = ALIGNMENT_LAYER_ID
    generator_id: str = ALIGNMENT_GENERATOR_ID
    output_role: str = ALIGNMENT_OUTPUT_ROLE
    authority: str = ALIGNMENT_AUTHORITY
    output_canonical: bool = False
    semantic_binding_performed: bool = False
    residual_close_performed: bool = False
    currentness_adjudication_performed: bool = False
    supersession_adjudication_performed: bool = False
    occurrence_binding_proven_count: int = 0
    proven_parentage_count: int = 0
    winner_selected_count: int = 0
    transformation_version: str = ALIGNMENT_TRANSFORMATION_VERSION
    extras: dict[str, Any] = field(default_factory=dict)

    def to_canonical(self) -> dict[str, Any]:
        return {
            "a_l_input_hashes": dict(self.a_l_input_hashes),
            "authority": self.authority,
            "counts": dict(self.counts),
            "cross_residual_edges": [e.to_canonical() for e in self.cross_residual_edges],
            "currentness_adjudication_performed": self.currentness_adjudication_performed,
            "disposition_input_hashes": dict(self.disposition_input_hashes),
            "endpoint_records": [r.to_canonical() for r in self.endpoint_records],
            "evidence_edge_report": dict(self.evidence_edge_report),
            "generated_from_sidecar_sha256": self.generated_from_sidecar_sha256,
            "generated_from_source_sha256": self.generated_from_source_sha256,
            "generator_id": self.generator_id,
            "layer3_records": [r.to_canonical() for r in self.layer3_records],
            "layer_id": self.layer_id,
            "non_identity_audit": dict(self.non_identity_audit),
            "non_identity_records": [r.to_canonical() for r in self.non_identity_records],
            "non_inference_audit": dict(self.non_inference_audit),
            "occurrence_binding_proven_count": self.occurrence_binding_proven_count,
            "output_canonical": self.output_canonical,
            "output_role": self.output_role,
            "proven_parentage_count": self.proven_parentage_count,
            "residual_close_performed": self.residual_close_performed,
            "residual_status": dict(self.residual_status),
            "semantic_binding_performed": self.semantic_binding_performed,
            "supersession_adjudication_performed": self.supersession_adjudication_performed,
            "t4_records": [r.to_canonical() for r in self.t4_records],
            "transformation_version": self.transformation_version,
            "view_records": [r.to_canonical() for r in self.view_records],
            "winner_selected_count": self.winner_selected_count,
        }
