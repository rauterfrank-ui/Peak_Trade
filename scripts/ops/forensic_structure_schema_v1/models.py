"""Explicit data models. Null, UNKNOWN, UNCLASSIFIED, NONE, false, and ABSENT are distinct."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    DEFAULT_AUTHORITY_STATUS,
    DEFAULT_CURRENTNESS_STATUS,
    DEFAULT_EPISTEMIC_CLASS,
    DEFAULT_GATE_MEMBERSHIP,
    DEFAULT_PRIMARY_LABEL,
    DEFAULT_SEMANTIC_CONTAINER,
    DEFAULT_SUPERSESSION,
    DEFAULT_WINNER_SELECTED,
    PRESENCE_ABSENT,
    PRESENCE_NULL,
    PRESENCE_PRESENT,
)


@dataclass(frozen=True)
class OptionalValue:
    """Presence-tagged value. Missing sidecar fields are ABSENT, not false."""

    presence: str
    value: Any = None

    @classmethod
    def present(cls, value: Any) -> OptionalValue:
        return cls(PRESENCE_PRESENT, value)

    @classmethod
    def null(cls) -> OptionalValue:
        return cls(PRESENCE_NULL, None)

    @classmethod
    def absent(cls) -> OptionalValue:
        return cls(PRESENCE_ABSENT, None)

    @classmethod
    def from_mapping(cls, record: dict[str, Any], key: str) -> OptionalValue:
        if key not in record:
            return cls.absent()
        if record[key] is None:
            return cls.null()
        return cls.present(record[key])

    def to_canonical(self) -> dict[str, Any]:
        if self.presence == PRESENCE_ABSENT:
            return {"presence": PRESENCE_ABSENT}
        if self.presence == PRESENCE_NULL:
            return {"presence": PRESENCE_NULL, "value": None}
        return {"presence": PRESENCE_PRESENT, "value": self.value}


def optional_from_mapping(record: dict[str, Any], key: str) -> OptionalValue:
    return OptionalValue.from_mapping(record, key)


@dataclass(frozen=True)
class Binding:
    kind: str
    value: str
    id_space: str
    unresolved_to_occurrence: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "id_space": self.id_space,
            "unresolved_to_occurrence": self.unresolved_to_occurrence,
        }


@dataclass
class InputWitness:
    source_path: str
    sidecar_path: str
    source_sha256: str
    sidecar_sha256: str
    source_bytes: int
    source_line_count: int
    schema_id: str
    schema_version: str
    generator_id: str
    target_authority: str
    sidecar_authority: str
    sidecar_role: str
    source_locator_at_observation: str
    bom: bool
    encoding: str
    newline: str
    trailing_newline: bool
    generated_from_immutable_source: bool

    def to_canonical(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "sidecar_path": self.sidecar_path,
            "source_sha256": self.source_sha256,
            "sidecar_sha256": self.sidecar_sha256,
            "source_bytes": self.source_bytes,
            "source_line_count": self.source_line_count,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generator_id": self.generator_id,
            "target_authority": self.target_authority,
            "sidecar_authority": self.sidecar_authority,
            "sidecar_role": self.sidecar_role,
            "source_locator_at_observation": self.source_locator_at_observation,
            "bom": self.bom,
            "encoding": self.encoding,
            "newline": self.newline,
            "trailing_newline": self.trailing_newline,
            "generated_from_immutable_source": self.generated_from_immutable_source,
        }


@dataclass(frozen=True)
class Layer1Occurrence:
    occurrence_id: str
    source_sequence: int
    byte_start: int
    byte_end: int
    line_start: int
    line_end: int
    content_hash_sha256: str
    mechanical_type: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "occurrence_id": self.occurrence_id,
            "source_sequence": self.source_sequence,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "content_hash_sha256": self.content_hash_sha256,
            "mechanical_type": self.mechanical_type,
        }


@dataclass
class OverlayRecord:
    overlay_id: str
    overlay_kind: OptionalValue
    overlay_class: str
    payload: dict[str, Any]
    sidecar_index: int
    byte_start: OptionalValue
    byte_end: OptionalValue

    def to_index_canonical(self) -> dict[str, Any]:
        """Index projection only. Full sidecar payload is not re-emitted."""
        return {
            "overlay_id": self.overlay_id,
            "overlay_kind": self.overlay_kind.to_canonical(),
            "overlay_class": self.overlay_class,
            "sidecar_index": self.sidecar_index,
            "byte_start": self.byte_start.to_canonical(),
            "byte_end": self.byte_end.to_canonical(),
        }


@dataclass
class ProvenanceTag:
    subject_kind: str
    subject_id: str
    provenance_type: str
    epistemic_basis: OptionalValue
    sidecar_index: int

    def to_canonical(self) -> dict[str, Any]:
        return {
            "subject_kind": self.subject_kind,
            "subject_id": self.subject_id,
            "provenance_type": self.provenance_type,
            "epistemic_basis": self.epistemic_basis.to_canonical(),
            "sidecar_index": self.sidecar_index,
        }


@dataclass
class SemanticEnvelope:
    transformation_local_id: str
    source_byte_start: int
    source_byte_end: int
    source_sha256: str
    sidecar_overlay_id: OptionalValue
    layer1_occurrence_id: OptionalValue
    token_occurrence_id: OptionalValue
    provenance_type: str
    epistemic_class: str = DEFAULT_EPISTEMIC_CLASS
    authority_status: str = DEFAULT_AUTHORITY_STATUS
    currentness_status: str = DEFAULT_CURRENTNESS_STATUS
    unresolved_status: OptionalValue = field(default_factory=OptionalValue.absent)
    source_order: int = 0
    gate_membership: str = DEFAULT_GATE_MEMBERSHIP
    supersession: str = DEFAULT_SUPERSESSION
    primary_label: str = DEFAULT_PRIMARY_LABEL
    semantic_container: str = DEFAULT_SEMANTIC_CONTAINER
    content_class: str = DEFAULT_EPISTEMIC_CLASS
    t5_label_verbatim: OptionalValue = field(default_factory=OptionalValue.absent)
    hash_kind: OptionalValue = field(default_factory=OptionalValue.absent)
    classified_source_line: OptionalValue = field(default_factory=OptionalValue.absent)
    binds_blob_sha256: OptionalValue = field(default_factory=OptionalValue.absent)
    binds_blob_sha256_matches_current: OptionalValue = field(default_factory=OptionalValue.absent)
    currentness_upgrade: OptionalValue = field(default_factory=OptionalValue.absent)
    temporal_status: OptionalValue = field(default_factory=OptionalValue.absent)
    overlay_kind: OptionalValue = field(default_factory=OptionalValue.absent)
    overlay_class: str = ""
    token_class: OptionalValue = field(default_factory=OptionalValue.absent)
    token_verbatim: OptionalValue = field(default_factory=OptionalValue.absent)
    normalized: OptionalValue = field(default_factory=OptionalValue.absent)
    locator_role: OptionalValue = field(default_factory=OptionalValue.absent)
    collapsed: OptionalValue = field(default_factory=OptionalValue.absent)
    instance_vs_mention: OptionalValue = field(default_factory=OptionalValue.absent)
    is_dependency: OptionalValue = field(default_factory=OptionalValue.absent)
    residuals: list[str] = field(default_factory=list)
    winner_selected: bool = DEFAULT_WINNER_SELECTED

    def to_canonical(self) -> dict[str, Any]:
        return {
            "transformation_local_id": self.transformation_local_id,
            "source_byte_start": self.source_byte_start,
            "source_byte_end": self.source_byte_end,
            "source_sha256": self.source_sha256,
            "sidecar_overlay_id": self.sidecar_overlay_id.to_canonical(),
            "layer1_occurrence_id": self.layer1_occurrence_id.to_canonical(),
            "token_occurrence_id": self.token_occurrence_id.to_canonical(),
            "provenance_type": self.provenance_type,
            "epistemic_class": self.epistemic_class,
            "authority_status": self.authority_status,
            "currentness_status": self.currentness_status,
            "unresolved_status": self.unresolved_status.to_canonical(),
            "source_order": self.source_order,
            "gate_membership": self.gate_membership,
            "supersession": self.supersession,
            "primary_label": self.primary_label,
            "semantic_container": self.semantic_container,
            "content_class": self.content_class,
            "t5_label_verbatim": self.t5_label_verbatim.to_canonical(),
            "hash_kind": self.hash_kind.to_canonical(),
            "classified_source_line": self.classified_source_line.to_canonical(),
            "binds_blob_sha256": self.binds_blob_sha256.to_canonical(),
            "binds_blob_sha256_matches_current": (
                self.binds_blob_sha256_matches_current.to_canonical()
            ),
            "currentness_upgrade": self.currentness_upgrade.to_canonical(),
            "temporal_status": self.temporal_status.to_canonical(),
            "overlay_kind": self.overlay_kind.to_canonical(),
            "overlay_class": self.overlay_class,
            "token_class": self.token_class.to_canonical(),
            "token_verbatim": self.token_verbatim.to_canonical(),
            "normalized": self.normalized.to_canonical(),
            "locator_role": self.locator_role.to_canonical(),
            "collapsed": self.collapsed.to_canonical(),
            "instance_vs_mention": self.instance_vs_mention.to_canonical(),
            "is_dependency": self.is_dependency.to_canonical(),
            "residuals": list(self.residuals),
            "winner_selected": self.winner_selected,
        }


@dataclass
class RelationEnvelope:
    transformation_local_id: str
    relation_id: str
    relation_type: str
    relation_provenance: str
    from_binding: Binding
    to_binding: Binding
    relation_epistemic_basis: str
    is_dependency: bool
    unresolved: OptionalValue
    winner_selected: bool
    source_occurrence_id: OptionalValue
    sidecar_overlay_id: OptionalValue
    end_occurrence_id: OptionalValue
    authority_status: str = DEFAULT_AUTHORITY_STATUS
    currentness_status: str = DEFAULT_CURRENTNESS_STATUS
    gate_membership: str = DEFAULT_GATE_MEMBERSHIP
    supersession: str = DEFAULT_SUPERSESSION
    semantic_container: str = DEFAULT_SEMANTIC_CONTAINER
    source_sha256: str = ""
    source_order: int = 0
    pointer_adjudication_performed: OptionalValue = field(default_factory=OptionalValue.absent)
    repo_z2cf_imported_as_resolution: OptionalValue = field(default_factory=OptionalValue.absent)
    not_invented_gate_edge: OptionalValue = field(default_factory=OptionalValue.absent)
    pair: OptionalValue = field(default_factory=OptionalValue.absent)
    explicit_source_note: OptionalValue = field(default_factory=OptionalValue.absent)

    def to_canonical(self) -> dict[str, Any]:
        return {
            "transformation_local_id": self.transformation_local_id,
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "relation_provenance": self.relation_provenance,
            "from_binding": self.from_binding.to_canonical(),
            "to_binding": self.to_binding.to_canonical(),
            "relation_epistemic_basis": self.relation_epistemic_basis,
            "is_dependency": self.is_dependency,
            "unresolved": self.unresolved.to_canonical(),
            "winner_selected": self.winner_selected,
            "source_occurrence_id": self.source_occurrence_id.to_canonical(),
            "sidecar_overlay_id": self.sidecar_overlay_id.to_canonical(),
            "end_occurrence_id": self.end_occurrence_id.to_canonical(),
            "authority_status": self.authority_status,
            "currentness_status": self.currentness_status,
            "gate_membership": self.gate_membership,
            "supersession": self.supersession,
            "semantic_container": self.semantic_container,
            "source_sha256": self.source_sha256,
            "source_order": self.source_order,
            "pointer_adjudication_performed": (self.pointer_adjudication_performed.to_canonical()),
            "repo_z2cf_imported_as_resolution": (
                self.repo_z2cf_imported_as_resolution.to_canonical()
            ),
            "not_invented_gate_edge": self.not_invented_gate_edge.to_canonical(),
            "pair": self.pair.to_canonical(),
            "explicit_source_note": self.explicit_source_note.to_canonical(),
        }


@dataclass
class ResidualRecord:
    residual_id: str
    title: str
    status: str
    auto_closed: bool
    residual_class: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "residual_id": self.residual_id,
            "title": self.title,
            "status": self.status,
            "auto_closed": self.auto_closed,
            "residual_class": self.residual_class,
        }


@dataclass
class ContractTestResult:
    test_id: str
    status: str
    detail: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class InvariantReport:
    results: dict[str, bool]
    measurements: dict[str, Any]
    passed: bool

    def to_canonical(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "results": dict(self.results),
            "measurements": dict(self.measurements),
        }


@dataclass
class LosslessnessAudit:
    passed: bool
    counts: dict[str, Any]
    source_mutated: bool
    sidecar_mutated: bool
    source_sha256_before: str
    source_sha256_after: str
    sidecar_sha256_before: str
    sidecar_sha256_after: str

    def to_canonical(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counts": dict(self.counts),
            "source_mutated": self.source_mutated,
            "sidecar_mutated": self.sidecar_mutated,
            "source_sha256_before": self.source_sha256_before,
            "source_sha256_after": self.source_sha256_after,
            "sidecar_sha256_before": self.sidecar_sha256_before,
            "sidecar_sha256_after": self.sidecar_sha256_after,
        }
