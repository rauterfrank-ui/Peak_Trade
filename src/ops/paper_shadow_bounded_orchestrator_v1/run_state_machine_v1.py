"""Explicit Paper-Shadow run lifecycle (fail-closed transitions)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunLifecycleState(str, Enum):
    CREATED = "CREATED"
    PREFLIGHT = "PREFLIGHT"
    READY_AWAITING_AUTHORIZATION = "READY_AWAITING_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


class RunStateMachineError(ValueError):
    pass


@dataclass
class RunStateMachineV1:
    state: RunLifecycleState = RunLifecycleState.CREATED
    history: list[str] = field(default_factory=list)

    def _transition(self, new: RunLifecycleState) -> None:
        allowed = _ALLOWED.get(self.state, frozenset())
        if new not in allowed:
            raise RunStateMachineError(f"transition_forbidden:{self.state.value}->{new.value}")
        self.history.append(f"{self.state.value}->{new.value}")
        self.state = new

    def begin_preflight(self) -> None:
        self._transition(RunLifecycleState.PREFLIGHT)

    def complete_preflight_ready(self) -> None:
        self._transition(RunLifecycleState.READY_AWAITING_AUTHORIZATION)

    def authorize(self) -> None:
        self._transition(RunLifecycleState.AUTHORIZED)

    def start_running(self) -> None:
        self._transition(RunLifecycleState.RUNNING)

    def begin_stopping(self) -> None:
        self._transition(RunLifecycleState.STOPPING)

    def complete(self) -> None:
        self._transition(RunLifecycleState.COMPLETED)

    def abort(self) -> None:
        self._transition(RunLifecycleState.ABORTED)

    def fail(self) -> None:
        self._transition(RunLifecycleState.FAILED)

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "history": list(self.history)}


_ALLOWED: dict[RunLifecycleState, frozenset[RunLifecycleState]] = {
    RunLifecycleState.CREATED: frozenset({RunLifecycleState.PREFLIGHT}),
    RunLifecycleState.PREFLIGHT: frozenset(
        {RunLifecycleState.READY_AWAITING_AUTHORIZATION, RunLifecycleState.FAILED}
    ),
    RunLifecycleState.READY_AWAITING_AUTHORIZATION: frozenset(
        {RunLifecycleState.AUTHORIZED, RunLifecycleState.FAILED}
    ),
    RunLifecycleState.AUTHORIZED: frozenset({RunLifecycleState.RUNNING, RunLifecycleState.FAILED}),
    RunLifecycleState.RUNNING: frozenset(
        {RunLifecycleState.STOPPING, RunLifecycleState.ABORTED, RunLifecycleState.FAILED}
    ),
    RunLifecycleState.STOPPING: frozenset(
        {RunLifecycleState.COMPLETED, RunLifecycleState.ABORTED, RunLifecycleState.FAILED}
    ),
    RunLifecycleState.COMPLETED: frozenset(),
    RunLifecycleState.ABORTED: frozenset(),
    RunLifecycleState.FAILED: frozenset(),
}
