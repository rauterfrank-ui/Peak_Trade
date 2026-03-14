#!/usr/bin/env python3
"""
Bounded Pilot Entry Gate Wrapper — Pre-Entry-Checks + Session Handoff.

Read-only gate for the first strictly bounded real-money pilot.
Runs Pre-Entry-Checks (go/no-go, cockpit, config). On Gates GREEN, invokes
run_execution_session --mode bounded_pilot (Slice 4 handoff).

Exit codes:
  0 — All gates GREEN; session completed successfully (or delegated to runner)
  1 — One or more gates RED; entry not permitted (or runner failed)
  2 — Script error (e.g. cockpit build failed)

Usage:
  python3 scripts/ops/run_bounded_pilot_session.py
  python3 scripts/ops/run_bounded_pilot_session.py --json
  python3 scripts/ops/run_bounded_pilot_session.py --no-invoke  # Gates check only, no session start

Reference: BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT, option_a_slice_4_wrapper_to_runner_handoff_review
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add repo root for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

RUNNER_SCRIPT = "scripts/run_execution_session.py"
DEFAULT_BOUNDED_STEPS = 1  # Entry Contract §4: bounded by configured caps


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bounded Pilot Entry Gate — Pre-Entry-Checks + Session Handoff (Slice 4)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (default: parent of scripts/ops)",
    )
    parser.add_argument(
        "--no-invoke",
        action="store_true",
        help="Gates check only; do not invoke run_execution_session (for dry-run / Slice 3 not ready)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_BOUNDED_STEPS,
        help=f"Bounded cap: max steps for session (default: {DEFAULT_BOUNDED_STEPS})",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.exists() else Path.cwd())

    try:
        from scripts.ops.pilot_go_no_go_eval_v1 import evaluate
        from src.webui.ops_cockpit import build_ops_cockpit_payload

        payload = build_ops_cockpit_payload(repo_root=repo_root)
    except Exception as e:
        print(f"ERR: failed to build cockpit payload: {e}", file=sys.stderr)
        return 2

    result = evaluate(payload)
    verdict = result["verdict"]

    if verdict != "GO_FOR_NEXT_PHASE_ONLY":
        if args.json:
            out = {
                "contract": "run_bounded_pilot_session",
                "verdict": verdict,
                "entry_permitted": False,
                "message": f"Gates not satisfied: verdict={verdict}",
                "go_no_go": result,
            }
            print(json.dumps(out, indent=2))
        else:
            print(f"GATES_RED: verdict={verdict}", file=sys.stderr)
            for r in result["rows"]:
                if r["status"] != "PASS":
                    print(f"  Row {r['row']} {r['area']}: {r['status']}", file=sys.stderr)
            print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
        return 1

    # All gates GREEN
    if args.no_invoke:
        # Dry-run: gates passed, but do not invoke runner (Slice 3 not ready, or operator check)
        msg = "Gates GREEN; session start skipped (--no-invoke)"
        if args.json:
            out = {
                "contract": "run_bounded_pilot_session",
                "verdict": verdict,
                "entry_permitted": True,
                "message": msg,
                "go_no_go": result,
            }
            print(json.dumps(out, indent=2))
        else:
            print(msg)
        return 0

    # Handoff: invoke run_execution_session --mode bounded_pilot (Slice 4)
    runner_path = repo_root / RUNNER_SCRIPT
    if not runner_path.exists():
        err = f"Runner not found: {runner_path}"
        if args.json:
            print(json.dumps({"contract": "run_bounded_pilot_session", "error": err}, indent=2))
        else:
            print(f"ERR: {err}", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        str(runner_path),
        "--mode",
        "bounded_pilot",
        "--strategy",
        "ma_crossover",
        "--steps",
        str(args.steps),
    ]
    result = subprocess.run(cmd, cwd=repo_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
