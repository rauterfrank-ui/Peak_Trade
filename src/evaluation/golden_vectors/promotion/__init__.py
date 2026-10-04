"""GVEF promotion handoff layer (BWP-8)."""

from __future__ import annotations

from src.evaluation.golden_vectors.promotion.errors import GvefPromotionAuthorityError
from src.evaluation.golden_vectors.promotion.external_governance_boundary_v1 import (
    EXTERNAL_GOVERNANCE_DECISION_OWNER,
    GVEF_AUTHORITY_END_STATE,
    PROMOTION_GVEF_AUTHORITY,
)
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    COMPONENT_ID,
    BWP_ID,
    PassThroughPromotionEvidenceAdapterV1,
    PromotionAdaptRequestV1,
    PromotionEvidenceAdapterV1,
    evidence_bundle_semantic_digest,
)

__all__ = [
    "BWP_ID",
    "COMPONENT_ID",
    "EXTERNAL_GOVERNANCE_DECISION_OWNER",
    "GVEF_AUTHORITY_END_STATE",
    "GvefPromotionAuthorityError",
    "PROMOTION_GVEF_AUTHORITY",
    "PassThroughPromotionEvidenceAdapterV1",
    "PromotionAdaptRequestV1",
    "PromotionEvidenceAdapterV1",
    "evidence_bundle_semantic_digest",
]
