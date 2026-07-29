#!/usr/bin/env python3
"""CLI for Pre-Economic Zero-Order Wallclock Execution Arming v1.

Two-stage authority:
  1) validate Operator-GO + authorization contract
  2) issue / validate short-lived wallclock arming lease

production-start requires both stages. This CLI never commits GO tokens.
This PR does not execute a real 6h session by default.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
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
from src.ops.pre_economic_zero_order_wallclock_arming_v1 import (  # noqa: E402
    TRUTH_CLAIM,
    WallclockArmingError,
    build_wallclock_arming_lease_dict_v1,
    load_wallclock_arming_lease_v1,
    validate_wallclock_arming_against_go_v1,
    wallclock_arming_defaults_blocked_v1,
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
        "truth_claim",
    ):
        if key in payload:
            print(f"{key}={payload[key]}")


def _resolve_go_token(cli_token: str | None) -> str | None:
    if cli_token:
        return cli_token
    env = os.environ.get("PEZ_OPERATOR_GO_TOKEN")
    return env if env else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            f"Pre-Economic Zero-Order Wallclock Arming ({TRUTH_CLAIM}; no implicit session start)."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    vc = sub.add_parser("validate-config", help="Validate canonical production config")
    vc.add_argument("--config", type=Path, default=None)
    vc.add_argument("--json", action="store_true")

    defaults = sub.add_parser("show-safety-defaults", help="Print fail-closed safety defaults")
    defaults.add_argument("--json", action="store_true")

    va = sub.add_parser("validate-authorization", help="Stage-1: GO + authorization contract")
    va.add_argument("--authorization", type=Path, required=True)
    va.add_argument("--config", type=Path, default=None)
    va.add_argument("--go-token", default=None)
    va.add_argument("--revision-sha", default="UNKNOWN")
    va.add_argument("--json", action="store_true")

    issue = sub.add_parser(
        "issue-arming-lease",
        help="Materialize a short-lived wallclock arming lease (runtime only; not committed)",
    )
    issue.add_argument("--authorization", type=Path, required=True)
    issue.add_argument("--output", type=Path, required=True)
    issue.add_argument("--arming-id", required=True)
    issue.add_argument("--go-token", default=None)
    issue.add_argument("--ttl-seconds", type=int, default=900)
    issue.add_argument("--json", action="store_true")

    varm = sub.add_parser("validate-arming", help="Stage-2: validate wallclock arming lease")
    varm.add_argument("--authorization", type=Path, required=True)
    varm.add_argument("--arming-lease", type=Path, required=True)
    varm.add_argument("--config", type=Path, default=None)
    varm.add_argument("--go-token", default=None)
    varm.add_argument("--revision-sha", default="UNKNOWN")
    varm.add_argument("--json", action="store_true")

    pf = sub.add_parser("preflight", help="Full two-stage preflight; does not start a session")
    pf.add_argument("--config", type=Path, default=None)
    pf.add_argument("--authorization", type=Path, default=None)
    pf.add_argument("--arming-lease", type=Path, default=None)
    pf.add_argument("--go-token", default=None)
    pf.add_argument("--revision-sha", default="UNKNOWN")
    pf.add_argument("--json", action="store_true")

    ps = sub.add_parser(
        "production-start",
        help=(
            "Start only with GO∧arming∧enabled∧armed∧authorized∧dry_run=false. "
            "Requires --confirm-wallclock-arming. No --force."
        ),
    )
    ps.add_argument("--config", type=Path, default=None)
    ps.add_argument("--authorization", type=Path, default=None)
    ps.add_argument("--arming-lease", type=Path, default=None)
    ps.add_argument("--go-token", default=None)
    ps.add_argument("--revision-sha", default="UNKNOWN")
    ps.add_argument("--session-id", default=None)
    ps.add_argument(
        "--confirm-wallclock-arming",
        action="store_true",
        help="Required explicit confirm for armed wallclock path",
    )
    ps.add_argument("--json", action="store_true")

    ver = sub.add_parser("verify-production", help="Run production verifier (read-only)")
    ver.add_argument("--evidence-root", type=Path, required=True)
    ver.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate-config":
        payload = validate_config_only_v1(repo_root=ROOT, config_path=args.config)
        payload["truth_claim"] = TRUTH_CLAIM
        _emit(payload, json_mode=args.json)
        return 0

    if args.command == "show-safety-defaults":
        payload = wallclock_arming_defaults_blocked_v1()
        _emit(payload, json_mode=args.json)
        return 0

    if args.command == "validate-authorization":
        cfg = load_production_config_v1(repo_root=ROOT, config_path=args.config)
        try:
            contract = load_authorization_contract_v1(args.authorization)
        except AuthorizationContractError as exc:
            payload = {"ok": False, "blockers": [str(exc)], "truth_claim": TRUTH_CLAIM}
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
        payload["truth_claim"] = TRUTH_CLAIM
        _emit(payload, json_mode=args.json)
        return 0 if result.ok else 1

    if args.command == "issue-arming-lease":
        go = _resolve_go_token(args.go_token)
        if not go:
            payload = {
                "ok": False,
                "blockers": ["OPERATOR_GO_TOKEN_ABSENT"],
                "truth_claim": TRUTH_CLAIM,
            }
            _emit(payload, json_mode=args.json)
            return 1
        try:
            contract = load_authorization_contract_v1(args.authorization)
        except AuthorizationContractError as exc:
            payload = {"ok": False, "blockers": [str(exc)], "truth_claim": TRUTH_CLAIM}
            _emit(payload, json_mode=args.json)
            return 1
        now = time.time()
        lease = build_wallclock_arming_lease_dict_v1(
            arming_id=args.arming_id,
            authorization_id=contract.authorization_id,
            config_digest=contract.config_digest,
            revision_sha=contract.revision_sha,
            go_token=go,
            issued_at=now,
            not_before=now,
            expires_at=now + float(min(args.ttl_seconds, 900)),
            max_arming_ttl_seconds=min(args.ttl_seconds, 900),
            wallclock_execution_authorized=True,
            dry_run=False,
            session_execution_authorized=True,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(lease, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload = {
            "ok": True,
            "arming_lease_path": str(args.output),
            "arming_id": args.arming_id,
            "truth_claim": TRUTH_CLAIM,
            "notes": [
                "LEASE_MATERIALIZED_RUNTIME_ONLY",
                "DOES_NOT_START_SESSION",
                "DO_NOT_COMMIT_GO_TOKEN",
            ],
        }
        _emit(payload, json_mode=args.json)
        return 0

    if args.command == "validate-arming":
        cfg = load_production_config_v1(repo_root=ROOT, config_path=args.config)
        try:
            contract = load_authorization_contract_v1(args.authorization)
            lease = load_wallclock_arming_lease_v1(args.arming_lease)
        except (AuthorizationContractError, WallclockArmingError) as exc:
            payload = {"ok": False, "blockers": [str(exc)], "truth_claim": TRUTH_CLAIM}
            _emit(payload, json_mode=args.json)
            return 1
        result = validate_wallclock_arming_against_go_v1(
            lease=lease,
            contract=contract,
            go_token=_resolve_go_token(args.go_token),
            expected_config_digest=cfg.config_digest if args.revision_sha != "UNKNOWN" else None,
            expected_revision_sha=args.revision_sha if args.revision_sha != "UNKNOWN" else None,
            require_production_flags=True,
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
            arming_lease_path=args.arming_lease,
        )
        payload["truth_claim"] = TRUTH_CLAIM
        _emit(payload, json_mode=args.json)
        return 0 if payload.get("ok") else 1

    if args.command == "production-start":
        if not args.confirm_wallclock_arming:
            payload = {
                "ok": False,
                "abort_reason": "CONFIRM_WALLCLOCK_ARMING_REQUIRED",
                "blockers": ["CONFIRM_WALLCLOCK_ARMING_REQUIRED"],
                "session_evidence_valid": False,
                "production_session_executed": False,
                "truth_claim": TRUTH_CLAIM,
                "notes": [
                    "OPERATOR_GO_ALONE_DOES_NOT_START",
                    "ARMING_ALONE_DOES_NOT_START",
                    "USE_OPERATOR_RUNBOOK_FOR_SEPARATE_6H_RUN",
                ],
            }
            _emit(payload, json_mode=args.json)
            return 2
        go = _resolve_go_token(args.go_token)
        cfg = load_production_config_v1(repo_root=ROOT, config_path=args.config)
        pre = preflight_production_session_v1(
            repo_root=ROOT,
            config=cfg,
            authorization_path=args.authorization,
            go_token=go,
            revision_sha=args.revision_sha,
            arming_lease_path=args.arming_lease,
        )
        if not pre.get("ok"):
            payload = {
                "ok": False,
                "abort_reason": "PRODUCTION_START_BLOCKED",
                "blockers": pre.get("blockers"),
                "session_evidence_valid": False,
                "production_session_executed": False,
                "truth_claim": TRUTH_CLAIM,
            }
            _emit(payload, json_mode=args.json)
            return 2
        # This capability PR does not auto-execute the 6h wallclock session.
        payload = {
            "ok": False,
            "abort_reason": "SESSION_EXECUTION_NOT_PERFORMED_IN_THIS_PR",
            "blockers": ["SESSION_EXECUTION_NOT_PERFORMED_IN_THIS_PR"],
            "session_evidence_valid": False,
            "production_session_executed": False,
            "production_start_allowed": True,
            "truth_claim": TRUTH_CLAIM,
            "notes": [
                "ARMING_IMPLEMENTED",
                "SEPARATE_OPERATOR_ACTION_REQUIRED_TO_RUN_6H",
                "SEE_OPERATOR_RUNBOOK",
            ],
        }
        _emit(payload, json_mode=args.json)
        return 2

    if args.command == "verify-production":
        result = verify_production_evidence_root_v1(evidence_root=args.evidence_root.resolve())
        payload = result.to_dict()
        payload["truth_claim"] = TRUTH_CLAIM
        _emit(payload, json_mode=args.json)
        return 0 if result.session_evidence_valid else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
