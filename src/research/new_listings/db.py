from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DEFAULT_OUT_DIR = Path("out/research/new_listings")
DEFAULT_DB_PATH = DEFAULT_OUT_DIR / "new_listings.sqlite"
DEFAULT_EVENTS_PATH = DEFAULT_OUT_DIR / "events.jsonl"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def stable_config_hash(config: Mapping[str, Any]) -> str:
    """
    Deterministic SHA256 over JSON with sorted keys and minimal separators.
    NOTE: Caller must pass only JSON-serializable content.
    """
    b = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(b).hexdigest()


def make_run_id(prefix: str, config_hash8: str) -> str:
    # Format: nl_YYYYMMDD_HHMMSSZ_<hash8>
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    return f"{prefix}_{ts}_{config_hash8}"


SCHEMA_SQL: str = r"""
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS raw_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  venue_type TEXT NOT NULL,
  observed_at TEXT NOT NULL, -- ISO8601 Z
  payload_json TEXT NOT NULL,
  run_id TEXT NOT NULL,
  config_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY, -- e.g. "eth:0x..."
  symbol TEXT,
  name TEXT,
  chain TEXT,
  contract_address TEXT,
  decimals INTEGER,
  first_seen_at TEXT NOT NULL, -- ISO8601 Z
  sources_json TEXT NOT NULL,  -- JSON array
  tags_json TEXT NOT NULL      -- JSON object/array
);

CREATE TABLE IF NOT EXISTS market_snapshots (
  asset_id TEXT NOT NULL,
  ts TEXT NOT NULL, -- ISO8601 Z
  price REAL,
  fdv REAL,
  liquidity_usd REAL,
  volume_24h_usd REAL,
  holders INTEGER,
  age_minutes INTEGER,
  run_id TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  PRIMARY KEY (asset_id, ts),
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risk_flags (
  asset_id TEXT NOT NULL,
  ts TEXT NOT NULL, -- ISO8601 Z
  severity TEXT NOT NULL, -- e.g. LOW/MED/HIGH
  flags_json TEXT NOT NULL,
  run_id TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  PRIMARY KEY (asset_id, ts),
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS listing_scores (
  asset_id TEXT NOT NULL,
  ts TEXT NOT NULL, -- ISO8601 Z
  score REAL NOT NULL,
  breakdown_json TEXT NOT NULL,
  reason TEXT,
  run_id TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  PRIMARY KEY (asset_id, ts),
  FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_raw_events_observed_at ON raw_events(observed_at);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_ts ON market_snapshots(ts);
CREATE INDEX IF NOT EXISTS idx_risk_flags_ts ON risk_flags(ts);
CREATE INDEX IF NOT EXISTS idx_listing_scores_ts ON listing_scores(ts);
"""

VIEWS_SQL: str = r"""
CREATE VIEW IF NOT EXISTS v_latest_snapshot AS
SELECT ms.*
FROM market_snapshots ms
JOIN (
  SELECT asset_id, MAX(ts) AS max_ts
  FROM market_snapshots
  GROUP BY asset_id
) t
ON t.asset_id = ms.asset_id AND t.max_ts = ms.ts;

CREATE VIEW IF NOT EXISTS v_latest_risk AS
SELECT rf.*
FROM risk_flags rf
JOIN (
  SELECT asset_id, MAX(ts) AS max_ts
  FROM risk_flags
  GROUP BY asset_id
) t
ON t.asset_id = rf.asset_id AND t.max_ts = rf.ts;

CREATE VIEW IF NOT EXISTS v_latest_score AS
SELECT ls.*
FROM listing_scores ls
JOIN (
  SELECT asset_id, MAX(ts) AS max_ts
  FROM listing_scores
  GROUP BY asset_id
) t
ON t.asset_id = ls.asset_id AND t.max_ts = ls.ts;

-- "new" assets: last X minutes based on first_seen_at (X provided at query time via WHERE)
CREATE VIEW IF NOT EXISTS v_assets_new AS
SELECT *
FROM assets;

-- candidates: defined by downstream L5 + thresholds; join latest score+risk with thresholds
CREATE VIEW IF NOT EXISTS v_assets_candidates AS
SELECT
  a.asset_id,
  a.symbol,
  a.chain,
  ls.score AS latest_score,
  rf.severity AS latest_severity
FROM assets a
LEFT JOIN v_latest_score ls ON ls.asset_id = a.asset_id
LEFT JOIN v_latest_risk rf ON rf.asset_id = a.asset_id
WHERE
  COALESCE(rf.severity, 'LOW') != 'HIGH'
  AND COALESCE(ls.score, 0) >= 50.0;
"""


def connect(db_path: Path) -> sqlite3.Connection:
    ensure_parent(db_path)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    return con


def apply_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA_SQL)
    con.executescript(VIEWS_SQL)
    con.commit()


@dataclass(frozen=True)
class Event:
    ts: str
    type: str
    run_id: str
    config_hash: str
    asset_id: str | None = None
    symbol: str | None = None
    chain: str | None = None
    source: str | None = None
    meta: dict[str, Any] | None = None

    def to_json(self) -> str:
        obj: dict[str, Any] = {
            "ts": self.ts,
            "type": self.type,
            "run_id": self.run_id,
            "config_hash": self.config_hash,
        }
        if self.asset_id is not None:
            obj["asset_id"] = self.asset_id
        if self.symbol is not None:
            obj["symbol"] = self.symbol
        if self.chain is not None:
            obj["chain"] = self.chain
        if self.source is not None:
            obj["source"] = self.source
        if self.meta is not None:
            obj["meta"] = self.meta
        return json.dumps(obj, ensure_ascii=False)


