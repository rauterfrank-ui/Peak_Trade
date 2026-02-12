"""Smoke tests for ingress orchestrator (A5): A2→A4 wiring, pointer-only outputs."""

from __future__ import annotations

from pathlib import Path

import json
import pytest

from src.ingress.normalized_event import NormalizedEvent
from src.ingress.io.jsonl_writer import JsonlEventWriter
from src.ingress.orchestrator import OrchestratorConfig, run_ingress


def test_run_ingress_empty_input(tmp_path: Path) -> None:
    """No input JSONL: still produces feature_view and capsule JSON (empty view)."""
    config = OrchestratorConfig(
        base_dir=tmp_path / "ops",
        run_id="run1",
        input_jsonl_path="",
    )
    fv_path, cap_path = run_ingress(config)
    assert fv_path.exists()
    assert cap_path.exists()
    fv_data = json.loads(fv_path.read_text(encoding="utf-8"))
    cap_data = json.loads(cap_path.read_text(encoding="utf-8"))
    assert "payload" not in fv_data
    assert "payload" not in cap_data
    assert fv_data.get("run_id") == "run1"
    assert cap_data.get("run_id") == "run1"


def test_run_ingress_with_events(tmp_path: Path) -> None:
    """With events JSONL: pipeline produces view + capsule; outputs remain pointer-only."""
    events_dir = tmp_path / "events"
    w = JsonlEventWriter(events_dir / "ev")
    w.append(
        [
            NormalizedEvent(
                "e1", 1000, "kraken.rest", "ohlcv", "market.BTC", [], "internal", {"x": 1}
            ),
        ]
    )
    jsonl_path = str(events_dir / "ev.jsonl")
    config = OrchestratorConfig(
        base_dir=tmp_path / "ops",
        run_id="run2",
        input_jsonl_path=jsonl_path,
    )
    fv_path, cap_path = run_ingress(config, labels={"process_score": 80})
    assert fv_path.exists()
    assert cap_path.exists()
    fv_data = json.loads(fv_path.read_text(encoding="utf-8"))
    cap_data = json.loads(cap_path.read_text(encoding="utf-8"))
    assert "payload" not in fv_data and "payload" not in cap_data
    assert fv_data.get("counts", {}).get("ohlcv") == 1
    assert cap_data.get("labels", {}).get("process_score") == 80
    assert len(cap_data.get("artifacts", [])) >= 1
