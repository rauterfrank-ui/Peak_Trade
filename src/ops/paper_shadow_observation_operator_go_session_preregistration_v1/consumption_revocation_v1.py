"""Pure consume/revoke/expire transitions for authorization artifacts.

No session execution. No global mutable registry. Returns new artifact models only.
Actual consume at session start is reserved for a later execution capability.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    AuthorizationArtifactV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.state_machine_v1 import (
    AuthorizationArmingState,
    AuthorizationStateMachineError,
    assert_transition_allowed,
    parse_arming_state,
)


class ConsumptionRevocationError(ValueError):
    """Fail-closed consumption/revocation error."""


def transition_consume_authorization_artifact_v1(
    artifact: AuthorizationArtifactV1,
    *,
    now_unix: Optional[float] = None,
) -> AuthorizationArtifactV1:
    """Pure transition AUTHORIZED -> CONSUMED. Does not start a session."""
    state = parse_arming_state(artifact.arming_state)
    try:
        assert_transition_allowed(from_state=state, to_state=AuthorizationArmingState.CONSUMED)
    except AuthorizationStateMachineError as exc:
        raise ConsumptionRevocationError(str(exc)) from exc
    if artifact.consumed:
        raise ConsumptionRevocationError("ALREADY_CONSUMED")
    if artifact.revoked:
        raise ConsumptionRevocationError("REVOKED_CANNOT_CONSUME")
    if now_unix is not None and now_unix > artifact.expires_at:
        raise ConsumptionRevocationError("EXPIRED_CANNOT_CONSUME")
    return replace(
        artifact,
        consumed=True,
        arming_state=AuthorizationArmingState.CONSUMED.value,
        paper_shadow_observation_authorized=False,
        notes=tuple(artifact.notes) + ("CONSUMED_CONTRACT_ONLY_NO_SESSION",),
    )


def transition_revoke_authorization_artifact_v1(
    artifact: AuthorizationArtifactV1,
    *,
    reason: str = "operator_revoke",
) -> AuthorizationArtifactV1:
    state = parse_arming_state(artifact.arming_state)
    try:
        assert_transition_allowed(from_state=state, to_state=AuthorizationArmingState.REVOKED)
    except AuthorizationStateMachineError as exc:
        raise ConsumptionRevocationError(str(exc)) from exc
    return replace(
        artifact,
        revoked=True,
        revocation_state=f"revoked:{reason}",
        arming_state=AuthorizationArmingState.REVOKED.value,
        paper_shadow_observation_authorized=False,
        notes=tuple(artifact.notes) + ("REVOKED_CONTRACT_ONLY",),
    )


def transition_expire_authorization_artifact_v1(
    artifact: AuthorizationArtifactV1,
) -> AuthorizationArtifactV1:
    state = parse_arming_state(artifact.arming_state)
    try:
        assert_transition_allowed(from_state=state, to_state=AuthorizationArmingState.EXPIRED)
    except AuthorizationStateMachineError as exc:
        raise ConsumptionRevocationError(str(exc)) from exc
    return replace(
        artifact,
        arming_state=AuthorizationArmingState.EXPIRED.value,
        paper_shadow_observation_authorized=False,
        notes=tuple(artifact.notes) + ("EXPIRED_CONTRACT_ONLY",),
    )
