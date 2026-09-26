"""P2 Component A intake and adjudication result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    CanonicalMasterV2EvidenceEnvelopeV1,
    EvidenceProducerFamilyV1,
    InstrumentBindingV1,
)


@dataclass(frozen=True)
class EvidenceIntakeRecordV1:
    """Raw producer delivery before bounded adjudication to the P1 A-output envelope."""

    delivery_id: str
    envelope_id: str
    producer_id: str
    producer_version: str
    evidence_type_version: str
    producer_family: EvidenceProducerFamilyV1
    evidence_kind: BoundedL6EvidenceKindV1
    instrument: InstrumentBindingV1
    market_observation_epoch: int
    observed_at_unix: float
    freshness_horizon_seconds: int
    source_evidence_digest: str
    typed_payload_digest: str
    provenance_refs: Tuple[str, ...]
    lineage_refs: Tuple[str, ...] = ()
    confidence_score: float | None = None
    quality_score: float | None = None
    extra_fields: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceIntakeAdjudicationContextV1:
    evaluated_at_unix: float
    expected_instrument: InstrumentBindingV1 | None = None
    expected_market_observation_epoch: int | None = None
    allow_epoch_mismatch: bool = False


@dataclass(frozen=True)
class RegisteredProducerEntryV1:
    producer_id: str
    producer_version: str
    producer_family: EvidenceProducerFamilyV1
    evidence_kind: BoundedL6EvidenceKindV1
    evidence_type_version: str


@dataclass(frozen=True)
class MasterV2EvidenceAdjudicationResultV1:
    """Bounded Component A output — envelope only on ADMIT; never trading/DP authority."""

    delivery_id: str
    disposition: str
    reason_codes: Tuple[str, ...]
    adjudication_digest: str
    envelope: CanonicalMasterV2EvidenceEnvelopeV1 | None = None
    envelope_digest: str | None = None
    dedup_replay: bool = False
