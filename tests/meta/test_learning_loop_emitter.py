"""Tests für ``src.meta.learning_loop.emitter`` (deterministisch, atomar)."""

from __future__ import annotations

import json
from pathlib import Path

from src.meta.learning_loop.emitter import emit_learning_snippet


def test_emit_learning_snippet_json_deterministic_bytes(tmp_path: Path) -> None:
    payload = {"target": "portfolio.leverage", "new_value": 1.5, "reason": "test"}
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    emit_learning_snippet(payload, out_path=p1)
    emit_learning_snippet(payload, out_path=p2)
    assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")
    data = json.loads(p1.read_text(encoding="utf-8"))
    assert data["target"] == "portfolio.leverage"
    assert data["new_value"] == 1.5


def test_emit_learning_snippet_jsonl_idempotent_same_payload(tmp_path: Path) -> None:
    patches = [
        {"target": "a.b", "new_value": 1},
        {"target": "c.d", "new_value": 2},
    ]
    out = tmp_path / "snippets.jsonl"
    emit_learning_snippet(patches, out_path=out, fmt="jsonl")
    first = out.read_text(encoding="utf-8")
    emit_learning_snippet(patches, out_path=out, fmt="jsonl")
    second = out.read_text(encoding="utf-8")
    assert first == second
    lines = [json.loads(line) for line in first.strip().split("\n")]
    assert len(lines) == 2
    assert lines[0]["target"] == "a.b"
