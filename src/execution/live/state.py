"""
State model for C2 live-session dryrun orchestration.

Minimal, deterministic, serialization-stable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class SessionStatus(str, Enum):
    INIT = "INIT"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class SessionStateSnapshot:
    run_id: str
    strategy_id: str
    status: SessionStatus
    ts_sim: int
    started_ts: Optional[str] = None
    ended_ts: Optional[str] = None
    step: int = 0
    events_emitted: int = 0
    sink_retries: int = 0
    reject_code: Optional[str] = None
    reject_reason: Optional[str] = None
    fail_code: Optional[str] = None
    fail_reason: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "status": self.status.value,
            "ts_sim": self.ts_sim,
            "started_ts": self.started_ts,
            "ended_ts": self.ended_ts,
            "step": self.step,
            "events_emitted": self.events_emitted,
            "sink_retries": self.sink_retries,
            "reject_code": self.reject_code,
            "reject_reason": self.reject_reason,
            "fail_code": self.fail_code,
            "fail_reason": self.fail_reason,
            "meta": dict(self.meta),
        }


def snapshot_json(snapshot: Mapping[str, Any]) -> str:
    return json.dumps(dict(snapshot), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
