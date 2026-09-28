#!/usr/bin/env python3
"""Preflight-only entry for persistent Natural-ENTER convergence (no S6 execution)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="CURRENT persistent Natural-ENTER convergence preflight (no runtime execution)"
    )
    parser.add_argument("--productivity-root", type=Path, required=True)
    parser.add_argument("--lane-state-root", type=Path, required=True)
    parser.add_argument("--authorization-native-id", required=True)
    parser.add_argument("--binding-epoch", required=True)
    parser.add_argument("--post-durable-store", type=Path, default=None)
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        CONTINUOUS_RUN_AUTHORIZED,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        adjudicate_existing_owner_go_reuse_read_only_v1,
        assert_productive_execution_forbidden_v1,
        preflight_current_productive_persistent_natural_enter_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
        GitCurrentProductive29PRuntimeIntegrityBackendV1,
    )

    assert_productive_execution_forbidden_v1()
    backend = GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=REPO_ROOT)
    origin_sha = backend.resolve_origin_main_sha_v1()
    pre = preflight_current_productive_persistent_natural_enter_v1(
        productivity_root=args.productivity_root,
        lane_state_root=args.lane_state_root,
        repository_sha=origin_sha,
        binding_epoch=args.binding_epoch,
        authorization_native_id=args.authorization_native_id,
    )
    owner_go = adjudicate_existing_owner_go_reuse_read_only_v1(
        post_durable_store_root=args.post_durable_store,
    )
    out = {
        "origin_main_sha": origin_sha,
        "continuous_run_authorized": CONTINUOUS_RUN_AUTHORIZED,
        "preflight_ok": pre.ok,
        "preflight_reason_code": pre.reason_code,
        "lane_state_root": pre.lane_state_root,
        "cursor_store_root": pre.cursor_store_root,
        "native_id": pre.native_id,
        "selection_id": pre.selection_id,
        "existing_owner_go_reuse_status": owner_go.status,
        "post_owner_go_consumed": owner_go.post_owner_go_consumed,
        "productive_runtime_executed": False,
        "external_io_performed": False,
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if pre.ok else 2


if __name__ == "__main__":
    raise SystemExit(_main())
