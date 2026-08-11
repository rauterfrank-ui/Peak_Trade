#!/usr/bin/env python3
"""CLI entrypoint for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION (preflight default; execute opt-in)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.config_v1 import (  # noqa: E402
    example_incomplete_config_dict_v1,
    load_live_shadow_recon_config_from_json_file_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (  # noqa: E402
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.owner_input_contract_v1 import (  # noqa: E402
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.runner_v1 import (  # noqa: E402
    LiveShadowReconRunnerError,
    run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "§11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION runner. Default --preflight "
            "performs zero network and loads no credential material. --execute requires "
            "Owner-GO, --authorized, --vault-file, and permission attestation."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--preflight",
        action="store_true",
        help="Validate call chain until before credential borrow / wire-send (default).",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Productive LIVE shadow exchange-reconciliation execute. Requires vault file, "
            f"Owner-GO {OWNER_GO_EXECUTE}, --authorized, and permission attestation. "
            "Does not authorize orders/Live trading."
        ),
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
        "--executed-code-sha",
        type=str,
        default="",
        help="Optional executed code SHA (defaults to origin-main-sha).",
    )
    parser.add_argument(
        "--evidence-root",
        type=str,
        default="",
        help="Evidence run directory (required for --execute).",
    )
    parser.add_argument(
        "--owner-go",
        type=str,
        default="",
        help=f"Owner-GO token (execute token is {OWNER_GO_EXECUTE}).",
    )
    parser.add_argument(
        "--authorized",
        action="store_true",
        help="Set LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED for auth validation.",
    )
    parser.add_argument(
        "--vault-file",
        type=str,
        default="",
        help="JSON SecretRef vault file for ephemeral credential resolve (execute only).",
    )
    parser.add_argument(
        "--permission-read",
        type=str,
        default="",
        help="Owner permission attestation READ (execute requires true).",
    )
    parser.add_argument(
        "--permission-trade",
        type=str,
        default="",
        help="Owner permission attestation TRADE (execute requires false).",
    )
    parser.add_argument(
        "--permission-withdraw",
        type=str,
        default="",
        help="Owner permission attestation WITHDRAW (execute requires false).",
    )
    parser.add_argument(
        "--allow-real-transport",
        action="store_true",
        help=(
            "Permit real UrllibLiveTransportV1 wire send under execute. "
            "Absent → fail closed unless tests inject transport."
        ),
    )
    return parser


def _parse_bool_flag(raw: str, *, field: str) -> bool:
    value = str(raw or "").strip().lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    raise SystemExit(f"FAIL_CLOSED:INVALID_BOOL:{field}")


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
        print("FAIL_CLOSED: --config required", file=sys.stderr)
        return 2
    if not args.origin_main_sha:
        print("FAIL_CLOSED: --origin-main-sha required", file=sys.stderr)
        return 2

    execute_mode = bool(args.execute)
    mode = "execute" if execute_mode else "preflight"

    config_obj = load_live_shadow_recon_config_from_json_file_v1(Path(args.config))
    permission_attestation = None
    if execute_mode:
        if not args.vault_file:
            print("FAIL_CLOSED: --vault-file required for --execute", file=sys.stderr)
            return 2
        if not args.evidence_root:
            print("FAIL_CLOSED: --evidence-root required for --execute", file=sys.stderr)
            return 2
        if not args.authorized:
            print("FAIL_CLOSED: --authorized required for --execute", file=sys.stderr)
            return 2
        if not args.owner_go:
            print("FAIL_CLOSED: --owner-go required for --execute", file=sys.stderr)
            return 2
        if not args.allow_real_transport:
            print(
                "FAIL_CLOSED: --allow-real-transport required for productive CLI execute",
                file=sys.stderr,
            )
            return 2
        if not args.permission_read or not args.permission_trade or not args.permission_withdraw:
            print(
                "FAIL_CLOSED: --permission-read/--permission-trade/--permission-withdraw required",
                file=sys.stderr,
            )
            return 2
        permission_attestation = {
            "READ": _parse_bool_flag(args.permission_read, field="permission-read"),
            "TRADE": _parse_bool_flag(args.permission_trade, field="permission-trade"),
            "WITHDRAW": _parse_bool_flag(args.permission_withdraw, field="permission-withdraw"),
        }

    try:
        result = run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode=mode,
            config_payload=config_obj.to_dict(),
            origin_main_sha=args.origin_main_sha,
            owner_go=args.owner_go or None,
            live_shadow_with_exchange_reconciliation_authorized=bool(args.authorized) or None,
            evidence_run_root=args.evidence_root or None,
            vault_file=args.vault_file or None,
            permission_attestation=permission_attestation,
            allow_real_transport=bool(args.allow_real_transport),
            executed_code_sha=args.executed_code_sha or None,
        )
    except LiveShadowReconRunnerError as exc:
        print(f"FAIL_CLOSED:{exc}", file=sys.stderr)
        return 1

    payload = result.to_dict()
    payload["PACKAGE_MARKER"] = PACKAGE_MARKER
    if mode == "preflight":
        payload["NETWORK_EFFECT"] = "NONE"
        payload["CREDENTIAL_ACCESS"] = "NONE"
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
