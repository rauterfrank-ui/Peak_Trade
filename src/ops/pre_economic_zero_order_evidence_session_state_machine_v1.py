"""Session state machine for Pre-Economic Zero-Order Evidence production path v1.

Capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION

COMPLETED means only that the full wallclock duration finished technically.
SESSION_EVIDENCE_VALID is never granted by this module.
"""

from __future__ import annotations

from enum import Enum


PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION=true"
CAPABILITY_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION"


class SessionState(str, Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


TERMINAL_STATES = frozenset(
    {
        SessionState.COMPLETED,
        SessionState.ABORTED,
        SessionState.INCOMPLETE,
        SessionState.INVALID,
        SessionState.REVOKED,
        SessionState.EXPIRED,
    }
)

ALLOWED_TRANSITIONS: dict[SessionState, frozenset[SessionState]] = {
    SessionState.CREATED: frozenset(
        {
            SessionState.AUTHORIZED,
            SessionState.INVALID,
            SessionState.EXPIRED,
            SessionState.REVOKED,
        }
    ),
    SessionState.AUTHORIZED: frozenset(
        {
            SessionState.STARTING,
            SessionState.REVOKED,
            SessionState.EXPIRED,
            SessionState.INVALID,
        }
    ),
    SessionState.STARTING: frozenset(
        {
            SessionState.RUNNING,
            SessionState.ABORTED,
            SessionState.INCOMPLETE,
            SessionState.INVALID,
            SessionState.REVOKED,
        }
    ),
    SessionState.RUNNING: frozenset(
        {
            SessionState.COMPLETED,
            SessionState.ABORTED,
            SessionState.INCOMPLETE,
            SessionState.INVALID,
            SessionState.REVOKED,
            SessionState.EXPIRED,
        }
    ),
    SessionState.COMPLETED: frozenset(),
    SessionState.ABORTED: frozenset(),
    SessionState.INCOMPLETE: frozenset(),
    SessionState.INVALID: frozenset(),
    SessionState.REVOKED: frozenset(),
    SessionState.EXPIRED: frozenset(),
}


class SessionStateMachineError(ValueError):
    """Fail-closed state transition error."""


def assert_transition_allowed(*, from_state: SessionState, to_state: SessionState) -> None:
    if from_state in TERMINAL_STATES:
        raise SessionStateMachineError(f"EVENT_AFTER_TERMINAL:{from_state.value}")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise SessionStateMachineError(
            f"INVALID_STATE_TRANSITION:{from_state.value}->{to_state.value}"
        )


def is_terminal(state: SessionState) -> bool:
    return state in TERMINAL_STATES


def completed_is_not_evidence_valid() -> bool:
    """Invariant helper: COMPLETED ≠ SESSION_EVIDENCE_VALID."""

    return True
