"""Runtime binding: credential access policy → checkout-independent capability seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.checkout_independent_credential_access_policy_v1 import (
    STATUS_ADMISSION_DENIED,
    TARGET_CAPABILITY_MODULE,
    checkout_independent_credential_access_policy_granted_v1,
    evaluate_checkout_independent_credential_access_admission_v1,
    validate_checkout_independent_credential_access_policy_record_v1,
)
from src.governance.external_effect_permit_mint_gate_binding_v1 import (
    evaluate_permit_mint_bound_external_effect_permit_seam_v1,
)

BINDING_OWNER: Final[str] = "governance.checkout_independent_credential_access_gate_binding_v1"


@dataclass(frozen=True, slots=True)
class CredentialAccessBoundCapabilityResultV1:
    credential_access_admission_granted: bool
    permit_mint_bound_admission_granted: bool
    capability_module: str
    credential_access_policy_record_digest: str | None
    permit_mint_policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    governed_credential_access_authorized: bool
    credential_access_authorized: bool
    credential_access_performed: bool
    real_credential_access_performed: bool
    real_secret_load_performed: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_credential_access_bound_checkout_independent_capability_seam_v1(
    *, repo_root: Path | None = None
) -> CredentialAccessBoundCapabilityResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    permit_bound = evaluate_permit_mint_bound_external_effect_permit_seam_v1(repo_root=root)

    if not checkout_independent_credential_access_policy_granted_v1(repo_root=root):
        cred_policy = validate_checkout_independent_credential_access_policy_record_v1(
            repo_root=root
        )
        return CredentialAccessBoundCapabilityResultV1(
            credential_access_admission_granted=False,
            permit_mint_bound_admission_granted=permit_bound.permit_mint_admission_granted,
            capability_module=TARGET_CAPABILITY_MODULE,
            credential_access_policy_record_digest=cred_policy.policy_record_digest,
            permit_mint_policy_record_digest=permit_bound.permit_mint_policy_record_digest,
            reason_codes=cred_policy.reason_codes or ("CREDENTIAL_ACCESS_POLICY_NOT_AUTHORIZED",),
            governed_credential_access_authorized=False,
            credential_access_authorized=False,
            credential_access_performed=False,
            real_credential_access_performed=False,
            real_secret_load_performed=False,
            post_allowed=False,
            real_venue_post_allowed=False,
        )

    admission = evaluate_checkout_independent_credential_access_admission_v1(repo_root=root)
    granted = admission.credential_access_policy_granted is True
    return CredentialAccessBoundCapabilityResultV1(
        credential_access_admission_granted=granted,
        permit_mint_bound_admission_granted=permit_bound.permit_mint_admission_granted,
        capability_module=TARGET_CAPABILITY_MODULE,
        credential_access_policy_record_digest=admission.policy_record_digest,
        permit_mint_policy_record_digest=permit_bound.permit_mint_policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_ADMISSION_DENIED,),
        governed_credential_access_authorized=admission.governed_credential_access_authorized,
        credential_access_authorized=admission.credential_access_authorized,
        credential_access_performed=admission.credential_access_performed,
        real_credential_access_performed=admission.real_credential_access_performed,
        real_secret_load_performed=admission.real_secret_load_performed,
        post_allowed=admission.post_allowed,
        real_venue_post_allowed=admission.real_venue_post_allowed,
        extra={
            "credential_access_capability_implemented": str(
                admission.credential_access_capability_implemented
            ).lower(),
        },
    )


__all__ = [
    "BINDING_OWNER",
    "CredentialAccessBoundCapabilityResultV1",
    "evaluate_credential_access_bound_checkout_independent_capability_seam_v1",
]
