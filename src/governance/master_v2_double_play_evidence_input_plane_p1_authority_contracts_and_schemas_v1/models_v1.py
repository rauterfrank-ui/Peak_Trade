"""Immutable P1 contract DTOs — Component A envelope, Component B binding, L6 typed input."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence, Tuple

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1


class EvidenceProducerFamilyV1(str, Enum):
    MARKET_INTELLIGENCE = "market_intelligence"
    LEARNING = "learning"
    OPTIMIZATION = "optimization"
    META_LEARNING = "meta_learning"
    RESEARCH = "research"


class BoundedL6EvidenceKindV1(str, Enum):
    """Owner-bounded typed evidence kinds admissible toward L6 (P1 contract only)."""

    MI_MARKET_CONTEXT_DESCRIPTIVE_V1 = "mi_market_context_descriptive_v1"
    LEARNING_CONDITIONED_EVALUATIVE_V1 = "learning_conditioned_evaluative_v1"
    OPTIMIZATION_ENVELOPE_EVIDENCE_V1 = "optimization_envelope_evidence_v1"
    META_LEARNING_ROUTED_EVIDENCE_V1 = "meta_learning_routed_evidence_v1"
    RESEARCH_PROMOTED_EVIDENCE_V1 = "research_promoted_evidence_v1"


ALLOWED_PRODUCER_FAMILIES_V1: frozenset[EvidenceProducerFamilyV1] = frozenset(
    EvidenceProducerFamilyV1
)
ALLOWED_L6_EVIDENCE_KINDS_V1: frozenset[BoundedL6EvidenceKindV1] = frozenset(
    BoundedL6EvidenceKindV1
)

P1_ALLOWED_B_TARGET_LAYERS_V1: frozenset[LayerIdV1] = frozenset(
    {LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR}
)


@dataclass(frozen=True)
class InstrumentBindingV1:
    instrument_id: str
    venue: str
    venue_instrument_id: str


@dataclass(frozen=True)
class CanonicalMasterV2EvidenceEnvelopeV1:
    """Component A — adjudicated evidence envelope (transport/adjudication contract only)."""

    envelope_id: str
    producer_family: EvidenceProducerFamilyV1
    evidence_kind: BoundedL6EvidenceKindV1
    instrument: InstrumentBindingV1
    market_observation_epoch: int
    observed_at_unix: float
    freshness_horizon_seconds: int
    source_evidence_digest: str
    typed_payload_digest: str
    provenance_refs: Tuple[str, ...]
    trading_authority: str = "NONE"
    schema_version: str = "canonical_master_v2_evidence_envelope.v1"
    adjudication_path: str = "component_a_bounded_adjudication_only"
    extra_fields: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalDpLayerInputBindingV1:
    """Component B — bind adjudicated envelope to a DP layer input (no DP state mutation)."""

    binding_id: str
    target_layer: LayerIdV1
    envelope_digest: str
    instrument: InstrumentBindingV1
    market_observation_epoch: int
    nullline_provenance_epoch: int
    binding_evaluated_at_unix: float
    trading_authority: str = "NONE"
    dp_state_mutation_authority: str = "NONE"
    schema_version: str = "canonical_dp_layer_input_binding.v1"
    producer_to_b_direct: bool = False
    extra_fields: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class L6BoundedTypedExternalEvidenceInputV1:
    """Typed external evidence input contract toward L6 (interpretation remains L6-only in P2+)."""

    input_id: str
    target_layer: LayerIdV1
    evidence_kind: BoundedL6EvidenceKindV1
    instrument: InstrumentBindingV1
    market_observation_epoch: int
    nullline_provenance_epoch: int
    envelope_digest: str
    binding_digest: str
    source_evidence_digest: str
    typed_payload_digest: str
    provenance_refs: Tuple[str, ...]
    interpretation_authority: str = "L6_ONLY"
    schema_version: str = "l6_bounded_typed_external_evidence_input.v1"


@dataclass(frozen=True)
class ContractValidationResultV1:
    ok: bool
    failure_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class AdjudicationContextV1:
    """Explicit evaluation context for deterministic freshness checks."""

    evaluated_at_unix: float
    allow_direct_producer_to_b: bool = False


@dataclass(frozen=True)
class BindingContextV1:
    evaluated_at_unix: float
    expected_envelope_digest: str
    adjudicated_envelope: CanonicalMasterV2EvidenceEnvelopeV1


def envelope_forbidden_numeric_fields_v1(extra: Mapping[str, Any]) -> Tuple[str, ...]:
    forbidden = ("proposed_d_t", "d_t", "final_d_t", "computed_d_t", "formula_id")
    hits = [k for k in forbidden if k in extra]
    return tuple(sorted(hits))
