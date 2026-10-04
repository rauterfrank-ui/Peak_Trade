"""BWP-8 Promotion evidence adapter — envelope handoff only, AUTHORITY=NONE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.evaluation.golden_vectors.contracts.enums import ExternalPromotionStatus
from src.evaluation.golden_vectors.contracts.models import (
    EvidenceBundleV1,
    PromotionEvidenceEnvelopeV1,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.evaluation.golden_vectors.promotion.errors import GvefPromotionAuthorityError

BWP_ID = "BWP-8"
COMPONENT_ID = "gvef.promotion_evidence_adapter_v1"
PRIMARY_FAILURE_CLASS = "AUTHORITY_FAILURE"
REPROOF_CLASS = "LOCAL_EVALUATION"


def evidence_bundle_semantic_digest(bundle: EvidenceBundleV1) -> str:
    payload = contract_to_canonical_mapping(bundle)
    payload.pop("evidence_digest", None)
    return sha256_hex(payload)


@dataclass(frozen=True)
class PromotionAdaptRequestV1:
    """Bound inputs only — no ambient wall-clock."""

    evidence_bundle_ref: str
    governance_handoff_timestamp: str
    authority_probe: dict[str, Any] | None = None


@dataclass(frozen=True)
class PromotionEvidenceAdapterV1:
    """Adapt EvidenceBundle → PromotionEvidenceEnvelope. Does not promote."""

    adapter_id: str = "promotion_evidence_adapter_v1"
    schema_version: str = "1.5.0"

    def adapt(
        self,
        *,
        bundle: EvidenceBundleV1,
        request: PromotionAdaptRequestV1,
    ) -> PromotionEvidenceEnvelopeV1:
        self._authority_violation(request.authority_probe)
        if request.authority_probe and request.authority_probe.get("treat_incomplete_as_complete"):
            raise GvefPromotionAuthorityError(
                "incomplete evidence treated as promotion-ready",
                field="evidence_complete",
            )
        if not bundle.post_constraint_gate_pass:
            raise GvefPromotionAuthorityError(
                "post_constraint_gate_pass must be true for handoff",
                field="post_constraint_gate_pass",
            )
        if bundle.failure_classification is not None:
            raise GvefPromotionAuthorityError(
                "failed run cannot produce promotion handoff envelope",
                field="failure_classification",
            )
        if bundle.promotion_status not in (
            ExternalPromotionStatus.EXTERNAL_UNSET,
            ExternalPromotionStatus.GOVERNANCE_REVIEW_PENDING,
        ):
            raise GvefPromotionAuthorityError(
                "GVEF must not hand off bundle with external eligibility/decision status",
                field="promotion_status",
            )
        recomputed = evidence_bundle_semantic_digest(bundle)
        if recomputed != bundle.evidence_digest:
            raise GvefPromotionAuthorityError(
                "evidence_digest mismatch — source bundle not immutable",
                field="evidence_digest",
            )
        return PromotionEvidenceEnvelopeV1(
            evidence_bundle_ref=request.evidence_bundle_ref,
            evidence_digest=bundle.evidence_digest,
            governance_handoff_timestamp=request.governance_handoff_timestamp,
            post_constraint_gate_pass=True,
            fan_out_evaluation_class=bundle.fan_out_evaluation_class,
        )

    def _authority_violation(self, probe: dict[str, Any] | None) -> None:
        if not probe:
            return
        checks = (
            ("claims_promotion_authority", "promotion authority claim forbidden"),
            ("claims_governance_self_approval", "external governance self-approval forbidden"),
            ("claims_post_authority", "POST authority claim forbidden"),
            ("selection_mutation", "Selection mutation forbidden"),
            ("productive_write", "productive write forbidden"),
            ("mutate_source_bundle", "source evidence mutation forbidden"),
        )
        for key, message in checks:
            if probe.get(key) is True:
                raise GvefPromotionAuthorityError(message, field=key)


class PassThroughPromotionEvidenceAdapterV1:
    """Default runner path: BWP-8 handoff not invoked."""

    def adapt(
        self,
        *,
        bundle: EvidenceBundleV1,
        request: PromotionAdaptRequestV1,
    ) -> PromotionEvidenceEnvelopeV1 | None:
        _ = (bundle, request)
        return None
