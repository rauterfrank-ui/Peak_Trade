#!/usr/bin/env python3
"""CLI entrypoint for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION (preflight default; no live execute)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.config_v1 import (
    example_incomplete_config_dict_v1,
    load_live_shadow_recon_config_from_json_file_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.owner_input_contract_v1 import (
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.runner_v1 import (
    LiveShadowReconRunnerError,
    run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "§11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION runner. Default --preflight performs "
            "zero network and loads no credential material."
        )
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        default=True,
        help="Validate call chain until before credential borrow / wire-send (default).",
    )
    parser.add_argument(
        "--print-owner-input-contract",
        action="store_true",
        help="Print Owner execute-time input contract and exit.",
    )
    parser.add_argument(
        "--print-example-config",
        action="store_true",
        help="Print incomplete example config schema and exit.",
    )
    parser.add_argument("--config", type=str, default="", help="Path to JSON config.")
    parser.add_argument(
        "--origin-main-sha",
        type=str,
        default="",
        help="origin/main SHA binding for authorization/evidence.",
    )
    parser.add_argument(
        "--evidence-root",
        type=str,
        default="",
        help="Optional evidence run directory for preflight artifacts.",
    )
    parser.add_argument(
        "--owner-go",
        type=str,
        default="",
        help=f"Optional Owner-GO token (execute token is {OWNER_GO_EXECUTE}).",
    )
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="Set LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED for auth validation in preflight.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.print_owner_input_contract:
        print(json.dumps(build_owner_execute_input_contract_v1(), indent=2, sort_keys=True))
        return 0
    if args.print_example_config:
        print(json.dumps(example_incomplete_config_dict_v1(), indent=2, sort_keys=True))
        return 0

    if not args.config:
        print("FAIL_CLOSED: --config required for preflight", file=sys.stderr)
        return 2
    if not args.origin_main_sha:
        print("FAIL_CLOSED: --origin-main-sha required", file=sys.stderr)
        return 2

    config_obj = load_live_shadow_recon_config_from_json_file_v1(Path(args.config))
    try:
        result = run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode="preflight",
            config_payload=config_obj.to_dict(),
            origin_main_sha=args.origin_main_sha,
            owner_go=args.owner_go or None,
            live_shadow_with_exchange_reconciliation_authorized=bool(args.authorized) or None,
            evidence_run_root=args.evidence_root or None,
        )
    except LiveShadowReconRunnerError as exc:
        print(f"FAIL_CLOSED:{exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()
    payload["PACKAGE_MARKER"] = PACKAGE_MARKER
    payload["NETWORK_EFFECT"] = "NONE"
    payload["CREDENTIAL_ACCESS"] = "NONE"
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
