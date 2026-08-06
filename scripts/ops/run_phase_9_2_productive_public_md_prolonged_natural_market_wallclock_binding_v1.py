#!/usr/bin/env python3
"""CLI for Phase 9.2 prolonged natural-market wallclock binding.

Commands:
  preflight / prove-binding — reuse/authority matrix + parity (no session)
  materialize-evidence      — offline implementation evidence only
  gate                      — Session-GO binding gate evaluation only
  prove-claim-semantics     — offline reconnect/trade claim separation proofs
  prove-disk-bounds         — offline disk preflight + evidence growth bounds
  assemble-session-request  — build session_request kwargs binding (no network)

Confirm tokens: --confirm-token-file | PEAK_TRADE_PSO_CONFIRM_TOKEN | present flag.
Plaintext --confirm-token argv is rejected.
This CLI never starts a network session and never issues/consumes auth/tokens.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.binding_gate_v1 import (  # noqa: E402
    assert_no_parallel_productive_authority_v1,
    evaluate_prolonged_natural_market_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.claims_v1 import (  # noqa: E402
    prove_claim_semantics_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.confirm_token_path_v1 import (  # noqa: E402
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.disk_preflight_v1 import (  # noqa: E402
    prove_disk_and_evidence_bounds_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.parity_v1 import (  # noqa: E402
    prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (  # noqa: E402
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_request_cli_adapter_v1 import (  # noqa: E402
    bind_session_request_to_runner_kwargs_v1,
    build_step5_session_request_v1,
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
            "gate",
            "prove-claim-semantics",
            "prove-disk-bounds",
            "assemble-session-request",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--session-go-file", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--authorization-present", action="store_true")
    p.add_argument("--confirm-token-present", action="store_true")
    p.add_argument("--owner-go", action="store_true")
    p.add_argument("--owner-session-go", action="store_true")
    p.add_argument("--request-real-network", action="store_true")
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--planned-duration-seconds", type=int, default=None)
    p.add_argument("--predecessor-step4-evidence-ref", default="")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argv_blockers = reject_confirm_token_argv_v1(argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.request_real_network and args.command != "gate":
        payload = {
            "ok": False,
            "blockers": ["REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI"],
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
            "network_session_allowed": NETWORK_SESSION_ALLOWED,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    if argv_blockers:
        payload = {
            "ok": False,
            "blockers": argv_blockers,
            "capability_id": CAPABILITY_ID,
            "network_session_started": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    sha = args.expected_repository_sha or _repo_sha()
    cfg = _cfg()

    if args.command in {"preflight", "prove-binding"}:
        parity = prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1()
        authority = assert_no_parallel_productive_authority_v1()
        contract = load_and_validate_session_contract_v1(repo_root=_REPO_ROOT)
        claims = prove_claim_semantics_offline_v1()
        payload = {
            "ok": bool(parity["ok"] and authority["ok"] and claims["ok"]),
            "capability_id": CAPABILITY_ID,
            "session_id": TARGET_SESSION_ID,
            "parity": parity,
            "authority": authority,
            "session_contract_ok": True,
            "session_ladder_step": contract["session_ladder_step"],
            "claim_semantics": claims,
            "network_session_started": False,
            "authorization_issued": False,
            "authorization_consumed": False,
            "confirm_token_issued": False,
            "confirm_token_consumed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload["ok"] else 1

    if args.command == "materialize-evidence":
        summary = materialize_capability_evidence_v1(
            repository_sha=sha,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
        print(json.dumps(summary, sort_keys=True, indent=2))
        return 0 if summary.get("ok") else 1

    if args.command == "gate":
        gate = evaluate_prolonged_natural_market_wallclock_binding_gate_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            now_unix=time.time(),
            owner_go=bool(args.owner_go),
            owner_session_go=bool(args.owner_session_go),
            session_go_path=args.session_go_file,
            authorization_present=bool(args.authorization_present),
            confirm_token_file=args.confirm_token_file,
            confirm_token_present_flag=bool(args.confirm_token_present),
            request_real_network=bool(args.request_real_network),
            argv=argv,
        )
        payload = gate.to_dict()
        payload["capability_id"] = CAPABILITY_ID
        payload["network_session_started"] = False
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if gate.ok else 1

    if args.command == "prove-claim-semantics":
        payload = prove_claim_semantics_offline_v1()
        payload["capability_id"] = CAPABILITY_ID
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "prove-disk-bounds":
        check = args.evidence_root or (_REPO_ROOT / "var" / "tmp" / "step5_disk_check")
        payload = prove_disk_and_evidence_bounds_offline_v1(check_path=Path(check))
        payload["capability_id"] = CAPABILITY_ID
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "assemble-session-request":
        request = build_step5_session_request_v1(
            expected_repository_sha=sha,
            expected_config_digest=cfg,
            planned_session_duration_seconds=(
                args.planned_duration_seconds if args.planned_duration_seconds is not None else 7200
            ),
            predecessor_step4_evidence_ref=args.predecessor_step4_evidence_ref,
        )
        kwargs = bind_session_request_to_runner_kwargs_v1(request)
        payload = {
            "ok": True,
            "capability_id": CAPABILITY_ID,
            "session_request": request,
            "runner_kwargs": kwargs,
            "network_session_started": False,
            "wallclock_runner_invoked": False,
            "authorization_consumed": False,
            "confirm_token_consumed": False,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0

    print(json.dumps({"ok": False, "blockers": ["UNKNOWN_COMMAND"]}, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
