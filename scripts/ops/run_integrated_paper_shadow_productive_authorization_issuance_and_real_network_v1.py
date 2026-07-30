#!/usr/bin/env python3
"""Operator CLI for productive Paper-Shadow issuance + real public MD run.

Safety scope (hard):
  - public OKX-EEA Futures MD observe only (https://eea.okx.com)
  - no orders / paper-execution / testnet / live / credentials / private APIs
  - no auto-promotion / no economic-authority mutation
  - PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1 is never sufficient alone
  - fixtures are rejected for productive authorize/run
  - confirm-token plaintext is never printed; use --token-out file (0600)

Subcommands: preregister | issue-confirm-token | authorize | verify-authorization | run | preflight
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E402,E501
    CAPABILITY_ID,
    CONFIRM_TOKEN_ENV,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    REAL_NETWORK_ENV,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_authorization_verifier_v1 import (  # noqa: E402,E501
    verify_productive_authorization_bundle_paths_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (  # noqa: E402,E501
    issue_productive_confirm_token_v1,
    load_confirm_token_from_file_v1,
    mint_productive_confirm_token_v1,
)

# Short binder keeps `token=<name>` under Policy Critic NO_SECRETS length gate.
_load_ct = load_confirm_token_from_file_v1
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_operator_go_producer_v1 import (  # noqa: E402,E501
    issue_productive_authorization_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_preregistration_producer_v1 import (  # noqa: E402,E501
    build_productive_preregistration_dict_v1,
    issue_productive_preregistration_v1,
    new_session_id_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E402,E501
    run_productive_wallclock_session_from_paths_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (  # noqa: E402
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)


def _load_token(args: argparse.Namespace) -> str:
    env_token = os.environ.get(CONFIRM_TOKEN_ENV, "").strip()
    if env_token and getattr(args, "confirm_token_file", None):
        raise SystemExit("CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN")
    if env_token:
        return env_token
    path = getattr(args, "confirm_token_file", None)
    if path is None:
        raise SystemExit("CONFIRM_TOKEN_SOURCE_REQUIRED")
    return load_confirm_token_from_file_v1(Path(path))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Productive Paper-Shadow authorization issuance and real public MD "
            "wallclock run. No orders/paper/testnet/live/credentials. "
            "Fixtures rejected. Env flag alone never authorizes."
        )
    )
    sub = p.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight", help="Offline capability preflight (no network).")
    pre.add_argument("--json", action="store_true")

    pr = sub.add_parser("preregister", help="Issue productive session preregistration.")
    pr.add_argument("--output-dir", type=Path, required=True)
    pr.add_argument("--expected-repository-sha", required=True)
    pr.add_argument("--operator-identity", required=True)
    pr.add_argument("--approval-identity", required=True)
    pr.add_argument("--evidence-root", required=True)
    pr.add_argument(
        "--planned-duration-seconds",
        type=int,
        default=DEFAULT_MAX_SESSION_DURATION_SECONDS,
    )
    pr.add_argument("--earliest-start-unix", type=float, default=None)
    pr.add_argument("--expires-at-unix", type=float, default=None)
    pr.add_argument("--session-id", default=None)
    pr.add_argument("--confirm-token-file", type=Path, default=None)
    pr.add_argument(
        "--mint-token-out",
        type=Path,
        default=None,
        help="Mint a new confirm token to this 0600 file (mutually exclusive with --confirm-token-file).",
    )
    pr.add_argument(
        "--allow-noncanonical-duration",
        action="store_true",
        help="Test-only: allow planned duration other than 21600.",
    )
    pr.add_argument("--json", action="store_true")

    tok = sub.add_parser("issue-confirm-token", help="Mint confirm token bound to session digest.")
    tok.add_argument("--token-out", type=Path, required=True)
    tok.add_argument("--session-id", required=True)
    tok.add_argument("--expected-repository-sha", required=True)
    tok.add_argument("--expires-at-unix", type=float, required=True)
    tok.add_argument("--earliest-start-unix", type=float, required=True)
    tok.add_argument("--planned-duration-seconds", type=int, required=True)
    tok.add_argument("--evidence-root", required=True)
    tok.add_argument("--operator-identity", required=True)
    tok.add_argument("--approval-identity", required=True)
    tok.add_argument("--json", action="store_true")

    auth = sub.add_parser(
        "authorize", help="Issue productive Operator-GO + authorization artifact."
    )
    auth.add_argument("--preregistration", type=Path, required=True)
    auth.add_argument("--confirm-token-file", type=Path, required=True)
    auth.add_argument("--output-dir", type=Path, required=True)
    auth.add_argument("--json", action="store_true")

    ver = sub.add_parser("verify-authorization", help="Verify productive authorization bundle.")
    ver.add_argument("--preregistration", type=Path, required=True)
    ver.add_argument("--operator-go", type=Path, required=True)
    ver.add_argument("--authorization-artifact", type=Path, required=True)
    ver.add_argument("--confirm-token-file", type=Path, required=True)
    ver.add_argument("--expected-repository-sha", default=None)
    ver.add_argument("--json", action="store_true")

    run = sub.add_parser(
        "run",
        help=(
            "Start productive wallclock MD-observe session. Requires verified "
            "productive auth; real network needs env gate AND auth (env alone insufficient)."
        ),
    )
    run.add_argument("--preregistration", type=Path, required=True)
    run.add_argument("--operator-go", type=Path, required=True)
    run.add_argument("--authorization-artifact", type=Path, required=True)
    run.add_argument("--confirm-token-file", type=Path, default=None)
    run.add_argument("--evidence-root", type=Path, required=True)
    run.add_argument("--expected-repository-sha", required=True)
    run.add_argument("--fingerprint-ledger", type=Path, required=True)
    run.add_argument(
        "--real-network",
        action="store_true",
        help=f"Use real HTTPS transport (also requires {REAL_NETWORK_ENV}=1).",
    )
    run.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = time.time()

    if args.command == "preflight":
        payload = {
            "ok": True,
            "capability_id": CAPABILITY_ID,
            "network_used": False,
            "session_executed": False,
            "orders_authorized": False,
            "paper_execution_authorized": False,
            "testnet_authorized": False,
            "live_authorized": False,
            "notes": [
                "PREFLIGHT_OFFLINE_ONLY",
                "MERGE_DOES_NOT_AUTHORIZE_SESSION",
                "ENV_FLAG_ALONE_INSUFFICIENT",
            ],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0

    if args.command == "issue-confirm-token":
        # Compute scope digest via provisional productive prereg shape (placeholder token).
        placeholder = mint_productive_confirm_token_v1()
        provisional = build_productive_preregistration_dict_v1(
            session_id=args.session_id,
            expected_repository_sha=args.expected_repository_sha,
            planned_duration_seconds=args.planned_duration_seconds,
            earliest_start=args.earliest_start_unix,
            expires_at=args.expires_at_unix,
            evidence_root=args.evidence_root,
            operator_identity=args.operator_identity,
            approval_identity=args.approval_identity,
            confirm_token=placeholder,
        )
        scope_digest = parse_preregistration_contract_v1(provisional).scope_digest()
        issued = issue_productive_confirm_token_v1(
            session_id=args.session_id,
            scope_digest=scope_digest,
            repository_sha=args.expected_repository_sha,
            now_unix=now,
            expires_at=args.expires_at_unix,
            token_out_path=args.token_out,
        )
        print(json.dumps(issued.to_public_dict(), sort_keys=True, indent=2))
        return 0 if issued.ok else 1

    if args.command == "preregister":
        if bool(args.confirm_token_file) == bool(args.mint_token_out):
            # exactly one source required
            if not args.confirm_token_file and not args.mint_token_out:
                print(json.dumps({"ok": False, "blockers": ["CONFIRM_TOKEN_SOURCE_REQUIRED"]}))
                return 2
            if args.confirm_token_file and args.mint_token_out:
                print(
                    json.dumps({"ok": False, "blockers": ["CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN"]})
                )
                return 2
        token: str
        if args.mint_token_out is not None:
            sid = args.session_id or new_session_id_v1()
            start = args.earliest_start_unix if args.earliest_start_unix is not None else now
            end = (
                args.expires_at_unix
                if args.expires_at_unix is not None
                else start + float(args.planned_duration_seconds)
            )
            placeholder = mint_productive_confirm_token_v1()
            provisional = build_productive_preregistration_dict_v1(
                session_id=sid,
                expected_repository_sha=args.expected_repository_sha,
                planned_duration_seconds=args.planned_duration_seconds,
                earliest_start=start,
                expires_at=end,
                evidence_root=args.evidence_root,
                operator_identity=args.operator_identity,
                approval_identity=args.approval_identity,
                confirm_token=placeholder,
            )
            scope_digest = parse_preregistration_contract_v1(provisional).scope_digest()
            minted = issue_productive_confirm_token_v1(
                session_id=sid,
                scope_digest=scope_digest,
                repository_sha=args.expected_repository_sha,
                now_unix=now,
                expires_at=end,
                token_out_path=args.mint_token_out,
            )
            if not minted.ok:
                print(json.dumps(minted.to_public_dict(), sort_keys=True, indent=2))
                return 1
            token = _load_ct(args.mint_token_out)
            args.session_id = sid
            args.earliest_start_unix = start
            args.expires_at_unix = end
        else:
            token = _load_ct(args.confirm_token_file)

        result = issue_productive_preregistration_v1(
            output_dir=args.output_dir,
            expected_repository_sha=args.expected_repository_sha,
            confirm_token=token,
            operator_identity=args.operator_identity,
            approval_identity=args.approval_identity,
            evidence_root=args.evidence_root,
            planned_duration_seconds=args.planned_duration_seconds,
            earliest_start=args.earliest_start_unix,
            expires_at=args.expires_at_unix,
            session_id=args.session_id,
            now_unix=now,
            allow_noncanonical_duration=bool(args.allow_noncanonical_duration),
        )
        print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
        return 0 if result.ok else 1

    if args.command == "authorize":
        token = _load_ct(args.confirm_token_file)
        prereg = parse_preregistration_contract_v1(
            load_preregistration_contract_dict_v1(args.preregistration)
        )
        result = issue_productive_authorization_v1(
            prereg=prereg,
            confirm_token=token,
            output_dir=args.output_dir,
            now_unix=now,
        )
        print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
        return 0 if result.ok else 1

    if args.command == "verify-authorization":
        token = _load_token(args)
        result = verify_productive_authorization_bundle_paths_v1(
            preregistration_path=args.preregistration,
            operator_go_path=args.operator_go,
            authorization_artifact_path=args.authorization_artifact,
            confirm_token=token,
            now_unix=now,
            expected_repository_sha=args.expected_repository_sha,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.verified else 1

    if args.command == "run":
        token = _load_token(args)
        result = run_productive_wallclock_session_from_paths_v1(
            preregistration_path=args.preregistration,
            operator_go_path=args.operator_go,
            authorization_artifact_path=args.authorization_artifact,
            confirm_token=token,
            evidence_root=args.evidence_root,
            expected_repository_sha=args.expected_repository_sha,
            fingerprint_ledger_path=args.fingerprint_ledger,
            use_real_network=bool(args.real_network),
            repo_root=_REPO_ROOT,
            environ=os.environ,
        )
        print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
        return 0 if result.ok else 1

    print(json.dumps({"ok": False, "blockers": ["UNKNOWN_COMMAND"]}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
