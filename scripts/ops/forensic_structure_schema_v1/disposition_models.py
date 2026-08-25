"""Derived binding-disposition records. Authority remains NONE."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    DISPOSITION_AUTHORITY,
    DISPOSITION_GENERATOR_ID,
    DISPOSITION_LAYER_ID,
    DISPOSITION_OUTPUT_ROLE,
    DISPOSITION_TRANSFORMATION_VERSION,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue


def _presence_list(values: list[str] | None) -> dict[str, Any]:
    if values is None:
        return {"presence": "absent"}
    return {"presence": "present", "value": list(values)}


@dataclass(frozen=True)
class SourceLocus:
    kind: str
    byte_start: int
    byte_end: int
    line_start: int | None
    line_end: int | None
    layer1_occurrence_id: str | None
    raw_excerpt: OptionalValue = field(default_factory=OptionalValue.absent)

    def to_canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "layer1_occurrence_id": self.layer1_occurrence_id,
            "raw_excerpt": self.raw_excerpt.to_canonical(),
        }


@dataclass
class DispositionRecord:
    derived_record_id: str
    record_class: str
    source_object_kind: str
    source_object_id: str
    source_layer: str
    source_field: OptionalValue
    raw_value: Any
    normalized_value: OptionalValue
    id_space: str
    source_loci: list[SourceLocus]
    sidecar_locus: dict[str, Any]
    epistemic_basis: str
    adjudication_status: str
    unresolved: bool
    relation_dispositions: list[str] | None
    endpoint_dispositions: list[str] | None
    parent_dispositions: list[str] | None
    governing_residual_ids: list[str]
    governing_dr_ids: list[str]
    guard_ids: list[str]
    generated_from_source_sha256: str
    generated_from_sidecar_sha256: str
    extras: dict[str, Any] = field(default_factory=dict)
    transformation_version: str = DISPOSITION_TRANSFORMATION_VERSION
    authority: str = DISPOSITION_AUTHORITY
    canonical: bool = False
    semantic_binding_performed: bool = False
    output_canonical: bool = False
    residual_close_performed: bool = False

    def to_canonical(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "adjudication_status": self.adjudication_status,
            "authority": self.authority,
            "canonical": self.canonical,
            "derived_record_id": self.derived_record_id,
            "endpoint_dispositions": _presence_list(self.endpoint_dispositions),
            "epistemic_basis": self.epistemic_basis,
            "generated_from_sidecar_sha256": self.generated_from_sidecar_sha256,
            "generated_from_source_sha256": self.generated_from_source_sha256,
            "governing_dr_ids": list(self.governing_dr_ids),
            "governing_residual_ids": list(self.governing_residual_ids),
            "guard_ids": list(self.guard_ids),
            "id_space": self.id_space,
            "normalized_value": self.normalized_value.to_canonical(),
            "output_canonical": self.output_canonical,
            "parent_dispositions": _presence_list(self.parent_dispositions),
            "raw_value": self.raw_value,
            "record_class": self.record_class,
            "relation_dispositions": _presence_list(self.relation_dispositions),
            "residual_close_performed": self.residual_close_performed,
            "semantic_binding_performed": self.semantic_binding_performed,
            "sidecar_locus": dict(self.sidecar_locus),
            "source_field": self.source_field.to_canonical(),
            "source_layer": self.source_layer,
            "source_loci": [locus.to_canonical() for locus in self.source_loci],
            "source_object_id": self.source_object_id,
            "source_object_kind": self.source_object_kind,
            "transformation_version": self.transformation_version,
            "unresolved": self.unresolved,
        }
        payload.update(self.extras)
        return payload


@dataclass
class DispositionLayer:
    relation_records: list[DispositionRecord]
    endpoint_records: list[DispositionRecord]
    view_parent_records: list[DispositionRecord]
    counts: dict[str, Any]
    guard_inventory: dict[str, Any]
    guard_gap_closure: dict[str, Any]
    residual_status: dict[str, Any]
    orientation: dict[str, int]
    generated_from_source_sha256: str
    generated_from_sidecar_sha256: str
    layer_id: str = DISPOSITION_LAYER_ID
    generator_id: str = DISPOSITION_GENERATOR_ID
    output_role: str = DISPOSITION_OUTPUT_ROLE
    authority: str = DISPOSITION_AUTHORITY
    output_canonical: bool = False
    semantic_binding_performed: bool = False
    residual_close_performed: bool = False
    transformation_version: str = DISPOSITION_TRANSFORMATION_VERSION

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "counts": dict(self.counts),
            "endpoint_dispositions": [r.to_canonical() for r in self.endpoint_records],
            "generated_from_sidecar_sha256": self.generated_from_sidecar_sha256,
            "generated_from_source_sha256": self.generated_from_source_sha256,
            "generator_id": self.generator_id,
            "guard_gap_closure": dict(self.guard_gap_closure),
            "guard_inventory": dict(self.guard_inventory),
            "layer_id": self.layer_id,
            "orientation": dict(self.orientation),
            "output_canonical": self.output_canonical,
            "output_role": self.output_role,
            "relation_dispositions": [r.to_canonical() for r in self.relation_records],
            "residual_close_performed": self.residual_close_performed,
            "residual_status": dict(self.residual_status),
            "semantic_binding_performed": self.semantic_binding_performed,
            "transformation_version": self.transformation_version,
            "view_parent_dispositions": [r.to_canonical() for r in self.view_parent_records],
        }
