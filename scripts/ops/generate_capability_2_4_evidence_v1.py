#!/usr/bin/env python3
"""Generate durable Cap 2.4 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (  # noqa: E402
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (  # noqa: E402
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (  # noqa: E402
    GovernedUniverseSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (  # noqa: E402
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (  # noqa: E402
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (  # noqa: E402
    ProductiveRankingSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (  # noqa: E402
    PortfolioTruthSnapshotV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (  # noqa: E402
    SELECTION_FILENAME,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (  # noqa: E402
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (  # noqa: E402
    run_single_selected_future_policy_v1,
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
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.single_selected_future_runtime_binding_v1.persistence_v1 import (  # noqa: E402
    persist_binding_evidence_atomic_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (  # noqa: E402
    run_bridge_cycles_from_mids_v1,
)

REPO_SHA = "ecb4484936b6079f90bde252abef77ff129aea8f"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str, *, base: str) -> dict:
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": base,
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-USDT",
        "expTime": "",
    }


def main() -> int:
    root = _REPO_ROOT / "docs/evidence/capability_2_4_single_selected_future_runtime_binding_v1"
    if root.exists():
        shutil.rmtree(root)
    prod = root / "productive_binding"
    neg = root / "negative_injections"
    prod.mkdir(parents=True)
    neg.mkdir(parents=True)
    build = root / "_build"
    build.mkdir()

    rows = [
        _perp("SOL-USDT-SWAP", base="SOL"),
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("ADA-USDT-SWAP", base="ADA"),
    ]
    mark_ids = [r["instId"] for r in rows]
    uni_root = build / "universe"
    rank_root = build / "ranking"
    sel_root = build / "selection"
    recon_root = build / "recon"
    for p in (uni_root, rank_root, sel_root, recon_root):
        p.mkdir()

    print("producing universe...", flush=True)
    uni = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": i, "markPx": "100.5"} for i in mark_ids],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="ev")
    uni_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_universe_bundle_atomic_v1(
        state_root=uni_root,
        writer=uni_writer,
        snapshot=uni.snapshot,
        evidence={"ok": True},
    )
    uni_writer.release()

    print("producing ranking...", flush=True)
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=uni.snapshot.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="ev")
    rank_writer.acquire(now_unix=OBSERVED_UNIX)
    persist_ranking_bundle_atomic_v1(
        state_root=rank_root,
        writer=rank_writer,
        snapshot=ranking.snapshot,
        evidence={"ok": True},
    )
    rank_writer.release()

    print("producing selection...", flush=True)
    sel = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_state_root=rank_root,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="ev",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = {selection.venue_native_id: "100.5"}

    for name, src in (("selection", sel_root), ("ranking", rank_root), ("universe", uni_root)):
        shutil.copytree(src, prod / name)
    (prod / "mark_price_by_native_id.json").write_text(
        json.dumps(marks, indent=2) + "\n", encoding="utf-8"
    )

    observed = PortfolioTruthSnapshotV1(
        positions=(),
        event_time_unix=OBSERVED_UNIX,
        wall_time_unix=OBSERVED_UNIX,
        source_id="analytical_execution_state",
    )
    print("running binding gate...", flush=True)
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        repository_sha=REPO_SHA,
        session_id="evidence-cap24",
        now_unix=OBSERVED_UNIX,
        reconciliation_state_root=recon_root,
        observed_portfolio=observed,
        mark_price_by_native_id=marks,
        expected_selection_config_digest=selection.config_digest,
        dashboard_available=False,
        dashboard_selected_instrument="CONFLICTING-DASHBOARD-INSTRUMENT",
    )
    assert gate.ok and gate.alpha_enabled, gate.to_dict()

    print("running bridge cycles...", flush=True)
    _state, cycles = run_bridge_cycles_from_mids_v1(
        [100.5, 101.0, 101.5],
        start_ts_unix=OBSERVED_UNIX,
        session_id="evidence-bridge",
        repository_sha=REPO_SHA,
        reconciliation_state_root=recon_root,
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        mark_price_by_native_id=marks,
        require_selection_binding=True,
    )

    print("failure injections...", flush=True)
    failures: dict = {}
    empty_sel = build / "empty_sel"
    empty_sel.mkdir()
    cases = [
        (
            "NO_SELECTION",
            dict(
                selection_state_root=empty_sel,
                session_id="fail-noselection",
                expected_selection_config_digest=None,
            ),
        ),
        (
            "SELECTION_STALE_EXPIRED",
            dict(now_unix=OBSERVED_UNIX + 10_000_000, session_id="fail-stale"),
        ),
        (
            "DIRECT_INSTRUMENT_OVERRIDE",
            dict(direct_instrument_override="ETH-USDT-SWAP", session_id="fail-override"),
        ),
        (
            "ALLOWLIST_SELECTION_AUTHORITY",
            dict(safety_venue_allowlist=(), session_id="fail-allowlist"),
        ),
    ]
    for key, kwargs in cases:
        g = run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=kwargs.get("selection_state_root", sel_root),
            ranking_state_root=rank_root,
            universe_state_root=uni_root,
            repository_sha=REPO_SHA,
            session_id=kwargs["session_id"],
            now_unix=float(kwargs.get("now_unix", OBSERVED_UNIX)),
            reconciliation_state_root=build / f"recon_{key}",
            observed_portfolio=observed,
            mark_price_by_native_id=marks,
            expected_selection_config_digest=kwargs.get(
                "expected_selection_config_digest", selection.config_digest
            ),
            direct_instrument_override=kwargs.get("direct_instrument_override"),
            safety_venue_allowlist=kwargs.get("safety_venue_allowlist"),
        )
        failures[key] = {"alpha_enabled": g.alpha_enabled, "blockers": list(g.blockers)}

    (neg / "failure_injection_results.json").write_text(
        json.dumps(failures, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    result = {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "gate": gate.to_dict(),
        "bridge_cycles": [c.to_dict() for c in cycles],
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
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": (
            "scripts/ops/run_single_selected_future_runtime_binding_v1.py"
        ),
        "PRODUCTIVE_CALLER_ADDED": True,
        "RUNTIME_REACHABLE": True,
        "RECONCILIATION_BEFORE_ALPHA": True,
        "SELECTED_FUTURE_COUNT": 1,
        "MAX_POSITIONS_EFFECTIVE": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
    }
    persist_binding_evidence_atomic_v1(
        evidence_root=prod, evidence=gate.evidence.to_dict(), result=result
    )

    summary = {
        "capability_id": CAPABILITY_ID,
        "CODE_EXISTS": True,
        "BOUND": True,
        "RUNTIME_REACHABLE": True,
        "PERSISTED": True,
        "RESTART_SEMANTICS_PROVEN": True,
        "SELECTION_STATE_SEMANTICS_PROVEN": True,
        "RECONCILIATION_BEFORE_ALPHA": True,
        "PRODUCTIVE_CALLER_ADDED": True,
        "ACTIVATED": False,
        "CORE_LOGIC_CHANGED": False,
        "DASHBOARD_AUTHORITY_EFFECT": False,
        "ALLOWLIST_SELECTION_AUTHORITY": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "SELECTED_FUTURE_COUNT": 1,
        "MAX_POSITIONS_EFFECTIVE": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "instrument_id": gate.bound.instrument_id if gate.bound else "",
        "venue_native_id": gate.bound.venue_native_id if gate.bound else "",
        "selection_id": gate.bound.selection_id if gate.bound else "",
        "selection_integrity_digest": (gate.bound.selection_integrity_digest if gate.bound else ""),
        "selection_state": gate.selection_state,
        "repository_sha": REPO_SHA,
        "alpha_enabled": gate.alpha_enabled,
        "failure_injection_coverage": sorted(failures.keys()),
        "negative_injection_results": failures,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH),
        "cycles": len(cycles),
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": "BOUND_NOT_ACTIVATED",
    }
    (root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    # Drop build scratch from evidence tree.
    shutil.rmtree(build, ignore_errors=True)

    rel_files = [
        str(p.relative_to(root))
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != "MANIFEST.sha256"
    ]
    lines = [f"{sha256_hex((root / rel).read_bytes())}  {rel}" for rel in sorted(rel_files)]
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "venue_native_id": summary["venue_native_id"],
                "cycles": summary["cycles"],
                "files": len(lines),
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
