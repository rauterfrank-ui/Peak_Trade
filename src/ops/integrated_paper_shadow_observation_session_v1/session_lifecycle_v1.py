"""Observation session lifecycle contract (non-executing).

Defines Start/Timeout/Stop/Lock/Killstate/No-Auto-Promotion semantics.
Wallclock session execution is refused by this offline capability.
Successor owner:
``INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    NO_AUTO_PROMOTION,
    WALLCLOCK_SESSION_EXECUTION_ALLOWED,
)

LIFECYCLE_OWNER = "ops.integrated_paper_shadow_observation_session_lifecycle_v1"
LIFECYCLE_SCHEMA_VERSION = "v1"


class ObservationSessionState(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"
    KILLSTATE = "KILLSTATE"
    INVALID = "INVALID"
    LOCKED = "LOCKED"


TERMINAL_STATES = frozenset(
    {
        ObservationSessionState.COMPLETED,
        ObservationSessionState.TIMED_OUT,
        ObservationSessionState.ABORTED,
        ObservationSessionState.KILLSTATE,
        ObservationSessionState.INVALID,
    }
)

ALLOWED_TRANSITIONS: dict[ObservationSessionState, frozenset[ObservationSessionState]] = {
    ObservationSessionState.CREATED: frozenset(
        {
            ObservationSessionState.READY,
            ObservationSessionState.LOCKED,
            ObservationSessionState.INVALID,
        }
    ),
    ObservationSessionState.READY: frozenset(
        {
            ObservationSessionState.STARTING,
            ObservationSessionState.LOCKED,
            ObservationSessionState.INVALID,
            ObservationSessionState.ABORTED,
        }
    ),
    ObservationSessionState.STARTING: frozenset(
        {
            ObservationSessionState.RUNNING,
            ObservationSessionState.ABORTED,
            ObservationSessionState.KILLSTATE,
            ObservationSessionState.INVALID,
        }
    ),
    ObservationSessionState.RUNNING: frozenset(
        {
            ObservationSessionState.STOPPING,
            ObservationSessionState.COMPLETED,
            ObservationSessionState.TIMED_OUT,
            ObservationSessionState.ABORTED,
            ObservationSessionState.KILLSTATE,
            ObservationSessionState.INVALID,
        }
    ),
    ObservationSessionState.STOPPING: frozenset(
        {
            ObservationSessionState.COMPLETED,
            ObservationSessionState.ABORTED,
            ObservationSessionState.KILLSTATE,
            ObservationSessionState.INVALID,
        }
    ),
    ObservationSessionState.LOCKED: frozenset({ObservationSessionState.INVALID}),
    ObservationSessionState.COMPLETED: frozenset(),
    ObservationSessionState.TIMED_OUT: frozenset(),
    ObservationSessionState.ABORTED: frozenset(),
    ObservationSessionState.KILLSTATE: frozenset(),
    ObservationSessionState.INVALID: frozenset(),
}

KILLSTATE_TRIGGERS: tuple[str, ...] = (
    "STALE_DATA",
    "DATA_GAP",
    "CLOCK_DRIFT",
    "INVARIANT_VIOLATION",
    "UNEXPECTED_WRITE_ATTEMPT",
    "CONFIG_DRIFT",
    "DUPLICATE_SESSION",
    "EVIDENCE_SINK_FAILURE",
    "SEQUENCE_DISCONNECT",
)


class ObservationLifecycleError(ValueError):
    """Fail-closed lifecycle error."""


@dataclass
class SessionLockRecordV1:
    lock_id: str
    owner: str
    acquired: bool
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObservationLifecyclePlanV1:
    schema_version: str
    lifecycle_owner: str
    state: str
    max_duration_seconds: int
    lock: SessionLockRecordV1
    killstate_armed: bool
    no_auto_promotion: bool
    wallclock_execution_allowed: bool
    authority_effect: str
    auto_promotion_triggered: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["lock"] = self.lock.to_dict()
        return payload


def assert_transition_allowed(
    *, from_state: ObservationSessionState, to_state: ObservationSessionState
) -> None:
    if from_state in TERMINAL_STATES:
        raise ObservationLifecycleError(f"EVENT_AFTER_TERMINAL:{from_state.value}")
    allowed = ALLOWED_TRANSITIONS.get(from_state, frozenset())
    if to_state not in allowed:
        raise ObservationLifecycleError(
            f"INVALID_STATE_TRANSITION:{from_state.value}->{to_state.value}"
        )


def is_terminal(state: ObservationSessionState) -> bool:
    return state in TERMINAL_STATES


def plan_observation_session_lifecycle_v1(
    *,
    lock_id: str = "ipso_session_lock_v1",
    owner: str = LIFECYCLE_OWNER,
    max_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS,
    operator_go_granted: bool = False,
    duplicate_session_detected: bool = False,
) -> ObservationLifecyclePlanV1:
    """Plan-only lifecycle. Never starts wallclock execution."""
    blockers: list[str] = []
    notes = [
        "WALLCLOCK_SESSION_EXECUTION_REFUSED_BY_CAPABILITY",
        "NO_AUTO_PROMOTION",
        "OBSERVATION_ONLY",
        "OPERATOR_GO_NOT_GRANTED_BY_THIS_CAPABILITY",
    ]
    if max_duration_seconds <= 0 or max_duration_seconds > DEFAULT_MAX_SESSION_DURATION_SECONDS:
        blockers.append("INVALID_MAX_DURATION")
    if duplicate_session_detected:
        blockers.append("DUPLICATE_SESSION")
    if operator_go_granted:
        # Capability never accepts GO grant as activation; record and keep blocked.
        blockers.append("OPERATOR_GO_NOT_CONSUMED_BY_THIS_CAPABILITY")
    else:
        blockers.append("OPERATOR_GO_ABSENT_SESSION_REMAINS_BLOCKED")
    if WALLCLOCK_SESSION_EXECUTION_ALLOWED:
        blockers.append("WALLCLOCK_FLAG_MUST_REMAIN_FALSE")

    lock = SessionLockRecordV1(
        lock_id=lock_id,
        owner=owner,
        acquired=False,
        blockers=["LOCK_NOT_ACQUIRED_WITHOUT_AUTHORIZED_EXECUTION"],
    )
    state = (
        ObservationSessionState.INVALID
        if blockers and "INVALID_MAX_DURATION" in blockers
        else ObservationSessionState.CREATED
    )
    return ObservationLifecyclePlanV1(
        schema_version=LIFECYCLE_SCHEMA_VERSION,
        lifecycle_owner=LIFECYCLE_OWNER,
        state=state.value,
        max_duration_seconds=max_duration_seconds,
        lock=lock,
        killstate_armed=True,
        no_auto_promotion=NO_AUTO_PROMOTION,
        wallclock_execution_allowed=False,
        authority_effect=AUTHORITY_EFFECT_NONE,
        auto_promotion_triggered=False,
        blockers=blockers,
        notes=notes,
    )


def refuse_wallclock_session_execution_v1(**_: Any) -> None:
    raise ObservationLifecycleError("WALLCLOCK_SESSION_EXECUTION_FORBIDDEN")


def evaluate_killstate_trigger_v1(trigger: str) -> tuple[bool, str]:
    code = str(trigger or "").strip().upper()
    if code not in KILLSTATE_TRIGGERS:
        return False, f"UNKNOWN_KILLSTATE_TRIGGER:{code}"
    return True, code


def assert_no_auto_promotion_v1(*, next_stage: Optional[str]) -> None:
    if next_stage:
        raise ObservationLifecycleError(f"AUTO_PROMOTION_FORBIDDEN:{next_stage}")
