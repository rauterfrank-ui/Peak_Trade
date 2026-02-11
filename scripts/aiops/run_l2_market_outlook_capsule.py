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
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add repo root for src imports when run as script
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p4c.evidence import build_manifest, write_json
from src.aiops.p4c.regime_rules_v0 import compute_outlook_v0


@dataclass(frozen=True)
class RunnerMeta:
    schema_version: str = "p4c.l2_market_outlook.v0"
    runner_version: str = "0.0.0"
    created_at_utc: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_outdir(base: Path, run_id: str = "") -> Path:
    ts = run_id.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
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
    ap.add_argument(
        "--run-id",
        type=str,
        default="",
        help="Deterministic run id (optional; used when outdir not provided)",
    )
    ap.add_argument("--dry-run", action="store_true", default=True, help="Dry-run (default true)")
    ap.add_argument(
        "--evidence",
        type=int,
        default=1,
        help="Write evidence manifest (1 default, 0 disable)",
    )
    ap.add_argument(
        "--deterministic",
        action="store_true",
        help="Use fixed timestamp for reproducible outputs (CI/testing)",
    )
    args = ap.parse_args()

    capsule_path = Path(args.capsule).expanduser().resolve()
    if not capsule_path.is_file():
        raise FileNotFoundError(capsule_path)

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else ensure_outdir(Path.cwd(), args.run_id)
    )

    created_at = "2026-02-11T12:00:00Z" if args.deterministic else utc_now_iso()
    meta = RunnerMeta(created_at_utc=created_at)

    capsule = load_capsule(capsule_path)

    outlook = compute_outlook_v0(capsule.get("features", {}) if isinstance(capsule, dict) else {})

    result: Dict[str, Any] = {
        "meta": asdict(meta),
        "inputs": {"capsule": str(capsule_path)},
        "outlook": {
            "regime": outlook.regime,
            "no_trade": outlook.no_trade,
            "no_trade_reasons": outlook.no_trade_reasons,
        },
        "capsule_preview_keys": sorted(list(capsule.keys())),
    }

    out_json = outdir / "l2_market_outlook.json"
    write_json(out_json, result)

    printed: List[Path] = [out_json]

    if int(args.evidence) == 1:
        manifest_meta = {
            "kind": "p4c_evidence_manifest",
            "schema_version": meta.schema_version,
            "runner_version": meta.runner_version,
            "created_at_utc": meta.created_at_utc,
        }
        manifest = build_manifest(printed, manifest_meta, base_dir=outdir)
        out_manifest = outdir / "evidence_manifest.json"
        write_json(out_manifest, manifest)
        printed.append(out_manifest)

    for fp in printed:
        print(str(fp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
