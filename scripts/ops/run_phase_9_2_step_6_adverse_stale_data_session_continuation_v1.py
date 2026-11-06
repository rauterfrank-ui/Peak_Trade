#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-6 adverse/stale-data session continuation binding.

Commands:
  preflight / prove-binding — reuse/authority/parity (no session)
  materialize-evidence      — offline implementation evidence only
  wire-executor             — productive executor wiring proof (no network)
  prove-fault-path          — offline adverse/stale fault proofs
  prove-network-boundary    — public-MD-only boundary negatives

This CLI never starts a network session and never issues/consumes auth/tokens.
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

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.fault_path_v1 import (  # noqa: E402
    prove_governed_adverse_stale_fault_path_offline_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.network_boundary_v1 import (  # noqa: E402
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.parity_v1 import (  # noqa: E402
    assert_no_parallel_productive_authority_v1,
    prove_phase92_step6_adverse_stale_continuation_parity_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1 import (  # noqa: E402
    run_step6_productive_executor_wiring_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_contract_v1 import (  # noqa: E402
    load_and_validate_session_contract_v1,
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
            "wire-executor",
            "prove-fault-path",
            "prove-network-boundary",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.request_real_network:
        payload = {
            "ok": False,
            "blockers": ["REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI"],
            "capability_id": CAPABILITY_ID,
            "NETWORK_SESSION_ALLOWED": NETWORK_SESSION_ALLOWED,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    if args.command in {"preflight", "prove-binding"}:
        contract = load_and_validate_session_contract_v1(repo_root=_REPO_ROOT)
        parity = prove_phase92_step6_adverse_stale_continuation_parity_v1()
        authority = assert_no_parallel_productive_authority_v1()
        payload = {
            "ok": bool(parity["ok"] and authority["ok"]),
            "capability_id": CAPABILITY_ID,
            "target_session_id": TARGET_SESSION_ID,
            "session_ladder_step": contract.get("session_ladder_step"),
            "parity": parity,
            "authority": authority,
            "NETWORK_SESSION_STARTED": False,
        }
    elif args.command == "materialize-evidence":
        payload = materialize_capability_evidence_v1(
            repository_sha=_repo_sha(),
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
    elif args.command == "wire-executor":
        result = run_step6_productive_executor_wiring_v1(
            repository_sha=_repo_sha(),
            config_digest=_cfg(),
            request_real_network=False,
            owner_go=True,
        )
        payload = result.to_dict()
    elif args.command == "prove-fault-path":
        payload = prove_governed_adverse_stale_fault_path_offline_v1()
    else:
        payload = prove_public_md_network_boundary_v1()

    print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
