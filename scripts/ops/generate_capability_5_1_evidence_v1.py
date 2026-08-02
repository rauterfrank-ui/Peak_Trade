#!/usr/bin/env python3
"""Generate durable Cap 5.1 evidence under docs/evidence/ (offline, no network)."""

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
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_HOST,
    RUNTIME_ACTIVATED,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.evidence_gate_v1 import (  # noqa: E402
    run_single_future_canonical_runtime_deterministic_offline_evidence_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (  # noqa: E402
    load_offline_market_data_fixture_v1,
    universe_rows_from_fixture_v1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.persistence_v1 import (  # noqa: E402
    persist_offline_evidence_atomic_v1,
    verify_manifest,
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


def main() -> int:
    repo_sha = _git_sha()
    root = (
        _REPO_ROOT
        / "docs/evidence/capability_5_1_single_future_canonical_runtime_deterministic_offline_evidence_v1"
    )
    if root.exists():
        shutil.rmtree(root)
    prod = root / "productive_offline_replay"
    neg = root / "negative_injections"
    prod.mkdir(parents=True)
    neg.mkdir(parents=True)
    build = root / "_build"
    build.mkdir()

    fixture = load_offline_market_data_fixture_v1(_REPO_ROOT / DEFAULT_FIXTURE_RELPATH)
    rows = universe_rows_from_fixture_v1(fixture)
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
            "data": [
                {"instId": i, "markPx": str(fixture.mark_price_baseline.get(i, "100.5"))}
                for i in mark_ids
            ],
        },
        repository_sha=repo_sha,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    uni_writer = GovernedUniverseSingleWriterV1(state_root=uni_root, session_id="ev51")
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
    rank_writer = ProductiveRankingSingleWriterV1(state_root=rank_root, session_id="ev51")
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
        session_id="ev51",
    )
    assert sel.get("ok"), sel
    selection = SingleSelectedFutureSelectionV1.from_dict(
        json.loads((sel_root / SELECTION_FILENAME).read_text(encoding="utf-8"))
    )
    marks = dict(fixture.mark_price_baseline)
    if selection.venue_native_id not in marks:
        marks[selection.venue_native_id] = "100.5"

    print("running Cap 5.1 deterministic offline evidence...", flush=True)
    gate = run_single_future_canonical_runtime_deterministic_offline_evidence_v1(
        selection_state_root=sel_root,
        ranking_state_root=rank_root,
        universe_state_root=uni_root,
        reconciliation_state_root=recon_root,
        accounting_state_root=acct_root,
        evidence_root=prod / "gate_evidence",
        lock_root=lock_root,
        repository_sha=repo_sha,
        baseline_sha=repo_sha,
        session_id="evidence-cap51",
        now_unix=OBSERVED_UNIX,
        mark_price_by_native_id=marks,
        authorization_artifact={
            "schema": "offline_structural_only",
            "consumed": False,
            "AUTHORIZATION_CONSUMED": False,
        },
        fixture_path=_REPO_ROOT / DEFAULT_FIXTURE_RELPATH,
        tmp_root=build / "tmp",
    )
    assert gate.ok and gate.ready_for_activation and not gate.runtime_activated

    for name, src in (("selection", sel_root), ("ranking", rank_root), ("universe", uni_root)):
        shutil.copytree(src, prod / name)
    (prod / "mark_price_by_native_id.json").write_text(
        json.dumps(marks, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(
        _REPO_ROOT / DEFAULT_FIXTURE_RELPATH,
        prod / "market_data_fixture_v1.json",
    )
    (neg / "failure_injection_results.json").write_text(
        json.dumps(gate.evidence.failure_injection_results, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    authority = inventory_offline_evidence_authority_surfaces_v1()
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
        "OFFLINE_REPLAY_ONLY": True,
        "fixture_digest": gate.evidence.fixture_digest,
        "config_digest": gate.evidence.config_digest,
        "canonical_outcome_digest": gate.evidence.canonical_outcome_digest,
        "gate": gate.to_dict(),
        "authority_map": authority,
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_ACCESS_OCCURRED": False,
        "AUTHORIZATION_CONSUMED": False,
    }
    persist_offline_evidence_atomic_v1(
        evidence_root=prod / "gate_evidence",
        evidence=gate.evidence.to_dict(),
        result=result,
        gate=gate.gate_flags.to_dict(),
        telemetry=gate.evidence.telemetry,
        restart=gate.evidence.restart_recovery,
        failure_injection=gate.evidence.failure_injection_results,
    )
    verify_manifest(prod / "gate_evidence")

    (prod / "single_future_canonical_runtime_deterministic_offline_result_v1.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (prod / "restart_recovery.json").write_text(
        json.dumps(gate.evidence.restart_recovery, sort_keys=True, indent=2) + "\n",
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
    (prod / "telemetry.json").write_text(
        json.dumps(gate.evidence.telemetry, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (prod / "verifier_result.json").write_text(
        json.dumps(gate.evidence.verifier_result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    tel = gate.evidence.telemetry
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
        "OFFLINE_REPLAY_ONLY": True,
        "CORE_LOGIC_CHANGED": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "gate_flags": gate.gate_flags.to_dict(),
        "fixture_digest": gate.evidence.fixture_digest,
        "config_digest": gate.evidence.config_digest,
        "canonical_outcome_digest": gate.evidence.canonical_outcome_digest,
        "independent_run": gate.evidence.independent_run,
        "restart_recovery": gate.evidence.restart_recovery,
        "failure_injection_coverage": sorted(gate.evidence.failure_injection_results.keys()),
        "telemetry": {
            "cycle_count": tel.get("cycle_count"),
            "distinct_observation_count": tel.get("distinct_observation_count"),
            "duplicate_observation_count": tel.get("duplicate_observation_count"),
            "missing_observation_count": tel.get("missing_observation_count"),
            "hold_count": tel.get("hold_count"),
            "entry_count": tel.get("entry_count"),
            "reduce_count": tel.get("reduce_count"),
            "exit_count": tel.get("exit_count"),
            "total_fees": tel.get("total_fees"),
            "total_slippage": tel.get("total_slippage"),
            "realized_pnl": tel.get("realized_pnl"),
            "unrealized_pnl": tel.get("unrealized_pnl"),
            "max_drawdown": tel.get("max_drawdown"),
            "profit_factor": tel.get("profit_factor"),
            "turnover": tel.get("turnover"),
        },
        "selection_id": selection.selection_id,
        "PRODUCTIVE_RUNTIME_HOST": PRODUCTIVE_RUNTIME_HOST,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
    }
    (root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (root / "CAPABILITY_SPEC.md").write_text(
        "\n".join(
            [
                "# CAPABILITY_5_1_SINGLE_FUTURE_CANONICAL_RUNTIME_DETERMINISTIC_OFFLINE_EVIDENCE_V1",
                "",
                "Deterministic offline replay evidence over the Cap 4.1-closed single-future call graph.",
                "",
                "- `CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION`",
                "- `RUNTIME_ACTIVATED=false`",
                "- Offline fixtures only; no network, auth consumption, or activation",
                "- Reuses Cap 4.1 / 2.4 / 3.1 / bridge / verifier owners",
                "",
            ]
        ),
        encoding="utf-8",
    )

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
                "cycles": summary["telemetry"]["cycle_count"],
                "canonical_outcome_digest": gate.evidence.canonical_outcome_digest,
                "selection_id": selection.selection_id,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
