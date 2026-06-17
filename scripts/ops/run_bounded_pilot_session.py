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
from typing import Any

# Add repo root for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

RUNNER_SCRIPT = "scripts/run_execution_session.py"
DEFAULT_BOUNDED_STEPS = 1  # Entry Contract §4: bounded by configured caps
# Safe default for acceptance runs: ~0.0005 BTC ≈ 30 EUR @ 60k (within bounded_live max_order_notional)
DEFAULT_POSITION_FRACTION_ACCEPTANCE = 0.0005


def evaluate_static_operator_entry_handoff(
    packet: dict[str, Any],
    *,
    expected_packet_identity: str | None = None,
    expected_packet_digest: str | None = None,
    expected_source_revision: str | None = None,
) -> dict[str, Any]:
    """
    Static operator entry handoff evaluation from a canonical operator preflight packet.

    Fail-closed before any session/runner action. Non-authorizing; preflight remains blocked.
    """
    from scripts.ops.bounded_pilot_operator_preflight_packet import READINESS_CANONICAL_OWNER

    fail_reasons: list[str] = []
    summary = packet.get("summary") or {}
    if packet.get("contract") != "bounded_pilot_operator_preflight_packet_v1":
        fail_reasons.append("packet: contract mismatch")
    if not summary.get("packet_ok"):
        fail_reasons.append("packet: packet_ok must be true for static handoff evaluation")

    packet_identity = packet.get("packet_identity")
    packet_digest = packet.get("packet_digest")
    if not packet_identity:
        fail_reasons.append("packet: packet_identity required")
    if not packet_digest:
        fail_reasons.append("packet: packet_digest required")
    if expected_packet_identity and packet_identity != expected_packet_identity:
        fail_reasons.append("packet: packet_identity mismatch")
    if expected_packet_digest and packet_digest != expected_packet_digest:
        fail_reasons.append("packet: packet_digest mismatch")

    handoff = packet.get("lifecycle_static_proof_handoff")
    if handoff is None:
        fail_reasons.append("packet: lifecycle_static_proof_handoff required")
    else:
        if handoff.get("handoff_mode") != (
            "bounded_pilot_operator_preflight_packet_lifecycle_static_proof_handoff_v0"
        ):
            fail_reasons.append("handoff: handoff_mode mismatch")
        if handoff.get("canonical_owner") != READINESS_CANONICAL_OWNER:
            fail_reasons.append("handoff: canonical_owner mismatch")
        if expected_source_revision and handoff.get("source_revision") != expected_source_revision:
            fail_reasons.append("handoff: source_revision mismatch")
        if not handoff.get("lifecycle_static_proof_identity"):
            fail_reasons.append("handoff: lifecycle_static_proof_identity required")
        if not handoff.get("lifecycle_static_proof_digest"):
            fail_reasons.append("handoff: lifecycle_static_proof_digest required")
        if handoff.get("proof_status") != "valid":
            fail_reasons.append("handoff: proof_status must be valid")
        if handoff.get("blocker_state") != "blocked":
            fail_reasons.append("handoff: blocker_state must be blocked")
        if handoff.get("handoff_pass") is not True:
            fail_reasons.extend(
                f"handoff: {reason}" for reason in handoff.get("fail_reasons") or []
            )

    readiness = packet.get("bounded_pilot_readiness") or {}
    if readiness.get("contract") != READINESS_CANONICAL_OWNER:
        fail_reasons.append("readiness: canonical_owner mismatch")
    if handoff is not None:
        composition = handoff.get("composition") or {}
        if composition.get("composition_pass") is not True:
            fail_reasons.append("handoff: composition_pass must be true")
        if readiness.get("static_readiness_proof_coherent") is not True:
            fail_reasons.append("readiness: static_readiness_proof_coherent must be true")

    handoff_pass = not fail_reasons
    return {
        "contract": "run_bounded_pilot_session_static_operator_entry_handoff_v0",
        "handoff_pass": handoff_pass,
        "entry_permitted": False,
        "session_started": False,
        "runner_started": False,
        "preflight_remains_blocked": True,
        "global_blocker_lift_authorized": False,
        "preflight_lift_authorized": False,
        "ready_for_operator_arming": False,
        "readiness_decision_authorized": False,
        "operator_decision_authorized": False,
        "operator_closure_authorized": False,
        "execution_authorized": False,
        "pilot_start_authorized": False,
        "promotion_authorized": False,
        "live_authorized": False,
        "authority_lift": False,
        "pilot_readiness_operationally_granted": False,
        "network_used": False,
        "credentials_used": False,
        "exchange_api_called": False,
        "packet_identity": packet_identity,
        "packet_digest": packet_digest,
        "lifecycle_static_proof_identity": (
            handoff.get("lifecycle_static_proof_identity") if handoff else None
        ),
        "lifecycle_static_proof_digest": (
            handoff.get("lifecycle_static_proof_digest") if handoff else None
        ),
        "fail_reasons": sorted(dict.fromkeys(fail_reasons)),
    }


