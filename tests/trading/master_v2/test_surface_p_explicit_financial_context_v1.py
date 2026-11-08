"""Current financial fixture inputs must reach the original sizing/intent owners."""

from dataclasses import replace
from decimal import Decimal, ROUND_DOWN

import pytest

from trading.master_v2 import (
    capital_risk_sizing_offline_replay_binding_adapter_v0 as sizing,
    canonical_order_intent_offline_replay_binding_adapter_v0 as intents,
    integrated_vs_scenario_replay_full_system_parity_harness_v0 as harness,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OfflineDoublePlayScenarioReplayInputV0,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)


KINDS = ["capital_risk_sizing_path", "canonical_order_intent_path"]


def financial_fixture(kind=KINDS[1], side="long", monkeypatch=None):
    fixture = next(
        f for f in harness.surface_p_core_bar_sequence_fixtures_v0() if f.path_kind == kind
    )
    if side == "short":
        # The default multi-tick fixture has no SHORT entry. Supply the real
        # current SHORT policy output as an isolated adapter counterfactual.
        assert monkeypatch is not None
        tick = harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture)
        fixture = replace(fixture, scenario_side_state=SideState.SHORT_ARMED)
        matrix = harness.evaluate_scenario_matrix_for_side_state_v0(
            side_state=SideState.SHORT_ARMED,
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
        )
        decision = harness.evaluate_scenario_entry_exit_for_fixture_v0(
            side_state=SideState.SHORT_ARMED,
            instrument_id=fixture.instrument_id,
            trading_epoch=fixture.trading_epoch,
            context_reference=fixture.context_reference,
            matrix_result=matrix,
            policy_context=harness.default_scenario_entry_exit_policy_context_v0(),
        )
        assert decision.decision_outcome.value == "enter_short"
        tick = replace(
            tick,
            side_state=SideState.SHORT_ARMED,
            composition_result_id=matrix.composition_id,
            entry_exit_policy_ref=decision.policy_decision_id,
            entry_exit_decision_outcome=decision.decision_outcome.value,
            entry_exit_reason_codes=decision.reason_codes,
            entry_exit_decision_precedence_trace=decision.decision_precedence_trace,
        )
        monkeypatch.setattr(
            harness, "_surface_p_scenario_replay_tick_for_fixture_v0", lambda f: tick
        )
        price = Decimal(str(tick.price))
        fixture = replace(
            fixture,
            capital_context=replace(
                fixture.capital_context, reference_price=price, protective_stop_price=price + 2
            ),
        )
    return fixture


def no_legacy_context(*args, **kwargs):
    raise AssertionError("Explicit current fixture must not recover legacy account literals")


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("side", ["long", "short"])
def test_current_financial_paths_bind_explicit_context_and_policy_side(monkeypatch, kind, side):
    fixture = financial_fixture(kind, side, monkeypatch)
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    direct = harness.build_surface_p_fixture_integrated_envelope_v0(fixture)
    scenario = harness.build_surface_p_fixture_scenario_envelope_v0(fixture)
    assert direct is not None and scenario is not None
    assert direct == scenario
    assert direct.decision_outcome == "enter_" + side
    assert direct.quantity_status in {"PASS", "REDUCE"}
    assert direct.quantity_provenance_ref and direct.risk_sizing_ref
    assert direct.risk_sizing_effect == "BOUND_OFFLINE"
    assert direct.authority_effect == direct.runtime_effect == "NONE"
    assert direct.execution_eligible is direct.adapter_compatible is False
    if kind == KINDS[1]:
        assert direct.order_intent_effect == "BOUND_OFFLINE" and direct.order_intent_ref


@pytest.mark.parametrize("scope_cap,expected", [("120", "1.20"), ("80", "0.80")])
def test_explicit_capital_changes_actual_stored_owner_quantity(monkeypatch, scope_cap, expected):
    fixture = financial_fixture()
    tick = harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture)
    parent = harness._surface_p_financial_evidence_v1(fixture, tick)
    context = replace(fixture.capital_context, scope_capital_limit=Decimal(scope_cap))
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    result = sizing.evaluate_scenario_capital_risk_sizing_v0(parent, capital_context=context)
    intent = intents.evaluate_scenario_canonical_order_intent_v0(
        result.evidence, sizing_decision=result.sizing_decision, capital_context=context
    )
    assert result.sizing_decision.outcome.value == "PASS"
    assert result.sizing_decision.final_quantity == Decimal(expected)
    assert (
        result.sizing_decision.canonical_position_sizing.resulting_notional
        == Decimal(expected) * 100
    )
    assert intent.canonical_intent.quantity == Decimal(expected)
    assert intent.canonical_intent.side.lower() == "long"
    assert result.evidence.execution_eligible is intent.evidence.execution_eligible is False


