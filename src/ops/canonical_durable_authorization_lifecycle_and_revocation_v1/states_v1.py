"""Canonical authorization lifecycle states (fail-closed enum)."""

from __future__ import annotations

from enum import Enum


class AuthorizationStateV2(str, Enum):
    CREATED_UNCONSUMED = "CREATED_UNCONSUMED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"
    INVALIDATED = "INVALIDATED"


TERMINAL_STATES: frozenset[AuthorizationStateV2] = frozenset(
    {
        AuthorizationStateV2.CONSUMED,
        AuthorizationStateV2.REVOKED,
        AuthorizationStateV2.INVALIDATED,
    }
)

ALLOWED_TRANSITIONS: dict[AuthorizationStateV2, frozenset[AuthorizationStateV2]] = {
    AuthorizationStateV2.CREATED_UNCONSUMED: frozenset(
        {
            AuthorizationStateV2.CONSUMED,
            AuthorizationStateV2.REVOKED,
            AuthorizationStateV2.INVALIDATED,
        }
    ),
    AuthorizationStateV2.CONSUMED: frozenset(),
    AuthorizationStateV2.REVOKED: frozenset(),
    AuthorizationStateV2.INVALIDATED: frozenset(),
}


class AuthorizationStateError(ValueError):
    """Fail-closed state/transition error."""


def parse_authorization_state_v2(value: object) -> AuthorizationStateV2:
    raw = str(value or "").strip()
    try:
        return AuthorizationStateV2(raw)
    except ValueError as exc:
        raise AuthorizationStateError(f"UNKNOWN_AUTHORIZATION_STATE:{value}") from exc


def assert_transition_allowed_v2(
    *,
    from_state: AuthorizationStateV2,
    to_state: AuthorizationStateV2,
) -> None:
    if from_state in TERMINAL_STATES:
        raise AuthorizationStateError(f"EVENT_AFTER_TERMINAL:{from_state.value}")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise AuthorizationStateError(
            f"INVALID_STATE_TRANSITION:{from_state.value}->{to_state.value}"
        )


def is_consumable_state_v2(state: AuthorizationStateV2) -> bool:
    return state is AuthorizationStateV2.CREATED_UNCONSUMED
