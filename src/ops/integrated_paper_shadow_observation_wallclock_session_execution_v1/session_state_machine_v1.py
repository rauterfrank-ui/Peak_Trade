"""Wallclock observation session state machine."""

from __future__ import annotations

from enum import Enum


class WallclockSessionState(str, Enum):
    CREATED = "CREATED"
    AUTH_VERIFIED = "AUTH_VERIFIED"
    CONSUMED = "CONSUMED"
    LOCKED = "LOCKED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    RECONNECTING = "RECONNECTING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    KILLSTATE = "KILLSTATE"
    INVALID = "INVALID"


TERMINAL_STATES = frozenset(
    {
        WallclockSessionState.COMPLETED,
        WallclockSessionState.TIMED_OUT,
        WallclockSessionState.FAILED,
        WallclockSessionState.ABORTED,
        WallclockSessionState.KILLSTATE,
        WallclockSessionState.INVALID,
    }
)

ALLOWED_TRANSITIONS: dict[WallclockSessionState, frozenset[WallclockSessionState]] = {
    # AUTH_VERIFIED is retained for historical enum compatibility but must never
    # occur before successful atomic v2 consumption. Productive path: CREATED→CONSUMED.
    WallclockSessionState.CREATED: frozenset(
        {
            WallclockSessionState.CONSUMED,
            WallclockSessionState.INVALID,
        }
    ),
    WallclockSessionState.AUTH_VERIFIED: frozenset(
        {
            WallclockSessionState.CONSUMED,
            WallclockSessionState.INVALID,
            WallclockSessionState.ABORTED,
        }
    ),
    WallclockSessionState.CONSUMED: frozenset(
        {
            WallclockSessionState.LOCKED,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
        }
    ),
    WallclockSessionState.LOCKED: frozenset(
        {
            WallclockSessionState.STARTING,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
        }
    ),
    WallclockSessionState.STARTING: frozenset(
        {
            WallclockSessionState.RUNNING,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
        }
    ),
    WallclockSessionState.RUNNING: frozenset(
        {
            WallclockSessionState.RECONNECTING,
            WallclockSessionState.STOPPING,
            WallclockSessionState.COMPLETED,
            WallclockSessionState.TIMED_OUT,
            WallclockSessionState.FAILED,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
        }
    ),
    WallclockSessionState.RECONNECTING: frozenset(
        {
            WallclockSessionState.RUNNING,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
            WallclockSessionState.STOPPING,
        }
    ),
    WallclockSessionState.STOPPING: frozenset(
        {
            WallclockSessionState.COMPLETED,
            WallclockSessionState.FAILED,
            WallclockSessionState.ABORTED,
            WallclockSessionState.KILLSTATE,
            WallclockSessionState.TIMED_OUT,
        }
    ),
    WallclockSessionState.COMPLETED: frozenset(),
    WallclockSessionState.TIMED_OUT: frozenset(),
    WallclockSessionState.FAILED: frozenset(),
    WallclockSessionState.ABORTED: frozenset(),
    WallclockSessionState.KILLSTATE: frozenset(),
    WallclockSessionState.INVALID: frozenset(),
}


class WallclockStateMachineError(ValueError):
    """Fail-closed state transition error."""


def assert_transition_allowed(
    *,
    from_state: WallclockSessionState,
    to_state: WallclockSessionState,
) -> None:
    if from_state in TERMINAL_STATES:
        raise WallclockStateMachineError(f"EVENT_AFTER_TERMINAL:{from_state.value}")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise WallclockStateMachineError(
            f"INVALID_STATE_TRANSITION:{from_state.value}->{to_state.value}"
        )


def is_terminal(state: WallclockSessionState) -> bool:
    return state in TERMINAL_STATES
