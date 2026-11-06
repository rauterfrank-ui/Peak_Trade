"""
Build EvidenceCapsule from FeatureView + optional labels (Runbook A4).
Output is pointer-only; no raw payload or transcript.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.ingress.capsules.evidence_capsule import ArtifactRef, EvidenceCapsule
from src.risk.cmes import CMES_FACT_KEYS, canonicalize_facts, default_cmes_facts


def build_evidence_capsule(
    capsule_id: str,
    run_id: str,
    ts_ms: int,
    feature_view: FeatureView | None = None,
    labels: Dict[str, Any] | None = None,
) -> EvidenceCapsule:
    """
    Build a pointer-only EvidenceCapsule.
    If feature_view is provided, its artifacts become capsule artifacts (path+sha256 only)
    and CMES facts are extracted (canonical) into capsule.facts.
    labels: optional numeric/flags (e.g. process_score, critic_flags count); no raw text.
    """
    artifacts: List[ArtifactRef] = []
    facts: Dict[str, Any] = {}
    if feature_view:
        for ap in feature_view.artifacts:
            artifacts.append(ArtifactRef(path=ap.path, sha256=ap.sha256))
        # CMES facts from feature view (canonical); merge defaults with any fv CMES keys
        fv_facts = feature_view.facts or {}
        cmes_raw = dict(default_cmes_facts())
        for k in CMES_FACT_KEYS:
            if k in fv_facts:
                cmes_raw[k] = fv_facts[k]
        facts = canonicalize_facts(cmes_raw)
    else:
        facts = default_cmes_facts()
    return EvidenceCapsule(
        capsule_id=capsule_id,
        run_id=run_id,
        ts_ms=ts_ms,
        artifacts=artifacts,
        labels=dict(labels) if labels else {},
        facts=facts,
    )
