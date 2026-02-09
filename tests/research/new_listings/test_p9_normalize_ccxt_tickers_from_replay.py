from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import subprocess
import sys


def _run(*args: str) -> dict:
    out = subprocess.check_output(
        [sys.executable, "-m", "src.research.new_listings", *args], text=True
    ).strip()
    return json.loads(out)


def test_p9_normalize_ccxt_tickers_from_replay(tmp_path: Path):
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg = tmp_path / "cfg.json"
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)

    # two ticker payloads (ccxt-style)
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
                        "quoteVolume": 1234.0,
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
                        "quoteVolume": 234.0,
                    },
                },
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # config: replay collector only (offline)
    cfg.write_text(
        json.dumps(
            {
                "collectors": ["replay"],
                "sources": {
                    "replay": {"enabled": True, "dir": str(replay_dir)},
                    "ccxt": {"enabled": False},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    _run("init", "--config", str(cfg), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg), "--db", str(db), "--events", str(events))
    payload = _run("normalize", "--config", str(cfg), "--db", str(db), "--events", str(events))
    assert payload["ok"] is True
    assert payload["assets"] >= 2
    assert payload["snapshots"] >= 2

    con = sqlite3.connect(str(db))
    # expect canonical cex assets
    assets = {r[0] for r in con.execute("SELECT asset_id FROM assets").fetchall()}
    assert "cex:kraken:BTC" in assets
    assert "cex:kraken:ETH" in assets

    # snapshots should carry price for ccxt-derived assets
    rows = con.execute(
        "SELECT asset_id, price FROM market_snapshots WHERE asset_id IN ('cex:kraken:BTC','cex:kraken:ETH')"
    ).fetchall()
    assert len(rows) >= 2
    assert any(r[0] == "cex:kraken:BTC" and isinstance(r[1], (int, float)) for r in rows)
    assert any(r[0] == "cex:kraken:ETH" and isinstance(r[1], (int, float)) for r in rows)
