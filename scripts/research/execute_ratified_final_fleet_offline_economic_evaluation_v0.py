#!/usr/bin/env python3
"""Execute ratified final fleet offline economic evaluation v0.

Offline-only economic evaluation for PR #4917 ratified fleet using Class-D
materialized bindings. No runtime, order, or authority effect.
Operator GO: GO_EXECUTE_RATIFIED_FINAL_FLEET_VERSIONED_OFFLINE_ECONOMIC_EVALUATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.research.ratified_final_fleet_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    ORDER_EFFECT,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    run_bounded_scope_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute ratified final fleet offline economic evaluation v0 "
            "for PR #4917 trend_following/bollinger_bands/momentum_1h."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ARCHIVE_ROOT)
    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Allow execution when worktree has uncommitted changes (local only).",
    )
    args = parser.parse_args()

    try:
        result = run_bounded_scope_v0(
            confirm=args.confirm_go_token,
            repo_root=_REPO_ROOT,
            durable_evidence_root=args.durable_evidence_root,
            require_clean_worktree=not args.allow_dirty_worktree,
        )
    except ValueError as exc:
        _die(f"ERR:{exc}")

    next_step = (
        "REVIEW_OFFLINE_ECONOMIC_VALIDITY_EVIDENCE_AND_PROMOTION_ADMISSIBILITY"
        if result.economic_validity_offline_gate_pass
        else "FIX_EXPLICIT_OFFLINE_EVALUATION_PRECONDITION_GAP_ONLY"
    )
    payload = {
        "verdict": (
            "RATIFIED_FINAL_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_V0"
            if not result.blockers
            else "RATIFIED_FINAL_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_BLOCKED_V0"
        ),
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": CONFIRM_GO,
        "fleet_verdict": result.fleet_verdict.value,
        "fleet_status": result.fleet_status.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "candidate_verdicts": {sid: v.value for sid, v in result.candidate_verdicts.items()},
        "manifest_verify_rc": result.manifest_verify_rc,
        "durable_evidence_path": str(result.evidence_root),
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "next_step": next_step,
        "generated_at_utc": _utc_now_z(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        if key != "candidate_verdicts":
            print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
