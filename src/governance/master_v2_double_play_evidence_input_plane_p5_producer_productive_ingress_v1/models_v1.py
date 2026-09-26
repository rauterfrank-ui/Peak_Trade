"""P5 producer ingress models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    MasterV2EvidenceAdjudicationResultV1,
)


@dataclass(frozen=True)
class ProducerEvidenceTerminationContextV1:
    """Binding context for producer → A termination (no trading semantics)."""

    market_observation_epoch: int
    instrument: InstrumentBindingV1
    freshness_horizon_seconds: int
    evaluated_at_unix: float | None = None


@dataclass(frozen=True)
class ProducerIngressProvenanceV1:
    adapter_id: str
    source_schema_version: str
    source_content_digest: str
    producer_class: EvidenceProducerFamilyV1


@dataclass(frozen=True)
class ProducerIngressTerminationResultV1:
    producer_class: EvidenceProducerFamilyV1
    producer_id: str
    adjudication: MasterV2EvidenceAdjudicationResultV1
    ingress_provenance: ProducerIngressProvenanceV1
    blocked_at_promotion: bool = False
    promotion_block_reason: str | None = None


@dataclass(frozen=True)
class PromotionAdmissionEntryV1:
    producer_family: EvidenceProducerFamilyV1
    source_artifact_schema: str
    source_content_digest: str
    promoted_evidence_kind: str
    promotion_record_id: str


@dataclass(frozen=True)
class ProducerCensusEntryV1:
    producer_class: str
    producer_id: str
    producer_version: str
    reachability: str
    implementation_status: str
    integration_status: str
    direct_b_bypass: bool
    direct_dp_bypass: bool
    promotion_required: bool
    promotion_status: str
    blocker: str | None
    evidence_refs: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "producer_class": self.producer_class,
            "producer_id": self.producer_id,
            "producer_version": self.producer_version,
            "reachability": self.reachability,
            "implementation_status": self.implementation_status,
            "integration_status": self.integration_status,
            "direct_b_bypass": self.direct_b_bypass,
            "direct_dp_bypass": self.direct_dp_bypass,
            "promotion_required": self.promotion_required,
            "promotion_status": self.promotion_status,
            "blocker": self.blocker,
            "evidence_refs": list(self.evidence_refs),
            "notes": self.notes,
        }


ProducerArtifactV1 = Mapping[str, Any]
