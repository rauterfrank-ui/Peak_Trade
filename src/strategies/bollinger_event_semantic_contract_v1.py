"""OBL_B07 Bollinger EVENT_ONLY semantic contract v1.

Ratifies Bollinger raw signals as direction-neutral entry/exit events only.

Canonical mapping (Operator-GO OPTION_EVENT_ONLY):
  +1 → ENTRY_EVENT
  -1 → EXIT_EVENT
  0  → FLAT_NO_EVENT
  missing/invalid → UNKNOWN_FAIL_CLOSED

Does NOT authorize:
  - LONG_ONLY / SHORT_ENTRY / symmetric short geometry
  - Classic-engine LONG reinterpretation as Strategy Intent
  - generic sign→direction heuristics
  - entry_side emission (always NONE)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

BOLLINGER_EVENT_SEMANTIC_CONTRACT_OWNER = "strategies.bollinger_event_semantic_contract_v1"
BOLLINGER_EVENT_SEMANTIC_CONTRACT_VERSION = "v1"
BOLLINGER_STRATEGY_ID = "bollinger_bands"

BollingerDirectionV1 = Literal["NONE"]
BollingerEntrySideV1 = Literal["NONE"]


class BollingerSignalEventV1(str, Enum):
    ENTRY_EVENT = "ENTRY_EVENT"
    EXIT_EVENT = "EXIT_EVENT"
    FLAT_NO_EVENT = "FLAT_NO_EVENT"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


@dataclass(frozen=True)
class BollingerEventSemanticResultV1:
    """Bollinger-scoped event classification; direction and entry_side stay NONE."""

    event: BollingerSignalEventV1
    direction: BollingerDirectionV1 = "NONE"
    entry_side: BollingerEntrySideV1 = "NONE"
    raw_signal: Optional[int] = None

    def __post_init__(self) -> None:
        if self.direction != "NONE":
            raise ValueError("bollinger_direction_must_be_none")
        if self.entry_side != "NONE":
            raise ValueError("bollinger_entry_side_must_be_none")


def classify_bollinger_raw_signal_event_v1(raw: Any) -> BollingerSignalEventV1:
    """Classify a Bollinger raw cycle signal into an EVENT_ONLY semantic.

    Fail-closed for missing/NaN/bool/non-integral/unsupported values.
    Never maps polarity to LONG/SHORT.
    """
    if raw is None:
        return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
    if isinstance(raw, bool):
        return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
    if isinstance(raw, float):
        if not math.isfinite(raw) or not float(raw).is_integer():
            return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
        value = int(raw)
    elif isinstance(raw, int):
        value = raw
    else:
        try:
            # Reject opaque objects; allow numeric strings only if exact int.
            as_float = float(raw)
        except (TypeError, ValueError):
            return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
        if not math.isfinite(as_float) or not as_float.is_integer():
            return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
        value = int(as_float)

    if value == 1:
        return BollingerSignalEventV1.ENTRY_EVENT
    if value == -1:
        return BollingerSignalEventV1.EXIT_EVENT
    if value == 0:
        return BollingerSignalEventV1.FLAT_NO_EVENT
    return BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED


def resolve_bollinger_event_semantic_v1(raw: Any) -> BollingerEventSemanticResultV1:
    """Full EVENT_ONLY result: event + forced NONE direction/entry_side."""
    event = classify_bollinger_raw_signal_event_v1(raw)
    raw_int: Optional[int]
    if event is BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED:
        raw_int = None
    else:
        raw_int = int(raw)
    return BollingerEventSemanticResultV1(
        event=event,
        direction="NONE",
        entry_side="NONE",
        raw_signal=raw_int,
    )


__all__ = [
    "BOLLINGER_EVENT_SEMANTIC_CONTRACT_OWNER",
    "BOLLINGER_EVENT_SEMANTIC_CONTRACT_VERSION",
    "BOLLINGER_STRATEGY_ID",
    "BollingerDirectionV1",
    "BollingerEntrySideV1",
    "BollingerEventSemanticResultV1",
    "BollingerSignalEventV1",
    "classify_bollinger_raw_signal_event_v1",
    "resolve_bollinger_event_semantic_v1",
]
