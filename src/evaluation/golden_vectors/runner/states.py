"""Canonical GVEF V1.5 runner state machine."""

from __future__ import annotations

from enum import Enum

from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError


class RunnerState(str, Enum):
    CREATED = "CREATED"
    BOUND = "BOUND"
    PRE_CONSTRAINT_CHECKED = "PRE_CONSTRAINT_CHECKED"
    REPLAY_READY = "REPLAY_READY"
    REPLAYED = "REPLAYED"
    EVALUATED = "EVALUATED"
    COMPARED = "COMPARED"
    DELTA_MANIFEST_BUILT = "DELTA_MANIFEST_BUILT"
    POST_CONSTRAINT_CHECKED = "POST_CONSTRAINT_CHECKED"
    EVIDENCE_BUILT = "EVIDENCE_BUILT"
    REGISTERED = "REGISTERED"
    FAILED = "FAILED"


_TRANSITIONS: dict[RunnerState, frozenset[RunnerState]] = {
    RunnerState.CREATED: frozenset({RunnerState.BOUND, RunnerState.FAILED}),
    RunnerState.BOUND: frozenset({RunnerState.PRE_CONSTRAINT_CHECKED, RunnerState.FAILED}),
    RunnerState.PRE_CONSTRAINT_CHECKED: frozenset({RunnerState.REPLAY_READY, RunnerState.FAILED}),
    RunnerState.REPLAY_READY: frozenset({RunnerState.REPLAYED, RunnerState.FAILED}),
    RunnerState.REPLAYED: frozenset({RunnerState.EVALUATED, RunnerState.FAILED}),
    RunnerState.EVALUATED: frozenset({RunnerState.COMPARED, RunnerState.FAILED}),
    RunnerState.COMPARED: frozenset({RunnerState.DELTA_MANIFEST_BUILT, RunnerState.FAILED}),
    RunnerState.DELTA_MANIFEST_BUILT: frozenset(
        {RunnerState.POST_CONSTRAINT_CHECKED, RunnerState.FAILED}
    ),
    RunnerState.POST_CONSTRAINT_CHECKED: frozenset(
        {RunnerState.EVIDENCE_BUILT, RunnerState.FAILED}
    ),
    RunnerState.EVIDENCE_BUILT: frozenset({RunnerState.REGISTERED, RunnerState.FAILED}),
    RunnerState.REGISTERED: frozenset(),
    RunnerState.FAILED: frozenset(),
}


def allowed_transitions(state: RunnerState) -> frozenset[RunnerState]:
    return _TRANSITIONS[state]


def transition(current: RunnerState, target: RunnerState) -> RunnerState:
    if current is RunnerState.FAILED:
        raise GvefSchemaError("FAILED is terminal; no transition allowed")
    allowed = _TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise GvefSchemaError(f"illegal transition {current.value} -> {target.value}")
    return target
