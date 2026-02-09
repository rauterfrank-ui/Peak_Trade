from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .db import (
    DEFAULT_DB_PATH,
    DEFAULT_EVENTS_PATH,
    append_events,
    apply_schema,
    connect,
    insert_raw_event,
    make_run_id,
    stable_config_hash,
    upsert_asset,
    utc_now_iso,
    Event,
)


def _load_config(path: Path) -> dict[str, Any]:
    # P0: JSON only (avoid adding TOML dep). Later can switch to project's config system.
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def cmd_init(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    cfg_hash = stable_config_hash(cfg)
    run_id = make_run_id(prefix="nl", config_hash8=cfg_hash[:8])

    con = connect(Path(args.db))
    apply_schema(con)

    # Seed: one synthetic raw event + one asset + one jsonl event (manual replay hook)
    observed_at = utc_now_iso()
    insert_raw_event(
        con,
        source="manual_seed",
        venue_type="seed",
        observed_at=observed_at,
        payload={"note": "P0 seed event", "observed_at": observed_at},
        run_id=run_id,
        config_hash=cfg_hash,
    )

    asset_id = "seed:asset"
    upsert_asset(
        con,
        asset_id=asset_id,
        symbol="SEED",
        name="Seed Asset",
        chain="seedchain",
        contract_address=None,
        decimals=None,
        first_seen_at=observed_at,
        sources=["manual_seed"],
        tags={"p0": True},
    )

    append_events(
        Path(args.events),
        [
            Event(
                ts=observed_at,
                type="asset.discovered",
                run_id=run_id,
                config_hash=cfg_hash,
                asset_id=asset_id,
                symbol="SEED",
                chain="seedchain",
                source="manual_seed",
                meta={"venue_type": "seed"},
            )
        ],
    )

    print(
        json.dumps(
            {
                "ok": True,
                "db": str(args.db),
                "events": str(args.events),
                "run_id": run_id,
                "config_hash": cfg_hash,
            }
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="new_listings")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize SQLite schema + seed event and events.jsonl")
    p_init.add_argument("--config", required=True, type=Path, help="Path to JSON config file (P0)")
    p_init.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help="SQLite path (default: out/research/new_listings/new_listings.sqlite)",
    )
    p_init.add_argument(
        "--events",
        default=str(DEFAULT_EVENTS_PATH),
        help="Events JSONL path (default: out/research/new_listings/events.jsonl)",
    )
    p_init.set_defaults(fn=cmd_init)

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
