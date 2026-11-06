"""Runtime binding: K1 PRE-POST policy → governed construction seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.current_productive_k1_opaque_signing_handle_pre_post_policy_v1 import (
    STATUS_PRE_POST_ADMISSION_DENIED,
    TARGET_GOVERNED_CONSTRUCTION_MODULE,
    evaluate_k1_opaque_signing_handle_pre_post_admission_v1,
    k1_opaque_signing_handle_pre_post_policy_granted_v1,
    validate_k1_opaque_signing_handle_pre_post_policy_record_v1,
)
from src.governance.real_keychain_access_or_credential_material_load_gate_binding_v1 import (
    evaluate_material_load_bound_credential_acquisition_seam_v1,
)

BINDING_OWNER: Final[str] = (
    "governance.current_productive_k1_opaque_signing_handle_pre_post_gate_binding_v1"
)


@dataclass(frozen=True, slots=True)
class K1PrePostBoundConstructionResultV1:
    k1_pre_post_admission_granted: bool
    material_load_admission_granted: bool
    governed_construction_module: str
    k1_pre_post_policy_record_digest: str | None
    material_load_policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    governed_k1_opaque_signing_authorized: bool
    opaque_signing_handle_authorized: bool
    request_signing_authorized: bool
    pre_post_envelope_authorized: bool
    post_allowed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_k1_pre_post_bound_opaque_signing_construction_seam_v1(
    *, repo_root: Path | None = None
) -> K1PrePostBoundConstructionResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    material_bound = evaluate_material_load_bound_credential_acquisition_seam_v1(repo_root=root)

    if not k1_opaque_signing_handle_pre_post_policy_granted_v1(repo_root=root):
        k1_policy = validate_k1_opaque_signing_handle_pre_post_policy_record_v1(repo_root=root)
        return K1PrePostBoundConstructionResultV1(
            k1_pre_post_admission_granted=False,
            material_load_admission_granted=material_bound.material_load_admission_granted,
            governed_construction_module=TARGET_GOVERNED_CONSTRUCTION_MODULE,
            k1_pre_post_policy_record_digest=k1_policy.policy_record_digest,
            material_load_policy_record_digest=material_bound.material_load_policy_record_digest,
            reason_codes=k1_policy.reason_codes or ("K1_PRE_POST_POLICY_NOT_AUTHORIZED",),
            governed_k1_opaque_signing_authorized=False,
            opaque_signing_handle_authorized=False,
            request_signing_authorized=False,
            pre_post_envelope_authorized=False,
            post_allowed=False,
        )

    admission = evaluate_k1_opaque_signing_handle_pre_post_admission_v1(repo_root=root)
    granted = admission.k1_pre_post_policy_granted is True
    return K1PrePostBoundConstructionResultV1(
        k1_pre_post_admission_granted=granted,
        material_load_admission_granted=material_bound.material_load_admission_granted,
        governed_construction_module=TARGET_GOVERNED_CONSTRUCTION_MODULE,
        k1_pre_post_policy_record_digest=admission.policy_record_digest,
        material_load_policy_record_digest=material_bound.material_load_policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_PRE_POST_ADMISSION_DENIED,),
        governed_k1_opaque_signing_authorized=admission.governed_k1_opaque_signing_authorized,
        opaque_signing_handle_authorized=admission.opaque_signing_handle_authorized,
        request_signing_authorized=admission.request_signing_authorized,
        pre_post_envelope_authorized=admission.pre_post_envelope_authorized,
        post_allowed=admission.post_allowed,
        extra={
            "governed_credential_material_load": str(
                admission.governed_credential_material_load_authorized
            ).lower(),
        },
    )


__all__ = [
    "BINDING_OWNER",
    "K1PrePostBoundConstructionResultV1",
    "evaluate_k1_pre_post_bound_opaque_signing_construction_seam_v1",
]
