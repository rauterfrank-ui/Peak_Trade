#!/usr/bin/env python3
"""Run momentum_1h/v1 offline economic evaluation execution v0.

Bounded offline evaluation with TRADE_LEDGER_V1.jsonl and EQUITY_CURVE_V1.jsonl persistence.
No runtime, order, credentials, arming, or authority effect.
Operator GO: GO_MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
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

from src.research.momentum_1h_v1_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    BINDING_MATERIALIZATION_CONFIG_REL,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_REASON,
    OPERATOR_GO,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    SCOPE_BINDING_CONFIG_REL,
    STRATEGY_BINDING_DIGEST,
    STRATEGY_BINDING_REF,
    EXECUTION_AUTHORIZED,
    run_momentum_1h_execution_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Execute momentum_1h/v1 offline economic evaluation v0 "
            "with pinned binding materialization."
        )
    )
    parser.add_argument("--confirm-go-token", choices=[OPERATOR_GO])
    parser.add_argument(
        "--binding-config",
        type=Path,
        default=_REPO_ROOT / BINDING_MATERIALIZATION_CONFIG_REL,
    )
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=DEFAULT_DURABLE_ARCHIVE_ROOT,
    )
    parser.add_argument(
        "--allow-dirty-worktree",
        action="store_true",
        help="Allow execution when worktree has uncommitted changes (tests only).",
    )
    args = parser.parse_args()

    if args.confirm_go_token is None:
        _die(
            f"{FAIL_CLOSED_REASON}: execution_authorized={EXECUTION_AUTHORIZED} "
            f"operator_go={OPERATOR_GO} authority_effect={AUTHORITY_EFFECT} "
            f"runtime_effect={RUNTIME_EFFECT}. Separate operator GO required.",
            code=2,
        )

    try:
        result = run_momentum_1h_execution_v0(
            confirm=args.confirm_go_token,
            repo_root=_REPO_ROOT,
            durable_evidence_root=args.durable_evidence_root,
            binding_config_path=args.binding_config,
            require_clean_worktree=not args.allow_dirty_worktree,
        )
    except ValueError as exc:
        _die(f"ERR:{exc}")

    payload = {
        "verdict": result.verdict.value,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": OPERATOR_GO,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "scope_binding_config_ref": SCOPE_BINDING_CONFIG_REL,
        "strategy_binding_ref": STRATEGY_BINDING_REF,
        "strategy_binding_digest": STRATEGY_BINDING_DIGEST,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "manifest_verify_rc": result.manifest_verify_rc,
        "durable_evidence_path": str(result.evidence_root),
        "trade_ledger_path": str(result.trade_ledger_path),
        "equity_curve_path": str(result.equity_curve_path),
        "trade_count": result.trade_count,
        "equity_point_count": result.equity_point_count,
        "metric_summary": result.metric_summary,
        "fail_reasons": list(result.fail_reasons),
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "generated_at_utc": _utc_now_z(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        if key not in {"metric_summary", "fail_reasons"}:
            print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
