#!/usr/bin/env python3
"""CLI for Paper-Shadow wallclock MD-observe capability.

preflight / verify-evidence: offline only.
run: delegates to productive successor path
  INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1
  — requires verified productive (non-fixture) authorization; real network additionally
  requires PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1 (never sufficient alone).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (  # noqa: E402
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CONFIRM_TOKEN_ENV,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (  # noqa: E402
    preflight_wallclock_session_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E402,E501
    REAL_NETWORK_ENV,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (  # noqa: E402,E501
    load_confirm_token_from_file_v1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E402,E501
    run_productive_wallclock_session_from_paths_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Paper-Shadow wallclock observation CLI. "
            "run requires productive non-fixture authorization; "
            f"real network also requires {REAL_NETWORK_ENV}=1 (never alone). "
            "No orders/paper/testnet/live/credentials."
        )
    )
    p.add_argument("command", choices=("preflight", "verify-evidence", "run"))
    p.add_argument("--preregistration", type=Path, default=None)
    p.add_argument("--operator-go", type=Path, default=None)
    p.add_argument("--authorization-artifact", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--fingerprint-ledger", type=Path, default=None)
    p.add_argument(
        "--real-network",
        action="store_true",
        help=f"Open real public MD transport after consumption (requires {REAL_NETWORK_ENV}=1).",
    )
    p.add_argument("--json", action="store_true")
    return p


def _load_confirm_token(args: argparse.Namespace) -> str:
    env_token = os.environ.get(CONFIRM_TOKEN_ENV, "").strip()
    if env_token and args.confirm_token_file is not None:
        raise SystemExit("CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN")
    if env_token:
        return env_token
    if args.confirm_token_file is not None:
        return load_confirm_token_from_file_v1(args.confirm_token_file)
    raise SystemExit("CONFIRM_TOKEN_SOURCE_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        payload = preflight_wallclock_session_v1(repo_root=_REPO_ROOT)
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "verify-evidence":
        if args.evidence_root is None:
            print(json.dumps({"ok": False, "blockers": ["EVIDENCE_ROOT_REQUIRED"]}))
            return 2
        result = verify_wallclock_evidence_bundle_v1(evidence_root=args.evidence_root)
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.verified else 1

    # run — productive successor path (fixtures rejected; env alone insufficient).
    missing = []
    for name, val in (
        ("preregistration", args.preregistration),
        ("operator-go", args.operator_go),
        ("authorization-artifact", args.authorization_artifact),
        ("evidence-root", args.evidence_root),
        ("expected-repository-sha", args.expected_repository_sha),
        ("fingerprint-ledger", args.fingerprint_ledger),
    ):
        if val is None:
            missing.append(name)
    try:
        token = _load_confirm_token(args)
    except SystemExit as exc:
        missing.append(str(exc))
        token = ""
    if missing:
        payload = {
            "ok": False,
            "blockers": [f"MISSING_ARG:{m}" for m in missing],
            "capability_id": CAPABILITY_ID,
            "network_used": False,
            "session_executed": False,
            "notes": [
                "PRODUCTIVE_RUN_REQUIRES_FULL_AUTH_BUNDLE",
                "FIXTURE_AUTH_REJECTED",
                f"ENV_FLAG_ALONE_INSUFFICIENT ({REAL_NETWORK_ENV})",
            ],
        }
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 2

    result = run_productive_wallclock_session_from_paths_v1(
        preregistration_path=args.preregistration,
        operator_go_path=args.operator_go,
        authorization_artifact_path=args.authorization_artifact,
        confirm_token=token,
        evidence_root=args.evidence_root,
        expected_repository_sha=str(args.expected_repository_sha),
        fingerprint_ledger_path=args.fingerprint_ledger,
        use_real_network=bool(args.real_network),
        repo_root=_REPO_ROOT,
        environ=os.environ,
    )
    print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
