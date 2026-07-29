"""Two-stage enabled/armed authorization state machine (non-executing)."""

from __future__ import annotations

from enum import Enum
from typing import Optional


class AuthorizationArmingState(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    ARMED = "armed"
    AUTHORIZED = "authorized"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REJECTED = "rejected"


TERMINAL_STATES = frozenset(
    {
        AuthorizationArmingState.CONSUMED,
        AuthorizationArmingState.EXPIRED,
        AuthorizationArmingState.REVOKED,
        AuthorizationArmingState.REJECTED,
    }
)

ALLOWED_TRANSITIONS: dict[AuthorizationArmingState, frozenset[AuthorizationArmingState]] = {
    AuthorizationArmingState.DISABLED: frozenset(
        {
            AuthorizationArmingState.ENABLED,
            AuthorizationArmingState.REJECTED,
            AuthorizationArmingState.EXPIRED,
            AuthorizationArmingState.REVOKED,
        }
    ),
    AuthorizationArmingState.ENABLED: frozenset(
        {
            AuthorizationArmingState.ARMED,
            AuthorizationArmingState.DISABLED,
            AuthorizationArmingState.REJECTED,
            AuthorizationArmingState.EXPIRED,
            AuthorizationArmingState.REVOKED,
        }
    ),
    AuthorizationArmingState.ARMED: frozenset(
        {
            AuthorizationArmingState.AUTHORIZED,
            AuthorizationArmingState.ENABLED,
            AuthorizationArmingState.REJECTED,
            AuthorizationArmingState.EXPIRED,
            AuthorizationArmingState.REVOKED,
        }
    ),
    AuthorizationArmingState.AUTHORIZED: frozenset(
        {
            AuthorizationArmingState.CONSUMED,
            AuthorizationArmingState.EXPIRED,
            AuthorizationArmingState.REVOKED,
            AuthorizationArmingState.REJECTED,
        }
    ),
    AuthorizationArmingState.CONSUMED: frozenset(),
    AuthorizationArmingState.EXPIRED: frozenset(),
    AuthorizationArmingState.REVOKED: frozenset(),
    AuthorizationArmingState.REJECTED: frozenset(),
}


class AuthorizationStateMachineError(ValueError):
    """Fail-closed arming state transition error."""


def parse_arming_state(value: str) -> AuthorizationArmingState:
    raw = str(value or "").strip().lower()
    try:
        return AuthorizationArmingState(raw)
    except ValueError as exc:
        raise AuthorizationStateMachineError(f"UNKNOWN_ARMING_STATE:{value}") from exc


def assert_transition_allowed(
    *,
    from_state: AuthorizationArmingState,
    to_state: AuthorizationArmingState,
) -> None:
    if from_state in TERMINAL_STATES:
        raise AuthorizationStateMachineError(f"EVENT_AFTER_TERMINAL:{from_state.value}")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise AuthorizationStateMachineError(
            f"INVALID_STATE_TRANSITION:{from_state.value}->{to_state.value}"
        )


def is_terminal(state: AuthorizationArmingState) -> bool:
    return state in TERMINAL_STATES


def derive_arming_state(
    *,
    enabled: bool,
    armed: bool,
    authorized: bool,
    consumed: bool,
    expired: bool,
    revoked: bool,
    rejected: bool,
) -> AuthorizationArmingState:
    """Deterministic derivation. Terminal flags dominate."""
    if rejected:
        return AuthorizationArmingState.REJECTED
    if revoked:
        return AuthorizationArmingState.REVOKED
    if expired:
        return AuthorizationArmingState.EXPIRED
    if consumed:
        return AuthorizationArmingState.CONSUMED
    if authorized:
        if not (enabled and armed):
            return AuthorizationArmingState.REJECTED
        return AuthorizationArmingState.AUTHORIZED
    if armed and enabled:
        return AuthorizationArmingState.ARMED
    if armed and not enabled:
        return AuthorizationArmingState.REJECTED
    if enabled:
        return AuthorizationArmingState.ENABLED
    return AuthorizationArmingState.DISABLED


def assert_authorization_preconditions(
    *,
    enabled: bool,
    armed: bool,
) -> Optional[str]:
    """enabled alone and armed alone never authorize."""
    if not enabled and not armed:
        return "ARMING_DISABLED"
    if enabled and not armed:
        return "ENABLED_BUT_NOT_ARMED"
    if armed and not enabled:
        return "ARMED_BUT_NOT_ENABLED"
    return None
