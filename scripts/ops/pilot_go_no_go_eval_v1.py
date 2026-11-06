#!/usr/bin/env python3
"""
Pilot Go/No-Go Eval v1 — Automated checklist evaluation against Ops Cockpit payload.

Read-only. Evaluates the 11 cockpit-based rows from PILOT_GO_NO_GO_CHECKLIST
(PILOT_GO_NO_GO_OPERATIONAL_SLICE). Does not add execution authority.

Exit codes:
  0 — GO_FOR_NEXT_PHASE_ONLY (all evaluated rows PASS)
  1 — CONDITIONAL (some UNKNOWN)
  2 — NO_GO (any FAIL)
  3 — Script error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add repo root for imports
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Navigate nested dict; return default if any key missing."""
    obj: Any = payload
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            return default
        obj = obj[k]
    return obj


def _eval_row_1_safety_gates(payload: dict[str, Any]) -> str:
    """Safety Gates: enabled/armed/confirm-token/dry-run explicit (typed, fail-closed)."""
    ps = _get(payload, "policy_state") or {}
    for key in ("enabled", "armed", "dry_run", "confirm_token_required"):
        if key not in ps:
            return "UNKNOWN"
        if not isinstance(ps[key], bool):
            return "UNKNOWN"
    return "PASS"


def _eval_row_2_kill_switch(payload: dict[str, Any]) -> str:
    """Kill Switch: posture visible and clear?"""
    ps = _get(payload, "policy_state") or {}
    if "kill_switch_active" not in ps:
        return "UNKNOWN"
    return "PASS"


def _eval_row_3_policy_posture(payload: dict[str, Any]) -> str:
    """Policy Posture: action visible and internally consistent (fail-closed for TRADE_READY)."""
    ps = _get(payload, "policy_state") or {}
    action = ps.get("action")
    if action not in ("NO_TRADE", "TRADE_READY"):
        return "UNKNOWN"
    if action == "NO_TRADE":
        return "PASS"
    # TRADE_READY must not be vacuous: require explicit real-order posture signals.
    if ps.get("kill_switch_active") is True:
        return "FAIL"
    if ps.get("blocked") is not False:
        return "FAIL"
    if ps.get("enabled") is not True:
        return "FAIL"
    if ps.get("armed") is not True:
        return "FAIL"
    dry_run = ps.get("dry_run")
    if dry_run is not False:
        return "FAIL"
    return "PASS"


def _eval_row_4_operator_visibility(payload: dict[str, Any]) -> str:
    """Operator Visibility: blocked vs allowed identifiable?"""
    ps = _get(payload, "policy_state") or {}
    inc = _get(payload, "incident_state") or {}
    if "blocked" not in ps or "requires_operator_attention" not in inc:
        return "UNKNOWN"
    return "PASS"


def _eval_row_5_pilot_caps(payload: dict[str, Any]) -> str:
    """Pilot Caps: bounded caps defined?"""
    exp = _get(payload, "exposure_state") or {}
    caps = exp.get("caps_configured") or []
    if not isinstance(caps, list):
        return "UNKNOWN"
    return "PASS" if len(caps) > 0 else "FAIL"


def _eval_row_6_treasury_separation(payload: dict[str, Any]) -> str:
    """Treasury Separation: trading vs treasury explicit?"""
    guard = _get(payload, "guard_state") or {}
    ts = guard.get("treasury_separation")
    if ts != "enforced":
        return "FAIL"
    return "PASS"


def _eval_row_9_stale_state(payload: dict[str, Any]) -> str:
    """Stale State Handling: stale balance/order/position handled safely?"""
    stale = _get(payload, "stale_state") or {}
    summary = stale.get("summary", "unknown")
    if summary == "stale":
        return "FAIL"
    return "PASS"


