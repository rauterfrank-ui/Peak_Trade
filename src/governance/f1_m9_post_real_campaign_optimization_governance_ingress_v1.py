"""Build optimization governance ingress from sealed F1/M9 REAL campaign evidence."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    RISK_CONSTRAINTS_REF as M9_RISK_CONSTRAINTS_REF,
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    DISPOSITION_PROPOSAL_ONLY,
    SCHEMA_VERSION,
    INGRESS_DOMAIN,
    PROMOTION_AUTHORITY,
    PRODUCTIVE_APPLY_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
    OptimizationProposalGovernanceIngressError,
    validate_optimization_proposal_governance_ingress_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    SOURCE_CANDIDATE_PARAMETER,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

WORKPACKAGE_ID: Final[str] = "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETION_V1"


def build_f1_m9_post_real_campaign_optimization_governance_ingress_v1(
    *,
    verification: F1M9ProspectiveRealCampaignDurableEvidenceVerificationV1,
    repo_root: Path | None = None,
) -> MappingProxyType[str, Any]:
    """Canonical ingress adapter for POST-REAL-CAMPAIGN productive handoff only."""
    if not verification.verified:
        raise OptimizationProposalGovernanceIngressError(
            "REAL_CAMPAIGN_DURABLE_EVIDENCE_NOT_VERIFIED"
        )
    if verification.selected_max_age_seconds is None or verification.selected_candidate_id is None:
        raise OptimizationProposalGovernanceIngressError("RESOLVED_CANDIDATE_INCOMPLETE")
    if verification.evidence_bundle_digest is None or verification.execution_identity is None:
        raise OptimizationProposalGovernanceIngressError("EVIDENCE_LINEAGE_INCOMPLETE")
    if verification.preregistration_digest is None or not is_valid_sha256_hex(
        verification.preregistration_digest
    ):
        raise OptimizationProposalGovernanceIngressError("PREREGISTRATION_DIGEST_INVALID")

    delta = {SOURCE_CANDIDATE_PARAMETER: int(verification.selected_max_age_seconds)}
    envelope_resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=M9_SURFACE_ID)
    )
    if envelope_resolution.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise OptimizationProposalGovernanceIngressError(
            f"ENVELOPE_NOT_AUTHORIZED:{envelope_resolution.get('reason')}"
        )
    envelope_identity = str(envelope_resolution.get("envelope_identity") or "")
    if not is_valid_sha256_hex(envelope_identity):
        raise OptimizationProposalGovernanceIngressError("ENVELOPE_IDENTITY_INVALID")

    plane_identity = compute_content_sha256(
        {
            "campaign_id": verification.campaign_id,
            "execution_identity": verification.execution_identity,
            "execution_mode": verification.execution_mode,
        }
    )
    experiment_id = verification.execution_identity
    candidate_ref = verification.selected_candidate_id
    evidence_hash = verification.evidence_bundle_digest
    learning_digest = verification.preregistration_digest

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": INGRESS_DOMAIN,
        "disposition": DISPOSITION_PROPOSAL_ONLY,
        "plane_identity": plane_identity,
        "experiment_id": experiment_id,
        "candidate_ref": candidate_ref,
        "optimization_surface_id": M9_SURFACE_ID,
        "parameter_config_delta": delta,
        "requested_productive_target": None,
        "optimization_evidence_record_id": verification.runtime_authorization_id
        or verification.campaign_id,
        "optimization_evidence_content_hash": evidence_hash,
        "optimization_evidence_reproducibility_digest": evidence_hash,
        "learning_evidence_digest": learning_digest,
        "plane_result_digest": evidence_hash,
        "search_identity": None,
        "template_identity_digest": None,
        "envelope_identity": envelope_identity,
        "envelope_owner_authorization_ref": None,
        "risk_constraints_ref": M9_RISK_CONSTRAINTS_REF,
        "governance_risk_constraints_ref": M9_RISK_CONSTRAINTS_REF,
        "envelope_resolution_digest": envelope_resolution.get("result_digest"),
        "promotion_authority": PROMOTION_AUTHORITY,
        "productive_apply_authority": PRODUCTIVE_APPLY_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "optimization_provenance": {
            "f1_m9_real_campaign_handoff_v1": True,
            "campaign_id": verification.campaign_id,
            "runtime_authorization_id": verification.runtime_authorization_id,
            "evidence_bundle_digest": evidence_hash,
            "execution_identity": verification.execution_identity,
            "selection_outcome": verification.selection_outcome,
            "ingress_is_not_config_patch": True,
            "optimization_self_promotion_forbidden": True,
        },
    }
    body["ingress_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "ingress_digest"}
    )
    return validate_optimization_proposal_governance_ingress_v1(body)


__all__ = [
    "WORKPACKAGE_ID",
    "build_f1_m9_post_real_campaign_optimization_governance_ingress_v1",
]
