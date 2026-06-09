#!/usr/bin/env python3
"""Order-Capability dry-validation adapter v1 (plan-only default, offline evidence only).

Validates accepted operator inputs offline and may write durable evidence under an
archive root when explicitly gated by operator GO token. No network, no secrets,
no orders, no cancel, no trade/position mutation, no live, no preflight lift.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    require_durable_archive_root,
    validate_order_capability_offline_durable_run_root,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.ops.bounded_testnet_order_cap_contract_v0 import default_bounded_normal_v0_spec
from src.ops.order_capability_dry_validation_contract_v1 import (
    OrderCapabilityDryValidationInputs,
    build_dry_validation_result,
    evaluate_order_capability_dry_validation,
)

ADAPTER_VERSION = "cli_order_capability_dry_validation_flow_v1"
REQUIRED_OPERATOR_GO_TOKEN = "GO_ORDER_CAPABILITY_DRY_VALIDATION_OFFLINE_EXECUTE_V1"
RUN_TYPE = "ORDER_CAPABILITY_DRY_VALIDATION_OFFLINE_V1"

USAGE_EXIT = 2
VALIDATION_EXIT = 1


def verify_manifest(root: Path) -> tuple[bool, str]:
    return verify_manifest_sha256(root)


def _inputs_from_namespace(args: argparse.Namespace) -> OrderCapabilityDryValidationInputs:
    return OrderCapabilityDryValidationInputs(
        instrument=str(args.instrument),
        venue=str(args.venue),
        max_loss_cap_eur=float(args.max_loss_cap_eur),
        max_notional_eur=float(args.max_notional_eur),
        order_type=str(args.order_type),
        session_duration_seconds=int(args.session_duration_seconds),
        abort_ack_confirmed=bool(args.abort_ack_confirmed),
        max_notional_confirmed=bool(args.max_notional_confirmed),
    )


def _validate_safety_flags(args: argparse.Namespace) -> list[str]:
    reasons: list[str] = []
    if not args.no_network:
        reasons.append("--no-network must remain true in v1")
    if not args.no_order:
        reasons.append("--no-order must remain true in v1")
    if args.operator_go_token and args.operator_go_token != REQUIRED_OPERATOR_GO_TOKEN:
        reasons.append(f"operator_go_token must be {REQUIRED_OPERATOR_GO_TOKEN!r}")
    if args.write_evidence and not args.operator_go_token:
        reasons.append("operator_go_token required for --write-evidence")
    return reasons


def build_plan_payload(args: argparse.Namespace) -> dict[str, Any]:
    inputs = _inputs_from_namespace(args)
    evaluation = evaluate_order_capability_dry_validation(inputs)
    return {
        "adapter_version": ADAPTER_VERSION,
        "mode": "plan-only",
        "run_type": RUN_TYPE,
        "archive_root": str(args.archive_root),
        "run_id": args.run_id,
        "no_network": bool(args.no_network),
        "no_order": bool(args.no_order),
        "operator_go_token_required_for_write": REQUIRED_OPERATOR_GO_TOKEN,
        "inputs": evaluation["input_status"],
        "blocker_status": evaluation["blocker_status"],
        "validation_verdict": evaluation["verdict"],
        "fail_reasons": evaluation["fail_reasons"],
        "safety_flags": evaluation["safety_flags"],
    }


def write_durable_evidence(args: argparse.Namespace) -> tuple[int, str]:
    safety_reasons = _validate_safety_flags(args)
    if safety_reasons:
        return VALIDATION_EXIT, "; ".join(safety_reasons)

    ok, reason = require_durable_archive_root(args.archive_root)
    if not ok:
        return VALIDATION_EXIT, reason

    inputs = _inputs_from_namespace(args)
    evaluation = evaluate_order_capability_dry_validation(inputs)
    if evaluation["verdict"] != "PASS":
        return VALIDATION_EXIT, "; ".join(evaluation["fail_reasons"]) or "validation failed"

    run_id = args.run_id or f"order_capability_dry_validation_{_utc_stamp()}"
    dest = args.archive_root / "runs" / "testnet" / run_id
    dest.mkdir(parents=True, exist_ok=True)

    result_payload = build_dry_validation_result(inputs, adapter_version=ADAPTER_VERSION)
    result_payload["run_id"] = run_id
    result_payload["archive_root"] = str(args.archive_root)
    result_payload["mode"] = "write-evidence"
    result_payload["operator_go_token_class"] = REQUIRED_OPERATOR_GO_TOKEN

    metadata = {
        "run_id": run_id,
        "run_type": RUN_TYPE,
        "adapter_version": ADAPTER_VERSION,
        "utc_timestamp": _utc_stamp(),
        "archive_root": str(args.archive_root),
        "no_network": True,
        "no_order": True,
        "dry_validation_executed": False,
        "order_submission_executed": False,
    }
    (dest / "RUN_METADATA.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dest / "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json").write_text(
        json.dumps(result_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (dest / "CLOSEOUT.md").write_text(_closeout_markdown(result_payload), encoding="utf-8")
    write_manifest_sha256(dest)
    layout_ok, layout_issues = validate_order_capability_offline_durable_run_root(dest)
    if not layout_ok:
        return VALIDATION_EXIT, "; ".join(layout_issues)
    return 0, str(dest)


def _closeout_markdown(result_payload: dict[str, Any]) -> str:
    safety = result_payload["safety_flags"]
    lines = [
        "# ORDER_CAPABILITY_DRY_VALIDATION CLOSEOUT",
        "",
        f"**Verdict:** `{result_payload['verdict']}`",
        f"**Run ID:** `{result_payload.get('run_id', '')}`",
        "",
        "## Safety",
        "",
        f"- no_order={safety['no_order']}",
        f"- no_network={safety['no_network']}",
        f"- order_submission_executed={safety['order_submission_executed']}",
        f"- network_api_called={safety['network_api_called']}",
        f"- dry_validation_authorized={safety['dry_validation_authorized']}",
        f"- order_capability_execute_authorized={safety['order_capability_execute_authorized']}",
        f"- no_authority_change={safety['no_authority_change']}",
        f"- preflight_remains_blocked={safety['preflight_remains_blocked']}",
        "",
        "Offline validation only. Does not authorize execute.",
    ]
    return "\n".join(lines) + "\n"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_arg_parser() -> argparse.ArgumentParser:
    spec = default_bounded_normal_v0_spec()
    parser = argparse.ArgumentParser(
        description=(
            "Order-Capability dry-validation adapter v1. "
            "Default plan-only; offline evidence write requires operator GO token."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan-only",
        action="store_true",
        help="Emit validation plan only (default when --write-evidence omitted).",
    )
    mode.add_argument(
        "--write-evidence",
        action="store_true",
        help="Write durable offline validation evidence (requires operator GO token).",
    )
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--instrument", type=str, default="PF_XBTUSD")
    parser.add_argument(
        "--venue",
        type=str,
        default="Kraken Futures Demo / demo-futures.kraken.com",
    )
    parser.add_argument("--max-loss-cap-eur", type=float, default=1.0)
    parser.add_argument("--max-notional-eur", type=float, default=spec.max_notional_eur)
    parser.add_argument("--order-type", type=str, default="limit")
    parser.add_argument("--session-duration-seconds", type=int, default=60)
    parser.add_argument("--abort-ack-confirmed", action="store_true")
    parser.add_argument("--max-notional-confirmed", action="store_true")
    parser.add_argument("--operator-go-token", type=str, default="")
    network = parser.add_mutually_exclusive_group()
    network.add_argument(
        "--no-network",
        dest="no_network",
        action="store_true",
        default=True,
        help="Required invariant for v1 (default: true).",
    )
    network.add_argument(
        "--allow-network",
        dest="no_network",
        action="store_false",
        help="Forbidden in v1.",
    )
    order = parser.add_mutually_exclusive_group()
    order.add_argument(
        "--no-order",
        dest="no_order",
        action="store_true",
        default=True,
        help="Required invariant for v1 (default: true).",
    )
    order.add_argument(
        "--allow-order",
        dest="no_order",
        action="store_false",
        help="Forbidden in v1.",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.no_network or not args.no_order:
        print("--no-network and --no-order must remain true in v1", file=sys.stderr)
        return VALIDATION_EXIT

    if args.write_evidence:
        safety_reasons = _validate_safety_flags(args)
        if safety_reasons:
            print("; ".join(safety_reasons), file=sys.stderr)
            return VALIDATION_EXIT
        rc, message = write_durable_evidence(args)
        if rc != 0:
            print(message, file=sys.stderr)
            return rc
        if args.json:
            print(json.dumps({"mode": "write-evidence", "dest": message}, indent=2))
        else:
            print(message)
        return 0

    plan = build_plan_payload(args)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if plan["validation_verdict"] == "PASS" else VALIDATION_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
