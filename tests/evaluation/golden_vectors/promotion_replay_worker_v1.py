"""Cross-process BWP-8 promotion adapter determinism worker."""

from __future__ import annotations

import json

from src.evaluation.golden_vectors.contracts.models import contract_digest_hex
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    PromotionAdaptRequestV1,
    PromotionEvidenceAdapterV1,
)
from tests.evaluation.golden_vectors.promotion_fixtures_v1 import valid_evidence_bundle


def main() -> None:
    bundle = valid_evidence_bundle()
    env = PromotionEvidenceAdapterV1().adapt(
        bundle=bundle,
        request=PromotionAdaptRequestV1(
            evidence_bundle_ref="registry/worker",
            governance_handoff_timestamp="2026-10-04T09:00:00Z",
        ),
    )
    print(json.dumps({"envelope_digest": contract_digest_hex(env)}))


if __name__ == "__main__":
    main()
