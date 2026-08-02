#!/usr/bin/env python3
"""Productive entrypoint for CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1.

Consumes Cap 2.3 persisted selection + Cap 2.2 ranking + Cap 2.1 universe roots,
binds the venue-native instrument, runs Cap 1.1 reconciliation before alpha, and
optionally exercises the analytical wallclock no-order bridge. No network trading
session, no order path, no runtime activation.
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

from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (  # noqa: E402
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_runtime_binding_v1.authority_inventory_v1 import (  # noqa: E402
    inventory_instrument_authority_surfaces_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (  # noqa: E402
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (  # noqa: E402
    CALL_GRAPH,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
)
from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (  # noqa: E402
    persist_binding_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (  # noqa: E402
    run_bridge_cycles_from_mids_v1,
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=CAPABILITY_ID)
    parser.add_argument("--selection-state-root", required=True, type=Path)
    parser.add_argument("--ranking-state-root", required=True, type=Path)
    parser.add_argument("--universe-state-root", required=True, type=Path)
    parser.add_argument("--reconciliation-state-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--session-id", type=str, default="cap24")
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument("--now-unix", type=float, required=True)
    parser.add_argument("--mark-price-json", type=Path, required=True)
    parser.add_argument("--run-bridge-cycles", type=int, default=0)
    parser.add_argument("--mid-price", type=float, default=100.5)
    parser.add_argument("--expected-selection-config-digest", type=str, default=None)
    args = parser.parse_args(argv)

    repository_sha = args.repository_sha or _git_sha()
    marks = json.loads(args.mark_price_json.read_text(encoding="utf-8"))
    if not isinstance(marks, dict):
        raise SystemExit("mark-price-json must be an object of venue_native_id -> mark")

    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=float(args.now_unix),
        wall_time_unix=float(args.now_unix),
        source_id="analytical_execution_state",
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=args.selection_state_root,
        ranking_state_root=args.ranking_state_root,
        universe_state_root=args.universe_state_root,
        repository_sha=repository_sha,
        session_id=args.session_id,
        now_unix=float(args.now_unix),
        reconciliation_state_root=args.reconciliation_state_root,
        observed_portfolio=observed,
        mark_price_by_native_id=marks,
        expected_selection_config_digest=args.expected_selection_config_digest,
        dashboard_available=False,
        dashboard_selected_instrument="CONFLICTING-DASHBOARD-INSTRUMENT",
    )

    bridge_cycles: list[dict] = []
    if args.run_bridge_cycles > 0 and gate.alpha_enabled and gate.bound is not None:
        mids = [float(args.mid_price) + (0.1 * i) for i in range(int(args.run_bridge_cycles))]
        _state, cycles = run_bridge_cycles_from_mids_v1(
            mids,
            start_ts_unix=float(args.now_unix),
            session_id=args.session_id + "-bridge",
            repository_sha=repository_sha,
            reconciliation_state_root=args.reconciliation_state_root,
            selection_state_root=args.selection_state_root,
            ranking_state_root=args.ranking_state_root,
            universe_state_root=args.universe_state_root,
            mark_price_by_native_id=marks,
            require_selection_binding=True,
        )
        bridge_cycles = [c.to_dict() for c in cycles]

    result = {
        "ok": gate.ok,
        "capability_id": CAPABILITY_ID,
        "gate": gate.to_dict(),
        "bridge_cycles": bridge_cycles,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH),
        "authority_inventory": inventory_instrument_authority_surfaces_v1(),
        "CORE_LOGIC_CHANGE": False,
        "DASHBOARD_AUTHORITY_EFFECT": False,
        "ALLOWLIST_SELECTION_AUTHORITY": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
    persist_binding_evidence_atomic_v1(
        evidence_root=args.evidence_root,
        evidence=gate.evidence.to_dict(),
        result=result,
    )
    verify_manifest(args.evidence_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if gate.ok and gate.alpha_enabled else 2


if __name__ == "__main__":
    raise SystemExit(main())
