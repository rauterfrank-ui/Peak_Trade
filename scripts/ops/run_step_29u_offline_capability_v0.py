#!/usr/bin/env python3
"""Operator CLI: STEP 29U Offline Capability v0.

Bounded offline Shadow capability. No orders, network Runtime, Scheduler, or
Runtime activation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.bounded_futures_testnet_venue_binding_v0 import (  # noqa: E402
    PRODUCTION_INSTRUMENT_ID,
)
from src.ops.step_29u_offline_capability_v0 import (  # noqa: E402
    RESULT_BLOCKED,
    RESULT_PASS,
    result_to_machine_lines,
    run_step_29u_offline_capability_v0,
)

EXIT_PASS = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2


def _git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Run STEP 29U offline capability (mode identity → lifecycle → "
            "decision/risk consumption → no-order execution → reconciliation → evidence)."
        )
    )
    p.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    p.add_argument(
        "--cycle-count",
        type=int,
        required=True,
        help="Bounded positive cycle count (required; no unbounded loop).",
    )
    p.add_argument("--instrument-id", default=PRODUCTION_INSTRUMENT_ID)
    p.add_argument(
        "--output-path",
        required=True,
        help="Repo-relative evidence output directory (required for PASS).",
    )
    p.add_argument("--overwrite-evidence", action="store_true")
    p.add_argument("--source-git-sha", default=None)
    p.add_argument("--json", action="store_true", help="Emit JSON result on stdout.")
    # Explicitly rejected activation/side-effect flags (presence fails closed).
    p.add_argument("--live", action="store_true")
    p.add_argument("--orders", action="store_true")
    p.add_argument("--testnet-orders", action="store_true")
    p.add_argument("--scheduler", action="store_true")
    p.add_argument("--daemon", action="store_true")
    p.add_argument("--network-runtime", action="store_true")
    p.add_argument("--runtime-activation", action="store_true")
    p.add_argument("--capital-change", action="store_true")
    p.add_argument("--venue", default="OKX")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sha = args.source_git_sha or _git_sha(args.repo_root)
    result = run_step_29u_offline_capability_v0(
        repo_root=args.repo_root,
        source_git_sha=sha,
        cycle_count=args.cycle_count,
        instrument_id=args.instrument_id,
        output_path=args.output_path,
        overwrite_evidence=bool(args.overwrite_evidence),
        live_enabled=bool(args.live),
        order_submission_enabled=bool(args.orders),
        testnet_order_submission_enabled=bool(args.testnet_orders),
        capital_change_enabled=bool(args.capital_change),
        scheduler_enabled=bool(args.scheduler),
        daemon_enabled=bool(args.daemon),
        network_runtime_enabled=bool(args.network_runtime),
        runtime_activation_enabled=bool(args.runtime_activation),
        venue=str(args.venue),
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        for line in result_to_machine_lines(result):
            print(line)
    if result.capability_result == RESULT_PASS:
        return EXIT_PASS
    if result.capability_result == RESULT_BLOCKED:
        return EXIT_BLOCKED
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