def append_events(events_path: Path, events: Sequence[Event]) -> None:
    ensure_parent(events_path)
    with events_path.open("a", encoding="utf-8") as f:
        for e in events:
            f.write(e.to_json())
            f.write("\n")


def insert_raw_event(
    con: sqlite3.Connection,
    *,
    source: str,
    venue_type: str,
    observed_at: str,
    payload: Mapping[str, Any],
    run_id: str,
    config_hash: str,
) -> None:
    con.execute(
        "INSERT INTO raw_events(source, venue_type, observed_at, payload_json, run_id, config_hash) VALUES(?,?,?,?,?,?)",
        (
            source,
            venue_type,
            observed_at,
            json.dumps(payload, ensure_ascii=False),
            run_id,
            config_hash,
        ),
    )
    con.commit()


def insert_raw_events_bulk(
    con: sqlite3.Connection,
    *,
    events: Sequence[
        tuple[str, str, str, Mapping[str, Any]]
    ],  # (source, venue_type, observed_at, payload)
    run_id: str,
    config_hash: str,
) -> int:
    """Insert many raw events in a single transaction. Returns inserted count."""
    rows = [
        (
            source,
            venue_type,
            observed_at,
            json.dumps(payload, ensure_ascii=False),
            run_id,
            config_hash,
        )
        for (source, venue_type, observed_at, payload) in events
    ]
    con.executemany(
        "INSERT INTO raw_events(source, venue_type, observed_at, payload_json, run_id, config_hash) VALUES(?,?,?,?,?,?)",
        rows,
    )
    con.commit()
    return len(rows)


def insert_market_snapshot(
    con: sqlite3.Connection,
    *,
    asset_id: str,
    ts: str,
    price: float | None,
    fdv: float | None,
    liquidity_usd: float | None,
    volume_24h_usd: float | None,
    holders: int | None,
    age_minutes: int | None,
    run_id: str,
    config_hash: str,
) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO market_snapshots(
          asset_id, ts, price, fdv, liquidity_usd, volume_24h_usd, holders, age_minutes, run_id, config_hash
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            asset_id,
            ts,
            price,
            fdv,
            liquidity_usd,
            volume_24h_usd,
            holders,
            age_minutes,
            run_id,
            config_hash,
        ),
    )
    con.commit()


def upsert_asset(
    con: sqlite3.Connection,
    *,
    asset_id: str,
    symbol: str | None,
    name: str | None,
    chain: str | None,
    contract_address: str | None,
    decimals: int | None,
    first_seen_at: str,
    sources: Sequence[str],
    tags: Mapping[str, Any] | Sequence[Any],
) -> None:
    con.execute(
        """
        INSERT INTO assets(asset_id, symbol, name, chain, contract_address, decimals, first_seen_at, sources_json, tags_json)
        VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(asset_id) DO UPDATE SET
          symbol=excluded.symbol,
          name=excluded.name,
          chain=excluded.chain,
          contract_address=excluded.contract_address,
          decimals=excluded.decimals,
          sources_json=excluded.sources_json,
          tags_json=excluded.tags_json
        """,
        (
            asset_id,
            symbol,
            name,
            chain,
            contract_address,
            decimals,
            first_seen_at,
            json.dumps(list(sources), ensure_ascii=False),
            json.dumps(tags, ensure_ascii=False),
        ),
    )
    con.commit()


def insert_risk_flag(
    con: sqlite3.Connection,
    *,
    asset_id: str,
    ts: str,
    severity: str,
    flags: Mapping[str, Any],
    run_id: str,
    config_hash: str,
) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO risk_flags(
          asset_id, ts, severity, flags_json, run_id, config_hash
        ) VALUES(?,?,?,?,?,?)
        """,
        (
            asset_id,
            ts,
            severity,
            json.dumps(flags, ensure_ascii=False),
            run_id,
            config_hash,
        ),
    )
    con.commit()


def insert_listing_score(
    con: sqlite3.Connection,
    *,
    asset_id: str,
    ts: str,
    score: float,
    breakdown: Mapping[str, Any],
    reason: str | None,
    run_id: str,
    config_hash: str,
) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO listing_scores(
          asset_id, ts, score, breakdown_json, reason, run_id, config_hash
        ) VALUES(?,?,?,?,?,?,?)
        """,
        (
            asset_id,
            ts,
            float(score),
            json.dumps(breakdown, ensure_ascii=False),
            reason,
            run_id,
            config_hash,
        ),
    )
    con.commit()


def fetch_candidates(con: sqlite3.Connection) -> list[dict]:
    """Return rows from v_assets_candidates as list[dict], with first_seen_at and reasons from joined tables."""
    cur = con.cursor()
    cur.execute(
        """
        SELECT
          a.asset_id,
          a.symbol,
          a.chain,
          a.first_seen_at,
          rf.severity AS risk_severity,
          rf.flags_json AS risk_reason,
          ls.score,
          ls.reason AS score_reason
        FROM assets a
        LEFT JOIN v_latest_score ls ON ls.asset_id = a.asset_id
        LEFT JOIN v_latest_risk rf ON rf.asset_id = a.asset_id
        WHERE
          COALESCE(rf.severity, 'LOW') != 'HIGH'
          AND COALESCE(ls.score, 0) >= 50.0
        ORDER BY ls.score DESC, a.first_seen_at ASC
        """
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
