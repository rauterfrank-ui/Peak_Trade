"""Monotonic lifecycle state machine for V5 process observability."""

from __future__ import annotations

from typing import Any

from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.constants_v5 import (
    LIFECYCLE_STATE_CHECKPOINT_COMMITTED,
    LIFECYCLE_STATE_MEMBER_COMPLETED,
    LIFECYCLE_STATE_MEMBER_STARTED,
    LIFECYCLE_STATE_TERMINAL_COMMITTED,
    MEMBER_LOOP_STATES,
    MONOTONIC_LIFECYCLE_STATES,
)


class LifecycleStateError(ValueError):
    """Fail-closed lifecycle transition error."""


_STATE_INDEX = {state: idx for idx, state in enumerate(MONOTONIC_LIFECYCLE_STATES)}


def assert_known_lifecycle_state(state: str) -> None:
    if state not in _STATE_INDEX:
        raise LifecycleStateError(f"UNKNOWN_LIFECYCLE_STATE:{state}")


def is_lifecycle_terminal(state: str) -> bool:
    assert_known_lifecycle_state(state)
    return state == LIFECYCLE_STATE_TERMINAL_COMMITTED


def assert_monotonic_transition(*, from_state: str, to_state: str) -> None:
    """Allow forward transitions; member-loop may revisit started/completed/checkpoint."""
    assert_known_lifecycle_state(from_state)
    assert_known_lifecycle_state(to_state)
    if from_state == to_state:
        return
    if is_lifecycle_terminal(from_state):
        raise LifecycleStateError("TRANSITION_FROM_TERMINAL_FORBIDDEN")
    from_idx = _STATE_INDEX[from_state]
    to_idx = _STATE_INDEX[to_state]
    if to_idx > from_idx:
        return
    # Bounded member loop: after CHECKPOINT_COMMITTED, may start next member.
    if (
        from_state == LIFECYCLE_STATE_CHECKPOINT_COMMITTED
        and to_state == LIFECYCLE_STATE_MEMBER_STARTED
    ):
        return
    if from_state in MEMBER_LOOP_STATES and to_state in MEMBER_LOOP_STATES:
        allowed_pairs = {
            (LIFECYCLE_STATE_MEMBER_STARTED, LIFECYCLE_STATE_MEMBER_COMPLETED),
            (LIFECYCLE_STATE_MEMBER_COMPLETED, LIFECYCLE_STATE_CHECKPOINT_COMMITTED),
            (LIFECYCLE_STATE_CHECKPOINT_COMMITTED, LIFECYCLE_STATE_MEMBER_STARTED),
        }
        if (from_state, to_state) in allowed_pairs:
            return
    raise LifecycleStateError(f"NON_MONOTONIC_TRANSITION:{from_state}->{to_state}")


def build_progress_metadata(
    *,
    run_id: str,
    process_id: int | None,
    started_at: str,
    last_heartbeat_at: str,
    current_member_index: int | None,
    completed_member_count: int,
    total_member_count: int | None,
    last_completed_member_id: str | None,
    lifecycle_state: str,
    checkpoint_sequence: int,
) -> dict[str, Any]:
    assert_known_lifecycle_state(lifecycle_state)
    if int(checkpoint_sequence) < 0:
        raise LifecycleStateError("CHECKPOINT_SEQUENCE_MUST_BE_NON_NEGATIVE")
    if int(completed_member_count) < 0:
        raise LifecycleStateError("COMPLETED_MEMBER_COUNT_MUST_BE_NON_NEGATIVE")
    return {
        "run_id": str(run_id),
        "process_id": process_id,
        "started_at": str(started_at),
        "last_heartbeat_at": str(last_heartbeat_at),
        "current_member_index": current_member_index,
        "completed_member_count": int(completed_member_count),
        "total_member_count": total_member_count,
        "last_completed_member_id": last_completed_member_id,
        "lifecycle_state": lifecycle_state,
        "checkpoint_sequence": int(checkpoint_sequence),
    }
