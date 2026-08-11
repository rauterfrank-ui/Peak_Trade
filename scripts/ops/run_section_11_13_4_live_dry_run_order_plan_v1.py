#!/usr/bin/env python3
"""CLI entrypoint for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN (preflight default; execute opt-in)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.config_v1 import (  # noqa: E402
    example_incomplete_config_dict_v1,
    load_live_dry_run_order_plan_config_from_json_file_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (  # noqa: E402
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.owner_input_contract_v1 import (  # noqa: E402
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.runner_v1 import (  # noqa: E402
    LiveDryRunOrderPlanRunnerError,
    run_section_11_13_4_live_dry_run_order_plan_v1,
)


def _parse_bool(raw: str) -> bool:
    v = str(raw or "").strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return True
    if v in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"boolean required, got {raw!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "§11.13.4 LIVE_DRY_RUN_ORDER_PLAN runner. Default --preflight performs zero "
            "network and loads no credential material. --execute requires Owner-GO, "
            "--authorized, --vault-file, and permission attestation. Never submits orders."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="Validate call chain (default).")
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Productive LIVE dry-run order-plan execute. Requires vault file, "
            f"Owner-GO {OWNER_GO_EXECUTE}, --authorized, and permission attestation."
        ),
    )
    parser.add_argument("--print-owner-input-contract", action="store_true")
    parser.add_argument("--print-example-config", action="store_true")
    parser.add_argument("--config", type=str, default="")
    parser.add_argument("--origin-main-sha", type=str, default="")
    parser.add_argument("--executed-code-sha", type=str, default="")
    parser.add_argument("--evidence-root", type=str, default="")
    parser.add_argument("--owner-go", type=str, default="")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--vault-file", type=str, default="")
    parser.add_argument("--permission-read", type=str, default="")
    parser.add_argument("--permission-trade", type=str, default="")
    parser.add_argument("--permission-withdraw", type=str, default="")
    parser.add_argument(
        "--allow-real-transport",
        action="store_true",
        help="Permit UrllibLiveTransportV1 for productive execute.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.print_owner_input_contract:
        print(json.dumps(build_owner_execute_input_contract_v1(), sort_keys=True, indent=2))
        return 0
    if args.print_example_config:
        print(json.dumps(example_incomplete_config_dict_v1(), sort_keys=True, indent=2))
        return 0

    mode = "execute" if args.execute else "preflight"
    if not args.config:
        parser.error("--config is required unless printing helpers")
    if not args.origin_main_sha:
        parser.error("--origin-main-sha is required")

    cfg = load_live_dry_run_order_plan_config_from_json_file_v1(args.config)
    permission = None
    if mode == "execute":
        if not args.authorized:
            parser.error("--authorized required for --execute")
        if not args.owner_go:
            parser.error("--owner-go required for --execute")
        if not args.vault_file:
            parser.error("--vault-file required for --execute")
        if not args.evidence_root:
            parser.error("--evidence-root required for --execute")
        if not args.permission_read or not args.permission_trade or not args.permission_withdraw:
            parser.error("permission attestation flags required for --execute")
        permission = {
            "READ": _parse_bool(args.permission_read),
            "TRADE": _parse_bool(args.permission_trade),
            "WITHDRAW": _parse_bool(args.permission_withdraw),
        }

    try:
        result = run_section_11_13_4_live_dry_run_order_plan_v1(
            mode=mode,
            config_payload=cfg.to_dict(),
            origin_main_sha=args.origin_main_sha,
            executed_code_sha=args.executed_code_sha or args.origin_main_sha,
            owner_go=args.owner_go or None,
            live_dry_run_order_plan_authorized=bool(args.authorized) if args.authorized else None,
            evidence_run_root=args.evidence_root or None,
            vault_file=args.vault_file or None,
            permission_attestation=permission,
            allow_real_transport=bool(args.allow_real_transport),
        )
    except LiveDryRunOrderPlanRunnerError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc), "PACKAGE_MARKER": PACKAGE_MARKER}, indent=2)
        )
        return 2

    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
