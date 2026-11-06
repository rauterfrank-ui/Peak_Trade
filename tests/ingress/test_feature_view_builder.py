"""Tests for FeatureView builder (no raw payload in output)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ingress.normalized_event import NormalizedEvent
from src.ingress.io.jsonl_writer import JsonlEventWriter
from src.ingress.views.feature_view import FeatureView
from src.ingress.views.feature_view_builder import build_feature_view_from_jsonl


def test_build_from_empty_path(tmp_path: Path) -> None:
    p = tmp_path / "nonexistent.jsonl"
    v = build_feature_view_from_jsonl(str(p), run_id="r1")
    assert v.run_id == "r1"
    assert v.ts_ms == 0
    assert v.counts == {}
    assert v.artifacts == []


def test_build_from_jsonl_no_raw_in_view(tmp_path: Path) -> None:
    """FeatureView must not contain payload, raw, transcript, api_key, secret, token."""
    base = tmp_path / "events"
    w = JsonlEventWriter(base / "ev")
    evs = [
        NormalizedEvent(
            "e1",
            1000,
            "kraken.rest",
            "ohlcv",
            "market.BTC/EUR",
            ["live"],
            "internal",
            {"raw": "never", "api_key": "x", "close": 42},
        ),
    ]
    w.append(evs)
    jsonl_path = base / "ev.jsonl"
    v = build_feature_view_from_jsonl(str(jsonl_path), run_id="r1")
    out = v.to_dict()
    # Must not leak payload: no payload key, no payload keys/values in facts
    assert "payload" not in out
    facts = out.get("facts", {})
    assert "api_key" not in facts
    assert "raw" not in facts
    assert "never" not in (facts or {}).values()
    # Must have counts/facts/pointers
    assert out["counts"].get("ohlcv") == 1
    assert "artifacts" in out
    assert len(out["artifacts"]) == 1
    assert "sha256" in out["artifacts"][0]


def test_build_deterministic(tmp_path: Path) -> None:
    base = tmp_path / "events"
    w = JsonlEventWriter(base / "ev")
    w.append(
        [
            NormalizedEvent("e1", 1, "s", "k1", "sc", [], "internal", {}),
            NormalizedEvent("e2", 2, "s", "k1", "sc", [], "internal", {}),
        ]
    )
    v1 = build_feature_view_from_jsonl(str(base / "ev.jsonl"), run_id="r1")
    v2 = build_feature_view_from_jsonl(str(base / "ev.jsonl"), run_id="r1")
    assert v1.counts == v2.counts
    assert v1.facts["event_count_total"] == 2
    assert v1.counts.get("k1") == 2
