"""
FeatureView (Runbook A3): compact summary for routing/layers.
Only path+sha256 pointers; no raw payload, transcript, or secrets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ArtifactPointer:
    """Reference to an artifact on disk; no raw content."""

    path: str
    sha256: str


@dataclass
class FeatureView:
    """
    Compact, deterministic view for layer routing.
    - run_id, ts_ms: scope
    - counts: event counts by kind (e.g. {"ohlcv": 10, "order_result": 2})
    - facts: key-value facts (symbol, timeframe, run_id, etc.); no raw payload
    - artifacts: list of path+sha256 only
    """

    run_id: str
    ts_ms: int
    counts: Dict[str, int] = field(default_factory=dict)
    facts: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[ArtifactPointer] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ts_ms": self.ts_ms,
            "counts": dict(self.counts),
            "facts": dict(self.facts),
            "artifacts": [{"path": a.path, "sha256": a.sha256} for a in self.artifacts],
        }
