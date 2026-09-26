"""P4 productive L6 seam binding request/result models."""

from __future__ import annotations

from dataclasses import dataclass

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    InstrumentBindingV1,
    L6BoundedTypedExternalEvidenceInputV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
    MasterV2EvidenceAdjudicationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    MasterV2LayerInputBindingResultV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    DynamicScopeGeneratorOutputV1,
    NullLineStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import LayerIdV1


@dataclass(frozen=True)
class ProductiveL6SeamBindingRequestV1:
    """End-to-end seam request: registered producer intake + B binding metadata."""

    seam_id: str
    intake: EvidenceIntakeRecordV1
    binding_id: str
    target_layer: LayerIdV1
    target_contract_version: str
    nullline_provenance_epoch: int


@dataclass(frozen=True)
class ProductiveL6SeamBindingContextV1:
    evaluated_at_unix: float
    expected_instrument: InstrumentBindingV1
    expected_market_observation_epoch: int
    expected_nullline_provenance_epoch: int | None = None
    mechanical_proposed_d_t: float | None = None
    nullline_for_mechanical_l6: NullLineStateV1 | None = None


@dataclass(frozen=True)
class L6TypedEvidenceAdmissionResultV1:
    disposition: str
    reason_codes: tuple[str, ...]
    admission_evidence_id: str
    admission_digest: str
    typed_input_digest: str | None = None


@dataclass(frozen=True)
class ProductiveL6SeamBindingResultV1:
    seam_id: str
    disposition: str
    reason_codes: tuple[str, ...]
    seam_result_digest: str
    adjudication: MasterV2EvidenceAdjudicationResultV1 | None = None
    binding: MasterV2LayerInputBindingResultV1 | None = None
    typed_layer_input: L6BoundedTypedExternalEvidenceInputV1 | None = None
    l6_admission: L6TypedEvidenceAdmissionResultV1 | None = None
    l6_generator_output: DynamicScopeGeneratorOutputV1 | None = None
    l6_consumption_evidence_id: str | None = None
    dedup_replay: bool = False