@pytest.mark.parametrize("side", ["long", "short"])
def test_short_and_long_native_quantity_reach_original_intent(monkeypatch, side):
    fixture = financial_fixture(side=side, monkeypatch=monkeypatch)
    tick = harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture)
    parent = harness._surface_p_financial_evidence_v1(fixture, tick)
    context = fixture.capital_context
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    result = sizing.evaluate_scenario_capital_risk_sizing_v0(parent, capital_context=context)
    intent = intents.evaluate_scenario_canonical_order_intent_v0(
        result.evidence, sizing_decision=result.sizing_decision, capital_context=context
    )
    expected = (Decimal("120") / context.reference_price).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    assert result.sizing_decision.final_quantity == expected
    assert intent.canonical_intent.quantity == expected
    assert parent.selected_side == side
    assert intent.canonical_intent.side.lower() == side


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "foreign_instrument",
        "wrong_price",
        "live_mode",
        "wrong_type",
        "zero_capital",
        "missing_stop",
        "unknown_side",
    ],
)
def test_invalid_financial_fixture_cannot_be_promoted(kind, fault):
    fixture = financial_fixture(kind)
    context = fixture.capital_context
    if fault == "missing":
        context = None
    elif fault == "foreign_instrument":
        context = replace(
            context, instrument=replace(context.instrument, instrument_id="foreign-future")
        )
    elif fault == "wrong_price":
        context = replace(context, reference_price=context.reference_price + 1)
    elif fault == "live_mode":
        context = replace(context, capital_risk_mode="LIVE_ACCOUNT_BOUND")
    elif fault == "wrong_type":
        context = {}
    elif fault == "zero_capital":
        context = replace(context, account_equity=Decimal(0))
    elif fault == "missing_stop":
        context = replace(context, protective_stop_price=None)
    elif fault == "unknown_side":
        fixture = replace(fixture, scenario_side_state=SideState.CHOP_GUARD_BLOCK)
    result = harness.evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0(
        replace(fixture, capital_context=context)
    )
    assert result.four_way_fixture_parity_bound is False
    assert result.integrated_scenario_evidence_aligned is False
    assert result.fail_closed_reasons


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_outcome", "blocked"),
        ("quantity_status", "BLOCK"),
        ("quantity_provenance_ref", "different-quantity"),
        ("risk_sizing_ref", "different-risk"),
        ("order_intent_ref", "different-intent"),
    ],
)
def test_equal_bound_labels_do_not_hide_financial_result_drift(monkeypatch, kind, field, value):
    fixture = financial_fixture(kind)
    original = harness.build_surface_p_fixture_scenario_envelope_v0
    monkeypatch.setattr(
        harness,
        "build_surface_p_fixture_scenario_envelope_v0",
        lambda f: replace(original(f), **{field: value}),
    )
    result = harness.evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0(fixture)
    assert result.scenario_lane_bound and result.integrated_lane_bound
    assert result.four_way_fixture_parity_bound is False
    assert "integrated_scenario_evidence_not_aligned" in result.fail_closed_reasons


def test_explicit_none_does_not_fall_back_in_either_wrapper(monkeypatch):
    fixture = financial_fixture()
    parent = harness._surface_p_financial_evidence_v1(
        fixture, harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture)
    )
    valid = sizing.evaluate_scenario_capital_risk_sizing_v0(
        parent, capital_context=fixture.capital_context
    )
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    absent = sizing.evaluate_scenario_capital_risk_sizing_v0(parent, capital_context=None)
    assert absent.sizing_decision is None and absent.risk_sizing_effect == "NONE"
    assert "CAPITAL_RISK_CONTEXT_UNRESOLVED" in absent.evidence.reason_codes
    intent = intents.evaluate_scenario_canonical_order_intent_v0(
        valid.evidence, sizing_decision=valid.sizing_decision, capital_context=None
    )
    assert intent.canonical_intent is None and intent.order_intent_effect == "NONE"
    assert "CAPITAL_RISK_CONTEXT_UNRESOLVED" in intent.evidence.reason_codes


@pytest.mark.parametrize("kind", KINDS)
def test_default_sequence_does_not_invent_missing_short_entry(kind):
    fixture = replace(financial_fixture(kind), scenario_side_state=SideState.SHORT_ARMED)
    assert harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture) is None
    assert harness.build_surface_p_fixture_integrated_envelope_v0(fixture) is None
    assert harness.build_surface_p_fixture_scenario_envelope_v0(fixture) is None


@pytest.mark.parametrize("fault", ["wrong_type", "conflicting_price"])
def test_explicit_context_errors_do_not_recover_defaults(monkeypatch, fault):
    fixture = financial_fixture()
    parent = harness._surface_p_financial_evidence_v1(
        fixture, harness._surface_p_scenario_replay_tick_for_fixture_v0(fixture)
    )
    valid = sizing.evaluate_scenario_capital_risk_sizing_v0(
        parent, capital_context=fixture.capital_context
    )
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    kwargs = (
        dict(capital_context={})
        if fault == "wrong_type"
        else dict(capital_context=fixture.capital_context, reference_price=Decimal("101"))
    )
    with pytest.raises(ValueError, match="SCENARIO_EXPLICIT"):
        sizing.evaluate_scenario_capital_risk_sizing_v0(parent, **kwargs)
    with pytest.raises(ValueError, match="SCENARIO_EXPLICIT"):
        intents.evaluate_scenario_canonical_order_intent_v0(
            valid.evidence, sizing_decision=valid.sizing_decision, **kwargs
        )


@pytest.mark.parametrize("populated", [False, True])
def test_scenario_replay_uses_explicit_per_tick_context_without_legacy_values(
    monkeypatch, populated
):
    context = financial_fixture().capital_context
    monkeypatch.setattr(
        sizing, "isolated_offline_replay_fixture_capital_context_v0", no_legacy_context
    )
    result = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=context.instrument.instrument_id,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            allow_test_scope_event_injection=True,
            capital_contexts_by_tick={0: context} if populated else {},
        )
    )
    assert result.replay_pass
    first = result.tick_records[0]
    assert first.orders == first.fills == first.positions_opened == 0
    assert first.quantity_status == ("PASS" if populated else "NOT_BOUND")
    assert first.order_intent_effect == ("BOUND_OFFLINE" if populated else "NONE")
    assert all(t.risk_sizing_effect == "NONE" for t in result.tick_records[1:])
    assert result.summary.orders_total == result.summary.fills_total == 0
