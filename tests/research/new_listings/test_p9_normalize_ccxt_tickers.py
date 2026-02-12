# tests/research/new_listings/test_p9_normalize_ccxt_tickers.py
"""
P9: Normalize CCXT tickers – raw_events (ccxt_ticker/replay) -> canonical assets + market_snapshots.
Regression tests using replay fixture / tmp fixtures (offline).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _run(*args: str, cwd: Path | None = None) -> dict:
    out = subprocess.check_output(
        [sys.executable, "-m", "src.research.new_listings", *args],
        text=True,
        cwd=cwd,
    ).strip()
    return json.loads(out)


def test_p9_normalize_ccxt_from_replay_fixture(tmp_path: Path) -> None:
    """Replay fixture with ccxt-shaped payload -> assets + market_snapshots with price/volume_24h_usd (offline)."""
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg_path = tmp_path / "cfg.json"
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)

    # Replay fixture: one ccxt-style event (BTC/EUR, price 1.0; no USD volume)
    fixture = replay_dir / "ccxt_fixture.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "source": "replay",
                    "venue_type": "ccxt",
                    "observed_at": "2026-02-09T12:00:00Z",
                    "payload": {
                        "exchange": "kraken",
                        "symbol": "BTC/EUR",
                        "observed_at": "2026-02-09T12:00:00Z",
                        "ticker": {"last": 1.0, "bid": 0.99, "ask": 1.01, "volume": 100.0},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    cfg = {
        "collectors": ["replay"],
        "sources": {"replay": {"dir": str(replay_dir), "enabled": True}},
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    _run("init", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    result = _run("normalize", "--config", str(cfg_path), "--db", str(db), "--events", str(events))

    assert result["ok"] is True
    assert result["assets"] >= 1
    assert result["snapshots"] >= 1

    con = sqlite3.connect(str(db))
    row = con.execute(
        "SELECT asset_id, symbol, chain FROM assets WHERE asset_id LIKE 'cex:%'"
    ).fetchone()
    assert row is not None
    asset_id, symbol, chain = row
    assert asset_id == "cex:kraken:BTC"
    assert symbol == "BTC/EUR"
    assert chain == "cex"

    snap = con.execute(
        "SELECT asset_id, price, volume_24h_usd FROM market_snapshots WHERE asset_id = ?",
        (asset_id,),
    ).fetchone()
    assert snap is not None
    assert snap[1] == 1.0  # price from ticker.last
    # volume_24h_usd not in USD quote so remains None
    assert snap[2] is None

    con.close()


def test_p9_normalize_ccxt_snapshot_volume_usd(tmp_path: Path) -> None:
    """CCXT ticker with USDT quote -> volume_24h_usd populated (best-effort)."""
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg_path = tmp_path / "cfg.json"
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir(parents=True, exist_ok=True)

    fixture = replay_dir / "ccxt_usdt.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "source": "ccxt_ticker",
                    "venue_type": "ccxt",
                    "observed_at": "2026-02-09T13:00:00Z",
                    "payload": {
                        "exchange": "binance",
                        "symbol": "ETH/USDT",
                        "observed_at": "2026-02-09T13:00:00Z",
                        "ticker": {"last": 3000.0, "volume": 10.0},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    cfg = {
        "collectors": ["replay"],
        "sources": {"replay": {"dir": str(replay_dir), "enabled": True}},
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    _run("init", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    _run("normalize", "--config", str(cfg_path), "--db", str(db), "--events", str(events))

    con = sqlite3.connect(str(db))
    row = con.execute(
        "SELECT asset_id, symbol FROM assets WHERE asset_id = 'cex:binance:ETH'"
    ).fetchone()
    assert row is not None

    snap = con.execute(
        "SELECT price, volume_24h_usd FROM market_snapshots WHERE asset_id = 'cex:binance:ETH'"
    ).fetchone()
    assert snap is not None
    assert snap[0] == 3000.0
    assert snap[1] == 30000.0  # 10 * 3000

    con.close()


def test_p9_normalize_seed_unchanged(tmp_path: Path) -> None:
    """Seed normalization still works; seed events get null price/volume in snapshots."""
    db = tmp_path / "nl.sqlite"
    events = tmp_path / "events.jsonl"
    cfg_path = tmp_path / "cfg.json"
    cfg = {"collectors": ["manual_seed"]}
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    _run("init", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    _run("collect", "--config", str(cfg_path), "--db", str(db), "--events", str(events))
    result = _run("normalize", "--config", str(cfg_path), "--db", str(db), "--events", str(events))

    assert result["ok"] is True
    assert result["assets"] >= 1
    assert result["snapshots"] >= 1

    con = sqlite3.connect(str(db))
    # Seed assets (no ccxt prefix)
    seed_assets = list(con.execute("SELECT asset_id FROM assets WHERE asset_id NOT LIKE 'cex:%'"))
    assert len(seed_assets) >= 1

    # At least one snapshot has null price/volume (seed path)
    snap = con.execute(
        "SELECT asset_id, price, volume_24h_usd FROM market_snapshots WHERE price IS NULL AND volume_24h_usd IS NULL"
    ).fetchone()
    assert snap is not None
    assert snap[1] is None
    assert snap[2] is None

    con.close()
