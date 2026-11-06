#!/usr/bin/env python3
"""Run post-PR4922 offline economic evaluation execution v0.

Offline-only economic evaluation for versioned research bindings materialized by PR #4922.
No runtime, order, or authority effect.
Operator GO: GO_POST_PR4922_VERSIONED_RESEARCH_BINDINGS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.research.post_pr4922_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    run_bounded_scope_v0,
)

DEFAULT_DURABLE_ROOT = DEFAULT_DURABLE_ARCHIVE_ROOT


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _git_status_short() -> str:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "(clean)"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute post-PR4922 offline economic evaluation for versioned "
            "research bindings (trend_following/v2, bollinger_bands/v2, momentum_1h/v2)."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Allow execution when worktree has uncommitted changes (tests only).",
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

    evidence_root = result.evidence_root
    (evidence_root / "git_status_short.txt").write_text(
        _git_status_short() + "\n",
        encoding="utf-8",
    )

    payload = {
        "verdict": "POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_V0",
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": CONFIRM_GO,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "fleet_verdict": result.fleet_verdict.value,
        "fleet_status": result.fleet_status.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "candidate_verdicts": {sid: v.value for sid, v in result.candidate_verdicts.items()},
        "manifest_verify_rc": result.manifest_verify_rc,
        "durable_evidence_path": str(result.evidence_root),
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "runtime_authority_created": False,
        "generated_at_utc": _utc_now_z(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        if key != "candidate_verdicts":
            print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
