#!/usr/bin/env python3
"""PRODUCTIVE Full-Core PRE_EXTERNAL closure (Cap-2.4 → envelope, no POST)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Full-Core PRE_EXTERNAL closure v1")
    parser.add_argument(
        "--owner-go",
        default="OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1",
    )
    parser.add_argument("--productivity-root", type=Path, default=None)
    parser.add_argument("--lane-state-root", type=Path, required=True)
    parser.add_argument("--binding-epoch", default=None)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--execute-network", action="store_true")
    parser.add_argument("--vault-file", type=Path, default=None)
    args = parser.parse_args()

    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
        default_current_productive_cap24_runtime_state_root_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
        GitCurrentProductive29PRuntimeIntegrityBackendV1,
        assert_current_productive_29p_execution_identity_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
        execute_current_productive_full_core_pre_external_closure_v1,
    )

    backend = GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=REPO_ROOT)
    origin_sha = backend.resolve_origin_main_sha_v1()
    assert_current_productive_29p_execution_identity_v1(
        declared_origin_main_sha=origin_sha,
        integrity_backend=backend,
    )
    prod = args.productivity_root or default_current_productive_cap24_runtime_state_root_v1()
    epoch = args.binding_epoch
    if epoch is None:
        from datetime import datetime, timezone

        epoch = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=prod,
        repository_sha=origin_sha,
        binding_epoch=epoch,
    )
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=args.owner_go,
        origin_main_sha=origin_sha,
        bound_instrument=handoff.bound_instrument,
        lane_state_root=args.lane_state_root,
        execute_network=bool(args.execute_network),
        vault_file=args.vault_file,
        evidence_root=args.evidence_root,
        execution_integrity_backend=backend,
    )
    out = {
        "store_root": result.store_root,
        "terminal_disposition": result.terminal_disposition,
        "earliest_remaining_blocker": result.earliest_remaining_blocker,
        "envelope_readiness": result.envelope_readiness,
        "pre_external_effect_boundary_reached": result.pre_external_effect_boundary_reached,
        "final_order_envelope_json": str(Path(result.store_root) / "FINAL_ORDER_ENVELOPE.json"),
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if result.terminal_disposition == "PRE_EXTERNAL_EFFECT" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
