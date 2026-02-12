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


def test_p3_normalize_persists_assets_and_snapshots(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"collectors": ["manual_seed"]}), encoding="utf-8")

    _run("init", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg), "--db", str(db), "--events", str(events))
    payload = _run("normalize", "--config", str(cfg), "--db", str(db), "--events", str(events))

    assert payload["ok"] is True
    assert payload["assets"] >= 1
    assert payload["snapshots"] >= 1

    con = sqlite3.connect(str(db))
    n_assets = con.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    n_snaps = con.execute("SELECT COUNT(*) FROM market_snapshots").fetchone()[0]
    assert n_assets >= 1
    assert n_snaps >= 1

    lines = events.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
