"""
EvidenceCapsule (Runbook A4): pointer-only bundle of artifacts.
No raw payload, transcript, or secrets in the model or serialization.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from src.experiments.cross_lane_identity_join_v1 import CrossLaneIdentityJoinV1
from src.ingress.capsules.i56_ingress_named_lane_identity_join_v1 import (
    join_i56_named_lane_identity_v1,
)


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
    - facts: CMES 7 facts (canonical, pointer-only); optional, default empty dict
    """

    capsule_id: str
    run_id: str
    ts_ms: int
    artifacts: List[ArtifactRef] = field(default_factory=list)
    labels: Dict[str, Any] = field(default_factory=dict)
    facts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "run_id": self.run_id,
            "ts_ms": self.ts_ms,
            "artifacts": [{"path": a.path, "sha256": a.sha256} for a in self.artifacts],
            "labels": dict(self.labels),
            "facts": dict(self.facts),
        }


@dataclass(frozen=True)
class EvidenceCapsuleNamedLaneIdentityJoinResultV1:
    contract: EvidenceCapsule
    join: CrossLaneIdentityJoinV1


@dataclass(frozen=True)
class ArtifactRefNamedLaneIdentityJoinResultV1:
    contract: ArtifactRef
    join: CrossLaneIdentityJoinV1


def parse_evidence_capsule_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> EvidenceCapsuleNamedLaneIdentityJoinResultV1:
    """Parse a live I56 capsule and fail-closed join Package-N IDENTITY sidecar."""
    snapshot = copy.deepcopy(dict(raw)) if isinstance(raw, Mapping) else None
    join = join_i56_named_lane_identity_v1(raw, surface="capsule", **sidecars)
    if not isinstance(raw, Mapping) or snapshot is None:
        raise ValueError("malformed plane data rejected: I56 capsule is not an object")
    artifacts_raw = raw.get("artifacts") or []
    if not isinstance(artifacts_raw, list):
        raise ValueError("malformed plane data rejected: I56 capsule artifacts is not a list")
    refs = [
        ArtifactRef(path=str(item["path"]), sha256=str(item["sha256"]))
        for item in artifacts_raw
        if isinstance(item, Mapping)
    ]
    capsule = EvidenceCapsule(
        capsule_id=str(raw["capsule_id"]),
        run_id=str(raw["run_id"]),
        ts_ms=int(raw["ts_ms"]),
        artifacts=refs,
        labels=dict(raw.get("labels") or {}),
        facts=dict(raw.get("facts") or {}),
    )
    if dict(raw) != snapshot:
        raise ValueError("I56 capsule input was mutated")
    return EvidenceCapsuleNamedLaneIdentityJoinResultV1(contract=capsule, join=join)


def parse_artifact_ref_with_identity_join_v1(
    raw: Mapping[str, Any],
    **sidecars: Any,
) -> ArtifactRefNamedLaneIdentityJoinResultV1:
    """Parse a live I56 artifact ref and fail-closed join Package-N IDENTITY sidecar."""
    snapshot = copy.deepcopy(dict(raw)) if isinstance(raw, Mapping) else None
    join = join_i56_named_lane_identity_v1(raw, surface="artifact", **sidecars)
    if not isinstance(raw, Mapping) or snapshot is None:
        raise ValueError("malformed plane data rejected: I56 artifact is not an object")
    artifact = ArtifactRef(path=str(raw["path"]), sha256=str(raw["sha256"]))
    if dict(raw) != snapshot:
        raise ValueError("I56 artifact input was mutated")
    return ArtifactRefNamedLaneIdentityJoinResultV1(contract=artifact, join=join)
