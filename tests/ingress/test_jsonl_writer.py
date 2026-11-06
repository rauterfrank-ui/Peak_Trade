from __future__ import annotations

from pathlib import Path
import json

from src.ingress.normalized_event import NormalizedEvent
from src.ingress.io.jsonl_writer import JsonlEventWriter


def test_normalized_event_json_line_is_deterministic():
    ev = NormalizedEvent(
        event_id="e1",
        ts_ms=1700000000000,
        source="unit",
        kind="trade",
        scope="market.BTCUSDT",
        tags=["shadow"],
        sensitivity="internal",
        payload={"b": 2, "a": 1},
    )
    line1 = ev.to_json_line()
    line2 = ev.to_json_line()
    assert line1 == line2
    assert line1.endswith("\n")
    obj = json.loads(line1)
    assert obj["payload"] == {"a": 1, "b": 2}


def test_jsonl_writer_chain_and_resume(tmp_path: Path):
    base = tmp_path / "events" / "stream"
    w = JsonlEventWriter(base)

    evs1 = [
        NormalizedEvent("e1", 1, "s", "k", "sc", ["t"], "internal", {"x": 1}),
        NormalizedEvent("e2", 2, "s", "k", "sc", ["t"], "internal", {"x": 2}),
    ]
    r1 = w.append(evs1)
    assert r1.records_written == 2
    assert r1.path_jsonl.exists()
    assert r1.path_manifest.exists()

    m1 = json.loads(r1.path_manifest.read_text(encoding="utf-8"))
    assert m1["records"] == 2
    head1 = m1["chain_head"]

    # resume + append
    evs2 = [NormalizedEvent("e3", 3, "s", "k", "sc", ["t"], "internal", {"x": 3})]
    r2 = w.append(evs2)

    m2 = json.loads(r2.path_manifest.read_text(encoding="utf-8"))
    assert m2["records"] == 3
    assert m2["chain_head"] != head1
    assert len(m2["chain"]) == 3


def test_validation_rejects_bad_sensitivity(tmp_path: Path):
    base = tmp_path / "events" / "stream"
    w = JsonlEventWriter(base)
    bad = NormalizedEvent("e1", 1, "s", "k", "sc", ["t"], "SECRET", {"x": 1})
    try:
        w.append([bad])
        assert False, "expected ValueError"
    except ValueError as e:
        assert "sensitivity" in str(e)


def test_dumps_disallows_nan():
    ev = NormalizedEvent("e1", 1, "s", "k", "sc", ["t"], "internal", {"x": float("nan")})
    try:
        ev.to_json_line()
        assert False, "expected ValueError due to allow_nan=False"
    except ValueError:
        pass
