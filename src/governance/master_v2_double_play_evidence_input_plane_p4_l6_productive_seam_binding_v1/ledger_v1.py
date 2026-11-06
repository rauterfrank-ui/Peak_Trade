"""Idempotent ledger for P4 productive L6 seam deliveries."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.digest_v1 import (
    compute_seam_request_fingerprint_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.models_v1 import (
    ProductiveL6SeamBindingRequestV1,
    ProductiveL6SeamBindingResultV1,
)


@dataclass
class ProductiveL6SeamLedgerV1:
    seam_results: dict[str, ProductiveL6SeamBindingResultV1] = field(default_factory=dict)
    seam_fingerprints: dict[str, str] = field(default_factory=dict)

    def prior_seam_result(
        self, request: ProductiveL6SeamBindingRequestV1
    ) -> ProductiveL6SeamBindingResultV1 | None:
        return self.seam_results.get(request.seam_id)
