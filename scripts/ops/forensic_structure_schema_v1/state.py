"""Shared mutable pipeline state. Stages remain separate modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.guards import GuardProgram
from scripts.ops.forensic_structure_schema_v1.models import (
    ContractTestResult,
    InputWitness,
    InvariantReport,
    Layer1Occurrence,
    LosslessnessAudit,
    OverlayRecord,
    ProvenanceTag,
    RelationEnvelope,
    ResidualRecord,
    SemanticEnvelope,
)


@dataclass
class PipelineState:
    source_path: Path
    sidecar_path: Path
    source_bytes: bytes
    sidecar_bytes: bytes
    sidecar: dict[str, Any]
    source_sha256_before: str
    sidecar_sha256_before: str
    stages_completed: list[str] = field(default_factory=list)
    witness: InputWitness | None = None
    layer1_ordered: list[Layer1Occurrence] = field(default_factory=list)
    layer1_by_id: dict[str, Layer1Occurrence] = field(default_factory=dict)
    overlays_by_class: dict[str, list[OverlayRecord]] = field(default_factory=dict)
    overlay_by_id: dict[str, OverlayRecord] = field(default_factory=dict)
    alias_to_overlay_id: dict[str, str] = field(default_factory=dict)
    token_occurrence_ids: set[str] = field(default_factory=set)
    body_sha_to_overlay_ids: dict[str, list[str]] = field(default_factory=dict)
    provenance: list[ProvenanceTag] = field(default_factory=list)
    guards: GuardProgram | None = None
    envelopes: list[SemanticEnvelope] = field(default_factory=list)
    envelope_by_overlay_id: dict[str, list[SemanticEnvelope]] = field(default_factory=dict)
    envelope_by_tlid: dict[str, SemanticEnvelope] = field(default_factory=dict)
    layer2_envelopes_by_occurrence: dict[str, list[SemanticEnvelope]] = field(default_factory=dict)
    relations: list[RelationEnvelope] = field(default_factory=list)
    relation_by_id: dict[str, RelationEnvelope] = field(default_factory=dict)
    residuals: list[ResidualRecord] = field(default_factory=list)
    invariant_report: InvariantReport | None = None
    losslessness_audit: LosslessnessAudit | None = None
    reconstruction_report: dict[str, Any] | None = None
    source_canary_report: dict[str, Any] | None = None
    contract_tests: dict[str, ContractTestResult] = field(default_factory=dict)
    output_eligible: bool = False
    source_sha256_after: str = ""
    sidecar_sha256_after: str = ""
