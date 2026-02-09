from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class CollectorContext:
    run_id: str
    config_hash: str


@dataclass(frozen=True)
class RawEvent:
    source: str
    venue_type: str
    observed_at: str  # ISO8601 Z
    payload: Mapping[str, Any]


class Collector(Protocol):
    name: str

    def collect(self, ctx: CollectorContext) -> Sequence[RawEvent]:
        """Offline-first: in P1 this may only emit synthetic or file-based events."""
        raise NotImplementedError
