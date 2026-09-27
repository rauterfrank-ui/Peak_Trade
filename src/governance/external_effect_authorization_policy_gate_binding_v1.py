"""Runtime binding: External Effect authorization policy → standing gate seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.external_effect_authorization_policy_v1 import (
    BOUNDARY_TERMINAL,
    GATE_SEAM,
    STATUS_ADMISSION_DENIED,
    evaluate_external_effect_policy_admission_v1,
    standing_external_effect_authorization_policy_authorized_v1,
    validate_external_effect_authorization_policy_record_v1,
)
from src.governance.checkout_independent_credential_access_policy_v1 import (
    governed_credential_access_authorized_v1,
)
from src.governance.external_effect_permit_mint_policy_v1 import (
    governed_permit_mint_authorized_v1,
)
from src.governance.standing_external_effect_lift_policy_v1 import (
    governed_standing_external_effect_authorized_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    ExternalEffectDecisionV1,
    evaluate_external_effect_v1,
)

BINDING_OWNER: Final[str] = "governance.external_effect_authorization_policy_gate_binding_v1"


@dataclass(frozen=True, slots=True)
class PolicyBoundExternalEffectGateResultV1:
    policy_admission_granted: bool
    gate_decision: ExternalEffectDecisionV1
    boundary_terminal: str
    gate_seam: str
    policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    standing_external_effect_authorized: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    permit_mint_authorized: bool
    credential_access_performed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_policy_bound_external_effect_gate_v1(
    *, repo_root: Path | None = None
) -> PolicyBoundExternalEffectGateResultV1:
    """Evaluate policy admission then re-read standing gate; never mutates standing flags."""
    root = repo_root or Path(__file__).resolve().parents[2]
    if not standing_external_effect_authorization_policy_authorized_v1(repo_root=root):
        gate = evaluate_external_effect_v1()
        policy = validate_external_effect_authorization_policy_record_v1(repo_root=root)
        return PolicyBoundExternalEffectGateResultV1(
            policy_admission_granted=False,
            gate_decision=gate,
            boundary_terminal=BOUNDARY_TERMINAL,
            gate_seam=GATE_SEAM,
            policy_record_digest=policy.policy_record_digest,
            reason_codes=policy.reason_codes or ("POLICY_NOT_AUTHORIZED",),
            standing_external_effect_authorized=False,
            post_allowed=False,
            real_venue_post_allowed=False,
            permit_mint_authorized=False,
            credential_access_performed=False,
        )

    admission = evaluate_external_effect_policy_admission_v1(repo_root=root)
    gate = admission.gate_decision or evaluate_external_effect_v1()
    granted = admission.policy_admission_granted is True
    lift_standing = governed_standing_external_effect_authorized_v1(repo_root=root)
    permit_mint = governed_permit_mint_authorized_v1(repo_root=root)
    credential_access = governed_credential_access_authorized_v1(repo_root=root)
    return PolicyBoundExternalEffectGateResultV1(
        policy_admission_granted=granted,
        gate_decision=gate,
        boundary_terminal=BOUNDARY_TERMINAL,
        gate_seam=GATE_SEAM,
        policy_record_digest=admission.policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_ADMISSION_DENIED,),
        standing_external_effect_authorized=lift_standing,
        post_allowed=admission.post_allowed,
        real_venue_post_allowed=admission.real_venue_post_allowed,
        permit_mint_authorized=permit_mint,
        credential_access_performed=admission.credential_access_performed,
        extra={
            "governed_standing_lift": str(lift_standing).lower(),
            "governed_permit_mint": str(permit_mint).lower(),
            "governed_credential_access": str(credential_access).lower(),
        },
    )


__all__ = [
    "BINDING_OWNER",
    "PolicyBoundExternalEffectGateResultV1",
    "evaluate_policy_bound_external_effect_gate_v1",
]
