from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ops.p67.shadow_session_scheduler_v1 import (
    P67RunContextV1,
    run_shadow_session_scheduler_v1,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="P67 shadow session scheduler v1 (paper/shadow only).")
    ap.add_argument("--mode", default="shadow", choices=["paper", "shadow"])
    ap.add_argument("--run-id", default="p67")
    ap.add_argument("--out-dir", default="", help="If set, write evidence under this directory.")
    ap.add_argument("--iterations", type=int, default=1)
    ap.add_argument("--interval-seconds", type=float, default=60.0)
    ap.add_argument("--json", action="store_true", help="Print JSON result.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else None
    ctx = P67RunContextV1(
        mode=args.mode,
        run_id=args.run_id,
        out_dir=out_dir,
        iterations=args.iterations,
        interval_seconds=args.interval_seconds,
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
