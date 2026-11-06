"""P3 Component B binding request/result models (A-output consumption only)."""

from __future__ import annotations

from dataclasses import dataclass

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    CanonicalDpLayerInputBindingV1,
    InstrumentBindingV1,
    L6BoundedTypedExternalEvidenceInputV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    MasterV2EvidenceAdjudicationResultV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1


@dataclass(frozen=True)
class LayerInputBindingRequestV1:
    """Binding request — must carry bounded Component A adjudication output only."""

    binding_id: str
    target_layer: LayerIdV1
    target_contract_version: str
    nullline_provenance_epoch: int
    adjudication: MasterV2EvidenceAdjudicationResultV1


@dataclass(frozen=True)
class LayerInputBindingContextV1:
    evaluated_at_unix: float
    expected_instrument: InstrumentBindingV1 | None = None
    expected_market_observation_epoch: int | None = None
    allow_direct_producer_to_b: bool = False


@dataclass(frozen=True)
class MasterV2LayerInputBindingResultV1:
    """Bounded Component B output — binding + typed L6 input on BIND only; never trading authority."""

    binding_id: str
    disposition: str
    reason_codes: tuple[str, ...]
    binding_result_digest: str
    binding: CanonicalDpLayerInputBindingV1 | None = None
    binding_digest: str | None = None
    typed_layer_input: L6BoundedTypedExternalEvidenceInputV1 | None = None
    typed_layer_input_digest: str | None = None
    adjudication_digest: str | None = None
    dedup_replay: bool = False
