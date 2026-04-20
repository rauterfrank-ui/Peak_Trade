#!/usr/bin/env python3
"""
Canonical bounded-pilot readiness / preflight (read-only).

Bundles:
- `scripts/check_live_readiness.py` — stage `live` technical checks (config, risk, exchange, API env)
- `scripts/ops/pilot_go_no_go_eval_v1.py` — Ops Cockpit Go/No-Go rows

Does not invoke a session, does not set handoff env, does not authorize live trading.
Fail-closed: any failed live-readiness check or non-GO verdict blocks.

Exit codes:
  0 — preflight GREEN (live readiness + GO_FOR_NEXT_PHASE_ONLY)
  1 — blocked (readiness or go/no-go)
  2 — script error (e.g. cockpit build failure)

Reference: docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONTRACT_ID = "bounded_pilot_readiness_v1"


def resolve_bounded_pilot_config_path(repo_root: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    env_path = os.environ.get("PEAK_TRADE_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return repo_root / "config" / "config.toml"


def _readiness_summary(report: Any) -> dict[str, Any]:
    from scripts.check_live_readiness import ReadinessReport

    assert isinstance(report, ReadinessReport)
    return {
        "stage": report.stage,
        "all_passed": report.all_passed,
        "passed_count": report.passed_count,
        "failed_count": report.failed_count,
        "failed_checks": [
            {"name": c.name, "message": c.message, "details": c.details}
            for c in report.checks
            if not c.passed
        ],
        "warning_count": report.warning_count,
    }


def run_bounded_pilot_readiness(
    repo_root: Path,
    config_path: Path,
    *,
    run_tests: bool = False,
) -> tuple[bool, dict[str, Any]]:
    """
    Run live-stage readiness checks, then pilot go/no-go eval.

    Returns:
        (ok, bundle) where bundle is JSON-serializable and includes `contract`.
    """
    from scripts.check_live_readiness import run_readiness_checks
    from scripts.ops.pilot_go_no_go_eval_v1 import evaluate
    from src.webui.ops_cockpit import build_ops_cockpit_payload

    bundle: dict[str, Any] = {"contract": CONTRACT_ID}

    try:
        readiness_report = run_readiness_checks(
            stage="live",
            config_path=config_path,
            run_tests=run_tests,
        )
    except Exception as e:
        bundle["ok"] = False
        bundle["blocked_at"] = "live_readiness"
        bundle["message"] = f"live readiness evaluation error: {e}"
        return False, bundle

    bundle["live_readiness"] = _readiness_summary(readiness_report)
    if not readiness_report.all_passed:
        bundle["ok"] = False
        bundle["blocked_at"] = "live_readiness"
        bundle["message"] = f"live readiness failed ({readiness_report.failed_count} check(s))"
        return False, bundle

    try:
        payload = build_ops_cockpit_payload(repo_root=repo_root)
    except Exception as e:
        bundle["ok"] = False
        bundle["blocked_at"] = "cockpit_payload"
        bundle["message"] = f"failed to build ops cockpit payload: {e}"
        return False, bundle

    go_no_go = evaluate(payload)
    bundle["go_no_go"] = go_no_go
    verdict = go_no_go.get("verdict")
    if verdict != "GO_FOR_NEXT_PHASE_ONLY":
        bundle["ok"] = False
        bundle["blocked_at"] = "go_no_go"
        bundle["message"] = f"go/no-go not GREEN: verdict={verdict}"
        return False, bundle

    bundle["ok"] = True
    bundle["blocked_at"] = None
    bundle["message"] = "bounded_pilot preflight GREEN: live readiness + GO_FOR_NEXT_PHASE_ONLY"
    return True, bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Canonical bounded-pilot preflight: live readiness + pilot go/no-go "
            "(read-only, no session invoke)"
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full result as JSON on stdout",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (default: inferred from script location)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Config path (default: PEAK_TRADE_CONFIG_PATH or config/config.toml)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Pass through to live readiness: run baseline pytest (slow)",
    )
    args = parser.parse_args()
    repo_root = args.repo_root or (_REPO_ROOT if _REPO_ROOT.exists() else Path.cwd())
    config_path = resolve_bounded_pilot_config_path(repo_root, args.config)

    try:
        ok, bundle = run_bounded_pilot_readiness(
            repo_root,
            config_path,
            run_tests=args.run_tests,
        )
    except Exception as e:
        err = {"contract": CONTRACT_ID, "ok": False, "error": str(e)}
        if args.json:
            print(json.dumps(err, indent=2))
        else:
            print(f"ERR: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(bundle.get("message", ""))
        if not ok:
            blocked = bundle.get("blocked_at")
            if blocked == "live_readiness":
                lr = bundle.get("live_readiness") or {}
                for fc in lr.get("failed_checks") or []:
                    print(f"  [readiness] {fc.get('name')}: {fc.get('message')}", file=sys.stderr)
            elif blocked == "go_no_go":
                gng = bundle.get("go_no_go") or {}
                for r in gng.get("rows") or []:
                    if r.get("status") != "PASS":
                        print(
                            f"  [go/no-go] Row {r.get('row')} {r.get('area')}: {r.get('status')}",
                            file=sys.stderr,
                        )
            print("Preflight not GREEN. Do not invoke bounded pilot.", file=sys.stderr)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
