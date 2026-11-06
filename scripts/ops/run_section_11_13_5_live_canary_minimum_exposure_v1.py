#!/usr/bin/env python3
"""CLI for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE (preflight/forensic; execute fail-closed)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (  # noqa: E402
    example_incomplete_config_dict_v1,
    load_live_canary_config_from_json_file_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (  # noqa: E402
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.owner_input_contract_v1 import (  # noqa: E402
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (  # noqa: E402
    LiveCanaryRunnerError,
    run_section_11_13_5_live_canary_minimum_exposure_v1,
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
            "§11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE runner. Default --preflight performs "
            "zero network and seals no orders. --forensic classifies sealed HARD_STOP "
            "layers. --execute remains fail-closed until all gates pass under "
            f"{OWNER_GO_EXECUTE}. Execute requires --vault-file, --authorized, "
            "session gates, and permission attestation. Authoring GO cannot submit."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="Validate call chain (default).")
    mode.add_argument("--forensic", action="store_true", help="Sealed-evidence forensic mode.")
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Gated execute path (fail-closed unless all submit gates pass).",
    )
    parser.add_argument("--print-owner-input-contract", action="store_true")
    parser.add_argument("--print-example-config", action="store_true")
    parser.add_argument("--config", type=str, default="")
    parser.add_argument("--origin-main-sha", type=str, default="")
    parser.add_argument("--executed-code-sha", type=str, default="")
    parser.add_argument("--evidence-root", type=str, default="")
    parser.add_argument("--seal-forensic-evidence", action="store_true")
    parser.add_argument("--owner-go", type=str, default="")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--live-enabled", action="store_true")
    parser.add_argument("--live-armed", action="store_true")
    parser.add_argument("--confirm-token", type=str, default="")
    parser.add_argument("--owner-go-consumed", action="store_true")
    parser.add_argument("--permission-read", type=str, default="")
    parser.add_argument("--permission-trade", type=str, default="")
    parser.add_argument("--permission-withdraw", type=str, default="")
    parser.add_argument(
        "--vault-file",
        type=str,
        default="",
        help="JSON SecretRef vault file for ephemeral credential resolve (execute only).",
    )
    parser.add_argument(
        "--allow-productive-wire-send",
        action="store_true",
        help="Required together with --execute to construct the productive urllib transport.",
    )
    parser.add_argument(
        "--live-canary-cybersecurity-gate",
        type=str,
        default="",
        help="Must be PASS for execute. Empty fails closed.",
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

    if args.execute:
        mode = "execute"
        if not args.vault_file:
            parser.error("--vault-file required for --execute")
    elif args.forensic:
        mode = "forensic"
    else:
        mode = "preflight"

    if not args.origin_main_sha:
        parser.error("--origin-main-sha is required")

    cfg_payload = None
    if args.config:
        cfg_payload = load_live_canary_config_from_json_file_v1(args.config).to_dict()

    permission = None
    if args.permission_read or args.permission_trade or args.permission_withdraw:
        if not (args.permission_read and args.permission_trade and args.permission_withdraw):
            parser.error("all permission attestation flags required together")
        permission = {
            "READ": _parse_bool(args.permission_read),
            "TRADE": _parse_bool(args.permission_trade),
            "WITHDRAW": _parse_bool(args.permission_withdraw),
        }

    try:
        result = run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode=mode,
            config_payload=cfg_payload,
            origin_main_sha=args.origin_main_sha,
            executed_code_sha=args.executed_code_sha or args.origin_main_sha,
            owner_go=args.owner_go or None,
            live_canary_authorized=bool(args.authorized) if args.authorized else None,
            evidence_run_root=args.evidence_root or None,
            permission_attestation=permission,
            live_enabled=bool(args.live_enabled),
            live_armed=bool(args.live_armed),
            confirm_token=args.confirm_token or None,
            owner_go_consumed=bool(args.owner_go_consumed),
            seal_forensic_evidence=bool(args.seal_forensic_evidence),
            allow_productive_wire_send=bool(args.allow_productive_wire_send),
            vault_file=args.vault_file or None,
            live_canary_cybersecurity_gate=str(args.live_canary_cybersecurity_gate or ""),
        )
    except LiveCanaryRunnerError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc), "PACKAGE_MARKER": PACKAGE_MARKER}, indent=2)
        )
        return 2

    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
