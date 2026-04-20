#!/usr/bin/env python3
"""
Bounded Pilot Entry Gate Wrapper — Pre-Entry-Checks + Session Handoff.

Read-only gate for the first strictly bounded real-money pilot.
Runs Pre-Entry-Checks (go/no-go, cockpit, config). On Gates GREEN, runs the
read-only operator preflight packet (readiness + stop-signal snapshot) once more
immediately before handoff; on packet_ok, invokes run_execution_session --mode
bounded_pilot (Slice 4 handoff).

Exit codes:
  0 — All gates GREEN; operator preflight packet GREEN; session completed successfully (or delegated to runner), or --no-invoke with same packet GREEN
  1 — One or more gates RED; entry not permitted; or operator preflight packet blocked (or runner failed)
  2 — Script error (e.g. cockpit build failed; operator preflight packet orchestration error)

Usage:
  python3 scripts/ops/run_bounded_pilot_session.py
  python3 scripts/ops/run_bounded_pilot_session.py --json
  python3 scripts/ops/run_bounded_pilot_session.py --no-invoke  # Readiness + operator preflight packet; no session start
  python3 scripts/ops/run_bounded_pilot_session.py --steps 25 --position-fraction 0.0005  # Safe acceptance sizing

Reference: BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT, option_a_slice_4_wrapper_to_runner_handoff_review
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add repo root for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

RUNNER_SCRIPT = "scripts/run_execution_session.py"
DEFAULT_BOUNDED_STEPS = 1  # Entry Contract §4: bounded by configured caps
# Safe default for acceptance runs: ~0.0005 BTC ≈ 30 EUR @ 60k (within bounded_live max_order_notional)
DEFAULT_POSITION_FRACTION_ACCEPTANCE = 0.0005


def _evaluate_operator_preflight_packet(
    *,
    json_mode: bool,
    repo_root: Path,
    config_path: Path,
    readiness_bundle: dict,
    verdict: object,
) -> tuple[int, dict | None]:
    """
    Run read-only operator preflight packet (same semantics as invoke path).

    Returns:
        (0, packet) if packet_ok; (1, packet) if blocked; (2, packet|None) on orchestration error.
        Emits stderr / JSON on failure to match existing CLI style.
    """
    try:
        from scripts.ops.bounded_pilot_operator_preflight_packet import (
            build_operator_preflight_packet,
        )

        packet, packet_code = build_operator_preflight_packet(
            repo_root,
            config_path,
            run_tests=False,
        )
    except Exception as e:
        print(f"ERR: operator preflight packet failed: {e}", file=sys.stderr)
        return 2, None

    summary = packet.get("summary") or {}
    packet_ok = bool(summary.get("packet_ok"))
    if packet_code == 2 or not packet_ok:
        blocked_at = "operator_preflight_packet"
        if packet_code == 2:
            if json_mode:
                out = {
                    "contract": "run_bounded_pilot_session",
                    "verdict": verdict,
                    "entry_permitted": False,
                    "message": "operator preflight packet orchestration error (fail-closed before handoff)",
                    "blocked_at": blocked_at,
                    "bounded_pilot_readiness": readiness_bundle,
                    "operator_preflight_packet": packet,
                }
                print(json.dumps(out, indent=2))
            else:
                print(
                    "GATES_RED: operator preflight packet failed before handoff",
                    file=sys.stderr,
                )
                for b in summary.get("blocked") or []:
                    print(f"  [packet] {b}", file=sys.stderr)
                print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
            return 2, packet
        if json_mode:
            out = {
                "contract": "run_bounded_pilot_session",
                "verdict": verdict,
                "entry_permitted": False,
                "message": "operator preflight packet not GREEN (fail-closed before handoff)",
                "blocked_at": blocked_at,
                "bounded_pilot_readiness": readiness_bundle,
                "operator_preflight_packet": packet,
            }
            print(json.dumps(out, indent=2))
        else:
            print(
                "GATES_RED: operator preflight packet blocked session handoff",
                file=sys.stderr,
            )
            for b in summary.get("blocked") or []:
                print(f"  [packet] {b}", file=sys.stderr)
            print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
        return 1, packet
    return 0, packet


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
        help=(
            "Readiness + operator preflight packet only; do not invoke run_execution_session "
            "(gate-only / operator check)"
        ),
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=DEFAULT_BOUNDED_STEPS,
        help=f"Bounded cap: max steps for session (default: {DEFAULT_BOUNDED_STEPS})",
    )
    parser.add_argument(
        "--position-fraction",
        type=float,
        default=DEFAULT_POSITION_FRACTION_ACCEPTANCE,
        help=f"Order size in base units (BTC); safe default for acceptance runs (default: {DEFAULT_POSITION_FRACTION_ACCEPTANCE})",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.exists() else Path.cwd())

    try:
        from scripts.ops.check_bounded_pilot_readiness import (
            resolve_bounded_pilot_config_path,
            run_bounded_pilot_readiness,
        )

        config_path = resolve_bounded_pilot_config_path(repo_root, None)
        ok, readiness_bundle = run_bounded_pilot_readiness(repo_root, config_path, run_tests=False)
    except Exception as e:
        print(f"ERR: bounded pilot preflight failed: {e}", file=sys.stderr)
        return 2

    result = readiness_bundle.get("go_no_go") or {}
    verdict = result.get("verdict")

    if not ok:
        blocked = readiness_bundle.get("blocked_at")
        if args.json:
            out = {
                "contract": "run_bounded_pilot_session",
                "verdict": verdict,
                "entry_permitted": False,
                "message": readiness_bundle.get("message", "Gates not satisfied"),
                "blocked_at": blocked,
                "bounded_pilot_readiness": readiness_bundle,
            }
            print(json.dumps(out, indent=2))
        else:
            if blocked == "live_readiness":
                print("GATES_RED: live readiness failed", file=sys.stderr)
                lr = readiness_bundle.get("live_readiness") or {}
                for fc in lr.get("failed_checks") or []:
                    print(
                        f"  [readiness] {fc.get('name')}: {fc.get('message')}",
                        file=sys.stderr,
                    )
            else:
                print(f"GATES_RED: verdict={verdict}", file=sys.stderr)
                for r in result.get("rows") or []:
                    if r["status"] != "PASS":
                        print(
                            f"  Row {r['row']} {r['area']}: {r['status']}",
                            file=sys.stderr,
                        )
            print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
        return 1

    # All gates GREEN
    if args.no_invoke:
        pkt_rc, packet = _evaluate_operator_preflight_packet(
            json_mode=args.json,
            repo_root=repo_root,
            config_path=config_path,
            readiness_bundle=readiness_bundle,
            verdict=verdict,
        )
        if pkt_rc != 0:
            return pkt_rc
        msg = "Gates GREEN; operator preflight packet GREEN; session start skipped (--no-invoke)"
        if args.json:
            out = {
                "contract": "run_bounded_pilot_session",
                "verdict": result.get("verdict"),
                "entry_permitted": True,
                "message": msg,
                "go_no_go": result,
                "bounded_pilot_readiness": readiness_bundle,
                "operator_preflight_packet": packet,
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

    pkt_rc, _packet = _evaluate_operator_preflight_packet(
        json_mode=args.json,
        repo_root=repo_root,
        config_path=config_path,
        readiness_bundle=readiness_bundle,
        verdict=verdict,
    )
    if pkt_rc != 0:
        return pkt_rc

    cmd = [
        sys.executable,
        str(runner_path),
        "--mode",
        "bounded_pilot",
        "--strategy",
        "ma_crossover",
        "--steps",
        str(args.steps),
        "--position-fraction",
        str(args.position_fraction),
    ]
    from src.core.environment import (
        LIVE_CONFIRM_TOKEN,
        PT_BOUNDED_PILOT_INVOKED_FROM_GATE,
        PT_LIVE_CONFIRM_TOKEN_ENV,
    )

    child_env = os.environ.copy()
    child_env[PT_BOUNDED_PILOT_INVOKED_FROM_GATE] = "1"
    child_env[PT_LIVE_CONFIRM_TOKEN_ENV] = LIVE_CONFIRM_TOKEN

    result = subprocess.run(cmd, cwd=repo_root, env=child_env)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
