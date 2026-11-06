#!/usr/bin/env python3
"""Offline assessment CLI for Paper-Shadow Observation Operator-GO / Preregistration.

Read-only by default. Never starts sessions, never contacts OKX, never needs
credentials. Explicitly refuses start/run/execute arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_readiness_producer_v1 import (  # noqa: E402
    produce_paper_shadow_observation_authorization_readiness_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.discovery_v1 import (  # noqa: E402
    discover_session_preregistration_and_operator_go_contract_present_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (  # noqa: E402
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (  # noqa: E402
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.verifier_v1 import (  # noqa: E402
    verify_paper_shadow_observation_authorization_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.readiness_producer_v1 import (  # noqa: E402
    produce_paper_shadow_observation_readiness_v1,
)

_FORBIDDEN_ACTION_ARGS = frozenset(
    {
        "start",
        "run",
        "execute",
        "launch",
        "arm-live",
        "connect",
        "order",
        "trade",
    }
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Assess Paper-Shadow Observation Operator-GO / Session-Preregistration "
            "(offline, no session, no network, no credentials)."
        )
    )
    p.add_argument(
        "--mode",
        choices=("assess", "verify", "discover"),
        default="assess",
        help="Assessment mode (default: assess).",
    )
    p.add_argument("--preregistration", type=Path, default=None)
    p.add_argument("--operator-go", type=Path, default=None)
    p.add_argument("--authorization-artifact", type=Path, default=None)
    p.add_argument(
        "--confirm-token",
        default=None,
        help="Confirm token supplied at runtime only; never persisted by this CLI.",
    )
    p.add_argument("--now-unix", type=float, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--force-pass",
        action="store_true",
        help="Forbidden: rejected by producers.",
    )
    return p


def _refuse_forbidden_argv(argv: list[str]) -> str | None:
    lowered = [a.strip().lstrip("-").lower() for a in argv]
    for item in lowered:
        if item in _FORBIDDEN_ACTION_ARGS:
            return item
        for forbidden in _FORBIDDEN_ACTION_ARGS:
            if item.startswith(forbidden):
                return item
    return None


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    refused = _refuse_forbidden_argv(raw_argv)
    if refused is not None:
        payload = {
            "ok": False,
            "blockers": [f"FORBIDDEN_ACTION_ARG:{refused}"],
            "session_executed": False,
            "network_used": False,
            "notes": ["CLI_REFUSES_START_RUN_EXECUTE"],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    args = build_parser().parse_args(raw_argv)
    discovery = discover_session_preregistration_and_operator_go_contract_present_v1(
        repo_root=_REPO_ROOT
    )
    observation_readiness = produce_paper_shadow_observation_readiness_v1(repo_root=_REPO_ROOT)

    prereg = None
    go = None
    if args.preregistration is not None:
        prereg = parse_preregistration_contract_v1(
            load_preregistration_contract_dict_v1(args.preregistration)
        )
    if args.operator_go is not None:
        go = parse_operator_go_contract_v1(load_operator_go_contract_dict_v1(args.operator_go))

    authz = produce_paper_shadow_observation_authorization_readiness_v1(
        prereg=prereg,
        go=go,
        confirm_token=args.confirm_token,
        now_unix=args.now_unix,
        expected_repository_sha=args.expected_repository_sha,
        force_pass=bool(args.force_pass),
    )
    verified = None
    if args.mode in {"verify", "assess"} and prereg is not None and go is not None:
        verified = verify_paper_shadow_observation_authorization_bundle_v1(
            prereg=prereg,
            go=go,
            artifact_path=args.authorization_artifact,
            confirm_token=args.confirm_token,
            now_unix=args.now_unix,
            expected_repository_sha=args.expected_repository_sha,
            require_artifact=args.authorization_artifact is not None,
        )

    payload = {
        "mode": args.mode,
        "discovery": discovery.to_dict(),
        "observation_readiness": {
            "PAPER_SHADOW_OBSERVATION_READINESS_PASS": (
                observation_readiness.PAPER_SHADOW_OBSERVATION_READINESS_PASS
            ),
            "PAPER_SHADOW_OBSERVATION_AUTHORIZED": (
                observation_readiness.PAPER_SHADOW_OBSERVATION_AUTHORIZED
            ),
            "readiness_blockers": list(observation_readiness.readiness_blockers),
        },
        "authorization_readiness": authz.to_dict(),
        "verification": None if verified is None else verified.to_dict(),
        "session_executed": False,
        "network_used": False,
        "credentials_used": False,
        "orders_created": False,
        "PAPER_SHADOW_OBSERVATION_AUTHORIZED_DEFAULT": False,
    }
    safe = redact_mapping_for_logs(payload)
    if args.json or True:
        print(json.dumps(safe, sort_keys=True, indent=2))
    return 0 if discovery.SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT else 1


if __name__ == "__main__":
    raise SystemExit(main())
