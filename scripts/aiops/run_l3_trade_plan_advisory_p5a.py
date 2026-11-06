#!/usr/bin/env python3
"""
P5A — L3 Trade Plan Advisory Runner (dry-run, advisory-only)

Stub for P5A integration. Consumes P5A input (incl. P4C outlook), outputs advisory JSON.
NO execution. NO exchange side effects.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p4c.evidence import build_manifest, write_json
from src.aiops.p5a.input_schema import validate_input
from src.aiops.p5a.schema import TradePlanAdvisory


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_outdir(base: Path, run_id: str = "") -> Path:
    ts = run_id.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = base / "out" / "ops" / "p5a" / f"run_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def load_input(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, required=True, help="Path to P5A input JSON")
    ap.add_argument(
        "--from-p4c",
        type=str,
        default="",
        help="Optional: path to P4C l2_market_outlook.json to populate p4c_outlook",
    )
    ap.add_argument("--outdir", type=str, default="", help="Override output directory (optional)")
    ap.add_argument(
        "--run-id",
        type=str,
        default="",
        help="Deterministic run id (optional; used when outdir not provided)",
    )
    ap.add_argument(
        "--evidence",
        type=int,
        default=1,
        help="Write evidence manifest (1 default, 0 disable)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry-run (default true; advisory-only)",
    )
    args = ap.parse_args()

    inp_path = Path(args.input).expanduser().resolve()
    if not inp_path.is_file():
        raise FileNotFoundError(inp_path)

    outdir = (
        Path(args.outdir).expanduser().resolve()
        if args.outdir
        else ensure_outdir(Path.cwd(), args.run_id)
    )

    inp = load_input(inp_path)

    if args.from_p4c:
        p4c_path = Path(args.from_p4c).expanduser().resolve()
        if not p4c_path.is_file():
            raise FileNotFoundError(p4c_path)
        p4c_obj = load_input(p4c_path)
        if isinstance(inp, dict):
            inp = dict(inp)
            inp["p4c_outlook"] = dict(
                (p4c_obj.get("outlook") or {}) if isinstance(p4c_obj, dict) else {}
            )

    if isinstance(inp, dict):
        validate_input(inp)

    p4c = (inp.get("p4c_outlook") or {}) if isinstance(inp, dict) else {}

    no_trade = bool(p4c.get("no_trade", False))
    no_trade_reasons = list(p4c.get("no_trade_reasons", []) or [])

    advisory = TradePlanAdvisory(
        asof_utc=str(inp.get("asof_utc", "")),
        universe=list(inp.get("universe", []) or []),
        stance="NO_TRADE" if no_trade else "HOLD",
        allocations={},
        constraints=dict(inp.get("risk", {}) or {}),
        rationale=["p5a_v0_stub"],
        no_trade=no_trade,
        no_trade_reasons=no_trade_reasons,
        evidence={},
    )

    out_json = outdir / "l3_trade_plan_advisory.json"
    write_json(out_json, advisory.to_dict())

    printed: list[Path] = [out_json]

    if int(args.evidence) == 1:
        manifest_meta = {
            "kind": "p5a_evidence_manifest",
            "schema_version": advisory.schema_version,
            "created_at_utc": utc_now_iso(),
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
