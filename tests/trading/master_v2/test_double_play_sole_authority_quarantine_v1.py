"""Contract tests: Double Play sole Bull/Bear + Switch authority quarantine v1."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE,
    BACKTEST_POSITION_FEEDBACK_ROLE,
    BacktestEnginePositionFeedbackV1,
    capture_backtest_engine_position_feedback_v1,
    init_legacy_realistic_bar_loop_state_v1,
)
from src.backtest.engine import BacktestEngine
from src.backtest import mv2_research_wiring_v1 as wiring
from src.ops.double_play.specialists import evaluate_double_play
from src.ops.gates.switch_gate import SwitchGateConfig, SwitchGateState, step_switch_gate
from trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_SCOPE_STATE_OWNER,
    CANONICAL_SWITCH_AUTHORITY,
    CHOP_BINDING_STATUS,
    CHOP_CAN_CREATE_DIRECTION,
    CHOP_CAN_TRIGGER_SWITCH,
    OPS_SWITCH_AUTHORIZATION,
    UNKNOWN_BINDING_STATUS,
    UNKNOWN_CAN_CREATE_DIRECTION,
    UNKNOWN_CAN_TRIGGER_SWITCH,
    build_double_play_sole_authority_status_fields_v1,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState, transition_state
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    make_offline_scenario_replay_input_for_tests_v0,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
)


def test_sole_owners_are_unique_and_canonical() -> None:
    fields = build_double_play_sole_authority_status_fields_v1()
    assert fields["CANONICAL_BULL_BEAR_STATE_OWNER"] == CANONICAL_BULL_BEAR_STATE_OWNER
    assert fields["CANONICAL_SWITCH_AUTHORITY"] == CANONICAL_SWITCH_AUTHORITY
    assert fields["CANONICAL_SCOPE_STATE_OWNER"] == CANONICAL_SCOPE_STATE_OWNER
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert "RuntimeScopeState" in CANONICAL_SCOPE_STATE_OWNER
    assert fields["DOUBLE_PLAY_PRIMARY_SSOT_CONFIRMED"] == "true"


def test_ops_evaluate_double_play_is_projection_only_no_switch() -> None:
    d = evaluate_double_play(
        context={
            "double_play_enabled": True,
            "switch_gate": {
                "score": -1.0,
                "state": {"active": "bull", "hold_remaining": 0, "cooldown_remaining": 0},
                "cfg": {"hysteresis": 0.1, "min_hold_steps": 0, "cooldown_steps": 0},
            },
        }
    )
    assert d.active_specialist == "bull"
    assert d.details["switch_gate_invoked"] is False
    assert d.details["switch_authorization"] == OPS_SWITCH_AUTHORIZATION == "false"
    assert d.details["may_write_side_state"] == "false"
    assert "ops_switch_authority_fail_closed_disabled" in d.reasons


def test_ops_switch_gate_primitive_does_not_feed_evaluate_double_play() -> None:
    # Primitive remains unit-testable but is not wired through evaluate_double_play.
    st = step_switch_gate(
        score=-1.0,
        state=SwitchGateState(active="bull"),
        cfg=SwitchGateConfig(hysteresis=0.1),
    )
    assert st.active == "bear"
    d = evaluate_double_play(
        context={
            "double_play_enabled": True,
            "switch_gate": {
                "score": -1.0,
                "state": {"active": "bull"},
                "cfg": {"hysteresis": 0.1},
            },
        }
    )
    assert d.active_specialist == "bull"
    assert d.details["switch_gate_invoked"] is False


def test_unmarked_scenario_scope_event_fail_closed() -> None:
    tick = OfflineDoublePlayScenarioTickV0(
        tick_index=0,
        timestamp_ms=1,
        price=100.0,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_event_provenance="UNMARKED",
    )
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id="ETH-PERP",
        ticks=(tick,),
        allow_test_scope_event_injection=False,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any(
        "scenario_scope_event_injection_requires_explicit_test_harness_flag" in r for r in reasons
    )
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert result.replay_pass is False


def test_test_harness_injection_allowed_when_marked() -> None:
    tick = OfflineDoublePlayScenarioTickV0(
        tick_index=0,
        timestamp_ms=1,
        price=100.0,
        scope_event=ScopeEvent.NOOP,
        scope_event_provenance="UNMARKED",
    )
    inp = make_offline_scenario_replay_input_for_tests_v0(
        selected_future_id="ETH-PERP",
        ticks=(tick,),
    )
    assert inp.allow_test_scope_event_injection is True
    assert inp.ticks[0].scope_event_provenance == "TEST_INJECTION"
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert reasons == [] or not any("unmarked_scope_event" in r for r in reasons)


def test_backtest_feedback_does_not_overwrite_side_state() -> None:
    initial = wiring.build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    prior_side = initial.side_state
    prior_dir = initial.direction_state
    prior_scope_dir = initial.scope_direction_state
    prior_runtime = initial.runtime_scope_state
    feedback = BacktestEnginePositionFeedbackV1(
        feedback_source_bar_epoch=0,
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        venue_flat=False,
        side_state=SideState.LONG_ACTIVE,  # hostile payload — must be ignored
        direction_state=EntryExitDirectionState.LONG_ACTIVE,
        position_management_context=PositionManagementContext.LONG_POSITION,
        reconciliation_state=ReconciliationState.RECONCILED,
        has_open_trade=True,
    )
    updated = wiring.apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1(
        initial, feedback
    )
    assert updated.side_state == prior_side
    assert updated.direction_state == prior_dir
    assert updated.scope_direction_state == prior_scope_dir
    assert updated.runtime_scope_state is prior_runtime
    assert updated.position_state == PositionState.OPEN_FULL
    assert updated.existing_position_side == ExistingPositionSide.LONG
    assert BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE is False
    assert BACKTEST_POSITION_FEEDBACK_ROLE == "OBSERVATION_ONLY"


def test_capture_feedback_never_invents_long_side_state() -> None:
    engine = BacktestEngine(use_execution_pipeline=False)
    engine.config = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.004,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }
    state = init_legacy_realistic_bar_loop_state_v1(engine, strategy_params={"stop_pct": 0.02})
    flat = capture_backtest_engine_position_feedback_v1(state=state, feedback_source_bar_epoch=0)
    assert flat.side_state == SideState.NEUTRAL_OBSERVE
    assert flat.direction_state == EntryExitDirectionState.NEUTRAL
    assert flat.existing_position_side == ExistingPositionSide.NONE
    assert flat.authority_role == "OBSERVATION_ONLY"


def test_chop_unknown_invariants_preserved() -> None:
    fields = build_double_play_sole_authority_status_fields_v1()
    assert fields["CHOP_BINDING_STATUS"] == CHOP_BINDING_STATUS == "NOT_BOUND_FAIL_CLOSED"
    assert fields["UNKNOWN_BINDING_STATUS"] == UNKNOWN_BINDING_STATUS == "NOT_BOUND_FAIL_CLOSED"
    assert fields["CHOP_CAN_CREATE_DIRECTION"] == CHOP_CAN_CREATE_DIRECTION == "false"
    assert fields["UNKNOWN_CAN_CREATE_DIRECTION"] == UNKNOWN_CAN_CREATE_DIRECTION == "false"
    assert fields["CHOP_CAN_TRIGGER_SWITCH"] == CHOP_CAN_TRIGGER_SWITCH == "false"
    assert fields["UNKNOWN_CAN_TRIGGER_SWITCH"] == UNKNOWN_CAN_TRIGGER_SWITCH == "false"


def test_transition_state_remains_switch_owner_for_confirmed_events() -> None:
    from trading.master_v2.double_play_state import (
        DynamicScopeRules,
        RuntimeEnvelope,
        RuntimeScopeState,
        StaticHardLimits,
    )

    env = RuntimeEnvelope(static=StaticHardLimits(min_band_width=1.0), live_authorization=False)
    rules = DynamicScopeRules(min_band_width=1.0)
    st = RuntimeScopeState(anchor_price=100.0)
    next_side, _, decision = transition_state(
        side_state=SideState.NEUTRAL_OBSERVE,
        event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_state=st,
        rules=rules,
        envelope=env,
        now_tick=1,
    )
    assert decision.allowed is True
    assert next_side is SideState.LONG_ARMED
