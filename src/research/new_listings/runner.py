from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .collectors.base import Collector, CollectorContext, RawEvent
from .collectors.manual_seed import ManualSeedCollector
from .collectors.ccxt_ticker import CcxtTickerCollector
from .collectors.replay import ReplayCollector
from .db import (
    DEFAULT_DB_PATH,
    DEFAULT_EVENTS_PATH,
    Event,
    append_events,
    connect,
    insert_listing_score,
    insert_market_snapshot,
    insert_risk_flag,
    insert_raw_events_bulk,
    make_run_id,
    stable_config_hash,
    utc_now_iso,
)
from .normalizer import normalize_seed_payload, persist_asset
from .risk import assess_risk_seed
from .scoring import score_seed


@dataclass(frozen=True)
class RunConfig:
    # P2 scope: still JSON-only config, minimal surface
    collectors: Sequence[str]


def parse_run_config(cfg: Mapping[str, Any]) -> RunConfig:
    cols = cfg.get("collectors", ["manual_seed"])
    if not isinstance(cols, list) or not all(isinstance(x, str) for x in cols):
        raise ValueError("config.collectors must be a list[str]")
    return RunConfig(collectors=tuple(cols))


def build_collectors(
    names: Sequence[str], cfg: Mapping[str, Any] | None = None
) -> Sequence[Collector]:
    cfg = cfg or {}
    out: list[Collector] = []
    for n in names:
        if n == "manual_seed":
            out.append(ManualSeedCollector())
        elif n == "ccxt_ticker":
            ccxt_cfg = (cfg.get("sources") or {}).get("ccxt") or {}
            if ccxt_cfg.get("enabled", True):
                out.append(CcxtTickerCollector(cfg))
        elif n == "replay":
            replay_cfg = (cfg.get("sources") or {}).get("replay") or {}
            if replay_cfg.get("enabled", True):
                out.append(ReplayCollector(cfg))
        else:
            raise ValueError(f"unknown collector: {n}")
    return out