def _evaluate_operator_preflight_packet(
    *,
    json_mode: bool,
    repo_root: Path,
    config_path: Path,
    readiness_bundle: dict,
    verdict: object,
    lifecycle_static_proof: object | None = None,
    lifecycle_static_proof_handoff_binding: object | None = None,
    lifecycle_handoff_extra_fields: dict | None = None,
    require_static_handoff: bool = False,
) -> tuple[int, dict | None, dict | None]:
    """
    Run read-only operator preflight packet (same semantics as invoke path).

    Returns:
        (0, packet, static_handoff) if packet_ok; (1, packet, static_handoff|None) if blocked;
        (2, packet|None, None) on orchestration error.
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
            lifecycle_static_proof=lifecycle_static_proof,
            lifecycle_static_proof_handoff_binding=lifecycle_static_proof_handoff_binding,
            lifecycle_handoff_extra_fields=lifecycle_handoff_extra_fields,
        )
    except Exception as e:
        print(f"ERR: operator preflight packet failed: {e}", file=sys.stderr)
        return 2, None, None

    static_handoff: dict | None = None
    if require_static_handoff or packet.get("lifecycle_static_proof_handoff") is not None:
        static_handoff = evaluate_static_operator_entry_handoff(packet)
        if not static_handoff.get("handoff_pass"):
            blocked_at = "operator_entry_static_handoff"
            handoff_failures = static_handoff.get("fail_reasons") or []
            if packet_code == 2 or not (packet.get("summary") or {}).get("packet_ok"):
                blocked_at = "operator_preflight_packet"
            if json_mode:
                out = {
                    "contract": "run_bounded_pilot_session",
                    "verdict": verdict,
                    "entry_permitted": False,
                    "message": "operator entry static handoff failed (fail-closed before action)",
                    "blocked_at": blocked_at,
                    "bounded_pilot_readiness": readiness_bundle,
                    "operator_preflight_packet": packet,
                    "static_operator_entry_handoff": static_handoff,
                }
                print(json.dumps(out, indent=2))
            else:
                print(
                    "GATES_RED: operator entry static handoff blocked before session action",
                    file=sys.stderr,
                )
                for b in handoff_failures:
                    print(f"  [handoff] {b}", file=sys.stderr)
                for b in (packet.get("summary") or {}).get("blocked") or []:
                    print(f"  [packet] {b}", file=sys.stderr)
                print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
            return 1, packet, static_handoff

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
            return 2, packet, static_handoff
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
            if static_handoff is not None:
                out["static_operator_entry_handoff"] = static_handoff
            print(json.dumps(out, indent=2))
        else:
            print(
                "GATES_RED: operator preflight packet blocked session handoff",
                file=sys.stderr,
            )
            for b in summary.get("blocked") or []:
                print(f"  [packet] {b}", file=sys.stderr)
            print("Entry not permitted. Fix blockers before retrying.", file=sys.stderr)
        return 1, packet, static_handoff
    return 0, packet, static_handoff


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
        pkt_rc, packet, static_handoff = _evaluate_operator_preflight_packet(
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
            if static_handoff is not None:
                out["static_operator_entry_handoff"] = static_handoff
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

    pkt_rc, _packet, _static_handoff = _evaluate_operator_preflight_packet(
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
