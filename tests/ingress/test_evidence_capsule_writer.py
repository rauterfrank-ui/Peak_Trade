"""Tests for EvidenceCapsule writer (JSON + sha256, no raw)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ingress.capsules.evidence_capsule import ArtifactRef, EvidenceCapsule
from src.ingress.io.evidence_capsule_writer import write_evidence_capsule


def test_write_produces_json_and_sha256(tmp_path: Path) -> None:
    cap = EvidenceCapsule(
        capsule_id="c1",
        run_id="r1",
        ts_ms=1000,
        artifacts=[ArtifactRef(path="/out/ev.jsonl", sha256="b" * 64)],
        labels={"process_score": 90},
    )
    p = tmp_path / "capsules" / "CAP_c1.json"
    json_path, digest = write_evidence_capsule(cap, p)
    assert json_path.exists()
    assert len(digest) == 64
    sha_path = json_path.with_suffix(".json.sha256")
    # Sidecar format: "<hex>  <relative_filename>" (shasum -c compatible)
    assert sha_path.read_text().strip() == f"{digest}  {json_path.name}"
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["capsule_id"] == "c1"
    assert "payload" not in loaded


def test_written_capsule_no_raw_fields(tmp_path: Path) -> None:
    cap = EvidenceCapsule("c1", "r1", 0, artifacts=[], labels={})
    json_path, _ = write_evidence_capsule(cap, tmp_path / "cap.json")
    content = json_path.read_text()
    for forbidden in ("payload", "api_key", "secret", "transcript"):
        assert forbidden not in content
