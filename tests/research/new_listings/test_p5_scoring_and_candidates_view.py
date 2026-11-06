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


def test_p5_scoring_and_candidates_view(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"collectors": ["manual_seed"]}), encoding="utf-8")

    _run("init", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("normalize", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("risk", "--config", str(cfg), "--db", str(db), "--events", str(events))
    payload = _run("score", "--config", str(cfg), "--db", str(db), "--events", str(events))

    assert payload["ok"] is True
    assert payload["score_rows"] >= 1

    con = sqlite3.connect(str(db))
    n_scores = con.execute("SELECT COUNT(*) FROM listing_scores").fetchone()[0]
    assert n_scores >= 1

    # candidates view should include seed asset (LOW risk, score >= 50)
    rows = con.execute(
        "SELECT asset_id, latest_score, latest_severity FROM v_assets_candidates"
    ).fetchall()
    assert len(rows) >= 1
