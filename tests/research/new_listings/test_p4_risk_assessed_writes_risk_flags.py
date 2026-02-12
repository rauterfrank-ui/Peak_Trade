from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> dict:
    out = subprocess.check_output(
        [sys.executable, "-m", "src.research.new_listings", *args],
        text=True,
    ).strip()
    return json.loads(out)


def test_p4_risk_assessed_writes_risk_flags(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"collectors": ["manual_seed"]}), encoding="utf-8")

    _run("init", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("normalize", "--config", str(cfg), "--db", str(db), "--events", str(events))
    payload = _run("risk", "--config", str(cfg), "--db", str(db), "--events", str(events))

    assert payload["ok"] is True
    assert payload["risk_rows"] >= 1

    con = sqlite3.connect(str(db))
    n = con.execute("SELECT COUNT(*) FROM risk_flags").fetchone()[0]
    assert n >= 1

    lines = events.read_text(encoding="utf-8").strip().splitlines()
    assert any(json.loads(x).get("type") == "risk.assessed" for x in lines)
