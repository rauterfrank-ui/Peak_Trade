#!/usr/bin/env python3
"""
P4C — L2 Market Outlook Runner (dry-run, deterministic)

Intent:
- Consume a prepared input capsule (from L1/L4 operational outputs)
- Produce a market outlook artifact:
  - regime scenario classification
  - NO-TRADE triggers
  - evidence pack manifest
- Write ONLY to out/ops/p4c/<timestamp>/ by default

This is a scaffold. Implementation is runbook-driven.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class RunnerMeta:
    schema_version: str = "p4c.l2_market_outlook.v0"
    runner_version: str = "0.0.0"
    created_at_utc: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_outdir(base: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = base / "out" / "ops" / "p4c" / f"run_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def load_capsule(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capsule", type=str, required=True, help="Path to input capsule JSON")
    ap.add_argument("--outdir", type=str, default="", help="Override output directory (optional)")
    ap.add_argument("--dry-run", action="store_true", default=True, help="Dry-run (default true)")
    args = ap.parse_args()

    capsule_path = Path(args.capsule).expanduser().resolve()
    if not capsule_path.is_file():
        raise FileNotFoundError(capsule_path)

    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else ensure_outdir(Path.cwd())

    meta = RunnerMeta(created_at_utc=utc_now_iso())

    capsule = load_capsule(capsule_path)

    # TODO (P4C): compute regimes + NO-TRADE triggers based on runbook-defined rules.
    result: Dict[str, Any] = {
        "meta": asdict(meta),
        "inputs": {"capsule": str(capsule_path)},
        "outlook": {
            "regime": None,
            "no_trade": False,
            "no_trade_reasons": [],
        },
        "capsule_preview_keys": sorted(list(capsule.keys())),
    }

    out_json = outdir / "l2_market_outlook.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    print(str(out_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
