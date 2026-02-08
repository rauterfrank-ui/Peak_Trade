"""Tests for FeatureView writer (JSON + sha256 sidecar)."""

from __future__ import annotations

from pathlib import Path

import json

import pytest

from src.ingress.views.feature_view import ArtifactPointer, FeatureView
from src.ingress.io.feature_view_writer import write_feature_view


def test_write_produces_json_and_sha256(tmp_path: Path) -> None:
    view = FeatureView(
        run_id="r1",
        ts_ms=1000,
        counts={"ohlcv": 5},
        facts={"symbol": "BTC/EUR"},
        artifacts=[ArtifactPointer(path="/out/ops/events/ev.jsonl", sha256="a" * 64)],
    )
    base = tmp_path / "views" / "FEATURE_VIEW_r1_1000"
    json_path, digest = write_feature_view(view, base)
    assert json_path.exists()
    assert json_path.suffix == ".json"
    sha_path = json_path.with_suffix(".json.sha256")
    assert sha_path.exists()
    assert sha_path.read_text().strip() == digest
    assert len(digest) == 64
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["run_id"] == "r1"
    assert loaded["counts"]["ohlcv"] == 5
    assert "payload" not in loaded


def test_written_view_has_no_raw_fields(tmp_path: Path) -> None:
    view = FeatureView(
        run_id="r1",
        ts_ms=0,
        counts={},
        facts={"scope": "market.BTC"},
        artifacts=[],
    )
    json_path, _ = write_feature_view(view, tmp_path / "v")
    content = json_path.read_text()
    for forbidden in ("payload", "api_key", "secret", "transcript"):
        assert forbidden not in content
