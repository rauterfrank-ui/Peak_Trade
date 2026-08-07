#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-3 governed restart/recovery session execution surface.

Commands:
  preflight / prove-implementation
  assemble-execution-request
  request-real-network          — always fail-closed (no session)
  execute-offline-campaign      — offline PRE→POST only; requires --execute
  verify-manifest
  materialize-implementation-evidence
  failure-injection

Confirm tokens: never via argv plaintext. Env fallback rejected.
This CLI never starts a real network session and never issues productive tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.confirm_token_path_v1 import (  # noqa: E402
    redact_confirm_token_mapping_v1,
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.digest_v1 import (  # noqa: E402
    read_json_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.evidence_v1 import (  # noqa: E402
    materialize_implementation_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.failure_injection_v1 import (  # noqa: E402
    run_step3_surface_failure_injection_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.governed_execution_surface_v1 import (  # noqa: E402
    assemble_execution_request_v1,
    execute_offline_step3_campaign_v1,
    prove_step3_execution_surface_implementation_v1,
    request_real_network_fail_closed_v1,
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
            "prove-implementation",
            "assemble-execution-request",
            "request-real-network",
            "execute-offline-campaign",
            "verify-manifest",
            "materialize-implementation-evidence",
            "failure-injection",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--authorization-artifact", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--operator-authorization-explicit", action="store_true")
    p.add_argument("--network-session-go", action="store_true")
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(raw)
    if argv_blockers:
        payload = {
            "ok": False,
            "blockers": sorted(set(argv_blockers)),
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
            "confirm_token_plaintext_exposed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    args = build_parser().parse_args(raw)

    env_blockers: list[str] = []
    if args.command in {"request-real-network", "execute-offline-campaign"}:
        env_blockers = reject_confirm_token_env_fallback_v1(os.environ)
    if env_blockers:
        payload = {
            "ok": False,
            "blockers": sorted(set(env_blockers)),
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
            "confirm_token_plaintext_exposed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()

    if args.command in {"preflight", "prove-implementation"}:
        result = prove_step3_execution_surface_implementation_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
            environ=os.environ,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.ok else 1

    if args.command == "assemble-execution-request":
        payload = assemble_execution_request_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(redact_confirm_token_mapping_v1(payload), sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "request-real-network":
        result = request_real_network_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            argv=raw,
            environ=os.environ,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 2

    if args.command == "execute-offline-campaign":
        if args.persistence_root is None or args.session_go_file is None:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blockers": ["PERSISTENCE_ROOT_AND_SESSION_GO_REQUIRED"],
                        "capability_id": CAPABILITY_ID,
                    },
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        auth_art = None
        if args.authorization_artifact is not None:
            auth_art = read_json_v1(args.authorization_artifact)
        result = execute_offline_step3_campaign_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            persistence_root=args.persistence_root,
            session_go_path=args.session_go_file,
            now_unix=float(time.time()),
            owner_go=bool(args.owner_go),
            operator_authorization_explicit=bool(args.operator_authorization_explicit),
            network_session_go=bool(args.network_session_go),
            authorization_present=bool(args.authorization_present),
            confirm_token_present=bool(args.confirm_token_present),
            authorization_artifact=auth_art,
            execute=bool(args.execute),
            request_real_network=bool(args.request_real_network),
            argv=raw,
            environ=os.environ,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.ok else 2

    if args.command == "verify-manifest":
        if args.manifest is None:
            print(json.dumps({"ok": False, "blockers": ["MANIFEST_REQUIRED"]}, indent=2))
            return 2
        payload = verify_session_manifest_v1(read_json_v1(args.manifest))
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "materialize-implementation-evidence":
        summary = materialize_implementation_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(redact_confirm_token_mapping_v1(summary), sort_keys=True, indent=2))
        return 0 if summary.get("ok") else 1

    # failure-injection
    fi_root = args.persistence_root or (_REPO_ROOT / "var" / "tmp_step3_surface_fi")
    fi_root.mkdir(parents=True, exist_ok=True)
    fi = run_step3_surface_failure_injection_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        repo_root=_REPO_ROOT,
        persistence_root=fi_root,
    )
    print(json.dumps(fi, sort_keys=True, indent=2))
    return 0 if fi.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