def collect_and_persist(
    *,
    cfg: Mapping[str, Any],
    db_path: Path = DEFAULT_DB_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> dict[str, Any]:
    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    rc = parse_run_config(cfg)
    collectors = build_collectors(rc.collectors, cfg)

    con = connect(db_path)

    # collect
    ctx = CollectorContext(run_id=run_id, config_hash=cfg_hash)
    raw: list[RawEvent] = []
    for c in collectors:
        raw.extend(list(c.collect(ctx)))

    # persist raw_events
    n = insert_raw_events_bulk(
        con,
        events=[(e.source, e.venue_type, e.observed_at, dict(e.payload)) for e in raw],
        run_id=run_id,
        config_hash=cfg_hash,
    )

    # emit jsonl events (append-only)
    ts = utc_now_iso()
    append_events(
        events_path,
        [
            Event(
                ts=ts,
                type="raw_event.ingested",
                run_id=run_id,
                config_hash=cfg_hash,
                source=e.source,
                meta={"venue_type": e.venue_type, "observed_at": e.observed_at},
            )
            for e in raw
        ],
    )

    return {
        "ok": True,
        "run_id": run_id,
        "config_hash": cfg_hash,
        "raw_events": n,
        "db": str(db_path),
        "events": str(events_path),
    }


def normalize_and_persist(
    *,
    cfg: Mapping[str, Any],
    db_path: Path = DEFAULT_DB_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> dict[str, Any]:
    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    con = connect(db_path)
    rows = list(
        con.execute(
            "SELECT source, venue_type, observed_at, payload_json FROM raw_events ORDER BY id DESC LIMIT 1000"
        )
    )

    n_assets = 0
    n_snaps = 0
    for r in rows:
        source = r[0]
        observed_at = r[2]
        payload = json.loads(r[3])
        # P3: only seed normalization
        a = normalize_seed_payload(payload, source=source, observed_at=observed_at)
        persist_asset(con, a)
        n_assets += 1

        ts = utc_now_iso()
        insert_market_snapshot(
            con,
            asset_id=a.asset_id,
            ts=ts,
            price=None,
            fdv=None,
            liquidity_usd=None,
            volume_24h_usd=None,
            holders=None,
            age_minutes=None,
            run_id=run_id,
            config_hash=cfg_hash,
        )
        n_snaps += 1

    append_events(
        events_path,
        [
            Event(
                ts=utc_now_iso(),
                type="asset.normalized",
                run_id=run_id,
                config_hash=cfg_hash,
                asset_id=None,
                source="normalizer.seed",
                meta={"assets": n_assets, "snapshots": n_snaps},
            )
        ],
    )
    return {
        "ok": True,
        "run_id": run_id,
        "config_hash": cfg_hash,
        "assets": n_assets,
        "snapshots": n_snaps,
        "db": str(db_path),
        "events": str(events_path),
    }


def risk_and_persist(
    *,
    cfg: Mapping[str, Any],
    db_path: Path = DEFAULT_DB_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> dict[str, Any]:
    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    con = connect(db_path)
    assets = list(
        con.execute(
            "SELECT asset_id, symbol, chain, tags_json FROM assets ORDER BY first_seen_at DESC LIMIT 1000"
        )
    )

    n = 0
    for r in assets:
        asset_id = r[0]
        row = {"asset_id": r[0], "symbol": r[1], "chain": r[2], "tags_json": r[3]}
        res = assess_risk_seed(row)
        ts = utc_now_iso()
        insert_risk_flag(
            con,
            asset_id=asset_id,
            ts=ts,
            severity=res.severity,
            flags=res.flags,
            run_id=run_id,
            config_hash=cfg_hash,
        )
        n += 1

    append_events(
        events_path,
        [
            Event(
                ts=utc_now_iso(),
                type="risk.assessed",
                run_id=run_id,
                config_hash=cfg_hash,
                source="risk.seed",
                meta={"assets": n},
            )
        ],
    )

    return {
        "ok": True,
        "run_id": run_id,
        "config_hash": cfg_hash,
        "risk_rows": n,
        "db": str(db_path),
        "events": str(events_path),
    }


def score_and_persist(
    *,
    cfg: Mapping[str, Any],
    db_path: Path = DEFAULT_DB_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> dict[str, Any]:
    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    con = connect(db_path)

    assets = list(
        con.execute(
            "SELECT asset_id, symbol, chain, tags_json FROM assets ORDER BY first_seen_at DESC LIMIT 1000"
        )
    )
    latest_risk = {
        r[0]: {"severity": r[2], "flags_json": r[3]}
        for r in con.execute("SELECT asset_id, ts, severity, flags_json FROM v_latest_risk")
    }
    latest_snap = {
        r[0]: {"ts": r[1]} for r in con.execute("SELECT asset_id, ts FROM v_latest_snapshot")
    }

    n = 0
    for r in assets:
        asset_id = r[0]
        asset_row = {"asset_id": r[0], "symbol": r[1], "chain": r[2], "tags_json": r[3]}
        rr = latest_risk.get(asset_id)
        sr = latest_snap.get(asset_id)

        res = score_seed(
            asset_row=asset_row,
            latest_risk_row=rr,
            latest_snapshot_row=sr,
        )
        ts = utc_now_iso()
        insert_listing_score(
            con,
            asset_id=asset_id,
            ts=ts,
            score=res.score,
            breakdown=res.breakdown,
            reason=res.reason,
            run_id=run_id,
            config_hash=cfg_hash,
        )
        n += 1

    append_events(
        events_path,
        [
            Event(
                ts=utc_now_iso(),
                type="score.assessed",
                run_id=run_id,
                config_hash=cfg_hash,
                source="score.seed",
                meta={"assets": n},
            )
        ],
    )

    return {
        "ok": True,
        "run_id": run_id,
        "config_hash": cfg_hash,
        "score_rows": n,
        "db": str(db_path),
        "events": str(events_path),
    }
