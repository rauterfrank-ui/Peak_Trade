"""Kill Switch State Machine for Peak_Trade.

This module defines the state machine, transitions, and events for the
Emergency Kill Switch system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class KillSwitchState(Enum):
    """States of the Kill Switch.

    State Transitions:
        ACTIVE → KILLED (trigger)
        KILLED → RECOVERING (request_recovery)
        RECOVERING → ACTIVE (complete_recovery)
        RECOVERING → KILLED (trigger during recovery)
        DISABLED (no transitions, backtest only)
    """

    ACTIVE = auto()  # Normal operation, trading allowed
    KILLED = auto()  # Emergency stop, no trading
    RECOVERING = auto()  # Cooldown after recovery request
    DISABLED = auto()  # Disabled (backtest mode only)


@dataclass(frozen=True)
class KillSwitchEvent:
    """Immutable event for audit trail.

    Attributes:
        timestamp: When the event occurred
        previous_state: State before transition
        new_state: State after transition
        trigger_reason: Human-readable reason
        triggered_by: Who/what triggered ("system", "manual", "threshold", etc.)
        metadata: Additional context data
    """

    timestamp: datetime
    previous_state: KillSwitchState
    new_state: KillSwitchState
    trigger_reason: str
    triggered_by: str
    metadata: dict

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "previous_state": self.previous_state.name,
            "new_state": self.new_state.name,
            "trigger_reason": self.trigger_reason,
            "triggered_by": self.triggered_by,
            "metadata": self.metadata,
        }


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current: KillSwitchState, requested: KillSwitchState):
        self.current = current
        self.requested = requested
        super().__init__(f"Invalid state transition: {current.name} → {requested.name}")


def validate_transition(
    current: KillSwitchState,
    target: KillSwitchState,
) -> bool:
    """Validate if a state transition is allowed.

    Args:
        current: Current state
        target: Target state

    Returns:
        True if transition is valid

    Raises:
        StateTransitionError: If transition is invalid
    """
    VALID_TRANSITIONS = {
        KillSwitchState.ACTIVE: {KillSwitchState.KILLED},
        KillSwitchState.KILLED: {KillSwitchState.RECOVERING},
        KillSwitchState.RECOVERING: {KillSwitchState.ACTIVE, KillSwitchState.KILLED},
        KillSwitchState.DISABLED: set(),  # No transitions allowed
    }

    valid = VALID_TRANSITIONS.get(current, set())

    if target not in valid:
        raise StateTransitionError(current, target)

    return True
