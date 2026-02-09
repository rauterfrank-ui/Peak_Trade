from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .collectors.base import Collector, CollectorContext, RawEvent
from .collectors.manual_seed import ManualSeedCollector
from .db import (
    DEFAULT_DB_PATH,
    DEFAULT_EVENTS_PATH,
    Event,
    append_events,
    connect,
    insert_raw_events_bulk,
    make_run_id,
    stable_config_hash,
    utc_now_iso,
)


@dataclass(frozen=True)
class RunConfig:
    # P2 scope: still JSON-only config, minimal surface
    collectors: Sequence[str]


def parse_run_config(cfg: Mapping[str, Any]) -> RunConfig:
    cols = cfg.get("collectors", ["manual_seed"])
    if not isinstance(cols, list) or not all(isinstance(x, str) for x in cols):
        raise ValueError("config.collectors must be a list[str]")
    return RunConfig(collectors=tuple(cols))


def build_collectors(names: Sequence[str]) -> Sequence[Collector]:
    out: list[Collector] = []
    for n in names:
        if n == "manual_seed":
            out.append(ManualSeedCollector())
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
    collectors = build_collectors(rc.collectors)

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
