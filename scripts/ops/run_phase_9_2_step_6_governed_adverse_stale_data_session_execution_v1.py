#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-6 governed adverse/stale session execution binding.

Commands:
  preflight / prove-binding     — binding proof only (no session)
  materialize-evidence          — offline implementation evidence
  prove-failure-injection       — offline gate/fault matrix
  request-real-network          — offline fail-closed
  execute-governed-session      — offline fail-closed without full ephemeral GO+TTY

Permanent NETWORK_SESSION_ALLOWED remains false. This CLI never starts a real
Public-MD network session and never consumes authorization/confirm tokens for
side effects.

Later separate Owner-GO session (real TTY required):
  execute-governed-session --owner-go --operator-authorization-explicit \\
    --network-session-allowed --request-real-network
  Confirm token: hidden PTY/stdin getpass only (no argv/env/file plaintext).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.evidence_v1 import (  # noqa: E402
    materialize_execution_binding_evidence_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.failure_injection_v1 import (  # noqa: E402
    run_step6_execution_binding_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.governed_session_execution_v1 import (  # noqa: E402
    execute_governed_step6_session_offline_fail_closed_v1,
    prove_step6_execution_binding_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "preflight",
            "prove-binding",
            "materialize-evidence",
            "prove-failure-injection",
            "request-real-network",
            "execute-governed-session",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--authorization-id", default="")
    p.add_argument("--authorization-digest", default="")
    p.add_argument("--confirm-token-binding-sha256", default="")
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--operator-authorization-explicit", action="store_true")
    p.add_argument("--network-session-allowed", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(raw)
    parser = build_parser()
    args = parser.parse_args(raw)

    env_blockers: list[str] = []
    if args.command in {"request-real-network", "execute-governed-session"}:
        env_blockers = reject_confirm_token_env_fallback_v1(os.environ)

    if argv_blockers or env_blockers:
        payload = {
            "ok": False,
            "blockers": sorted(set(argv_blockers + env_blockers)),
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
            "confirm_token_plaintext_exposed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()

    if args.command in {"preflight", "prove-binding"}:
        result = prove_step6_execution_binding_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
            environ=os.environ,
        )
        payload = result.to_dict()
    elif args.command == "materialize-evidence":
        payload = materialize_execution_binding_evidence_v1(
            repository_sha=sha,
            config_digest=cfg,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
    elif args.command == "prove-failure-injection":
        payload = run_step6_execution_binding_failure_injection_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
        )
    elif args.command == "request-real-network":
        result = request_real_network_offline_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            owner_go=bool(args.owner_go),
            operator_authorization_explicit=bool(args.operator_authorization_explicit),
            network_session_allowed=bool(args.network_session_allowed),
            stdin_isatty=sys.stdin.isatty(),
        )
        payload = result.to_dict()
        payload["NETWORK_SESSION_ALLOWED_CONSTANT"] = NETWORK_SESSION_ALLOWED
    else:
        result = execute_governed_step6_session_offline_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            authorization_id=args.authorization_id,
            authorization_digest=args.authorization_digest,
            confirm_token_binding_sha256=args.confirm_token_binding_sha256,
            owner_go=bool(args.owner_go),
            operator_authorization_explicit=bool(args.operator_authorization_explicit),
            network_session_allowed=bool(args.network_session_allowed),
            allow_real_network_side_effects=bool(args.request_real_network),
            stdin_isatty=sys.stdin.isatty(),
            argv=raw,
            environ=os.environ,
            repo_root=_REPO_ROOT,
        )
        payload = result.to_dict()

    print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
