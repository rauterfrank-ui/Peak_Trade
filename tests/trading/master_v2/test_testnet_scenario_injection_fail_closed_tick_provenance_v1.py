"""Fail-closed scenario injection default + required tick provenance v1."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    TestnetCompletionPathMarketInputV0 as MarketInputV0,
    build_replay_input_from_testnet_market_input,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_SCOPE_STATE_OWNER,
    CANONICAL_SWITCH_AUTHORITY,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    RUNTIME_BRIDGE_STATUS,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState, transition_state
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_SCENARIO_TICK_PROVENANCE_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioTickV0,
    OfflineScenarioTickProvenanceV1,
    SYNTHETIC_FUTURES_INSTRUMENT,
    build_default_bull_bear_bull_scenario_ticks,
    make_offline_scenario_replay_input_for_tests_v0,
    make_offline_scenario_tick_provenance_v1,
    resolve_allow_test_scope_event_injection,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
    validate_offline_scenario_tick_provenance_v1,
)


def _valid_provenance(*, tick_index: int = 0) -> OfflineScenarioTickProvenanceV1:
    return make_offline_scenario_tick_provenance_v1(
        source_kind="offline_scenario_fixture",
        source_id="injection_fail_closed_contract_v1",
        tick_index=tick_index,
        event_time_ms=1_700_000_000_000 + tick_index * 60_000,
        sequence_number=tick_index,
    )


def _tick(
    *,
    tick_index: int = 0,
    provenance: OfflineScenarioTickProvenanceV1 | None = None,
    mark: str = "TEST_INJECTION",
    event: ScopeEvent = ScopeEvent.NOOP,
) -> OfflineDoublePlayScenarioTickV0:
    return OfflineDoublePlayScenarioTickV0(
        tick_index=tick_index,
        timestamp_ms=1_700_000_000_000 + tick_index * 60_000,
        price=100.0 + tick_index,
        scope_event=event,
        scope_event_provenance=mark,
        tick_provenance=provenance,
    )


def test_allow_injection_default_false_on_replay_input() -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(_tick(provenance=_valid_provenance()),),
    )
    assert inp.allow_test_scope_event_injection is False
    field = next(
        f
        for f in fields(OfflineDoublePlayScenarioReplayInputV0)
        if f.name == ("allow_test_scope_event_injection")
    )
    assert field.default is False


def test_allow_injection_default_false_on_testnet_market_input() -> None:
    market = MarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_run_id="default-check",
    )
    assert market.allow_test_scope_event_injection is False
    field = next(f for f in fields(MarketInputV0) if f.name == "allow_test_scope_event_injection")
    assert field.default is False


def test_missing_field_and_truthy_strings_resolve_false() -> None:
    assert resolve_allow_test_scope_event_injection(None) is False
    assert resolve_allow_test_scope_event_injection(False) is False
    assert resolve_allow_test_scope_event_injection("true") is False
    assert resolve_allow_test_scope_event_injection("1") is False
    assert resolve_allow_test_scope_event_injection("yes") is False
    assert resolve_allow_test_scope_event_injection("on") is False
    assert resolve_allow_test_scope_event_injection(1) is False
    assert resolve_allow_test_scope_event_injection(True) is True


def test_build_replay_input_defaults_fail_closed_without_opt_in() -> None:
    market = MarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_run_id="no-opt-in",
    )
    replay = build_replay_input_from_testnet_market_input(market)
    assert replay.allow_test_scope_event_injection is False
    reasons = validate_offline_double_play_scenario_replay_input_v0(replay)
    assert any("requires_explicit_test_harness_flag" in r for r in reasons)


def test_explicit_opt_in_with_valid_provenance_accepted() -> None:
    tick = _tick(provenance=_valid_provenance())
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(tick,),
        allow_test_scope_event_injection=True,
        execution_surface="offline_scenario",
    )
    assert validate_offline_double_play_scenario_replay_input_v0(inp) == []


def test_true_without_provenance_blocked() -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(_tick(provenance=None),),
        allow_test_scope_event_injection=True,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("scenario_tick_provenance_required" in r for r in reasons)


def test_false_with_provenance_blocked() -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(_tick(provenance=_valid_provenance()),),
        allow_test_scope_event_injection=False,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("requires_explicit_test_harness_flag" in r for r in reasons)


@pytest.mark.parametrize("surface", ["runtime", "live", "order", "exchange", "testnet_runtime"])
def test_runtime_live_order_surfaces_blocked(surface: str) -> None:
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(_tick(provenance=_valid_provenance()),),
        allow_test_scope_event_injection=True,
        execution_surface=surface,
    )
    reasons = validate_offline_double_play_scenario_replay_input_v0(inp)
    assert any("execution_surface_forbidden" in r for r in reasons)


def test_build_replay_input_opt_in_requires_provenance() -> None:
    bare = OfflineDoublePlayScenarioTickV0(
        tick_index=0,
        timestamp_ms=1_700_000_000_000,
        price=100.0,
        scope_event=ScopeEvent.NOOP,
        scope_event_provenance="TEST_INJECTION",
    )
    market = MarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(bare,),
        source_run_id="missing-prov",
        allow_test_scope_event_injection=True,
    )
    with pytest.raises(ValueError, match="validated tick provenance"):
        build_replay_input_from_testnet_market_input(market)


def test_build_replay_input_opt_in_with_provenance_ok() -> None:
    market = MarketInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_run_id="with-prov",
        allow_test_scope_event_injection=True,
    )
    replay = build_replay_input_from_testnet_market_input(market)
    assert replay.allow_test_scope_event_injection is True
    assert validate_offline_double_play_scenario_replay_input_v0(replay) == []


def test_provenance_full_valid_accepted() -> None:
    assert validate_offline_scenario_tick_provenance_v1(_valid_provenance()) == []


def test_provenance_missing_source_kind_blocked() -> None:
    bad = replace(_valid_provenance(), source_kind="")
    assert any(
        "unknown_source_kind" in r for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_provenance_missing_source_id_blocked() -> None:
    bad = replace(_valid_provenance(), source_id="", fixture_id="")
    assert any(
        "missing_source_id_or_fixture_id" in r
        for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_provenance_missing_sequence_blocked() -> None:
    # sequence_number is required int; negative is invalid
    bad = replace(_valid_provenance(), sequence_number=-1)
    assert any(
        "negative_sequence_number" in r for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_provenance_missing_event_time_blocked() -> None:
    bad = replace(_valid_provenance(), event_time_ms=0)
    assert any(
        "missing_or_invalid_event_time" in r
        for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_provenance_unknown_version_blocked() -> None:
    bad = replace(_valid_provenance(), provenance_version="v99")
    assert any(
        "unknown_provenance_version" in r for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_provenance_unknown_source_kind_blocked() -> None:
    bad = replace(_valid_provenance(), source_kind="invented_kind")
    assert any(
        "unknown_source_kind" in r for r in validate_offline_scenario_tick_provenance_v1(bad)
    )


def test_injection_does_not_bypass_transition_state_for_switch() -> None:
    from trading.master_v2.double_play_state import (
        DynamicScopeRules,
        RuntimeEnvelope,
        RuntimeScopeState,
        StaticHardLimits,
    )

    # Injection may supply ScopeEvent only; SideState/Switch remain transition_state-owned.
    inp = make_offline_scenario_replay_input_for_tests_v0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
    )
    assert validate_offline_double_play_scenario_replay_input_v0(inp) == []
    result = run_offline_double_play_scenario_replay_v0(inp)
    assert result.replay_pass is True, result.fail_reasons
    assert result.summary.orders_total == 0
    # Side transitions observed via canonical transition_state path only.
    assert any(r.transition_reason_code for r in result.tick_records)
    env = RuntimeEnvelope(static=StaticHardLimits(min_band_width=1.0), live_authorization=False)
    next_side, _, decision = transition_state(
        side_state=SideState.NEUTRAL_OBSERVE,
        event=ScopeEvent.UPSCOPE_CONFIRMED,
        scope_state=RuntimeScopeState(anchor_price=100.0),
        rules=DynamicScopeRules(min_band_width=1.0),
        envelope=env,
        now_tick=1,
    )
    assert decision.allowed is True
    assert next_side is SideState.LONG_ARMED
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert "RuntimeScopeState" in CANONICAL_SCOPE_STATE_OWNER
    assert OFFLINE_SCENARIO_TICK_PROVENANCE_OWNER.endswith("OfflineScenarioTickProvenanceV1")
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    assert RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"


def test_factory_marks_provenance_and_opt_in() -> None:
    bare = _tick(provenance=None, mark="UNMARKED")
    inp = make_offline_scenario_replay_input_for_tests_v0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=(bare,),
    )
    assert inp.allow_test_scope_event_injection is True
    assert inp.ticks[0].scope_event_provenance == "TEST_INJECTION"
    assert inp.ticks[0].tick_provenance is not None
    assert validate_offline_double_play_scenario_replay_input_v0(inp) == []
