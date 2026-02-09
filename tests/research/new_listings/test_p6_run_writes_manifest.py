from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_p6_run_writes_manifest(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    out_dir = tmp_path / "out"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"collectors": ["manual_seed"]}), encoding="utf-8")

    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "src.research.new_listings",
            "run",
            "--config",
            str(cfg),
            "--out-dir",
            str(out_dir),
            "--db",
            str(db),
            "--events",
            str(events),
        ],
        text=True,
    ).strip()
    payload = json.loads(out)
    assert payload["ok"] is True
    mp = Path(payload["manifest_path"])
    assert mp.exists()
    m = json.loads(mp.read_text(encoding="utf-8"))
    assert m["ok"] is True
    assert "outputs" in m

    con = sqlite3.connect(str(db))
    n_assets = con.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    n_scores = con.execute("SELECT COUNT(*) FROM listing_scores").fetchone()[0]
    n_risk = con.execute("SELECT COUNT(*) FROM risk_flags").fetchone()[0]
    assert n_assets >= 1
    assert n_scores >= 1
    assert n_risk >= 1
