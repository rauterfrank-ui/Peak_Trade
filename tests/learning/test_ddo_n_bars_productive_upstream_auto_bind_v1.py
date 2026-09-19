"""POST_6630 Slice 1 — auto-bind DDO N_BARS upstream from capture + O4 producer."""

from __future__ import annotations

from pathlib import Path

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    build_account_identity_record_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_from_canonical_bar_producer_v1 import (
    materialize_o4_n_bars_bar_evidence_snapshot_v1,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision


def _norm(*, mark: float, event_ts: float) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx_eea",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 1.0,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="digest-o4-upstream",
        mapping_version="v1",
    )


def _producer_with_two_gapless_finalized_bars() -> CanonicalPublicMdBarProducerV1:
    producer = CanonicalPublicMdBarProducerV1(
        session_id="o4-upstream-session",
        repository_sha="abc12345deadbeef",
        config_digest="cfgdigest001",
    )
    first = producer.ingest_normalized_event(_norm(mark=100.0, event_ts=1_756_732_800.0))
    producer.finalize_bar(
        canonical_instrument_id="ETH-USDT-SWAP",
        bar_open_time=float(first["envelope"]["bar_open_time"]),
    )
    second = producer.ingest_normalized_event(_norm(mark=110.0, event_ts=1_756_736_400.0))
    producer.finalize_bar(
        canonical_instrument_id="ETH-USDT-SWAP",
        bar_open_time=float(second["envelope"]["bar_open_time"]),
    )
    return producer


def test_materialize_o4_snapshot_from_canonical_producer() -> None:
    producer = _producer_with_two_gapless_finalized_bars()
    snap = materialize_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref="dec-upstream-0001",
        producer=producer,
        n_bars=2,
    )
    assert snap["n_bars"] == 2
    assert len(snap["o4_bars"]) == 2


def test_bridge_resolves_n_bars_upstream_without_manual_injection(tmp_path: Path) -> None:
    producer = _producer_with_two_gapless_finalized_bars()
    account = build_account_identity_record_v1(
        account_identity="acct-nbars-upstream",
        venue="OKX",
        credential_ref_id="cred-nbars-upstream",
        account_scope="trading-only",
        expected_uid="acct-nbars-upstream",
    )
    state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="nbars-upstream-auto",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_canonical_public_md_bar_producer=producer,
        ddo_n_bars_horizon_n_bars=2,
    )
    assert state.ddo_n_bars_horizon_decision_event is not None
    assert state.ddo_o4_n_bars_bar_evidence_snapshot is not None
    horizon = state.last_ddo_n_bars_horizon_observation
    runtime = state.last_ddo_n_bars_evaluation_runtime
    assert horizon is not None and horizon.get("ok") is True
    assert runtime is not None and runtime.get("ok") is True
    assert runtime.get("external_effect_authorized") is False


def test_c1_observation_feeds_o4_enabling_n_bars_without_manual_producer(tmp_path: Path) -> None:
    account = build_account_identity_record_v1(
        account_identity="acct-c1-o4-feed",
        venue="OKX",
        credential_ref_id="cred-c1-o4-feed",
        account_scope="trading-only",
        expected_uid="acct-c1-o4-feed",
    )
    t0 = 1_756_732_800.0
    t1 = t0 + 3600.0
    t2 = t1 + 3600.0
    t3 = t2 + 3600.0
    common = dict(
        session_id="nbars-c1-o4-feed",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_n_bars=2,
    )
    state, _ = run_bridge_cycles_from_mids_v1([3500.0], start_ts_unix=t0, **common)
    run_bridge_cycle_v1(
        state,
        mid_price=3510.0,
        event_ts_unix=t1,
        force_observation_event_time=t1,
        session_id=common["session_id"],
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
    )
    run_bridge_cycle_v1(
        state,
        mid_price=3520.0,
        event_ts_unix=t2,
        force_observation_event_time=t2,
        session_id=common["session_id"],
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
    )
    run_bridge_cycle_v1(
        state,
        mid_price=3530.0,
        event_ts_unix=t3,
        force_observation_event_time=t3,
        session_id=common["session_id"],
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
    )
    assert state.ddo_canonical_public_md_bar_producer is not None
    assert state.ddo_o4_n_bars_bar_evidence_snapshot is not None
    horizon = state.last_ddo_n_bars_horizon_observation
    runtime = state.last_ddo_n_bars_evaluation_runtime
    assert horizon is not None and horizon.get("ok") is True
    assert runtime is not None and runtime.get("ok") is True


def test_explicit_injection_still_wins_over_auto_bind(tmp_path: Path) -> None:
    producer = _producer_with_two_gapless_finalized_bars()
    injected = build_decision_event_v0(_decision(record_id="dec-explicit-inject"))
    account = build_account_identity_record_v1(
        account_identity="acct-nbars-explicit",
        venue="OKX",
        credential_ref_id="cred-nbars-explicit",
        account_scope="trading-only",
        expected_uid="acct-nbars-explicit",
    )
    state, _ = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="nbars-explicit-win",
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=account,
        ddo_n_bars_horizon_decision_event=injected,
        ddo_canonical_public_md_bar_producer=producer,
    )
    assert state.ddo_n_bars_horizon_decision_event is not None
    assert state.ddo_n_bars_horizon_decision_event["record_id"] == injected["record_id"]
