from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.ai.audit.ai_model_policy_audit_v1 import append_audit_event_v1
from src.ai.policy.ai_model_enablement_policy_v1 import (
    AiModelPolicyError,
    get_status_v1,
    mint_confirm_token_v1,
    policy_allows_ai_call_v1,
    read_policy_v1,
    write_policy_v1,
)


def _print(obj: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, sort_keys=True))
    else:
        if isinstance(obj, str):
            print(obj)
        else:
            print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_status(args: argparse.Namespace) -> int:
    st = get_status_v1()
    _print(st.__dict__, args.json)
    return 0


def _toggle(key: str, value: bool) -> None:
    p = read_policy_v1()
    p[key] = bool(value)
    write_policy_v1(p)
    append_audit_event_v1(event=f"policy_set_{key}", details={"value": bool(value)})


def cmd_enable(args: argparse.Namespace) -> int:
    _toggle("enabled", True)
    return 0


def cmd_disable(args: argparse.Namespace) -> int:
    _toggle("enabled", False)
    return 0


def cmd_arm(args: argparse.Namespace) -> int:
    _toggle("armed", True)
    return 0


def cmd_disarm(args: argparse.Namespace) -> int:
    _toggle("armed", False)
    return 0


def cmd_mint_token(args: argparse.Namespace) -> int:
    p = read_policy_v1()
    tok = mint_confirm_token_v1(p, reason=args.reason)
    append_audit_event_v1(event="token_minted", details={"reason": args.reason})
    _print(tok, args.json)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        policy_allows_ai_call_v1(confirm_token=args.token)
        append_audit_event_v1(event="token_verified_ok", details={})
        _print({"ok": True}, args.json)
        return 0
    except AiModelPolicyError as e:
        append_audit_event_v1(event="token_verified_fail", details={"error": str(e)})
        _print({"ok": False, "error": str(e)}, args.json)
        return 2


def main() -> int:
    ap = argparse.ArgumentParser(prog="ai_model_policy_cli_v1")
    ap.add_argument("--json", action="store_true", help="deterministic JSON output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("enable")
    sub.add_parser("disable")
    sub.add_parser("arm")
    sub.add_parser("disarm")

    ap_tok = sub.add_parser("mint-token")
    ap_tok.add_argument("--reason", required=True)

    ap_ver = sub.add_parser("verify")
    ap_ver.add_argument("--token", required=True)

    args = ap.parse_args()

    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "enable":
        return cmd_enable(args)
    if args.cmd == "disable":
        return cmd_disable(args)
    if args.cmd == "arm":
        return cmd_arm(args)
    if args.cmd == "disarm":
        return cmd_disarm(args)
    if args.cmd == "mint-token":
        return cmd_mint_token(args)
    if args.cmd == "verify":
        return cmd_verify(args)

    raise SystemExit("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
