"""Contract: EvidenceCapsule contains CMES facts; pointer-only scan passes (Runbook K3)."""

from __future__ import annotations

import pytest

from src.risk.cmes import CMES_FACT_KEYS
from src.ingress.capsules.evidence_capsule_builder import build_evidence_capsule


FORBIDDEN_KEYS = frozenset(
    {"payload", "raw", "transcript", "api_key", "secret", "token", "content"}
)


def _scan_dict_forbidden(d: dict, path: str = "") -> list[str]:
    hits = []
    for k, v in d.items():
        key_lower = k.lower()
        if any(f in key_lower for f in FORBIDDEN_KEYS):
            hits.append(f"{path}.{k}" if path else k)
        if isinstance(v, dict):
            hits.extend(_scan_dict_forbidden(v, f"{path}.{k}" if path else k))
    return hits


def test_capsule_without_fv_has_cmes_facts() -> None:
    cap = build_evidence_capsule("c1", "r1", 0, feature_view=None)
    out = cap.to_dict()
    facts = out.get("facts", {})
    for k in CMES_FACT_KEYS:
        assert k in facts, f"missing CMES fact {k}"


def test_capsule_pointer_only_scan() -> None:
    cap = build_evidence_capsule("c1", "r1", 0, feature_view=None)
    out = cap.to_dict()
    hits = _scan_dict_forbidden(out)
    assert not hits, f"forbidden keys in EvidenceCapsule: {hits}"


def test_capsule_with_fv_has_cmes_facts() -> None:
    from src.ingress.views.feature_view import FeatureView
    from src.risk.cmes import default_cmes_facts

    fv = FeatureView(run_id="r1", ts_ms=0, counts={}, facts=default_cmes_facts(), artifacts=[])
    cap = build_evidence_capsule("c1", "r1", 0, feature_view=fv)
    out = cap.to_dict()
    facts = out.get("facts", {})
    for k in CMES_FACT_KEYS:
        assert k in facts
