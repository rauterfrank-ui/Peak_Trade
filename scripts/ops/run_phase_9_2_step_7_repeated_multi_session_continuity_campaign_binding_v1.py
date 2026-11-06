#!/usr/bin/env python3
"""CLI for Phase 9.2 Step-7 multi-session continuity campaign binding.

Commands:
  preflight / prove-binding — reuse/authority/parity (no session)
  materialize-evidence      — offline implementation evidence only
  wire-harness              — campaign harness binding proof (no network)
  verify-bundle             — read-only campaign bundle verification

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

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_bundle_v1 import (  # noqa: E402
    aggregate_completed_sessions_read_only_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (  # noqa: E402
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_state_contract_v1 import (  # noqa: E402
    load_and_validate_campaign_state_contract_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_verifier_v1 import (  # noqa: E402
    verify_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    NETWORK_SESSION_ALLOWED,
    TARGET_CAMPAIGN_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.evidence_v1 import (  # noqa: E402
    materialize_capability_evidence_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (  # noqa: E402
    assert_no_parallel_campaign_authority_v1,
    prove_phase92_step7_campaign_binding_parity_v1,
    prove_step7_reuse_bindings_v1,
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
            "wire-harness",
            "verify-bundle",
        ),
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--session-evidence", type=Path, action="append", default=[])
    p.add_argument("--expected-repository-sha", type=str, default="")
    p.add_argument("--expected-config-digest", type=str, default="")
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
        contract = load_and_validate_campaign_state_contract_v1(repo_root=_REPO_ROOT)
        parity = prove_phase92_step7_campaign_binding_parity_v1()
        reuse = prove_step7_reuse_bindings_v1()
        authority = assert_no_parallel_campaign_authority_v1()
        payload = {
            "ok": bool(parity["ok"] and reuse["ok"] and authority["ok"]),
            "capability_id": CAPABILITY_ID,
            "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
            "session_ladder_step": contract.get("session_ladder_step"),
            "multi_session_requirement": contract.get("multi_session_requirement"),
            "parity": parity,
            "reuse": reuse,
            "authority": authority,
            "NETWORK_SESSION_STARTED": False,
            "PHASE_9_2_STEP_7_STATUS": "OPEN",
            "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        }
    elif args.command == "materialize-evidence":
        payload = materialize_capability_evidence_v1(
            repository_sha=_repo_sha(),
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )
    elif args.command == "wire-harness":
        payload = run_step7_campaign_harness_binding_v1(
            repository_sha=_repo_sha(),
            config_digest=_cfg(),
            request_real_network=False,
            owner_go=True,
            repo_root=_REPO_ROOT,
        )
    else:
        if not args.session_evidence:
            payload = {
                "ok": False,
                "blockers": ["SESSION_EVIDENCE_PATHS_REQUIRED"],
                "capability_id": CAPABILITY_ID,
            }
            print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
            return 1
        bundle = aggregate_completed_sessions_read_only_v1(
            session_evidence_paths=args.session_evidence,
            expected_repository_sha=args.expected_repository_sha or _repo_sha(),
            expected_config_digest=args.expected_config_digest or _cfg(),
        )
        payload = {
            "bundle": bundle,
            "verifier": verify_campaign_bundle_v1(bundle),
            "ok": bool(verify_campaign_bundle_v1(bundle).get("ok")),
            "NETWORK_SESSION_STARTED": False,
        }
        payload["ok"] = bool(payload["verifier"].get("ok"))

    print(json.dumps(payload, sort_keys=True, indent=2 if args.json else None))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
