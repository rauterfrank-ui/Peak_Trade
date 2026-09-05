"""Typed SideState restore for Cap-7.2 host restart.

Invalid persisted SideState fails closed. No silent enum swallow.
No implicit fallback to another SideState. Not FILEGATE. Not Double Play
transition_state. Cap 6.2 forbids silent reinitialization; Cap 7.2 host
must not continue alpha/decision compute on an unvalidated restore.
"""

from __future__ import annotations

from trading.master_v2.double_play_state import SideState

SIDESTATE_RESTORE_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    ".sidestate_restore_v1"
)
INVALID_PERSISTED_SIDESTATE = "INVALID_PERSISTED_SIDESTATE"


class SideStateRestoreError(ValueError):
    """Typed fail-closed restore error. Does not normalize the persisted value."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}")


def parse_persisted_side_state_v1(raw: object) -> SideState:
    """Validate a persisted SideState. Unknown/unparseable values fail closed.

    Missing/None is not silently defaulted at this seam. Persist-load missing
    defaulting (Cap 6.2 ``neutral_observe``) remains the persist-layer owner.
    """
    if isinstance(raw, SideState):
        return raw
    if raw is None:
        raise SideStateRestoreError(INVALID_PERSISTED_SIDESTATE, "persisted_sidestate_missing")
    if not isinstance(raw, str):
        raise SideStateRestoreError(
            INVALID_PERSISTED_SIDESTATE,
            f"persisted_sidestate_unparseable:{type(raw).__name__}",
        )
    value = raw.strip()
    if not value:
        raise SideStateRestoreError(INVALID_PERSISTED_SIDESTATE, "persisted_sidestate_empty")
    try:
        return SideState(value)
    except ValueError as exc:
        raise SideStateRestoreError(
            INVALID_PERSISTED_SIDESTATE,
            f"persisted_sidestate_unknown:{value}",
        ) from exc
