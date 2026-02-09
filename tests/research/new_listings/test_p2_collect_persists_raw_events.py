from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_p2_collect_persists_raw_events(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"collectors": ["manual_seed"]}), encoding="utf-8")

    # init schema first
    subprocess.check_output(
        [
            sys.executable,
            "-m",
            "src.research.new_listings",
            "init",
            "--config",
            str(cfg),
            "--db",
            str(db),
            "--events",
            str(events),
        ],
        text=True,
    )

    # then collect
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "src.research.new_listings",
            "collect",
            "--config",
            str(cfg),
            "--db",
            str(db),
            "--events",
            str(events),
        ],
        text=True,
    ).strip()
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["raw_events"] == 1

    con = sqlite3.connect(str(db))
    n = con.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
    # init already inserts 1 seed raw_event; collect adds 1 more
    assert n == 2

    lines = events.read_text(encoding="utf-8").strip().splitlines()
    # init writes 1 event; collect appends 1 event
    assert len(lines) == 2
    e2 = json.loads(lines[-1])
    assert e2["type"] == "raw_event.ingested"
