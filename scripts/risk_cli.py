#!/usr/bin/env python3
"""Peak_Trade risk_cli – VaR and evidence pack (offline, Phase C2)."""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

import numpy as np

# Projekt-Root zum Python-Path hinzufügen
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.evidence import ensure_evidence_dirs, write_meta
from src.risk.var_core import compute_var


def _default_run_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _load_returns(path: Path) -> np.ndarray:
    # expects newline-separated floats or a single-column CSV (with/without header)
    txt = path.read_text(encoding="utf-8").strip().splitlines()
    vals = []
    for ln in txt:
        ln = ln.strip()
        if not ln:
            continue
        if "," in ln:
            ln = ln.split(",")[0].strip()
        try:
            vals.append(float(ln))
        except ValueError:
            # header or non-numeric line
            continue
    if not vals:
        raise SystemExit(f"no numeric returns found in {path}")
    return np.asarray(vals, dtype=float)


def main() -> int:
    ap = argparse.ArgumentParser("risk_cli")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--artifacts-dir", default="artifacts/risk")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_var = sub.add_parser("var", help="compute VaR from a returns file")
    p_var.add_argument("--returns-file", required=True)
    p_var.add_argument("--alpha", type=float, default=0.99)
    p_var.add_argument("--horizon", type=int, default=1)
    p_var.add_argument(
        "--method",
        choices=["historical", "parametric_normal"],
        default="historical",
    )

    args = ap.parse_args()
    run_id = args.run_id or _default_run_id(args.cmd)
    base_dir = Path(args.artifacts_dir) / run_id
    dirs = ensure_evidence_dirs(base_dir)
    write_meta(
        base_dir / "meta.json",
        extra={"command": "risk_cli " + args.cmd, "run_id": run_id},
    )

    if args.cmd == "var":
        r = _load_returns(Path(args.returns_file))
        res = compute_var(
            r, alpha=args.alpha, horizon=args.horizon, method=args.method
        )
        out = {
            "method": res.method,
            "alpha": res.alpha,
            "horizon": res.horizon,
            "var": res.var,
            "sample_size": res.sample_size,
        }
        (dirs["results"] / "var.json").write_text(
            json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
