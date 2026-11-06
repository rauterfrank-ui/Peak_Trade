"""Runtime binding: material load policy → governed acquisition seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.checkout_independent_credential_access_gate_binding_v1 import (
    evaluate_credential_access_bound_checkout_independent_capability_seam_v1,
)
from src.governance.real_keychain_access_or_credential_material_load_policy_v1 import (
    STATUS_LOAD_ADMISSION_DENIED,
    TARGET_GOVERNED_ACQUISITION_MODULE,
    evaluate_real_keychain_access_or_credential_material_load_admission_v1,
    real_keychain_access_or_credential_material_load_policy_granted_v1,
    validate_real_keychain_access_or_credential_material_load_policy_record_v1,
)

BINDING_OWNER: Final[str] = (
    "governance.real_keychain_access_or_credential_material_load_gate_binding_v1"
)


@dataclass(frozen=True, slots=True)
class MaterialLoadBoundAcquisitionResultV1:
    material_load_admission_granted: bool
    credential_access_admission_granted: bool
    governed_acquisition_module: str
    material_load_policy_record_digest: str | None
    credential_access_policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    governed_credential_material_load_authorized: bool
    real_keychain_access_authorized: bool
    credential_material_load_authorized: bool
    request_signing_authorized: bool
    post_allowed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_material_load_bound_credential_acquisition_seam_v1(
    *, repo_root: Path | None = None
) -> MaterialLoadBoundAcquisitionResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    cred_bound = evaluate_credential_access_bound_checkout_independent_capability_seam_v1(
        repo_root=root
    )

    if not real_keychain_access_or_credential_material_load_policy_granted_v1(repo_root=root):
        load_policy = validate_real_keychain_access_or_credential_material_load_policy_record_v1(
            repo_root=root
        )
        return MaterialLoadBoundAcquisitionResultV1(
            material_load_admission_granted=False,
            credential_access_admission_granted=cred_bound.credential_access_admission_granted,
            governed_acquisition_module=TARGET_GOVERNED_ACQUISITION_MODULE,
            material_load_policy_record_digest=load_policy.policy_record_digest,
            credential_access_policy_record_digest=cred_bound.credential_access_policy_record_digest,
            reason_codes=load_policy.reason_codes or ("MATERIAL_LOAD_POLICY_NOT_AUTHORIZED",),
            governed_credential_material_load_authorized=False,
            real_keychain_access_authorized=False,
            credential_material_load_authorized=False,
            request_signing_authorized=False,
            post_allowed=False,
        )

    admission = evaluate_real_keychain_access_or_credential_material_load_admission_v1(
        repo_root=root
    )
    granted = admission.material_load_policy_granted is True
    return MaterialLoadBoundAcquisitionResultV1(
        material_load_admission_granted=granted,
        credential_access_admission_granted=cred_bound.credential_access_admission_granted,
        governed_acquisition_module=TARGET_GOVERNED_ACQUISITION_MODULE,
        material_load_policy_record_digest=admission.policy_record_digest,
        credential_access_policy_record_digest=cred_bound.credential_access_policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_LOAD_ADMISSION_DENIED,),
        governed_credential_material_load_authorized=admission.governed_credential_material_load_authorized,
        real_keychain_access_authorized=admission.real_keychain_access_authorized,
        credential_material_load_authorized=admission.credential_material_load_authorized,
        request_signing_authorized=admission.request_signing_authorized,
        post_allowed=admission.post_allowed,
        extra={
            "credential_material_load_capability_implemented": str(
                admission.credential_material_load_capability_implemented
            ).lower(),
        },
    )


__all__ = [
    "BINDING_OWNER",
    "MaterialLoadBoundAcquisitionResultV1",
    "evaluate_material_load_bound_credential_acquisition_seam_v1",
]
