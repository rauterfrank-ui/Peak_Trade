"""
Build EvidenceCapsule from FeatureView + optional labels (Runbook A4).
Output is pointer-only; no raw payload or transcript.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.ingress.capsules.evidence_capsule import ArtifactRef, EvidenceCapsule


def build_evidence_capsule(
    capsule_id: str,
    run_id: str,
    ts_ms: int,
    feature_view: FeatureView | None = None,
    labels: Dict[str, Any] | None = None,
) -> EvidenceCapsule:
    """
    Build a pointer-only EvidenceCapsule.
    If feature_view is provided, its artifacts become capsule artifacts (path+sha256 only).
    labels: optional numeric/flags (e.g. process_score, critic_flags count); no raw text.
    """
    artifacts: List[ArtifactRef] = []
    if feature_view:
        for ap in feature_view.artifacts:
            artifacts.append(ArtifactRef(path=ap.path, sha256=ap.sha256))
    return EvidenceCapsule(
        capsule_id=capsule_id,
        run_id=run_id,
        ts_ms=ts_ms,
        artifacts=artifacts,
        labels=dict(labels) if labels else {},
    )
