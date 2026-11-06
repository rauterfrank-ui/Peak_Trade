"""Golden Happy scope/G17 causal trace forensic observability (default OFF)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    SCOPE_DECISION_TRACE_LEDGER_FILENAME,
    SCOPE_DECISION_TRACE_SCHEMA_VERSION,
    GoldenHappyVectorForensicObservabilitySessionV1,
    append_scope_decision_trace_from_productive_cycle_v1,
    bind_golden_happy_vector_forensic_observability_session_v1,
    build_scope_decision_trace_record_v1,
    reset_golden_happy_vector_forensic_observability_session_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    resolve_legacy_volatility_float_for_consumer_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)


def test_scope_trace_default_off_emits_nothing(tmp_path: Path) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert (
        append_scope_decision_trace_from_productive_cycle_v1(
            cycle_id="c1",
            replay_id="r1",
            instrument_id="inst-eth-usdt-perp",
            venue_native_id="ETH-USDT-SWAP",
            trading_epoch=44,
            now_tick=1,
            observation_event_time_unix=1.0,
            cmc_pre_bind_volatility=0.08,
            g17_cmc_bind_outcome="PRODUCED",
            g17_cmc_bind_performed=True,
            g17_estimate_present=True,
            g17_typed_vol_producer=None,
            cmc_post_bind_volatility=0.01,
            scope_resolved_volatility=0.01,
            layer_c_up_distance=1.0,
            layer_c_adverse_exit_distance=0.4,
            layer_c_reversal_distance=0.6,
            layer_c_dynamic_scope_magnitude=1.0,
            side_state_before=SideState.NEUTRAL_OBSERVE.value,
            scope_direction="long",
            replay=replay,
        )
        is None
    )
    assert not (tmp_path / SCOPE_DECISION_TRACE_LEDGER_FILENAME).exists()


def test_scope_trace_persists_scope_event_fields(tmp_path: Path) -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert replay.intermediate is not None
    ctx = replay.intermediate.market_context
    resolved = float(resolve_legacy_volatility_float_for_consumer_v1(ctx))
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=tmp_path,
        run_id="run-scope",
        continuous_run_id="run-scope",
    )
    reset = bind_golden_happy_vector_forensic_observability_session_v1(session)
    try:
        record = append_scope_decision_trace_from_productive_cycle_v1(
            cycle_id="cycle-x",
            replay_id="replay-x",
            instrument_id="inst-eth-usdt-perp",
            venue_native_id="ETH-USDT-SWAP",
            trading_epoch=44,
            now_tick=2,
            observation_event_time_unix=100.0,
            cmc_pre_bind_volatility=float(ctx.volatility_estimate),
            g17_cmc_bind_outcome="NOT_APPLICABLE_FIXTURE",
            g17_cmc_bind_performed=True,
            g17_estimate_present=True,
            g17_typed_vol_producer=None,
            cmc_post_bind_volatility=float(ctx.volatility_estimate),
            scope_resolved_volatility=resolved,
            layer_c_up_distance=100.0,
            layer_c_adverse_exit_distance=40.0,
            layer_c_reversal_distance=60.0,
            layer_c_dynamic_scope_magnitude=100.0,
            side_state_before=SideState.NEUTRAL_OBSERVE.value,
            scope_direction="long",
            replay=replay,
        )
    finally:
        reset_golden_happy_vector_forensic_observability_session_v1(reset)
    assert record is not None
    assert record["capture_ok"] is True
    assert record["schema_version"] == SCOPE_DECISION_TRACE_SCHEMA_VERSION
    scope_ev = replay.intermediate.scope_event
    assert record["scope_event_type"] == scope_ev.event_type.value
    assert record["evaluated_up_candidate_threshold"] == float(
        scope_ev.evaluated_thresholds.up_candidate_threshold
    )
    assert record["scope_resolved_volatility"] == resolved
    assert record["decision_input_anchor"] == float(scope_ev.semantic_binding.trailing_anchor)
    lines = (tmp_path / SCOPE_DECISION_TRACE_LEDGER_FILENAME).read_text().splitlines()
    assert len(lines) == 1


def test_replay_decision_identity_with_scope_trace_hook() -> None:
    inp = _replay_input()
    baseline = run_integrated_offline_trading_logic_replay_v1(inp)
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=Path("/tmp/unused-scope-trace"),
        run_id="parity",
        continuous_run_id="parity",
    )
    reset = bind_golden_happy_vector_forensic_observability_session_v1(session)
    try:
        with patch(
            "src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1._append_jsonl_v1"
        ):
            observed = run_integrated_offline_trading_logic_replay_v1(inp)
    finally:
        reset_golden_happy_vector_forensic_observability_session_v1(reset)
    assert observed.evidence.decision_outcome == baseline.evidence.decision_outcome
    assert observed.replay_pass == baseline.replay_pass
    assert observed.fail_reasons == baseline.fail_reasons


def test_noop_trace_exposes_empty_matched_conditions() -> None:
    replay = run_integrated_offline_trading_logic_replay_v1(_replay_input())
    assert replay.intermediate is not None
    assert replay.intermediate.scope_event.event_type is CanonicalScopeEventType.NOOP
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=Path("/tmp/unused"),
        run_id="r",
        continuous_run_id="r",
    )
    record = build_scope_decision_trace_record_v1(
        session=session,
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
        g17_history_summary={"history_digest": "abc"},
        cmc_post_bind_volatility=0.01,
        scope_resolved_volatility=0.01,
        layer_c_up_distance=100.0,
        layer_c_adverse_exit_distance=40.0,
        layer_c_reversal_distance=60.0,
        layer_c_dynamic_scope_magnitude=100.0,
        side_state_before=SideState.NEUTRAL_OBSERVE.value,
        scope_direction="long",
        replay=replay,
    )
    assert record is not None
    assert record["matched_scope_conditions"] == []


def test_adverse_matched_conditions_copied_from_scope_owner() -> None:
    from tests.trading.master_v2.test_deterministic_scope_event_generator_v1 import (
        _generate as scope_generate_v1,
    )

    evidence = scope_generate_v1(current_price=3410.0)
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert "adverse_exit" in evidence.matched_conditions


def test_upscope_candidate_count_progression_in_trace() -> None:
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        ScopeConfirmationStateV1,
    )

    first = run_integrated_offline_trading_logic_replay_v1(
        _replay_input(
            current_price=5000.0,
            scope_confirmation_state=ScopeConfirmationStateV1(
                candidate_kind=None,
                candidate_count=0,
                last_evaluated_trading_epoch=43,
            ),
        )
    )
    assert first.intermediate is not None
    ev = first.intermediate.scope_event
    assert ev.event_type in (
        CanonicalScopeEventType.UPSCOPE_CANDIDATE,
        CanonicalScopeEventType.UPSCOPE_CONFIRMED,
    )
    session = GoldenHappyVectorForensicObservabilitySessionV1(
        enabled=True,
        product_evidence_root=Path("/tmp/unused"),
        run_id="r",
        continuous_run_id="r",
    )
    record = build_scope_decision_trace_record_v1(
        session=session,
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
        replay=first,
    )
    assert record is not None
    assert record["scope_candidate_count_after"] >= record["scope_candidate_count_before"]
