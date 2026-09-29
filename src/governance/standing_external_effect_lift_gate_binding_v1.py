"""Runtime binding: Standing External Effect Lift → gate seam (parameterized standing)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from src.governance.external_effect_authorization_policy_gate_binding_v1 import (
    evaluate_policy_bound_external_effect_gate_v1,
)
from src.governance.standing_external_effect_lift_policy_v1 import (
    STATUS_LIFT_DENIED,
    evaluate_standing_external_effect_lift_admission_v1,
    standing_external_effect_lift_granted_v1,
    validate_standing_external_effect_lift_policy_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    ExternalEffectDecisionV1,
    evaluate_external_effect_v1,
)

BINDING_OWNER: Final[str] = "governance.standing_external_effect_lift_gate_binding_v1"


@dataclass(frozen=True, slots=True)
class LiftBoundExternalEffectGateResultV1:
    lift_admission_granted: bool
    policy_bound_admission_granted: bool
    gate_decision_at_lift_standing: ExternalEffectDecisionV1
    gate_decision_at_import_standing: ExternalEffectDecisionV1
    lift_policy_record_digest: str | None
    external_effect_policy_record_digest: str | None
    reason_codes: tuple[str, ...]
    governed_standing_external_effect_authorized: bool
    post_allowed: bool
    real_venue_post_allowed: bool
    permit_mint_authorized: bool
    credential_access_performed: bool
    extra: dict[str, str] = field(default_factory=dict)


def evaluate_lift_bound_external_effect_gate_v1(
    *, repo_root: Path | None = None
) -> LiftBoundExternalEffectGateResultV1:
    root = repo_root or Path(__file__).resolve().parents[2]
    import_standing = evaluate_external_effect_v1()
    policy_bound = evaluate_policy_bound_external_effect_gate_v1(repo_root=root)

    if not standing_external_effect_lift_granted_v1(repo_root=root):
        lift_policy = validate_standing_external_effect_lift_policy_record_v1(repo_root=root)
        return LiftBoundExternalEffectGateResultV1(
            lift_admission_granted=False,
            policy_bound_admission_granted=policy_bound.policy_admission_granted,
            gate_decision_at_lift_standing=import_standing,
            gate_decision_at_import_standing=import_standing,
            lift_policy_record_digest=lift_policy.policy_record_digest,
            external_effect_policy_record_digest=policy_bound.policy_record_digest,
            reason_codes=lift_policy.reason_codes or ("LIFT_POLICY_NOT_AUTHORIZED",),
            governed_standing_external_effect_authorized=False,
            post_allowed=False,
            real_venue_post_allowed=False,
            permit_mint_authorized=False,
            credential_access_performed=False,
        )

    admission = evaluate_standing_external_effect_lift_admission_v1(repo_root=root)
    lift_gate = admission.gate_decision or evaluate_external_effect_v1(
        standing_external_effect_authorized=True
    )
    granted = admission.standing_external_effect_lift_granted is True
    return LiftBoundExternalEffectGateResultV1(
        lift_admission_granted=granted,
        policy_bound_admission_granted=policy_bound.policy_admission_granted,
        gate_decision_at_lift_standing=lift_gate,
        gate_decision_at_import_standing=import_standing,
        lift_policy_record_digest=admission.policy_record_digest,
        external_effect_policy_record_digest=policy_bound.policy_record_digest,
        reason_codes=admission.reason_codes
        if granted
        else admission.reason_codes or (STATUS_LIFT_DENIED,),
        governed_standing_external_effect_authorized=admission.governed_standing_external_effect_authorized,
        post_allowed=admission.post_allowed,
        real_venue_post_allowed=admission.real_venue_post_allowed,
        permit_mint_authorized=admission.permit_mint_authorized,
        credential_access_performed=admission.credential_access_performed,
    )


__all__ = [
    "BINDING_OWNER",
    "LiftBoundExternalEffectGateResultV1",
    "evaluate_lift_bound_external_effect_gate_v1",
]
