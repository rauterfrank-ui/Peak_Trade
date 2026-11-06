"""Derived-only adjudication records. Authority remains NONE."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_CONTRACT_VERSION,
    ADJUDICATION_GENERATOR_ID,
    ADJUDICATION_LAYER_ID,
    ADJUDICATION_OUTPUT_ROLE,
    ADJUDICATION_TRANSFORMATION_VERSION,
    OPERATOR_AUTHORIZATION_SCOPE,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue


def _optional_from_presence(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {"presence": "absent"}
    if payload.get("presence") == "absent":
        return {"presence": "absent"}
    return dict(payload)


@dataclass(frozen=True)
class PresenceTagged:
    """ABSENT / NULL / PRESENT stay distinct. Null is not ABSENT."""

    presence: str
    value: Any = None

    @classmethod
    def present(cls, value: Any) -> PresenceTagged:
        return cls("present", value)

    @classmethod
    def absent(cls) -> PresenceTagged:
        return cls("absent", None)

    @classmethod
    def null(cls) -> PresenceTagged:
        return cls("null", None)

    def to_canonical(self) -> dict[str, Any]:
        if self.presence == "absent":
            return {"presence": "absent"}
        if self.presence == "null":
            return {"presence": "null", "value": None}
        return {"presence": "present", "value": self.value}


@dataclass
class EvidenceRecord:
    evidence_id: str
    candidate_id: str
    dimension: str
    epistemic_class: str
    record_class: str
    polarity: str
    source_sha256: str
    sidecar_sha256: str
    locus_availability: str
    locus: dict[str, Any] | None
    evidence_reference: str
    reason_code: str
    applicable: bool
    source_provenance: str
    human_detail: str = ""
    authority: str = ADJUDICATION_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        locus_payload: dict[str, Any]
        if self.locus_availability == "ABSENT":
            locus_payload = {"presence": "absent"}
        elif self.locus is None:
            locus_payload = {"presence": "absent"}
        else:
            locus_payload = {"presence": "present", "value": dict(self.locus)}
        return {
            "applicable": self.applicable,
            "authority": self.authority,
            "candidate_id": self.candidate_id,
            "dimension": self.dimension,
            "epistemic_class": self.epistemic_class,
            "evidence_id": self.evidence_id,
            "evidence_reference": self.evidence_reference,
            "human_detail": self.human_detail,
            "locus": locus_payload,
            "locus_availability": self.locus_availability,
            "output_canonical": self.output_canonical,
            "polarity": self.polarity,
            "reason_code": self.reason_code,
            "record_class": self.record_class,
            "sidecar_sha256": self.sidecar_sha256,
            "source_provenance": self.source_provenance,
            "source_sha256": self.source_sha256,
        }


@dataclass
class AdjudicationDecisionRecord:
    decision_id: str
    candidate_id: str
    dimension: str
    outcome: str
    reason_codes: list[str]
    positive_evidence_ids: list[str]
    negative_evidence_ids: list[str]
    ambiguity_set_id: PresenceTagged
    input_source_sha256: str
    input_sidecar_sha256: str
    input_candidate_index_sha256: str
    generator_id: str
    contract_version: str
    operator_authorization_scope: str
    dimension_executed: bool
    authority: str = ADJUDICATION_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "ambiguity_set_id": self.ambiguity_set_id.to_canonical(),
            "authority": self.authority,
            "candidate_id": self.candidate_id,
            "contract_version": self.contract_version,
            "decision_id": self.decision_id,
            "dimension": self.dimension,
            "dimension_executed": self.dimension_executed,
            "generator_id": self.generator_id,
            "input_candidate_index_sha256": self.input_candidate_index_sha256,
            "input_sidecar_sha256": self.input_sidecar_sha256,
            "input_source_sha256": self.input_source_sha256,
            "negative_evidence_ids": list(self.negative_evidence_ids),
            "operator_authorization_scope": self.operator_authorization_scope,
            "outcome": self.outcome,
            "output_canonical": self.output_canonical,
            "positive_evidence_ids": list(self.positive_evidence_ids),
            "reason_codes": list(self.reason_codes),
        }


@dataclass
class CompetingSetRecord:
    ambiguity_set_id: str
    member_candidate_ids: list[str]
    shared_endpoint_string: str
    candidate_count: int
    duplicate_record: bool
    identity_resolved: bool
    resolution_status: str
    competing_set_kind: str
    original_ambiguous_binding_member_count: int
    original_ambiguous_binding_member_ids: list[str]
    source_sha256: str
    sidecar_sha256: str
    authority: str = ADJUDICATION_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "ambiguity_set_id": self.ambiguity_set_id,
            "authority": self.authority,
            "candidate_count": self.candidate_count,
            "competing_set_kind": self.competing_set_kind,
            "duplicate_record": self.duplicate_record,
            "identity_resolved": self.identity_resolved,
            "member_candidate_ids": list(self.member_candidate_ids),
            "original_ambiguous_binding_member_count": (
                self.original_ambiguous_binding_member_count
            ),
            "original_ambiguous_binding_member_ids": list(
                self.original_ambiguous_binding_member_ids
            ),
            "output_canonical": self.output_canonical,
            "resolution_status": self.resolution_status,
            "shared_endpoint_string": self.shared_endpoint_string,
            "sidecar_sha256": self.sidecar_sha256,
            "source_sha256": self.source_sha256,
        }


@dataclass
class CandidateAdjudicationResult:
    candidate_id: str
    endpoint_string: str
    candidate_family: str
    candidate_state: str
    occurrence_binding_proven: bool
    original_ambiguous_binding: bool
    original_dispositions: list[str]
    competing_set_id: PresenceTagged
    occurrence_identity_outcome: str
    source_locus_availability: str
    residual_ids: list[str]
    authority: str = ADJUDICATION_AUTHORITY
    output_canonical: bool = False

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "candidate_family": self.candidate_family,
            "candidate_id": self.candidate_id,
            "candidate_state": self.candidate_state,
            "competing_set_id": self.competing_set_id.to_canonical(),
            "endpoint_string": self.endpoint_string,
            "occurrence_binding_proven": self.occurrence_binding_proven,
            "occurrence_identity_outcome": self.occurrence_identity_outcome,
            "original_ambiguous_binding": self.original_ambiguous_binding,
            "original_dispositions": list(self.original_dispositions),
            "output_canonical": self.output_canonical,
            "residual_ids": list(self.residual_ids),
            "source_locus_availability": self.source_locus_availability,
        }


@dataclass
class AdjudicationContract:
    dimension_model: dict[str, Any]
    evidence_records: list[EvidenceRecord]
    competing_sets: list[CompetingSetRecord]
    candidate_results: list[CandidateAdjudicationResult]
    decision_records: list[AdjudicationDecisionRecord]
    non_inference_audit: dict[str, Any]
    execution_boundaries: dict[str, Any]
    counts: dict[str, Any]
    residual_status: dict[str, str]
    generated_from_source_sha256: str
    generated_from_sidecar_sha256: str
    generated_from_candidate_index_sha256: str
    family_inventory: dict[str, Any]
    layer_id: str = ADJUDICATION_LAYER_ID
    generator_id: str = ADJUDICATION_GENERATOR_ID
    contract_version: str = ADJUDICATION_CONTRACT_VERSION
    transformation_version: str = ADJUDICATION_TRANSFORMATION_VERSION
    output_role: str = ADJUDICATION_OUTPUT_ROLE
    operator_authorization_scope: str = OPERATOR_AUTHORIZATION_SCOPE
    authority: str = ADJUDICATION_AUTHORITY
    output_canonical: bool = False
    semantic_binding_performed: bool = False
    residual_close_performed: bool = False
    currentness_adjudication_performed: bool = False
    supersession_adjudication_performed: bool = False
    occurrence_binding_proven_count: int = 0
    proven_occurrence_identity_count: int = 0
    proven_parentage_count: int = 0
    winner_selected_count: int = 0
    extras: dict[str, Any] = field(default_factory=dict)

    def to_canonical(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "candidate_results": [row.to_canonical() for row in self.candidate_results],
            "competing_sets": [row.to_canonical() for row in self.competing_sets],
            "contract_version": self.contract_version,
            "counts": dict(self.counts),
            "currentness_adjudication_performed": self.currentness_adjudication_performed,
            "decision_records": [row.to_canonical() for row in self.decision_records],
            "dimension_model": dict(self.dimension_model),
            "evidence_records": [row.to_canonical() for row in self.evidence_records],
            "execution_boundaries": dict(self.execution_boundaries),
            "family_inventory": dict(self.family_inventory),
            "generated_from_candidate_index_sha256": self.generated_from_candidate_index_sha256,
            "generated_from_sidecar_sha256": self.generated_from_sidecar_sha256,
            "generated_from_source_sha256": self.generated_from_source_sha256,
            "generator_id": self.generator_id,
            "layer_id": self.layer_id,
            "non_inference_audit": dict(self.non_inference_audit),
            "occurrence_binding_proven_count": self.occurrence_binding_proven_count,
            "operator_authorization_scope": self.operator_authorization_scope,
            "output_canonical": self.output_canonical,
            "output_role": self.output_role,
            "proven_occurrence_identity_count": self.proven_occurrence_identity_count,
            "proven_parentage_count": self.proven_parentage_count,
            "residual_close_performed": self.residual_close_performed,
            "residual_status": dict(self.residual_status),
            "semantic_binding_performed": self.semantic_binding_performed,
            "supersession_adjudication_performed": self.supersession_adjudication_performed,
            "transformation_version": self.transformation_version,
            "winner_selected_count": self.winner_selected_count,
        }


def optional_from_json(payload: dict[str, Any] | None) -> OptionalValue:
    if payload is None:
        return OptionalValue.absent()
    presence = str(payload.get("presence", "absent"))
    if presence == "absent":
        return OptionalValue.absent()
    if presence == "null":
        return OptionalValue.null()
    return OptionalValue.present(payload.get("value"))


def presence_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    return _optional_from_presence(payload)
