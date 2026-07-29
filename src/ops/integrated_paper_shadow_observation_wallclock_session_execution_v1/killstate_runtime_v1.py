"""Kill-state triggers and classification for wallclock observation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TerminalVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ABORT = "ABORT"


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
    "FORBIDDEN_ENDPOINT",
    "AUTH_HEADER_DETECTED",
    "ORDER_SURFACE_REACHED",
    "SCOPE_MISMATCH",
    "SHA_MISMATCH",
    "LOCK_LOSS",
    "IMPORT_GUARD_BREACH",
    "EVIDENCE_TAMPER",
    "HEARTBEAT_LOSS",
    "ABORT_AFTER_CONSUMPTION",
    "ABORT_CREDENTIAL_OR_AUTH_SURFACE",
    "ABORT_DUPLICATE_SESSION",
    "RECONNECT_BUDGET_EXCEEDED",
    "HTTP_429_BUDGET_EXCEEDED",
    "OPERATOR_ABORT",
    "REVOKED",
)


SAFETY_ABORT_TRIGGERS = frozenset(KILLSTATE_TRIGGERS)


@dataclass
class KillstateEventV1:
    trigger: str
    detail: str
    mono_ts: float
    wall_ts: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KillstateRuntimeV1:
    events: list[KillstateEventV1] = field(default_factory=list)
    active: bool = False
    last_trigger: str = ""

    def raise_killstate(
        self,
        *,
        trigger: str,
        detail: str = "",
        mono_ts: float = 0.0,
        wall_ts: float = 0.0,
    ) -> None:
        if trigger not in SAFETY_ABORT_TRIGGERS and trigger not in KILLSTATE_TRIGGERS:
            trigger = "INVARIANT_VIOLATION"
        self.active = True
        self.last_trigger = trigger
        self.events.append(
            KillstateEventV1(
                trigger=trigger,
                detail=detail,
                mono_ts=mono_ts,
                wall_ts=wall_ts,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "last_trigger": self.last_trigger,
            "events": [e.to_dict() for e in self.events],
        }


def classify_terminal_verdict(
    *,
    killstate_active: bool,
    quality_fail: bool,
    incomplete: bool,
    aborted: bool,
) -> TerminalVerdict:
    """Safety/authority/incomplete always ABORT; never remap to FAIL."""
    if killstate_active or aborted or incomplete:
        return TerminalVerdict.ABORT
    if quality_fail:
        return TerminalVerdict.FAIL
    return TerminalVerdict.PASS
