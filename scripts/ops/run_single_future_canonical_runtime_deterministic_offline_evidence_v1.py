#!/usr/bin/env python3
"""Productive Cap 5.1 deterministic offline evidence entrypoint.

Consumes only local versioned fixtures. No HTTP, WebSocket, exchange credentials,
wallclock decision authority, sleep loops, authorization consumption, or runtime
activation. Reuses Cap 4.1 host/owners + productive bridge.
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

from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.authority_inventory_v1 import (  # noqa: E402
    inventory_offline_evidence_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (  # noqa: E402
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    DEFAULT_FIXTURE_RELPATH,
    OFFLINE_REPLAY_ONLY,
    PRODUCTIVE_RUNTIME_HOST,
    RUNTIME_ACTIVATED,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.evidence_gate_v1 import (  # noqa: E402
    OfflineEvidenceGateError,
    run_single_future_canonical_runtime_deterministic_offline_evidence_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.persistence_v1 import (  # noqa: E402
    persist_offline_evidence_atomic_v1,
    verify_manifest,
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
    parser.add_argument("--session-id", type=str, default="cap51")
    parser.add_argument("--repository-sha", type=str, default=None)
    parser.add_argument("--baseline-sha", type=str, default=None)
    parser.add_argument("--now-unix", type=float, required=True)
    parser.add_argument("--mark-price-json", type=Path, default=None)
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--authorization-artifact-json", type=Path, default=None)
    args = parser.parse_args(argv)

    repository_sha = args.repository_sha or _git_sha()
    baseline_sha = args.baseline_sha or repository_sha
    marks = None
    if args.mark_price_json is not None:
        marks = json.loads(args.mark_price_json.read_text(encoding="utf-8"))
        if not isinstance(marks, dict):
            raise SystemExit("mark-price-json must be an object of venue_native_id -> mark")
    auth_artifact = None
    if args.authorization_artifact_json is not None:
        auth_artifact = json.loads(args.authorization_artifact_json.read_text(encoding="utf-8"))
    lock_root = args.lock_root or (Path(args.evidence_root) / "locks")
    fixture_path = args.fixture_json or (_REPO_ROOT / DEFAULT_FIXTURE_RELPATH)

    try:
        gate = run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
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
            authorization_artifact=auth_artifact,
            fixture_path=fixture_path,
        )
    except OfflineEvidenceGateError as exc:
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
        "OFFLINE_REPLAY_ONLY": OFFLINE_REPLAY_ONLY,
        "PRODUCTIVE_RUNTIME_HOST": PRODUCTIVE_RUNTIME_HOST,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "gate": gate.to_dict(),
        "authority_inventory": inventory_offline_evidence_authority_surfaces_v1(),
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_ACCESS_OCCURRED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
    persist_offline_evidence_atomic_v1(
        evidence_root=args.evidence_root,
        evidence=gate.evidence.to_dict(),
        result=result,
        gate=gate.gate_flags.to_dict(),
        telemetry=gate.evidence.telemetry,
        restart=gate.evidence.restart_recovery,
        failure_injection=gate.evidence.failure_injection_results,
    )
    verify_manifest(args.evidence_root)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if gate.ok and gate.ready_for_activation and not gate.runtime_activated else 2


if __name__ == "__main__":
    raise SystemExit(main())
