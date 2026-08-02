#!/usr/bin/env python3
"""Productive entrypoint for CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.

Consumes a Cap 2.1 governed universe snapshot (file or state-root). No network
trading session, no selection/alpha/execution authority, no runtime activation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from time import time

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (  # noqa: E402
    run_productive_futures_ranking_producer_v1,
)


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
        return out
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=CAPABILITY_ID)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--universe-snapshot-json", type=Path, default=None)
    parser.add_argument("--universe-state-root", type=Path, default=None)
    parser.add_argument("--session-id", type=str, default="default")
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument("--observed-at-unix", type=float, default=None)
    parser.add_argument("--max-universe-age-seconds", type=float, default=86400.0)
    args = parser.parse_args(argv)

    if args.universe_snapshot_json is None and args.universe_state_root is None:
        parser.error("one of --universe-snapshot-json or --universe-state-root is required")

    universe_snapshot = None
    if args.universe_snapshot_json is not None:
        universe_snapshot = json.loads(args.universe_snapshot_json.read_text(encoding="utf-8"))

    result = run_productive_futures_ranking_producer_v1(
        state_root=args.state_root,
        universe_snapshot=universe_snapshot,
        universe_state_root=args.universe_state_root,
        repository_sha=args.repository_sha or _git_sha(),
        producer_observed_at_unix=(
            float(args.observed_at_unix) if args.observed_at_unix is not None else time()
        ),
        session_id=args.session_id,
        max_universe_age_seconds=float(args.max_universe_age_seconds),
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
