#!/usr/bin/env python3
"""CLI for Phase 9.2 rate-limit/reconnect wallclock binding.

Commands:
  preflight            — reuse/authority matrix + parity (no session)
  materialize-evidence — offline implementation evidence only
  gate                 — Session-GO binding gate evaluation only
  prove-fault-path     — offline deterministic 429/reconnect/stale proofs

Confirm tokens: --confirm-token-file | PEAK_TRADE_PSO_CONFIRM_TOKEN | present flag.
Plaintext --confirm-token argv is rejected.
This capability does not start a real network or fault session.
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
    CAPABILITY_ID,
    TARGET_SESSION_ID,
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
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (  # noqa: E402
    load_and_validate_session_contract_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (  # noqa: E402
    load_activation_config_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=("preflight", "materialize-evidence", "gate", "prove-fault-path"),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--owner-session-go", action="store_true")
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
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
    if args.request_real_network and args.command != "gate":
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

    if args.command == "preflight":
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
            "session_id": TARGET_SESSION_ID,
            "parity": parity,
            "authority_reuse": authority,
            "session_contract_ok": contract_ok,
            "session_contract_gaps": contract_gaps,
            "session_contract_id": (contract or {}).get("session_id"),
            "network_session_started": False,
            "fault_session_started": False,
            "notes": [
                "BINDING_IMPLEMENTED",
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

    # gate
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
