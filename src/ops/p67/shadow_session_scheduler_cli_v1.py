from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ops.p67.shadow_session_scheduler_v1 import (
    P67RunContextV1,
    run_shadow_session_scheduler_v1,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _assert_scheduler_start_authorized() -> None:
    root = _repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.ops.scheduler_start_boundary_guard_v0 import assert_scheduler_start_authorized

    assert_scheduler_start_authorized(repo_root=root)


def main() -> int:
    ap = argparse.ArgumentParser(description="P67 shadow session scheduler v1 (paper/shadow only).")
    ap.add_argument("--mode", default="shadow", choices=["paper", "shadow"])
    ap.add_argument("--run-id", default="p67")
    ap.add_argument("--out-dir", default="", help="If set, write evidence under this directory.")
    ap.add_argument("--iterations", type=int, default=1)
    ap.add_argument("--interval-seconds", type=float, default=60.0)
    ap.add_argument(
        "--recorded-price-source",
        default="",
        help="Absolute path to local directory with recorded public REST JSON snapshots.",
    )
    ap.add_argument("--json", action="store_true", help="Print JSON result.")
    args = ap.parse_args()

    _assert_scheduler_start_authorized()

    out_dir = Path(args.out_dir) if args.out_dir else None
    rec = args.recorded_price_source.strip()
    ctx = P67RunContextV1(
        mode=args.mode,
        run_id=args.run_id,
        out_dir=out_dir,
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
        recorded_price_source=Path(rec) if rec else None,
    )
    res = run_shadow_session_scheduler_v1(ctx)
    if args.json:
        print(json.dumps(res, indent=2, sort_keys=True))
    else:
        print(
            f"OK mode={args.mode} iterations={args.iterations} out_dir={args.out_dir or '(none)'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
