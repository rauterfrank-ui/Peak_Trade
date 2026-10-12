"""GHV scope trace L10 seal fields (read-only, no productive recompute)."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    L10_OBSERVABILITY_PROVENANCE,
    L10_OBSERVABILITY_STATUS_PRESENT,
    L10_OBSERVABILITY_STATUS_UNAVAILABLE,
    GoldenHappyVectorForensicObservabilitySessionV1,
    build_scope_decision_trace_record_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layered_core_authority_seal_v1 import (
    build_layered_core_authority_seal_v1,
)
from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1


def _session() -> GoldenHappyVectorForensicObservabilitySessionV1:
    return GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=Path("/tmp/unused-l10-trace"),
        run_id="run-l10",
        continuous_run_id="run-l10",
    )


def test_l10_fields_absent_when_seal_missing() -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    record = build_scope_decision_trace_record_v1(
        session=_session(),
        cycle_id="c",
        replay_id="r",
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        trading_epoch=44,
        now_tick=1,
        observation_event_time_unix=1.0,
        cmc_pre_bind_volatility=0.08,
        g17_cmc_bind_outcome="PRODUCED",
        g17_cmc_bind_performed=True,
        g17_estimate_present=True,
        g17_typed_volatility=0.01,
        g17_output_port_outcome="PRODUCED",
        g17_history_summary=None,
        cmc_post_bind_volatility=0.01,
        scope_resolved_volatility=0.01,
        layer_c_up_distance=100.0,
        layer_c_adverse_exit_distance=40.0,
        layer_c_reversal_distance=60.0,
        layer_c_dynamic_scope_magnitude=100.0,
        side_state_before=SideState.NEUTRAL_OBSERVE.value,
        scope_direction="long",
        replay=replay,
        layered_core_authority_seal=None,
    )
    assert record is not None
    assert record["l10_observability_status"] == L10_OBSERVABILITY_STATUS_UNAVAILABLE
    assert record["l10_observability_provenance"] == L10_OBSERVABILITY_PROVENANCE
    assert record["cm_t"] is None
    assert record["d_t"] is None
    assert record["switch_condition_met"] is None
    assert record["regime_pre"] is None
    assert record["regime_post"] is None


def test_l10_fields_copied_from_authoritative_seal() -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    seal = build_layered_core_authority_seal_v1(
        seal_id="seal-l10-test",
        instrument_id="inst-eth-usdt-perp",
        episode_snapshot_id="ep-1",
        store_manifest_digest="a" * 64,
        regime_pre=NakedRegimeV1.BULL,
        regime_post=NakedRegimeV1.BEAR,
        nullline_price=100.0,
        d_t=25.0,
        r_t=105.0,
        cm_t=30.0,
        switch_condition_met=True,
        mechanical_step_count=3,
        cz4_delegation_active=True,
    )
    record = build_scope_decision_trace_record_v1(
        session=_session(),
        cycle_id="c",
        replay_id="r",
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        trading_epoch=44,
        now_tick=1,
        observation_event_time_unix=1.0,
        cmc_pre_bind_volatility=0.08,
        g17_cmc_bind_outcome="PRODUCED",
        g17_cmc_bind_performed=True,
        g17_estimate_present=True,
        g17_typed_volatility=0.01,
        g17_output_port_outcome="PRODUCED",
        g17_history_summary=None,
        cmc_post_bind_volatility=0.01,
        scope_resolved_volatility=0.01,
        layer_c_up_distance=100.0,
        layer_c_adverse_exit_distance=40.0,
        layer_c_reversal_distance=60.0,
        layer_c_dynamic_scope_magnitude=100.0,
        side_state_before=SideState.NEUTRAL_OBSERVE.value,
        scope_direction="long",
        replay=replay,
        layered_core_authority_seal=seal,
    )
    assert record is not None
    assert record["l10_observability_status"] == L10_OBSERVABILITY_STATUS_PRESENT
    assert record["cm_t"] == 30.0
    assert record["d_t"] == 25.0
    assert record["switch_condition_met"] is True
    assert record["regime_pre"] == "bull"
    assert record["regime_post"] == "bear"
    assert record["l10_seal_id"] == "seal-l10-test"
