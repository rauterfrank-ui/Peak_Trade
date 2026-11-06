#!/usr/bin/env python3
"""Productive Cap 4.1 pre-activation closure entrypoint.

Reuses Cap 2.4 host + Cap 1.1–3.1 owners to prove the full single-future call
graph offline and emit READY_FOR_ACTIVATION. Does not activate runtime, consume
authorization, start a network trading session, or mutate core decision logic.
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

from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.authority_inventory_v1 import (  # noqa: E402
    inventory_pre_activation_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (  # noqa: E402
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    PRODUCTIVE_RUNTIME_HOST,
    RUNTIME_ACTIVATED,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.persistence_v1 import (  # noqa: E402
    persist_pre_activation_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.pre_activation_gate_v1 import (  # noqa: E402
    PreActivationGateError,
    run_single_future_canonical_runtime_pre_activation_closure_v1,
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
    parser.add_argument("--accounting-state-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--lock-root", type=Path, default=None)
    parser.add_argument("--session-id", type=str, default="cap41")
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument("--baseline-sha", type=str, default=None)
    parser.add_argument("--now-unix", type=float, required=True)
    parser.add_argument("--mark-price-json", type=Path, required=True)
    parser.add_argument("--mid-prices", type=str, default="100.5,101.0,101.5,102.0")
    parser.add_argument("--authorization-artifact-json", type=Path, default=None)
    args = parser.parse_args(argv)

    repository_sha = args.repository_sha or _git_sha()
    baseline_sha = args.baseline_sha or repository_sha
    marks = json.loads(args.mark_price_json.read_text(encoding="utf-8"))
    if not isinstance(marks, dict):
        raise SystemExit("mark-price-json must be an object of venue_native_id -> mark")
    mids = [float(x.strip()) for x in str(args.mid_prices).split(",") if x.strip()]
    auth_artifact = None
    if args.authorization_artifact_json is not None:
        auth_artifact = json.loads(args.authorization_artifact_json.read_text(encoding="utf-8"))
    lock_root = args.lock_root or (Path(args.evidence_root) / "locks")

    try:
        gate = run_single_future_canonical_runtime_pre_activation_closure_v1(
            selection_state_root=args.selection_state_root,
            ranking_state_root=args.ranking_state_root,
            universe_state_root=args.universe_state_root,
            reconciliation_state_root=args.reconciliation_state_root,
            accounting_state_root=args.accounting_state_root,
            evidence_root=args.evidence_root,
            lock_root=lock_root,
            repository_sha=repository_sha,
            baseline_sha=baseline_sha,
            session_id=args.session_id,
            now_unix=float(args.now_unix),
            mark_price_by_native_id=marks,
            mid_prices=mids,
            authorization_artifact=auth_artifact,
        )
    except PreActivationGateError as exc:
        print(
            json.dumps({"ok": False, "error": str(exc), "capability_id": CAPABILITY_ID}, indent=2)
        )
        return 2

    result = {
        "ok": gate.ok,
        "capability_id": CAPABILITY_ID,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE": CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS_AFTER": gate.status,
        "READY_FOR_ACTIVATION": gate.ready_for_activation,
        "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
        "PRODUCTIVE_RUNTIME_HOST": PRODUCTIVE_RUNTIME_HOST,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "gate": gate.to_dict(),
        "authority_inventory": inventory_pre_activation_authority_surfaces_v1(),
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
    persist_pre_activation_evidence_atomic_v1(
        evidence_root=args.evidence_root,
        evidence=gate.evidence.to_dict(),
        result=result,
        gate=gate.gate_flags.to_dict(),
    )
    verify_manifest(args.evidence_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if gate.ok and gate.ready_for_activation and not gate.runtime_activated else 2


if __name__ == "__main__":
    raise SystemExit(main())
