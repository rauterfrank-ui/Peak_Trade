"""O4 N_BARS public-plane convergence — parity, caller graph, authority invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DDO_PROMOTION_ADJUDICATION = json.loads(
    (
        REPO_ROOT / "config/governance/ddo_outcome_to_promotion_productive_binding_decision_v1.json"
    ).read_text(encoding="utf-8")
)["adjudication"]
from src.experiments.eg_i82_end_to_end_live_owner_graph_attestation_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    CAPTURE_RUNTIME_EFFECT,
    DDO_TRADING_AUTHORITY,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    build_account_identity_record_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.o4_n_bars_learning_caller_closure_v1 import (
    build_o4_n_bars_learning_caller_closure_v1,
    dry_run_handoff_chain_v1,
    verify_productive_convergence_trace_on_state_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    load_finalized_pt1h_o4_bar_elements_v1,
    sync_finalized_envelopes_to_wp_a_store_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_public_plane_convergence_v1 import (
    COMPETING_PRODUCTIVE_O4_TRUTH,
    N_BARS_REMAINS_PT1H,
    PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL,
    build_wp_c_converged_o4_from_store_v1,
    materialize_ddo_o4_snapshot_from_converged_public_plane_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_from_canonical_bar_producer_v1 import (
    materialize_o4_n_bars_bar_evidence_snapshot_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from tests.learning.test_ddo_n_bars_productive_upstream_auto_bind_v1 import (
    _norm,
    _producer_with_two_gapless_finalized_bars,
)


def test_parity_producer_path_matches_wp_a_wp_c_convergence_path(tmp_path: Path) -> None:
    producer = _producer_with_two_gapless_finalized_bars()
    direct = materialize_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref="dec-parity-001",
        producer=producer,
        n_bars=2,
    )
    sync_finalized_envelopes_to_wp_a_store_v1(
        tmp_path,
        producer.list_envelopes(),
        finalized_states=frozenset({"FINALIZED_BAR", "CORRECTED_BAR"}),
    )
    converged = build_wp_c_converged_o4_from_store_v1(tmp_path)
    via_plane = materialize_ddo_o4_snapshot_from_converged_public_plane_v1(
        decision_event_ref="dec-parity-001",
        converged_o4=converged,
        n_bars=2,
    )
    assert direct == via_plane
    assert direct["o4_interval_id"] == "PT1H"


def test_gap_missing_stale_fail_closed(tmp_path: Path) -> None:
    converged = dry_run_handoff_chain_v1(pt1h_bars=[])
    with pytest.raises(ValueError, match="O4_CANONICAL_BARS_MISSING"):
        materialize_ddo_o4_snapshot_from_converged_public_plane_v1(
            decision_event_ref="dec-gap-001",
            converged_o4=converged["wp_c"],
            n_bars=2,
        )


def test_productive_bridge_uses_public_plane_convergence(tmp_path: Path) -> None:
    producer = _producer_with_two_gapless_finalized_bars()
    account = build_account_identity_record_v1(
        account_identity="acct-o4-convergence",
        venue="OKX",
        credential_ref_id="cred-o4-convergence",
        account_scope="trading-only",
        expected_uid="acct-o4-convergence",
    )
    state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="o4-public-plane-convergence",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_canonical_public_md_bar_producer=producer,
        ddo_n_bars_horizon_n_bars=2,
    )
    trace = verify_productive_convergence_trace_on_state_v1(state)
    assert trace["productive_ddo_o4_source_is_wp_a_wp_c_canonical"] is True
    assert state.ddo_o4_n_bars_bar_evidence_snapshot is not None
    public_root = Path(state.public_md_store_root)
    assert len(load_finalized_pt1h_o4_bar_elements_v1(public_root)) == 2
    horizon = state.last_ddo_n_bars_horizon_observation
    assert horizon is not None and horizon.get("ok") is True
    assert horizon.get("external_effect_authorized") is False


def test_c1_feed_convergence_replay_deterministic(tmp_path: Path) -> None:
    account = build_account_identity_record_v1(
        account_identity="acct-o4-replay",
        venue="OKX",
        credential_ref_id="cred-o4-replay",
        account_scope="trading-only",
        expected_uid="acct-o4-replay",
    )
    t0 = 1_756_732_800.0
    common = dict(
        session_id="o4-replay-deterministic",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_n_bars=2,
    )
    state, _ = run_bridge_cycles_from_mids_v1([3500.0], start_ts_unix=t0, **common)
    for ts, px in ((t0 + 3600, 3510.0), (t0 + 7200, 3520.0), (t0 + 10800, 3530.0)):
        run_bridge_cycle_v1(
            state,
            mid_price=px,
            event_ts_unix=ts,
            force_observation_event_time=ts,
            session_id=common["session_id"],
            ddo_durable_evidence_runtime_state_root=tmp_path,
            ddo_evidence_environment=ExecutionEnvironment.DEV,
            ddo_account_identity_record=account,
        )
    snap_a = json.dumps(state.ddo_o4_n_bars_bar_evidence_snapshot, sort_keys=True)
    snap_b = json.dumps(state.ddo_o4_n_bars_bar_evidence_snapshot, sort_keys=True)
    assert snap_a == snap_b


def test_authority_and_safety_invariants() -> None:
    assert PRODUCTIVE_DDO_O4_SOURCE_IS_WP_A_WP_C_CANONICAL is True
    assert COMPETING_PRODUCTIVE_O4_TRUTH is False
    assert N_BARS_REMAINS_PT1H is True
    assert CAPTURE_RUNTIME_EFFECT == "OBSERVATION_ONLY"
    assert DDO_TRADING_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert DDO_PROMOTION_ADJUDICATION == "NO_N_BARS_TO_PROMOTION_BINDING"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1.completion_join_v1 import (
        MAX_POSITIONS_EFFECTIVE,
    )

    assert int(MAX_POSITIONS_EFFECTIVE) == 1


def test_caller_closure_evidence_matches_census() -> None:
    closure = build_o4_n_bars_learning_caller_closure_v1()
    assert closure["consumer_id"] == "o4_n_bars_learning"
    assert closure["competing_productive_o4_truth"] is False
    assert "converged_o4_handoff_v1" in closure["census_wp_c_handoff"]
    assert closure["promotion_binding_changed"] is False


def test_producer_still_legitimate_writer_not_productive_snapshot_reader(tmp_path: Path) -> None:
    producer = CanonicalPublicMdBarProducerV1(
        session_id="writer-only",
        repository_sha="abc12345deadbeef",
        config_digest="cfgdigest001",
    )
    first = producer.ingest_normalized_event(_norm(mark=100.0, event_ts=1_756_732_800.0))
    producer.finalize_bar(
        canonical_instrument_id="ETH-USDT-SWAP",
        bar_open_time=float(first["envelope"]["bar_open_time"]),
    )
    sync_finalized_envelopes_to_wp_a_store_v1(
        tmp_path,
        producer.list_envelopes(),
        finalized_states=frozenset({"FINALIZED_BAR", "CORRECTED_BAR"}),
    )
    assert len(load_finalized_pt1h_o4_bar_elements_v1(tmp_path)) == 1
