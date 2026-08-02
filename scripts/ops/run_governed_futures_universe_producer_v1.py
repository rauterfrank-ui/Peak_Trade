#!/usr/bin/env python3
"""Productive entrypoint for CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1.

Offline/injected OKX EEA public instruments payload only — no network trading session,
no ranking/selection/alpha/execution authority, no runtime activation.
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

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    VENUE,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (  # noqa: E402
    run_governed_futures_universe_producer_v1,
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
    parser.add_argument("--instruments-json", required=True, type=Path)
    parser.add_argument("--mark-price-json", type=Path, default=None)
    parser.add_argument("--source-event-time", type=str, default=None)
    parser.add_argument("--session-id", type=str, default="default")
    parser.add_argument("--venue", type=str, default=VENUE)
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument("--observed-at-unix", type=float, default=None)
    args = parser.parse_args(argv)

    instruments = json.loads(args.instruments_json.read_text(encoding="utf-8"))
    marks = None
    if args.mark_price_json is not None:
        marks = json.loads(args.mark_price_json.read_text(encoding="utf-8"))

    result = run_governed_futures_universe_producer_v1(
        state_root=args.state_root,
        source_payload=instruments,
        mark_price_payload=marks,
        repository_sha=args.repository_sha or _git_sha(),
        producer_observed_at_unix=(
            float(args.observed_at_unix) if args.observed_at_unix is not None else time()
        ),
        source_event_time=args.source_event_time,
        venue=args.venue,
        session_id=args.session_id,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
