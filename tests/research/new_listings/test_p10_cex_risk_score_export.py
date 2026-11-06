from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _run(*args: str) -> dict:
    out = subprocess.check_output(
        [sys.executable, "-m", "src.research.new_listings", *args], text=True
    ).strip()
    return json.loads(out)


def test_p10_cex_risk_score_export(tmp_path: Path) -> None:
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    out_dir = tmp_path / "out"
    cfg = tmp_path / "cfg.json"
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)

    (replay_dir / "tickers.json").write_text(
        json.dumps(
            [
                {
                    "source": "ccxt_ticker:kraken",
                    "venue_type": "ccxt_ticker",
                    "observed_at": "2026-02-09T00:00:00Z",
                    "payload": {
                        "exchange": "kraken",
                        "symbol": "BTC/USD",
                        "last": 100.0,
                        "bid": 99.0,
                        "ask": 101.0,
                        "quoteVolume": 10_000.0,
                    },
                },
                {
                    "source": "ccxt_ticker:kraken",
                    "venue_type": "ccxt_ticker",
                    "observed_at": "2026-02-09T00:00:01Z",
                    "payload": {
                        "exchange": "kraken",
                        "symbol": "ETH/USD",
                        "last": 10.0,
                        "bid": 9.9,
                        "ask": 10.5,
                        "quoteVolume": 1.0,
                    },
                },
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    cfg.write_text(
        json.dumps(
            {
                "collectors": ["replay"],
                "sources": {
                    "replay": {"enabled": True, "dir": str(replay_dir)},
                    "ccxt": {"enabled": False},
                    "ccxt_risk": {"min_quote_volume": 5.0, "max_spread_pct": 10.0},
                    "ccxt_score": {"volume_bonus_k": 0.001, "spread_penalty_max": 20.0},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    run_result = _run(
        "run",
        "--config",
        str(cfg),
        "--out-dir",
        str(out_dir),
        "--db",
        str(db),
        "--events",
        str(events),
    )
    run_id = run_result["run_id"]

    _run("risk", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("score", "--config", str(cfg), "--db", str(db), "--events", str(events))

    exp = _run(
        "export",
        "--db",
        str(db),
        "--out-dir",
        str(out_dir),
        "--run-id",
        run_id,
    )
    assert exp["ok"] is True
    assert exp["rows"] >= 1
    assert Path(exp["json_path"]).exists()
    assert Path(exp["csv_path"]).exists()

    data = json.loads(Path(exp["json_path"]).read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 1

    con = sqlite3.connect(str(db))
    n = con.execute("SELECT COUNT(*) FROM listing_scores").fetchone()[0]
    assert n >= 2
