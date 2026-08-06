#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-5 governed prolonged natural-market session execution.

Commands:
  preflight                 — contract digests + implementation proof (no session)
  assemble-execution-request
  request-real-network      — offline fail-closed (no session)
  execute-governed-session  — offline fail-closed without separate Owner-GO
  verify-session            — verify a materialized terminal evidence manifest
  materialize-terminal-evidence
  prove-implementation      — alias of preflight proof path

Binding CLI remains separate and binding-only:
  scripts/ops/run_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.py

Confirm tokens: hidden PTY/stdin getpass only. Plaintext --confirm-token argv
and env fallbacks are rejected. This CLI never issues/consumes auth/tokens and
never starts a real network session under this capability.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (  # noqa: E402
    BINDING_CLI_PATH,
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_PATH,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E402
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (  # noqa: E402
    read_json_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.evidence_v1 import (  # noqa: E402
    materialize_terminal_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (  # noqa: E402
    assemble_execution_request_v1,
    execute_governed_step5_session_v1,
    prove_step5_execution_implementation_v1,
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
            "prove-implementation",
            "assemble-execution-request",
            "request-real-network",
            "execute-governed-session",
            "verify-session",
            "materialize-terminal-evidence",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--authorization-id", default="")
    p.add_argument("--authorization-digest", default="")
    p.add_argument("--confirm-token-binding-sha256", default="")
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--expected-session-contract-digest", default=None)
    p.add_argument("--expected-binding-config-digest", default=None)
    p.add_argument("--planned-duration-seconds", type=int, default=None)
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    import os
    import time

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
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()
    bundle = load_execution_contract_bundle_v1(repo_root=_REPO_ROOT)
    contract_digest = args.expected_session_contract_digest or bundle["session_contract_digest"]
    binding_digest = args.expected_binding_config_digest or bundle["binding_config_digest"]

    if args.command in {"preflight", "prove-implementation"}:
        proof = prove_step5_execution_implementation_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            argv=raw,
        )
        payload = proof.to_dict()
        payload["session_contract_digest"] = bundle["session_contract_digest"]
        payload["binding_config_digest"] = bundle["binding_config_digest"]
        payload["binding_cli_path"] = BINDING_CLI_PATH
        payload["productive_entrypoint"] = PRODUCTIVE_ENTRYPOINT_PATH
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if proof.ok else 1

    if args.command == "assemble-execution-request":
        assembled = assemble_execution_request_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
            planned_session_duration_seconds=(
                args.planned_duration_seconds if args.planned_duration_seconds is not None else 7200
            ),
            authorization_id=args.authorization_id,
            authorization_digest=args.authorization_digest,
            confirm_token_binding_sha256=args.confirm_token_binding_sha256,
        )
        print(json.dumps(assembled, sort_keys=True, indent=2))
        return 0 if assembled.get("ok") else 1

    if args.command == "request-real-network":
        result = request_real_network_offline_fail_closed_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            repo_root=_REPO_ROOT,
        )
        payload = result.to_dict()
        payload["network_session_allowed"] = NETWORK_SESSION_ALLOWED
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    if args.command == "execute-governed-session":
        persistence = args.persistence_root or (
            _REPO_ROOT / "var" / "tmp" / "step5_execution_persistence"
        )
        evidence = args.evidence_root or (_REPO_ROOT / "var" / "tmp" / "step5_execution_evidence")
        result = execute_governed_step5_session_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            expected_session_contract_digest=str(contract_digest),
            expected_binding_config_digest=str(binding_digest),
            authorization_id=args.authorization_id,
            authorization_digest=args.authorization_digest,
            confirm_token_binding_sha256=args.confirm_token_binding_sha256,
            persistence_root=Path(persistence),
            evidence_root=Path(evidence),
            now_unix=time.time(),
            getpass_fn=None,
            argv=raw,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 2

    if args.command == "verify-session":
        if args.manifest is None:
            print(
                json.dumps(
                    {"ok": False, "blockers": ["MANIFEST_PATH_REQUIRED"]},
                    indent=2,
                )
            )
            return 2
        manifest = read_json_v1(Path(args.manifest))
        verified = verify_session_manifest_v1(manifest)
        print(json.dumps(verified, sort_keys=True, indent=2))
        return 0 if verified.get("ok") else 1

    if args.command == "materialize-terminal-evidence":
        summary = materialize_terminal_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(summary, sort_keys=True, indent=2))
        return 0 if summary.get("ok") else 1

    print(json.dumps({"ok": False, "blockers": ["UNKNOWN_COMMAND"]}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
