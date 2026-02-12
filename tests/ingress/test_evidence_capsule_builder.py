"""Tests for EvidenceCapsule builder (no raw in output)."""

from __future__ import annotations

import pytest

from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.ingress.capsules.evidence_capsule_builder import build_evidence_capsule


def test_build_minimal() -> None:
    c = build_evidence_capsule("cap1", "run1", 1000)
    assert c.capsule_id == "cap1"
    assert c.run_id == "run1"
    assert c.ts_ms == 1000
    assert c.artifacts == []
    assert c.labels == {}


def test_build_from_feature_view_no_raw() -> None:
    fv = FeatureView(
        run_id="r1",
        ts_ms=2000,
        counts={"k": 1},
        facts={"scope": "market.BTC"},
        artifacts=[ArtifactPointer(path="/ops/events/ev.jsonl", sha256="a" * 64)],
    )
    c = build_evidence_capsule("cap2", "r1", 2000, feature_view=fv, labels={"process_score": 85})
    out = c.to_dict()
    assert "payload" not in out
    assert "raw" not in str(out.get("labels", {}))
    assert len(out["artifacts"]) == 1
    assert out["artifacts"][0]["sha256"] == "a" * 64
    assert out["labels"].get("process_score") == 85
