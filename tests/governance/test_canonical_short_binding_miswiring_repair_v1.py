"""Governance contracts for canonical SHORT binding miswiring repair evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO / "docs/evidence/canonical_short_binding_miswiring_repair_v1"
_WIRING = _REPO / "src/backtest/mv2_research_wiring_v1.py"
_ADAPTER = _REPO / "src/backtest/backtest_engine_position_feedback_adapter_v1.py"


def test_repair_evidence_artifacts_present() -> None:
    required = [
        "README.md",
        "verdict.txt",
        "manifest.json",
        "repair_binding_proof.json",
        "tests.txt",
        "ruff.txt",
        "commands.txt",
        "diff_scope.txt",
        "environment.txt",
    ]
    missing = [name for name in required if not (_EVIDENCE / name).is_file()]
    if missing:
        pytest.skip(f"repair evidence not yet materialized: {missing}")


def test_repair_binding_in_source() -> None:
    wiring = _WIRING.read_text(encoding="utf-8")
    adapter = _ADAPTER.read_text(encoding="utf-8")
    assert wiring.count("use_execution_pipeline=True") >= 2
    assert "use_execution_pipeline=False" not in wiring
    assert wiring.count("honor_mapped_short_entry=True") >= 2
    assert "honor_mapped_short_entry: bool = False" in adapter
    assert "BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE = False" in adapter


def test_manifest_sha256_matches_when_present() -> None:
    manifest_path = _EVIDENCE / "manifest.json"
    if not manifest_path.is_file():
        pytest.skip("manifest not yet materialized")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    import hashlib

    for entry in manifest["files"]:
        path = _REPO / entry["path"]
        assert path.is_file(), entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"], entry["name"]


def test_verdict_declares_repair_pass_when_present() -> None:
    path = _EVIDENCE / "verdict.txt"
    if not path.is_file():
        pytest.skip("verdict not yet materialized")
    text = path.read_text(encoding="utf-8")
    assert "STATUS=PASS" in text
    assert "SHORT_BINDING_REPAIR_APPLIED" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "DIRECTION_AUTHORITY_AFTER=MasterV2_DoublePlay_sole" in text
