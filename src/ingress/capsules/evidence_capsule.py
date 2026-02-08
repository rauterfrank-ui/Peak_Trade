"""
EvidenceCapsule (Runbook A4): pointer-only bundle of artifacts.
No raw payload, transcript, or secrets in the model or serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ArtifactRef:
    """Reference to an artifact; path + sha256 only."""

    path: str
    sha256: str


@dataclass
class EvidenceCapsule:
    """
    Pointer-only bundle for learning/audit.
    - capsule_id: stable id
    - run_id, ts_ms: scope
    - artifacts: list of path+sha256 (no raw content)
    - labels: optional numeric/flag summary (e.g. process_score 0-100, critic_flags count); no raw text
    """

    capsule_id: str
    run_id: str
    ts_ms: int
    artifacts: List[ArtifactRef] = field(default_factory=list)
    labels: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "run_id": self.run_id,
            "ts_ms": self.ts_ms,
            "artifacts": [{"path": a.path, "sha256": a.sha256} for a in self.artifacts],
            "labels": dict(self.labels),
        }
