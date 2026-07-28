#!/usr/bin/env python3
"""CLI for Pre-Economic Zero-Order Evidence AUTHORIZATION_AND_EXECUTION v1.

Commands: validate-config, validate-authorization, preflight, dry-run, production-start.

production-start is hard-blocked without external authorization + GO.
No --force. No implicit authority defaults. Never commits GO tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (  # noqa: E402
    AuthorizationContractError,
    load_authorization_contract_v1,
    validate_operator_go_and_contract_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_production_runner_v1 import (  # noqa: E402
    load_production_config_v1,
    preflight_production_session_v1,
    validate_config_only_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_production_verifier_v1 import (  # noqa: E402
    verify_production_evidence_root_v1,
)


def _emit(payload: dict, *, json_mode: bool) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if json_mode:
        print(text, end="")
        return
    for key in (
        "ok",
        "production_start_allowed",
        "session_evidence",
        "session_evidence_valid",
        "state",
        "abort_reason",
        "blockers",
    ):
        if key in payload:
            print(f"{key}={payload[key]}")


def _resolve_go_token(cli_token: str | None) -> str | None:
    # Runtime-only. Env may supply token material but never alone grants authority.
    if cli_token:
        return cli_token
    env = os.environ.get("PEZ_OPERATOR_GO_TOKEN")
    return env if env else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-Economic Zero-Order Evidence AUTHORIZATION_AND_EXECUTION "
            "(implementation readiness; no implicit session start)."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    vc = sub.add_parser("validate-config", help="Validate canonical production config")
    vc.add_argument("--config", type=Path, default=None)
    vc.add_argument("--json", action="store_true")

    va = sub.add_parser(
        "validate-authorization", help="Validate authorization contract + optional GO"
    )
    va.add_argument("--authorization", type=Path, required=True)
    va.add_argument("--config", type=Path, default=None)
    va.add_argument("--go-token", default=None)
    va.add_argument("--revision-sha", default="UNKNOWN")
    va.add_argument("--json", action="store_true")

    pf = sub.add_parser("preflight", help="Full preflight; does not start a session")
    pf.add_argument("--config", type=Path, default=None)
    pf.add_argument("--authorization", type=Path, default=None)
    pf.add_argument("--go-token", default=None)
    pf.add_argument("--revision-sha", default="UNKNOWN")
    pf.add_argument("--json", action="store_true")

    dry = sub.add_parser(
        "dry-run",
        help="Blocked dry-run surface for this capability (never production VALID)",
    )
    dry.add_argument("--json", action="store_true")

    ps = sub.add_parser(
        "production-start",
        help="Hard-blocked unless enabled∧armed∧authorized∧valid GO (no --force)",
    )
    ps.add_argument("--config", type=Path, default=None)
    ps.add_argument("--authorization", type=Path, default=None)
    ps.add_argument("--go-token", default=None)
    ps.add_argument("--revision-sha", default="UNKNOWN")
    ps.add_argument("--session-id", default=None)
    ps.add_argument("--json", action="store_true")

    ver = sub.add_parser("verify-production", help="Run production verifier (read-only)")
    ver.add_argument("--evidence-root", type=Path, required=True)
    ver.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate-config":
        payload = validate_config_only_v1(repo_root=ROOT, config_path=args.config)
        _emit(payload, json_mode=args.json)
        return 0

    if args.command == "validate-authorization":
        cfg = load_production_config_v1(repo_root=ROOT, config_path=args.config)
        try:
            contract = load_authorization_contract_v1(
                args.authorization,
                expected_config_digest=None if cfg.config_digest.startswith("") else None,
            )
        except AuthorizationContractError as exc:
            payload = {"ok": False, "blockers": [str(exc)]}
            _emit(payload, json_mode=args.json)
            return 1
        result = validate_operator_go_and_contract_v1(
            contract=contract,
            go_token=_resolve_go_token(args.go_token),
            expected_config_digest=cfg.config_digest if args.revision_sha != "UNKNOWN" else None,
            expected_revision_sha=args.revision_sha if args.revision_sha != "UNKNOWN" else None,
            require_enabled_armed_authorized=True,
        )
        payload = result.to_dict()
        _emit(payload, json_mode=args.json)
        return 0 if result.ok else 1

    if args.command == "preflight":
        payload = preflight_production_session_v1(
            repo_root=ROOT,
            config=load_production_config_v1(repo_root=ROOT, config_path=args.config),
            authorization_path=args.authorization,
            go_token=_resolve_go_token(args.go_token),
            revision_sha=args.revision_sha,
        )
        # Never claim start allowed from CLI defaults.
        payload["production_start_allowed"] = (
            False if not payload.get("ok") else payload.get("production_start_allowed")
        )
        _emit(payload, json_mode=args.json)
        return 0 if payload.get("ok") else 1

    if args.command == "dry-run":
        payload = {
            "ok": True,
            "mode": "DRY_RUN_IMPLEMENTATION_SURFACE",
            "session_evidence_valid": False,
            "production_session_executed": False,
            "operator_go_granted": False,
            "notes": [
                "DRY_RUN_DOES_NOT_EXECUTE_6H",
                "USE_EXISTING_IMPLEMENTATION_READINESS_DRY_RUN_FOR_OFFLINE_PROOF",
            ],
        }
        _emit(payload, json_mode=args.json)
        return 0

    if args.command == "production-start":
        go = _resolve_go_token(args.go_token)
        cfg = load_production_config_v1(repo_root=ROOT, config_path=args.config)
        # Hard block: defaults and missing GO never start.
        pre = preflight_production_session_v1(
            repo_root=ROOT,
            config=cfg,
            authorization_path=args.authorization,
            go_token=go,
            revision_sha=args.revision_sha,
        )
        if not pre.get("ok"):
            payload = {
                "ok": False,
                "abort_reason": "PRODUCTION_START_BLOCKED",
                "blockers": pre.get("blockers"),
                "session_evidence_valid": False,
                "production_session_executed": False,
                "operator_go_granted": False,
            }
            _emit(payload, json_mode=args.json)
            return 2
        # Even if preflight passes, this PR refuses live 6h wallclock execution.
        payload = {
            "ok": False,
            "abort_reason": "PRODUCTION_WALLCLOCK_EXECUTION_NOT_ARMED_IN_THIS_PR",
            "blockers": ["PRODUCTION_WALLCLOCK_EXECUTION_NOT_ARMED_IN_THIS_PR"],
            "session_evidence_valid": False,
            "production_session_executed": False,
            "operator_go_granted": False,
            "notes": [
                "PREFLIGHT_PASSED_BUT_REAL_6H_REQUIRES_SEPARATE_OPERATOR_GO_EXECUTION_STEP",
                "NO_FORCE_OPTION",
            ],
        }
        _emit(payload, json_mode=args.json)
        return 2

    if args.command == "verify-production":
        result = verify_production_evidence_root_v1(evidence_root=args.evidence_root.resolve())
        payload = result.to_dict()
        _emit(payload, json_mode=args.json)
        return 0 if result.session_evidence_valid else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
