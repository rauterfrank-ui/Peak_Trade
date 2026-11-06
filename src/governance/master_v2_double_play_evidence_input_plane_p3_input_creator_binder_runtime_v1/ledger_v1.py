"""In-memory idempotency tracking for bounded Component B binding."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.digest_v1 import (
    compute_binding_request_fingerprint_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.models_v1 import (
    LayerInputBindingRequestV1,
    MasterV2LayerInputBindingResultV1,
)


@dataclass
class BindingLedgerV1:
    binding_results: dict[str, MasterV2LayerInputBindingResultV1] = field(default_factory=dict)
    binding_fingerprints: dict[str, str] = field(default_factory=dict)

    def prior_binding_result(
        self, request: LayerInputBindingRequestV1
    ) -> MasterV2LayerInputBindingResultV1 | None:
        prior = self.binding_results.get(request.binding_id)
        if prior is None:
            return None
        fingerprint = compute_binding_request_fingerprint_digest_v1(request)
        if self.binding_fingerprints.get(request.binding_id) != fingerprint:
            return None
        return prior

    def record_result(
        self, request: LayerInputBindingRequestV1, result: MasterV2LayerInputBindingResultV1
    ) -> None:
        self.binding_results[request.binding_id] = result
        self.binding_fingerprints[request.binding_id] = (
            compute_binding_request_fingerprint_digest_v1(request)
        )
