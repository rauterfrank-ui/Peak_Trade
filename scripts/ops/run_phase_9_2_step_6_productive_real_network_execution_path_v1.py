#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-6 productive Real-Network execution path implementation.

Commands:
  preflight / prove-path           — prove productive path (no session)
  prove-contrast                   — BINDING_EXECUTOR vs PRODUCTIVE_REAL_NETWORK_EXECUTOR
  materialize-evidence             — offline implementation evidence
  prove-failure-injection          — offline gate/fault matrix
  execute-governed-session         — offline fail-closed in this capability

This capability never starts a real Public-MD network session and never mints
or consumes confirm tokens. Binding-only execute-governed-session remains
fail-closed and unchanged.

Later separate Owner-GO Real-TTY session (after merge; not this capability):
  execute-governed-session --owner-go --operator-authorization-explicit \\
    --network-session-go --request-real-network
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

from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.evidence_v1 import (  # noqa: E402
    materialize_productive_execution_path_evidence_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.executor_contrast_v1 import (  # noqa: E402
    prove_binding_vs_productive_executor_contrast_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.failure_injection_v1 import (  # noqa: E402
    run_step6_productive_execution_path_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.productive_executor_v1 import (  # noqa: E402
    invoke_productive_executor_offline_fail_closed_v1,
    prove_productive_real_network_execution_path_v1,
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
            "prove-path",
            "prove-contrast",
            "materialize-evidence",
            "prove-failure-injection",
            "execute-governed-session",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--operator-authorization-explicit", action="store_true")
    p.add_argument("--network-session-go", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--enable-receive-lag", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(raw)
    parser = build_parser()
    args = parser.parse_args(raw)

    env_blockers: list[str] = []
    if args.command == "execute-governed-session":
        env_blockers = reject_confirm_token_env_fallback_v1(os.environ)

    if argv_blockers or env_blockers:
        payload = {
            "ok": False,
            "blockers": sorted(set(argv_blockers + env_blockers)),
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
            "confirm_token_minted": False,
            "confirm_token_consumed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 2

    if NETWORK_SESSION_ALLOWED:
        payload = {
            "ok": False,
            "blockers": ["PERMANENT_NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE"],
            "capability_id": CAPABILITY_ID,
        }
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()

    if args.command in {"preflight", "prove-path"}:
        result = prove_productive_real_network_execution_path_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
            environ=os.environ,
        )
        payload = result.to_dict()
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 0 if result.ok else 1

    if args.command == "prove-contrast":
        payload = prove_binding_vs_productive_executor_contrast_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
        )
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 0 if payload.get("ok") else 1

    if args.command == "materialize-evidence":
        payload = materialize_productive_execution_path_evidence_v1(
            repository_sha=sha,
            config_digest=cfg,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 0 if payload.get("ok") else 1

    if args.command == "prove-failure-injection":
        payload = run_step6_productive_execution_path_failure_injection_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
        )
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        return 0 if payload.get("ok") else 1

    if args.command == "execute-governed-session":
        result = invoke_productive_executor_offline_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            owner_go=bool(args.owner_go),
            operator_authorization_explicit=bool(args.operator_authorization_explicit),
            network_session_go=bool(args.network_session_go),
            authorization_valid=False,
            confirm_token_valid=False,
            enable_receive_lag=bool(args.enable_receive_lag),
            allow_real_network_side_effects=bool(args.request_real_network),
            stdin_isatty=sys.stdin.isatty(),
            argv=raw,
            environ=os.environ,
            repo_root=_REPO_ROOT,
        )
        payload = result.to_dict()
        print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
        # Always non-zero in this capability: no network session is started here.
        return 2

    print(json.dumps({"ok": False, "blockers": ["UNKNOWN_COMMAND"]}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
