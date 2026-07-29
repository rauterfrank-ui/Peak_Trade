"""Heartbeat and staleness trackers (fake-clock friendly)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional


@dataclass
class HeartbeatTrackerV1:
    interval_seconds: float = 5.0
    loss_seconds: float = 15.0
    last_beat_mono: float = 0.0
    beat_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def beat(self, *, mono_ts: float, wall_ts: float) -> None:
        self.last_beat_mono = mono_ts
        self.beat_count += 1
        self.events.append({"mono_ts": mono_ts, "wall_ts": wall_ts, "n": self.beat_count})

    def check_loss(self, *, mono_ts: float) -> Optional[str]:
        if self.beat_count == 0:
            return None
        if mono_ts - self.last_beat_mono > self.loss_seconds:
            return "HEARTBEAT_LOSS"
        return None

    def due(self, *, mono_ts: float) -> bool:
        if self.beat_count == 0:
            return True
        return (mono_ts - self.last_beat_mono) >= self.interval_seconds


@dataclass
class StalenessTrackerV1:
    max_stale_seconds: float = 5.0
    consecutive_stale_budget: int = 3
    consecutive_stale: int = 0
    soft_warnings: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def observe(
        self,
        *,
        receive_ts: float,
        wall_now: float,
        mono_ts: float,
    ) -> tuple[str, Optional[str]]:
        """Return (status, kill_trigger_or_none). status in ok|warn|kill."""
        stale = wall_now - receive_ts
        if stale <= self.max_stale_seconds:
            self.consecutive_stale = 0
            return "ok", None
        self.consecutive_stale += 1
        self.soft_warnings += 1
        self.events.append(
            {
                "kind": "stale",
                "stale_seconds": stale,
                "consecutive": self.consecutive_stale,
                "mono_ts": mono_ts,
                "wall_ts": wall_now,
            }
        )
        if self.consecutive_stale > self.consecutive_stale_budget:
            return "kill", "STALE_DATA"
        return "warn", None
