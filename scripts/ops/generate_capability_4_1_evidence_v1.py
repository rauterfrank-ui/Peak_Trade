#!/usr/bin/env python3
"""Generate durable Cap 4.1 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (  # noqa: E402
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (  # noqa: E402
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (  # noqa: E402
    GovernedUniverseSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (  # noqa: E402
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (  # noqa: E402
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (  # noqa: E402
    ProductiveRankingSingleWriterV1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.authority_inventory_v1 import (  # noqa: E402
    inventory_pre_activation_authority_surfaces_v1,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1 import (  # noqa: E402
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
    CAPABILITY_ID,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    RUNTIME_ACTIVATED,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.persistence_v1 import (  # noqa: E402
    persist_pre_activation_evidence_atomic_v1,
    verify_manifest,
)
from src.ops.single_future_canonical_runtime_pre_activation_closure_v1.pre_activation_gate_v1 import (  # noqa: E402
    run_single_future_canonical_runtime_pre_activation_closure_v1,
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

OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


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
    repo_sha = _git_sha()
    root = (
        _REPO_ROOT
        / "docs/evidence/capability_4_1_single_future_canonical_runtime_pre_activation_closure_v1"
    )
    if root.exists():
        shutil.rmtree(root)
    prod = root / "productive_pre_activation"
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
    acct_root = build / "accounting"
    lock_root = build / "locks"
    for p in (uni_root, rank_root, sel_root, recon_root, acct_root, lock_root):
        p.mkdir()

    print("producing universe...", flush=True)
    uni = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": rows},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": i, "markPx": "100.5"} for i in mark_ids],
        },
        repository_sha=repo_sha,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="ev41")
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
        repository_sha=repo_sha,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="ev41")
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
        repository_sha=repo_sha,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="ev41",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = {selection.venue_native_id: "100.5"}

    print("running Cap 4.1 pre-activation closure...", flush=True)
    gate = run_single_future_canonical_runtime_pre_activation_closure_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        reconciliation_state_root=recon_root,
        accounting_state_root=acct_root,
        evidence_root=prod / "gate_evidence",
        lock_root=lock_root,
        repository_sha=repo_sha,
        baseline_sha=repo_sha,
        session_id="evidence-cap41",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=marks,
        mid_prices=(100.5, 101.0, 101.5, 102.0),
        authorization_artifact={
            "schema": "offline_structural_only",
            "consumed": False,
            "AUTHORIZATION_CONSUMED": False,
        },
        tmp_root=build / "tmp",
        run_bridge=True,
    )
    assert gate.ok and gate.ready_for_activation and not gate.runtime_activated

    for name, src in (("selection", sel_root), ("ranking", rank_root), ("universe", uni_root)):
        shutil.copytree(src, prod / name)
    (prod / "mark_price_by_native_id.json").write_text(
        json.dumps(marks, indent=2) + "\n", encoding="utf-8"
    )
    (neg / "failure_injection_results.json").write_text(
        json.dumps(gate.evidence.failure_injection_results, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    authority = inventory_pre_activation_authority_surfaces_v1()
    result = {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repo_sha,
        "baseline_sha": repo_sha,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "PRODUCTIVE_RUNTIME_HOST": PRODUCTIVE_RUNTIME_HOST,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE": CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS_AFTER": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        "READY_FOR_ACTIVATION": True,
        "RUNTIME_ACTIVATED": RUNTIME_ACTIVATED,
        "gate": gate.to_dict(),
        "authority_map": authority,
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
    persist_pre_activation_evidence_atomic_v1(
        evidence_root=prod / "gate_evidence",
        evidence=gate.evidence.to_dict(),
        result=result,
        gate=gate.gate_flags.to_dict(),
    )
    verify_manifest(prod / "gate_evidence")

    (prod / "single_future_canonical_runtime_pre_activation_result_v1.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (prod / "config_effective_values.json").write_text(
        json.dumps(gate.evidence.effective_config, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (prod / "restart_recovery.json").write_text(
        json.dumps(gate.evidence.restart_recovery, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (prod / "exit_risk_safety_independence.json").write_text(
        json.dumps(gate.evidence.exit_risk_safety_independence, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (prod / "activation_negative.json").write_text(
        json.dumps(gate.evidence.activation_negative, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (prod / "network_order_negative.json").write_text(
        json.dumps(gate.evidence.network_order_negative, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (prod / "authority_map.json").write_text(
        json.dumps(authority, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "capability_id": CAPABILITY_ID,
        "repository_sha": repo_sha,
        "CODE_EXISTS": True,
        "BOUND": True,
        "RUNTIME_REACHABLE": True,
        "PRODUCTIVE_CALLER_ADDED": True,
        "READY_FOR_ACTIVATION": True,
        "RUNTIME_ACTIVATED": False,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE": CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE,
        "CORE_LOGIC_CHANGED": False,
        "ACTIVATED": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "gate_flags": gate.gate_flags.to_dict(),
        "failure_injection_coverage": sorted(gate.evidence.failure_injection_results.keys()),
        "negative_injection_results": gate.evidence.failure_injection_results,
        "restart_recovery": gate.evidence.restart_recovery,
        "exit_risk_safety_independence": gate.evidence.exit_risk_safety_independence,
        "effective_config": gate.evidence.effective_config,
        "cycles": (gate.offline_end_to_end or {}).get("cycles", 0),
        "instrument_id": (gate.offline_end_to_end or {}).get("instrument_id"),
        "selection_id": selection.selection_id,
        "PRODUCTIVE_RUNTIME_HOST": PRODUCTIVE_RUNTIME_HOST,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
    }
    (root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    # Drop build artifacts from durable tree
    shutil.rmtree(build, ignore_errors=True)

    rels = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "_build" in path.parts or path.name == "MANIFEST.sha256":
            continue
        if "_tmp" in path.parts or "locks" in path.parts:
            continue
        rels.append(str(path.relative_to(root)))
    lines = [f"{sha256_hex((root / rel).read_bytes())}  {rel}" for rel in sorted(rels)]
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "evidence_root": str(root),
                "status": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
                "runtime_activated": RUNTIME_ACTIVATED,
                "cycles": summary["cycles"],
                "selection_id": selection.selection_id,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