def _eval_row_12_evidence_continuity(payload: dict[str, Any]) -> str:
    """Evidence Continuity: evidence/audit trail sufficient?"""
    ev = _get(payload, "evidence_state") or {}
    summary = ev.get("summary", "unknown")
    if summary in ("ok", "partial"):
        return "PASS"
    if summary == "stale":
        return "FAIL"
    return "UNKNOWN"


def _eval_row_13_dependency_degradation(payload: dict[str, Any]) -> str:
    """Dependency Degradation: degraded exchange/telemetry explicit?"""
    dep = _get(payload, "dependencies_state") or {}
    summary = dep.get("summary", "unknown")
    if summary == "degraded":
        return "FAIL"
    if summary in ("ok", "partial"):
        return "PASS"
    return "UNKNOWN"


def _eval_row_14_human_supervision(payload: dict[str, Any]) -> str:
    """Human Supervision: pilot explicitly operator-supervised?"""
    sup = _get(payload, "human_supervision_state") or {}
    status = sup.get("status", "")
    if status == "operator_supervised":
        return "PASS"
    return "FAIL"


def _eval_row_15_ambiguity_rule(payload: dict[str, Any]) -> str:
    """Ambiguity Rule: ambiguity → NO_TRADE / safe stop?"""
    ps = _get(payload, "policy_state") or {}
    blocked = ps.get("blocked")
    action = ps.get("action")
    if blocked is True and action != "NO_TRADE":
        return "FAIL"
    return "PASS"


ROWS = [
    (1, "Safety Gates", _eval_row_1_safety_gates),
    (2, "Kill Switch", _eval_row_2_kill_switch),
    (3, "Policy Posture", _eval_row_3_policy_posture),
    (4, "Operator Visibility", _eval_row_4_operator_visibility),
    (5, "Pilot Caps", _eval_row_5_pilot_caps),
    (6, "Treasury Separation", _eval_row_6_treasury_separation),
    (9, "Stale State Handling", _eval_row_9_stale_state),
    (12, "Evidence Continuity", _eval_row_12_evidence_continuity),
    (13, "Dependency Degradation", _eval_row_13_dependency_degradation),
    (14, "Human Supervision", _eval_row_14_human_supervision),
    (15, "Ambiguity Rule", _eval_row_15_ambiguity_rule),
]


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate all cockpit-based rows. Returns rows + verdict."""
    results: list[dict[str, Any]] = []
    for num, area, fn in ROWS:
        try:
            status = fn(payload)
        except Exception:
            status = "UNKNOWN"
        results.append({"row": num, "area": area, "status": status})

    has_fail = any(r["status"] == "FAIL" for r in results)
    has_unknown = any(r["status"] == "UNKNOWN" for r in results)
    all_pass = all(r["status"] == "PASS" for r in results)

    if has_fail:
        verdict = "NO_GO"
    elif has_unknown or not all_pass:
        verdict = "CONDITIONAL"
    else:
        verdict = "GO_FOR_NEXT_PHASE_ONLY"

    return {
        "contract": "pilot_go_no_go_eval_v1",
        "verdict": verdict,
        "rows": results,
        "pass_count": sum(1 for r in results if r["status"] == "PASS"),
        "fail_count": sum(1 for r in results if r["status"] == "FAIL"),
        "unknown_count": sum(1 for r in results if r["status"] == "UNKNOWN"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pilot Go/No-Go Eval v1 — checklist evaluation against Ops Cockpit"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full result as JSON",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (default: parent of scripts/ops)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.exists() else Path.cwd())

    try:
        from src.webui.ops_cockpit import build_ops_cockpit_payload

        payload = build_ops_cockpit_payload(repo_root=repo_root)
    except Exception as e:
        print(f"ERR: failed to build cockpit payload: {e}", file=sys.stderr)
        return 3

    result = evaluate(payload)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"verdict={result['verdict']}")
        for r in result["rows"]:
            print(f"  {r['row']:2} {r['area']:<25} {r['status']}")

    verdict = result["verdict"]
    if verdict == "NO_GO":
        return 2
    if verdict == "CONDITIONAL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
