"""Runtime binding: External Effect Permit Mint policy → permit producer seam (admission only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.external_effect_permit_mint_policy_v1 import (
    STATUS_MINT_ADMISSION_DENIED,
    TARGET_PERMIT_MODULE,
    evaluate_external_effect_permit_mint_admission_v1,
    external_effect_permit_mint_policy_granted_v1,
    validate_external_effect_permit_mint_policy_record_v1,
)
from src.governance.standing_external_effect_lift_gate_binding_v1 import (
    evaluate_lift_bound_external_effect_gate_v1,
)

BINDING_OWNER: Final[str] = "governance.external_effect_permit_mint_gate_binding_v1"


@dataclass(frozen=True, slots=True)
class PermitMintBoundExternalEffectPermitResultV1:
    permit_mint_admission_granted: bool
    lift_bound_admission_granted: bool
    permit_producer_module: str
    permit_mint_policy_record_digest: str | None
    standing_lift_policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    governed_permit_mint_authorized: bool
    permit_mint_authorized: bool
    permit_mint_performed: bool
    credential_access_authorized: bool
    credential_access_performed: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_permit_mint_bound_external_effect_permit_seam_v1(
    *, repo_root: Path | None = None
) -> PermitMintBoundExternalEffectPermitResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    lift_bound = evaluate_lift_bound_external_effect_gate_v1(repo_root=root)

    if not external_effect_permit_mint_policy_granted_v1(repo_root=root):
        mint_policy = validate_external_effect_permit_mint_policy_record_v1(repo_root=root)
        return PermitMintBoundExternalEffectPermitResultV1(
            permit_mint_admission_granted=False,
            lift_bound_admission_granted=lift_bound.lift_admission_granted,
            permit_producer_module=TARGET_PERMIT_MODULE,
            permit_mint_policy_record_digest=mint_policy.policy_record_digest,
            standing_lift_policy_record_digest=lift_bound.lift_policy_record_digest,
            reason_codes=mint_policy.reason_codes or ("PERMIT_MINT_POLICY_NOT_AUTHORIZED",),
            governed_permit_mint_authorized=False,
            permit_mint_authorized=False,
            permit_mint_performed=False,
            credential_access_authorized=False,
            credential_access_performed=False,
            post_allowed=False,
            real_venue_post_allowed=False,
        )

    admission = evaluate_external_effect_permit_mint_admission_v1(repo_root=root)
    granted = admission.permit_mint_policy_granted is True
    return PermitMintBoundExternalEffectPermitResultV1(
        permit_mint_admission_granted=granted,
        lift_bound_admission_granted=lift_bound.lift_admission_granted,
        permit_producer_module=TARGET_PERMIT_MODULE,
        permit_mint_policy_record_digest=admission.policy_record_digest,
        standing_lift_policy_record_digest=lift_bound.lift_policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_MINT_ADMISSION_DENIED,),
        governed_permit_mint_authorized=admission.governed_permit_mint_authorized,
        permit_mint_authorized=admission.permit_mint_authorized,
        permit_mint_performed=admission.permit_mint_performed,
        credential_access_authorized=admission.credential_access_authorized,
        credential_access_performed=admission.credential_access_performed,
        post_allowed=admission.post_allowed,
        real_venue_post_allowed=admission.real_venue_post_allowed,
        extra={
            "permit_mint_capability_implemented": str(
                admission.permit_mint_capability_implemented
            ).lower(),
        },
    )


__all__ = [
    "BINDING_OWNER",
    "PermitMintBoundExternalEffectPermitResultV1",
    "evaluate_permit_mint_bound_external_effect_permit_seam_v1",
]
