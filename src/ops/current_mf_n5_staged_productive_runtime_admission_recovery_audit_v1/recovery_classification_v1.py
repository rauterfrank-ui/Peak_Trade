"""Restart/recovery classification — fail-closed portfolio; canonical lane path."""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    PORTFOLIO_RESTART_STATUS,
    RECOVERY_LANE_DURABLE,
    RECOVERY_PORTFOLIO_FAIL_CLOSED,
    RESTART_SELF_AUTHORIZATION_FORBIDDEN,
)
from src.ops.mf_membership_context_artifact_contract_v1 import MembershipContextArtifactV1


@dataclass(frozen=True)
class ProductiveRuntimeRecoveryClassificationV1:
    lane_recovery_class: str
    portfolio_restart_class: str
    membership_bootstrap: bool
    prior_membership_reference: str | None
    restart_self_authorization_forbidden: bool
    portfolio_reconstruction_attempted: bool


def classify_productive_runtime_recovery_v1(
    *,
    membership: MembershipContextArtifactV1,
) -> ProductiveRuntimeRecoveryClassificationV1:
    """Classify recovery surfaces. Does not reconstruct portfolio capital."""
    return ProductiveRuntimeRecoveryClassificationV1(
        lane_recovery_class=RECOVERY_LANE_DURABLE,
        portfolio_restart_class=(
            RECOVERY_PORTFOLIO_FAIL_CLOSED
            if PORTFOLIO_RESTART_STATUS == "FAIL_CLOSED_NO_UNPROVEN_RESTORE"
            else PORTFOLIO_RESTART_STATUS
        ),
        membership_bootstrap=bool(membership.bootstrap),
        prior_membership_reference=membership.prior_membership_reference,
        restart_self_authorization_forbidden=RESTART_SELF_AUTHORIZATION_FORBIDDEN,
        portfolio_reconstruction_attempted=False,
    )
