"""Fail-closed guard: standalone capability CLIs must not target Cap24 productivity root.

AUTHORITY_EFFECT=NONE. Does not change Cap-2.x owners or Cap24 canonical writer semantics.
"""

from __future__ import annotations

from pathlib import Path

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    default_current_productive_cap24_runtime_state_root_v1,
)

FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT = "RESERVED_CAP24_PRODUCTIVITY_ROOT_FORBIDDEN"


class ReservedCap24ProductivityRootError(RuntimeError):
    """Standalone capability CLI attempted to use the authoritative Cap24 carrier root."""

    def __init__(self, message: str = FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT) -> None:
        super().__init__(message)
        self.failure_code = FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT


def reserved_cap24_productivity_root_v1() -> Path:
    """Normalized reserved root for runtime/current_productive/cap24_selection_state."""

    return default_current_productive_cap24_runtime_state_root_v1().resolve()


def state_root_targets_reserved_cap24_productivity_root_v1(state_root: Path | str) -> bool:
    candidate = Path(state_root).expanduser().resolve()
    reserved = reserved_cap24_productivity_root_v1()
    if candidate == reserved:
        return True
    try:
        candidate.relative_to(reserved)
    except ValueError:
        return False
    return True


def assert_standalone_capability_state_root_not_reserved_cap24_v1(
    state_root: Path | str,
) -> None:
    """Reject --state-root values inside the canonical Cap24 productivity carrier."""

    if state_root_targets_reserved_cap24_productivity_root_v1(state_root):
        raise ReservedCap24ProductivityRootError(
            f"{FAILURE_RESERVED_CAP24_PRODUCTIVITY_ROOT}:state_root={Path(state_root)!s}"
        )
