#!/usr/bin/env python3
"""CLI for Phase 9.2 rate-limit/reconnect wallclock binding + productive activation.

Commands:
  preflight / prove-binding — reuse/authority matrix + parity (no session)
  materialize-evidence      — offline implementation evidence only
  gate                      — Session-GO binding gate evaluation only
  prove-fault-path          — offline deterministic 429/reconnect/stale proofs
  execute-productive-session
      — without --request-real-network: wiring bind (no runner invoke)
      — with --request-real-network: activation path
        * --permit-canonical-runner-invoke transports explicit Owner Session Permit
        * NETWORK_SESSION_ALLOWED remains false by default (dry / no consume)
        * when issuance artifact paths are provided, builds canonical session_request
          via session_request_cli_adapter_v1 (no mint, no consume)
        * real runner invoke requires network_session_allowed + full gates

Confirm tokens: --confirm-token-file | PEAK_TRADE_PSO_CONFIRM_TOKEN | present flag.
Plaintext --confirm-token argv is rejected.
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

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (  # noqa: E402
    assert_no_parallel_productive_authority_v1,
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (  # noqa: E402
    ACTIVATION_CAPABILITY_ID,
    CAPABILITY_ID,
    CLI_OWNER_SESSION_PERMIT_DEFAULT,
    NETWORK_SESSION_ALLOWED,
    OWNER_PERMIT_WIRING_CAPABILITY_ID,
    SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
    TARGET_SESSION_ID,
    WIRING_CAPABILITY_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (  # noqa: E402
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (  # noqa: E402
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_executor_v1 import (  # noqa: E402
    execute_productive_rate_limit_reconnect_session_activation_v1,
    execute_productive_rate_limit_reconnect_session_wiring_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (  # noqa: E402
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (  # noqa: E402
    load_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_request_cli_adapter_v1 import (  # noqa: E402
    build_canonical_session_request_from_issuance_artifacts_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def _issuance_paths_requested(args: argparse.Namespace) -> bool:
    return any(
        getattr(args, name, None) is not None
        for name in (
            "preregistration",
            "operator_go",
            "authorization_artifact",
            "fingerprint_ledger",
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "preflight",
            "prove-binding",
            "materialize-evidence",
            "gate",
            "prove-fault-path",
            "execute-productive-session",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--persistence-root", type=Path, default=None)
    p.add_argument("--authorization-id", default="")
    p.add_argument("--authorization-digest", default="")
    p.add_argument("--confirm-token-binding-sha256", default="")
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--owner-session-go", action="store_true")
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument(
        "--network-session-allowed",
        action="store_true",
        help="Explicit runtime network-session allow for activation (default false).",
    )
    p.add_argument(
        "--permit-canonical-runner-invoke",
        action="store_true",
        default=CLI_OWNER_SESSION_PERMIT_DEFAULT,
        help=(
            "Explicit Owner Session Permit to bind/invoke the canonical wallclock "
            "runner. Distinct from --owner-go / --owner-session-go / "
            "--network-session-allowed. Default false (fail-closed)."
        ),
    )
    p.add_argument(
        "--preregistration",
        type=Path,
        default=None,
        help="Canonical issuance preregistration.json path (session_request adapter).",
    )
    p.add_argument(
        "--operator-go",
        type=Path,
        default=None,
        help="Canonical issuance operator_go.json path (session_request adapter).",
    )
    p.add_argument(
        "--authorization-artifact",
        type=Path,
        default=None,
        help="Canonical issuance authorization artifact path (session_request adapter).",
    )
    p.add_argument(
        "--fingerprint-ledger",
        type=Path,
        default=None,
        help="Canonical fingerprint ledger path bound for the session (required with adapter).",
    )
    p.add_argument(
        "--execute",
        action="store_true",
        help="Required for execute-productive-session; keeps other commands side-effect free.",
    )
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    argv_blockers = reject_confirm_token_argv_v1(raw_argv)
    if argv_blockers:
        print(json.dumps({"ok": False, "blockers": argv_blockers}, sort_keys=True, indent=2))
        return 2

    args = build_parser().parse_args(raw_argv)
    if args.request_real_network and args.command not in {"gate", "execute-productive-session"}:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blockers": [
                        "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI",
                        "USE_SEPARATE_GOVERNED_SESSION_ORDER_AFTER_BINDING_MERGE",
                    ],
                    "network_session_started": False,
                    "fault_session_started": False,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = str(
        load_activation_config_v1(
            config_path=_REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )

    if args.command in {"preflight", "prove-binding"}:
        parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
        authority = assert_no_parallel_productive_authority_v1()
        try:
            contract = load_and_validate_session_contract_v1(repo_root=_REPO_ROOT)
            contract_ok = True
            contract_gaps: list[str] = []
        except Exception as exc:  # noqa: BLE001
            contract = None
            contract_ok = False
            contract_gaps = [str(exc)]
        payload = {
            "ok": bool(parity.get("ok") and authority.get("ok") and contract_ok),
            "capability_id": CAPABILITY_ID,
            "wiring_capability_id": WIRING_CAPABILITY_ID,
            "activation_capability_id": ACTIVATION_CAPABILITY_ID,
            "owner_permit_wiring_capability_id": OWNER_PERMIT_WIRING_CAPABILITY_ID,
            "session_request_adapter_capability_id": SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
            "session_id": TARGET_SESSION_ID,
            "parity": parity,
            "authority_reuse": authority,
            "session_contract_ok": contract_ok,
            "session_contract_gaps": contract_gaps,
            "session_contract_id": (contract or {}).get("session_id"),
            "network_session_started": False,
            "fault_session_started": False,
            "default_network_session_allowed": NETWORK_SESSION_ALLOWED,
            "cli_owner_session_permit_default": CLI_OWNER_SESSION_PERMIT_DEFAULT,
            "notes": [
                "BINDING_IMPLEMENTED",
                "ACTIVATION_PATH_BOUND",
                "OWNER_SESSION_PERMIT_EXPLICIT_FLAG_BOUND",
                "SESSION_REQUEST_CLI_ADAPTER_BOUND",
                "NO_REAL_NETWORK_SESSION_STARTED",
                "NO_FAULT_SESSION_STARTED",
                "LADDER_STEP_REMAINS_OPEN",
            ],
        }
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload["ok"] else 1

    if args.command == "materialize-evidence":
        summary = materialize_capability_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(redact_mapping_for_logs(summary), sort_keys=True, indent=2))
        return 0 if summary.get("ok") else 1

    if args.command == "prove-fault-path":
        fault = prove_governed_fault_path_offline_v1()
        print(json.dumps(redact_mapping_for_logs(fault), sort_keys=True, indent=2))
        return 0 if fault.get("ok") else 1

    if args.command == "execute-productive-session":
        if args.request_real_network:
            network_allowed = bool(args.network_session_allowed)
            if args.session_go_file is not None and args.session_go_file.is_file():
                try:
                    sgo = load_session_go_authority_v1(args.session_go_file)
                    network_allowed = bool(
                        network_allowed and sgo.network_session_execution_authorized_by_this_go
                    )
                except Exception:  # noqa: BLE001
                    network_allowed = False
            owner_session_permit = bool(args.permit_canonical_runner_invoke)

            session_request = None
            adapter_payload: dict | None = None
            if _issuance_paths_requested(args) or args.confirm_token_file is not None:
                # This capability forbids productive network; adapter always dry.
                if network_allowed:
                    print(
                        json.dumps(
                            {
                                "ok": False,
                                "blockers": [
                                    "SESSION_REQUEST_ADAPTER_CAPABILITY_FORBIDS_NETWORK_SESSION",
                                    "NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE",
                                ],
                                "network_session_started": False,
                                "authorization_consumed": False,
                                "confirm_token_consumed": False,
                                "session_request_adapter_capability_id": (
                                    SESSION_REQUEST_ADAPTER_CAPABILITY_ID
                                ),
                            },
                            sort_keys=True,
                            indent=2,
                        )
                    )
                    return 2
                adapter = build_canonical_session_request_from_issuance_artifacts_v1(
                    preregistration_path=args.preregistration,
                    operator_go_path=args.operator_go,
                    authorization_artifact_path=args.authorization_artifact,
                    confirm_token_file=args.confirm_token_file,
                    fingerprint_ledger_path=args.fingerprint_ledger,
                    expected_repository_sha=str(args.expected_repository_sha)
                    if args.expected_repository_sha
                    else None,
                    evidence_root_override=args.evidence_root,
                    permit_canonical_runner_invoke=owner_session_permit,
                    use_real_network=False,
                    environ=os.environ,
                )
                adapter_payload = adapter.to_dict()
                if not adapter.ok:
                    print(
                        json.dumps(
                            redact_mapping_for_logs(adapter_payload), sort_keys=True, indent=2
                        )
                    )
                    return 2
                session_request = adapter.session_request

            result = execute_productive_rate_limit_reconnect_session_activation_v1(
                expected_repository_sha=sha,
                expected_config_digest=cfg,
                now_unix=float(time.time()),
                owner_go=bool(args.owner_go),
                owner_session_go=bool(args.owner_session_go),
                session_go_path=args.session_go_file,
                authorization_present=bool(args.authorization_present),
                request_real_network=True,
                network_session_allowed=network_allowed,
                confirm_token_file=args.confirm_token_file,
                confirm_token_present_flag=bool(args.confirm_token_present),
                authorization_id=str(args.authorization_id or ""),
                authorization_digest=str(args.authorization_digest or ""),
                confirm_token_binding_sha256=str(args.confirm_token_binding_sha256 or ""),
                persistence_root=args.persistence_root,
                execute=bool(args.execute),
                argv=raw_argv,
                environ=os.environ,
                permit_canonical_runner_invoke=owner_session_permit,
                wallclock_runner=None,
                session_request=session_request,
            )
            out = result.to_dict()
            # Never serialize live session_request (token plaintext / Path objects).
            if out.get("session_request_forwarded") is not None:
                forwarded_keys = sorted(dict(out["session_request_forwarded"]).keys())
                out["session_request_forwarded"] = {
                    "redacted": True,
                    "keys": forwarded_keys,
                    "confirm_token": "[REDACTED]",
                }
            if adapter_payload is not None:
                out["session_request_adapter"] = adapter_payload
                out["session_request_adapter_capability_id"] = SESSION_REQUEST_ADAPTER_CAPABILITY_ID
                out["claims"] = dict(out.get("claims") or {})
                out["claims"].update(dict(adapter_payload.get("claims") or {}))
            print(json.dumps(redact_mapping_for_logs(out), sort_keys=True, indent=2))
            return 0 if result.ok else 2

        result = execute_productive_rate_limit_reconnect_session_wiring_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=float(time.time()),
            owner_go=bool(args.owner_go),
            owner_session_go=bool(args.owner_session_go),
            session_go_path=args.session_go_file,
            authorization_present=bool(args.authorization_present),
            confirm_token_file=args.confirm_token_file,
            confirm_token_present_flag=bool(args.confirm_token_present),
            execute=bool(args.execute),
            allow_real_network=False,
            argv=raw_argv,
            environ=os.environ,
        )
        print(json.dumps(redact_mapping_for_logs(result.to_dict()), sort_keys=True, indent=2))
        return 0 if result.ok else 2

    gate = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=float(time.time()),
        owner_go=bool(args.owner_go),
        owner_session_go=bool(args.owner_session_go),
        session_go_path=args.session_go_file,
        authorization_present=bool(args.authorization_present),
        confirm_token_file=args.confirm_token_file,
        confirm_token_present_flag=bool(args.confirm_token_present),
        request_real_network=bool(args.request_real_network),
        argv=raw_argv,
        environ=os.environ,
    )
    print(json.dumps(redact_mapping_for_logs(gate.to_dict()), sort_keys=True, indent=2))
    return 0 if gate.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
