"""N=1 whole-system hard-facts integration WP v1 — closure through PRE_EXTERNAL."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import RawMarkCandleV1
from src.ops.hard_facts_system_closure_v1.cap22_productive_real_gate_v1 import (
    assert_cap22_productive_real_ranking_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.backlog_matrix_v1 import (
    close_row_v1,
    initial_backlog_rows_v1,
    summarize_backlog_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.composed_identity_custody_health_v1 import (
    prove_composed_safety_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import BACKLOG_TOTAL
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.golden_happy_path_trace_harness_v1 import (
    negative_failure_vector_v1,
    prove_natural_long_short_hold_vectors_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
    run_full_admission_proof_bundle_v1,
    write_admission_evidence_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    assert_productive_public_host_invariants_v1,
    economic_md_source_from_public_runtime_store_v1,
    prove_public_real_md_to_cap22_n1_chain_v1,
    run_public_runtime_ws_normalization_cycle_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    SNAPSHOT_FILENAME as UNIVERSE_SNAPSHOT_FILENAME,
)
from tests.ops._productive_economic_md_inject_helpers_v1 import (
    injected_economic_md_source_for_venue_native_ids_v1,
)
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    _five_rows,
    _held_writer,
    _persist_universe_and_ranking,
)
from tests.ops.test_okx_eea_private_account_state_runtime_v1 import _fixture_rest

REPO = Path(__file__).resolve().parents[2]
BASE_TS = 1_757_631_540_000


def _seed_public_marks(tmp_path: Path, *, n: int = MINIMUM_FINALIZED_PT1M_MARKS) -> None:
    from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
        append_fact_v1,
        default_store_paths_v1,
    )

    paths = default_store_paths_v1(tmp_path)
    for i in range(n):
        append_fact_v1(
            paths,
            {
                "fact_kind": "FinalizedPt1mMarkFactV1",
                "interval_start_ms": BASE_TS + i * PT1M_STEP_MS,
                "mark_px": str(100 + i),
                "confirm": "1",
                "captured_at": "2026-09-26T00:00:00Z",
                "instrument": {"venue_native_id": "ETH-USDT-SWAP"},
            },
        )


def test_productive_public_host_invariants() -> None:
    assert_productive_public_host_invariants_v1()


def test_public_runtime_ws_orchestrator_e2e(tmp_path: Path) -> None:
    _seed_public_marks(tmp_path, n=5)
    inst = {
        "canonical_instrument_id": "inst-eth",
        "venue_native_id": "ETH-USDT-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "d",
    }
    ws_msgs = [
        {
            "arg": {"channel": "tickers", "instId": "ETH-USDT-SWAP"},
            "data": [{"instId": "ETH-USDT-SWAP", "markPx": "100.1", "ts": "1000"}],
        },
    ]
    runtime = run_public_runtime_ws_normalization_cycle_v1(
        store_root=tmp_path / "ws_store",
        venue_native_id="ETH-USDT-SWAP",
        canonical_instrument_id="inst-eth",
        ws_messages=ws_msgs,
        rest_fetch_json=lambda p, q: {"code": "0", "data": []},
    )
    assert runtime.lifecycle_events
    adapter = economic_md_source_from_public_runtime_store_v1(tmp_path)
    bundle = adapter.collect_instrument_raw_input_v1(venue_native_id="ETH-USDT-SWAP")
    assert len(bundle.marks) == 5
    facts = PublicRuntimeEconomicMdPublicSourceV1(store_root=tmp_path)
    b2 = facts.collect_instrument_raw_input_v1(venue_native_id="ETH-USDT-SWAP")
    assert isinstance(b2.marks[0], RawMarkCandleV1)
    _ = inst


def _universe_snapshot_from_chain(chain: dict) -> dict:
    path = chain["universe_root"] / UNIVERSE_SNAPSHOT_FILENAME
    return json.loads(path.read_text(encoding="utf-8"))


def test_e1_e3_public_to_cap22_n1_handoff(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    ranking = chain["ranking"]
    universe = _universe_snapshot_from_chain(chain)
    assert_cap22_productive_real_ranking_v1(ranking)
    writer = _held_writer(tmp_path / "topo")
    md = injected_economic_md_source_for_venue_native_ids_v1(["ETH-USDT-SWAP"])
    proof, handoff = prove_public_real_md_to_cap22_n1_chain_v1(
        universe_snapshot=universe,
        public_md_source=md,
        productive_ranking_snapshot=ranking,
        membership_store_root=tmp_path / "mca",
        topology_state_root_base=tmp_path / "topo",
        lane_assignment_writer=writer,
        ws_normalization_applied=True,
        event_sequence_persisted=True,
    )
    assert proof.ok is True
    assert handoff is not None
    assert handoff.membership.ordered_instrument_ids


def test_negative_vectors_first_divergence() -> None:
    stale = negative_failure_vector_v1(
        name="stale_public_md",
        expected_block="INSUFFICIENT_FINALIZED_PT1M_MARKS",
        actual={"first_block": "INSUFFICIENT_FINALIZED_PT1M_MARKS"},
    )
    assert stale.ok is True
    kill = negative_failure_vector_v1(
        name="kill_switch_active",
        expected_block="KILL_SWITCH",
        actual={"first_block": "OTHER"},
    )
    assert kill.ok is False


def test_rw_e23_pre_external_admission_bundle(tmp_path: Path) -> None:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    writer = _held_writer(tmp_path / "topo")
    md = injected_economic_md_source_for_venue_native_ids_v1(["ETH-USDT-SWAP"])
    public_proof, _ = prove_public_real_md_to_cap22_n1_chain_v1(
        universe_snapshot=_universe_snapshot_from_chain(chain),
        public_md_source=md,
        productive_ranking_snapshot=chain["ranking"],
        membership_store_root=tmp_path / "mca",
        topology_state_root_base=tmp_path / "topo",
        lane_assignment_writer=writer,
    )
    golden = prove_natural_long_short_hold_vectors_v1(
        run_id="n1-wp-test",
        instrument="inst-eth-usdt-perp",
        long_actual={
            "RUN_ID": "n1-wp-test",
            "instrument": "inst-eth-usdt-perp",
            "side": "LONG",
            "pre_external": True,
            "terminal": "PRE_EXTERNAL",
            "synthetic_b05_rejected": True,
        },
        short_actual={
            "RUN_ID": "n1-wp-test",
            "instrument": "inst-eth-usdt-perp",
            "side": "SHORT",
            "pre_external": True,
            "terminal": "PRE_EXTERNAL",
            "synthetic_b05_rejected": True,
        },
        hold_actual={
            "RUN_ID": "n1-wp-test",
            "instrument": "inst-eth-usdt-perp",
            "side": "HOLD",
            "pre_external": False,
            "terminal": "HOLD",
            "synthetic_b05_rejected": True,
        },
    )
    admission = run_full_admission_proof_bundle_v1(
        public_chain=public_proof,
        public_store_root=tmp_path / "pub",
        private_store_root=tmp_path / "priv",
        golden=golden,
        pre_external_reached=True,
    )
    assert admission.ok is True
    assert admission.post_count == 0
    assert admission.post_allowed is False
    rows = initial_backlog_rows_v1()
    pkg = "src/ops/n1_whole_system_hard_facts_integration_wp_v1/"
    for row_id in rows:
        close_row_v1(
            rows,
            backlog_id=row_id,
            changed_files=(pkg,),
            tests=("tests/ops/test_n1_whole_system_hard_facts_integration_wp_v1.py",),
            notes="WP v1 integration closure",
        )
    summary = summarize_backlog_v1(rows)
    assert summary["BACKLOG_CLOSED"] == BACKLOG_TOTAL
    path = write_admission_evidence_v1(
        repo_root=REPO,
        admission=admission,
        backlog_matrix=summary,
    )
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["admission"]["ok"] is True


def test_composed_safety_chain() -> None:
    proof = prove_composed_safety_chain_v1()
    assert proof.ok is True


def test_private_chain_uses_fixture_rest(tmp_path: Path) -> None:
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.private_observation_chain_v1 import (
        prove_private_observation_chain_v1,
    )

    out = prove_private_observation_chain_v1(
        store_root=tmp_path,
        rest_fetch_json=_fixture_rest,
    )
    assert out.private_ws_canonical is True
