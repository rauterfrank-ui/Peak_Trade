from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .db import (
    DEFAULT_DB_PATH,
    DEFAULT_EVENTS_PATH,
    Event,
    append_events,
    apply_schema,
    connect,
    insert_raw_event,
    make_run_id,
    stable_config_hash,
    upsert_asset,
    utc_now_iso,
)
from .orchestrator import run_pipeline
from .runner import (
    collect_and_persist,
    normalize_and_persist,
    risk_and_persist,
    score_and_persist,
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


def cmd_collect(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    payload = collect_and_persist(cfg=cfg, db_path=Path(args.db), events_path=Path(args.events))
    print(json.dumps(payload))
    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    payload = normalize_and_persist(cfg=cfg, db_path=Path(args.db), events_path=Path(args.events))
    print(json.dumps(payload))
    return 0


def cmd_risk(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    payload = risk_and_persist(cfg=cfg, db_path=Path(args.db), events_path=Path(args.events))
    print(json.dumps(payload))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    payload = score_and_persist(cfg=cfg, db_path=Path(args.db), events_path=Path(args.events))
    print(json.dumps(payload))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    steps_str = (args.steps or "").strip()
    steps = [x.strip() for x in steps_str.split(",") if x.strip()] if steps_str else []
    payload = run_pipeline(
        cfg=cfg,
        out_dir=Path(args.out_dir),
        db_path=Path(args.db),
        events_path=Path(args.events),
        steps=steps if steps else None,
    )
    print(
        json.dumps(
            {
                "ok": payload.ok,
                "run_id": payload.run_id,
                "config_hash": payload.config_hash,
                "steps": payload.steps,
                "manifest_path": payload.manifest_path,
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

    p_collect = sub.add_parser(
        "collect",
        help="Run collectors and persist raw_events + append events.jsonl (P2)",
    )
    p_collect.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    p_collect.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite path")
    p_collect.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Events JSONL path")
    p_collect.set_defaults(fn=cmd_collect)

    p_norm = sub.add_parser(
        "normalize",
        help="Normalize raw_events into assets + market_snapshots (P3)",
    )
    p_norm.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    p_norm.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite path")
    p_norm.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Events JSONL path")
    p_norm.set_defaults(fn=cmd_normalize)

    p_risk = sub.add_parser(
        "risk",
        help="Assess deterministic risk flags for assets (P4)",
    )
    p_risk.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    p_risk.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite path")
    p_risk.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Events JSONL path")
    p_risk.set_defaults(fn=cmd_risk)

    p_score = sub.add_parser(
        "score",
        help="Compute deterministic listing scores for assets (P5)",
    )
    p_score.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    p_score.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite path")
    p_score.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Events JSONL path")
    p_score.set_defaults(fn=cmd_score)

    p_run = sub.add_parser(
        "run",
        help="Orchestrator-lite pipeline: init,collect,normalize,risk,score (P6)",
    )
    p_run.add_argument("--config", required=True, type=Path, help="Path to JSON config file")
    p_run.add_argument(
        "--out-dir",
        default="out/research/new_listings",
        help="Output dir for run manifest",
    )
    p_run.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite path")
    p_run.add_argument("--events", default=str(DEFAULT_EVENTS_PATH), help="Events JSONL path")
    p_run.add_argument(
        "--steps",
        default="",
        help="Comma list of steps (default: all). Ex: collect,normalize,risk,score",
    )
    p_run.set_defaults(fn=cmd_run)

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
