from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import sqlite3



def test_p0_init_creates_db_and_events(tmp_path: Path, monkeypatch):
    # run CLI in isolated tmp
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"scope": "research", "phase": "P0", "sources": []}), encoding="utf-8")

    # call as module path (python -m ...)
    cmd = [
        sys.executable,
        "-m",
        "src.research.new_listings.cli",
        "init",
        "--config",
        str(cfg),
        "--db",
        str(db),
        "--events",
        str(events),
    ]
    # Run from repo root so "src" is importable; use absolute paths for outputs in tmp_path
    out = subprocess.check_output(cmd, text=True).strip()
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["run_id"].startswith("nl_")
    assert len(payload["config_hash"]) == 64

    assert db.exists()
    assert events.exists()
    lines = events.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    e = json.loads(lines[0])
    assert e["type"] == "asset.discovered"
    assert e["asset_id"] == "seed:asset"

    con = sqlite3.connect(str(db))
    cur = con.execute("SELECT COUNT(*) FROM raw_events")
    assert cur.fetchone()[0] == 1
    cur = con.execute("SELECT COUNT(*) FROM assets")
    assert cur.fetchone()[0] == 1
