#!/usr/bin/env python3
"""Prepare CURRENT productive Enter one-shot E2E handoff (stops before POST)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main() -> int:
    parser = argparse.ArgumentParser(description="One-shot Enter E2E prepare (no POST)")
    parser.add_argument("--post-store-root", type=Path, required=True)
    parser.add_argument("--lane-state-root", type=Path, required=True)
    parser.add_argument("--productivity-root", type=Path, default=None)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--binding-epoch", default=None)
    parser.add_argument("--execute-network", action="store_true")
    parser.add_argument("--vault-file", type=Path, default=None)
    parser.add_argument(
        "--prove-k1-pre-live",
        action="store_true",
        help="Run macOS K1 PRE-POST + pre-live proof (requires Keychain scope)",
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
        K1_OPAQUE_SIGNING_OWNER_GO,
        POST_OWNER_GO,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        OWNER_GO as PRE_EXTERNAL_OWNER_GO,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_shot_enter_e2e_runtime_handoff_v1 import (
        OWNER_GO,
        CurrentProductiveOneShotEnterE2ERuntimeHandoffError,
        prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1,
    )

    try:
        result = prepare_current_productive_one_shot_enter_e2e_runtime_handoff_v1(
            owner_go=OWNER_GO,
            pre_external_owner_go=PRE_EXTERNAL_OWNER_GO,
            post_owner_go=POST_OWNER_GO,
            k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
            productivity_root=args.productivity_root,
            lane_state_root=args.lane_state_root,
            post_durable_store_root=args.post_store_root,
            binding_epoch=args.binding_epoch,
            execute_network=bool(args.execute_network),
            vault_file=args.vault_file,
            evidence_root=args.evidence_root,
            prove_k1_pre_live=bool(args.prove_k1_pre_live),
            use_macos_k1=bool(args.prove_k1_pre_live),
        )
    except CurrentProductiveOneShotEnterE2ERuntimeHandoffError as exc:
        print(f"FAIL_CLOSED:{exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "E2E_RUNTIME_READY": result.e2e_runtime_ready,
                "HANDOFF_STORE_ROOT": result.handoff_store_root,
                "ENVELOPE_JSON_PATH": result.envelope_json_path,
                "POST_DURABLE_STORE_ROOT": result.post_durable_store_root,
                "PRE_LIVE_PROOF_COMPLETE": result.pre_live_proof_complete,
                "FINAL_PRE_LIVE_COMMAND": result.final_pre_live_command,
                "FINAL_OPERATOR_COMMAND": result.final_operator_command,
            },
            sort_keys=True,
        )
    )
    return 0 if result.e2e_runtime_ready == "true" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
