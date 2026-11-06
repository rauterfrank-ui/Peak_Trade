#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-3 governed restart/recovery session executor.

Commands:
  preflight / prove-implementation
  assemble-execution-request
  request-real-network          — always fail-closed (no session)
  execute-governed-session      — offline fail-closed without separate Owner session GO flags
  verify-session
  materialize-implementation-evidence
  failure-injection

Surface CLI remains separate and fail-closed for real network:
  scripts/ops/run_phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.py

Confirm tokens: hidden PTY/stdin getpass only. Plaintext --confirm-token argv
and env fallbacks are rejected. This CLI never issues production auth/tokens
and never starts a real network session under permanent constants.
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

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SURFACE_CLI_PATH,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.contract_bindings_v1 import (  # noqa: E402
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (  # noqa: E402
    read_json_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.evidence_v1 import (  # noqa: E402
    materialize_implementation_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.failure_injection_v1 import (  # noqa: E402
    run_step3_executor_failure_injection_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.governed_executor_execution_v1 import (  # noqa: E402
    assemble_execution_request_v1,
    execute_governed_step3_executor_session_v1,
    prove_step3_executor_implementation_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.hidden_pty_handoff_v1 import (  # noqa: E402
    redact_confirm_token_mapping_v1,
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
            "execute-governed-session",
            "verify-session",
            "materialize-implementation-evidence",
            "failure-injection",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--authorization-id", default="")
    p.add_argument("--authorization-digest", default="")
    p.add_argument("--confirm-token-binding-sha256", default="")
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--expected-session-contract-digest", default=None)
    p.add_argument("--expected-binding-config-digest", default=None)
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(raw)
    args = build_parser().parse_args(raw)

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
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()
    bundle = load_execution_contract_bundle_v1(repo_root=_REPO_ROOT)

    if args.command in {"preflight", "prove-implementation"}:
        result = prove_step3_executor_implementation_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
            environ=os.environ,
        )
        payload = result.to_dict()
        payload["surface_cli_path"] = SURFACE_CLI_PATH
        payload["productive_entrypoint"] = PRODUCTIVE_ENTRYPOINT_PATH
        payload["session_contract_digest"] = bundle["session_contract_digest"]
        payload["binding_config_digest"] = bundle["binding_config_digest"]
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if result.ok else 1

    if args.command == "assemble-execution-request":
        payload = assemble_execution_request_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            authorization_id=args.authorization_id,
            authorization_digest=args.authorization_digest,
            confirm_token_binding_sha256=args.confirm_token_binding_sha256,
        )
        print(json.dumps(redact_confirm_token_mapping_v1(payload), sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "request-real-network":
        result = request_real_network_offline_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 2

    if args.command == "execute-governed-session":
        # Default: fail-closed without ephemeral GO consume/real network.
        # Persistence/session-go optional for gate-only fail-closed path.
        persistence = args.persistence_root or (_REPO_ROOT / "var" / "tmp_step3_executor")
        persistence.mkdir(parents=True, exist_ok=True)
        evidence = args.evidence_root or (persistence / "evidence")
        sgo = args.session_go_file or (persistence / "missing_session_go.json")
        result = execute_governed_step3_executor_session_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_session_contract_digest=(
                args.expected_session_contract_digest or bundle["session_contract_digest"]
            ),
            expected_binding_config_digest=(
                args.expected_binding_config_digest or bundle["binding_config_digest"]
            ),
            authorization_id=args.authorization_id,
            authorization_digest=args.authorization_digest,
            confirm_token_binding_sha256=args.confirm_token_binding_sha256,
            persistence_root=persistence,
            evidence_root=evidence,
            session_go_path=sgo,
            now_unix=float(time.time()),
            owner_go=False,
            operator_authorization_explicit=False,
            network_session_go=False,
            invoke_executor=False,
            allow_real_network_side_effects=False,
            argv=raw,
            environ=os.environ,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 2

    if args.command == "verify-session":
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

    fi_root = args.persistence_root or (_REPO_ROOT / "var" / "tmp_step3_executor_fi")
    fi_root.mkdir(parents=True, exist_ok=True)
    fi = run_step3_executor_failure_injection_v1(
        repository_sha=sha,
        config_digest=cfg,
        persistence_root=fi_root,
        repo_root=_REPO_ROOT,
    )
    print(json.dumps(fi, sort_keys=True, indent=2))
    return 0 if fi.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
