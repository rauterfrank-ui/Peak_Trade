"""Offline SOPH model capital: original CRS/intent, units, readback and cost veto."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, ROUND_FLOOR
from hashlib import sha256
import json
import socket
from types import SimpleNamespace

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    bind_zkp_paper_market_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1
from src.ops.instrument_card_stream_v1 import shadow_budget_source_v1
from src.ops.soph_shadow_capital_risk_binding_v1 import (
    soph_shadow_capital_binding_v1,
    soph_shadow_cost_check_v1,
    soph_shadow_portfolio_action_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from tests.ops.test_instrument_card_stream_v1 import SOPH, REPO
from tests.ops.test_zkp_lane1_paper_opening_v1 import _market, _observations
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    bind_canonical_order_intent_offline_replay_evidence_v0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    build_mv2_dynamic_boundary_capital_context_v1,
    build_mv2_offline_boundary_dynamic_price_context_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
    overlay_portfolio_observation_on_capital_context_v0,
)

D = Decimal


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("OFFLINE_ONLY")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)


def setup_market(*, fx="1", **kwargs):
    observations, policy, now = _observations(slot=SOPH, depth=10000, **kwargs)
    receipt = observations["usdc-index"]
    payload = deepcopy(receipt.payload)
    payload["data"][0]["idxPx"] = fx
    observations["usdc-index"] = replace(
        receipt, payload=payload, body_sha256=sha256(json.dumps(payload).encode()).hexdigest()
    )
    market = bind_zkp_paper_market_v1(observations, policy=policy, observed_unix=now, slot=SOPH)
    state = HardenedBridgeSessionStateV2(
        instrument_id=SOPH.instrument_id, venue_instrument_id=SOPH.native_id
    )
    source = shadow_budget_source_v1(state, repo=REPO)
    return market, state, source


def context_for(state, market, budget, side="long"):
    boundary, position, receipt = soph_shadow_capital_binding_v1(
        state=state, market=market, budget=budget, now=market.observed_unix
    )
    price = build_mv2_offline_boundary_dynamic_price_context_v1(
        mark_price=market.mark, selected_side=side, adverse_exit_distance=market.mark / 10
    )
    context = overlay_portfolio_observation_on_capital_context_v0(
        build_mv2_dynamic_boundary_capital_context_v1(
            state_file=boundary, dynamic_price_context=price
        ),
        position,
    )
    return context, receipt


def scenario_evidence(side, outcome):
    # Explicit mechanism fixture; no claim of a natural full-Core entry.
    return build_scenario_tick_decision_evidence_v0(
        decision_id="offline-mechanism",
        replay_id="offline-mechanism",
        instrument_id=SOPH.instrument_id,
        trading_epoch=1,
        composition_result_id="explicit-mechanism-composition",
        entry_exit_policy_ref="explicit-mechanism-policy",
        selected_side=side,
        decision_outcome=outcome,
        reason_codes=(),
        decision_precedence_trace=(),
        config_digest="a" * 64,
        implementation_digest="b" * 64,
    )


@pytest.mark.parametrize("fx", ["0.8", "1", "2"])
@pytest.mark.parametrize("side", ["long", "short"])
def test_actual_sizing_and_intent_consume_converted_budget_and_native_grid(fx, side):
    market, state, source = setup_market(fx=fx)
    budget = source(market=market, now=market.observed_unix)
    before = state.portfolio.snapshot()
    context, receipt = context_for(state, market, budget, side)
    sizing = bind_capital_risk_sizing_offline_replay_evidence_v0(
        scenario_evidence(side, "enter_" + side), capital_context=context
    )
    assert sizing.sizing_decision.outcome.value == "PASS", sizing.sizing_decision
    expected = (25 * D(fx) / market.mark / 10).to_integral_value(rounding=ROUND_FLOOR)
    assert sizing.sizing_decision.final_quantity == expected
    intent = bind_canonical_order_intent_offline_replay_evidence_v0(
        sizing.evidence, sizing_decision=sizing.sizing_decision, capital_context=context
    )
    assert intent.canonical_intent.quantity == expected
    assert intent.canonical_intent.side.lower() == side
    action, projection = soph_shadow_portfolio_action_v1(
        replay=SimpleNamespace(
            evidence=intent.evidence,
            replay_pass=True,
            intermediate=SimpleNamespace(canonical_order_intent=intent.canonical_intent),
        ),
        state=state,
        market=market,
    )
    assert action.intended_quantity == expected * 10
    assert D(projection["mapper_quantity_contracts"]) == expected
    assert projection["portfolio_quantity_unit"] == "SOPH"
    assert not intent.evidence.execution_eligible
    assert intent.canonical_intent.quantity_unit == "CONTRACTS"
    assert context.instrument.contract_multiplier == 10
    assert context.instrument.lot_size == context.instrument.minimum_quantity == 1
    assert context.scope_capital_limit == context.total_capital_limit == D(fx) * 25
    assert context.account_equity == D(fx) * 25
    assert receipt["capital_risk_mode"] == "OFFLINE_ALGEBRA" and receipt["authority"] == "NONE"
    assert receipt["daily_loss_field_lineage"].endswith("NOT_ACCOUNT_DAILY_BALANCE")
    assert state.portfolio.snapshot() == before


@pytest.mark.parametrize("side", ["BUY", "SELL"])
def test_flat_notional_capacity_is_vetoed_when_model_costs_do_not_fit(side):
    market, state, source = setup_market(price=D("0.02498"))
    budget = source(market=market, now=market.observed_unix)
    quantity = D(1000)
    notional = assess_instrument_budget_v1(
        market=market, available_usdc="25", side=side, quantity_contracts=quantity / 10
    )
    assert notional["measurement_admitted"] and not notional["fees_and_funding_included"]
    check = soph_shadow_cost_check_v1(
        state=state,
        market=market,
        budget=budget,
        side=side,
        quantity=quantity,
        stop_distance=market.mark / 10,
    )
    assert not check["measurement_admitted"] and check["fees_and_funding_included"]
    assert check["reason_codes"] == ["SOPH_SHADOW_MODEL_COST_ENVELOPE_EXCEEDED"]
    costs = check["model_costs"]
    assert all(
        D(costs[key]) > 0
        for key in (
            "opening_fee",
            "opening_slippage",
            "closing_fee_allowance",
            "closing_slippage_allowance",
            "next_funding_allowance",
        )
    )
    smaller = soph_shadow_cost_check_v1(
        state=state,
        market=market,
        budget=budget,
        side=side,
        quantity=D(990),
        stop_distance=market.mark / 10,
    )
    assert smaller["measurement_admitted"]
    assert state.portfolio.model.params.fee_rate_bps == 2
    assert state.portfolio.model.params.slippage_bps == 1
    assert state.portfolio.model.params.funding_rate_per_interval == 0


@pytest.mark.parametrize("side", ["long", "short"])
def test_original_exit_uses_actual_open_quantity_with_zero_free_entry_capital(side):
    market, state, source = setup_market()
    source(market=market, now=market.observed_unix)
    state.portfolio.apply_intended_action(
        instrument_id=state.instrument_id,
        side="BUY" if side == "long" else "SELL",
        quantity=D(20),
        mark_price=market.mark,
        intent_id="seed",
        fill_id="seed-fill",
    )
    budget = source(market=market, now=market.observed_unix)
    assert D(budget["available_for_new_entry"]) == 0
    context, _ = context_for(state, market, budget, side)
    assert context.reconciled_open_position_quantity == 2
    sizing = bind_capital_risk_sizing_offline_replay_evidence_v0(
        scenario_evidence(side, "exit"), capital_context=context
    )
    assert sizing.sizing_decision.final_quantity == 2, sizing.sizing_decision
    intent = bind_canonical_order_intent_offline_replay_evidence_v0(
        sizing.evidence, sizing_decision=sizing.sizing_decision, capital_context=context
    )
    assert intent.canonical_intent.quantity == 2
    assert intent.canonical_intent.reduce_only
    action, _ = soph_shadow_portfolio_action_v1(
        replay=SimpleNamespace(
            evidence=intent.evidence,
            replay_pass=True,
            intermediate=SimpleNamespace(canonical_order_intent=intent.canonical_intent),
        ),
        state=state,
        market=market,
    )
    assert action.intended_quantity == 20
    assert action.intended_side == ("SELL" if side == "long" else "BUY")


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "lane",
        "instrument",
        "currency",
        "owner",
        "digest",
        "amount",
        "free",
        "time",
        "future",
        "nan_time",
        "missing_snapshot",
        "equity_readback",
        "marked_readback",
        "fx_readback",
        "policy_readback",
        "portfolio_changed",
        "foreign_position",
    ],
)
def test_bad_capital_is_rejected_before_original_cycle_or_portfolio_mutation(fault):
    market, state, source = setup_market()
    budget = source(market=market, now=market.observed_unix)
    if fault == "missing":
        budget = None
    elif fault in {"lane", "instrument", "currency", "owner", "digest"}:
        field = dict(
            lane="lane_id",
            instrument="instrument_id",
            currency="currency",
            owner="owner",
            digest="source_digest",
        )[fault]
        budget[field] = "foreign"
    elif fault in {"amount", "free"}:
        budget["available_amount" if fault == "amount" else "available_for_new_entry"] = "100000"
    elif fault in {"time", "future", "nan_time"}:
        budget["observed_unix"] = (
            float("nan")
            if fault == "nan_time"
            else market.observed_unix + (1 if fault == "future" else -1)
        )
    elif fault == "missing_snapshot":
        budget.pop("original_snapshot")
    elif fault == "portfolio_changed":
        state.portfolio.model.state.cash -= 1
    else:
        snapshot = budget["original_snapshot"]
        if fault == "equity_readback":
            snapshot["original_portfolio"]["state"]["equity"] = "100000"
        elif fault == "marked_readback":
            snapshot["marked_portfolio"]["state"]["cash"] = "100000"
        elif fault == "fx_readback":
            snapshot["usd_per_usdc"] = "2"
        elif fault == "policy_readback":
            snapshot["policy"]["per_slot_test_loss_limit"] = "100000"
        elif fault == "foreign_position":
            from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
                SimulatedPositionV1,
            )

            state.portfolio.model.state.positions["foreign"] = SimulatedPositionV1(
                "foreign", quantity=D(1)
            )
            budget = source(market=market, now=market.observed_unix)
            snapshot = budget["original_snapshot"]
        budget["source_digest"] = canonical_digest_v1(snapshot)
    before = state.portfolio.snapshot()
    with pytest.raises(ValueError, match="SOPH_SHADOW_CAPITAL"):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=float(market.mark),
            event_ts_unix=market.observed_unix,
            session_id="offline-invalid-input",
            instrument_card_market=market,
            instrument_card_budget=budget,
        )
    assert state.cycle_index == 0 and state.session_id == ""
    assert state.portfolio.snapshot() == before


def test_fresh_mark_uses_current_fx_without_reinitializing_original_capital():
    market, state, source = setup_market(fx="1")
    source(market=market, now=market.observed_unix)
    changed, _, _ = setup_market(fx="0.8")
    budget = source(market=changed, now=changed.observed_unix)
    context, _ = context_for(state, changed, budget)
    assert context.account_equity == 25
    assert context.scope_capital_limit == context.total_capital_limit == 20
    assert D(state.portfolio.snapshot()["params"]["initial_equity"]) == 25


def test_current_market_expiry_and_exhausted_equity_are_not_refilled():
    market, state, source = setup_market()
    budget = source(market=market, now=market.observed_unix)
    with pytest.raises(ValueError):
        soph_shadow_capital_binding_v1(
            state=state, market=market, budget=budget, now=market.funding_time_unix
        )
    state.portfolio.model.state.cash = D(0)
    budget = source(market=market, now=market.observed_unix)
    with pytest.raises(ValueError, match="CAPITAL_EXHAUSTED"):
        context_for(state, market, budget)
    assert D(state.portfolio.snapshot()["state"]["cash"]) == 0


@pytest.mark.parametrize("fault", ["type", "identity", "market", "kind"])
def test_explicit_native_constraints_never_fall_back_to_multiplier_one(fault):
    market, state, source = setup_market()
    boundary, _, _ = soph_shadow_capital_binding_v1(
        state=state,
        market=market,
        budget=source(market=market, now=market.observed_unix),
        now=market.observed_unix,
    )
    constraints = boundary.instrument_quantity_constraints
    changed = (
        {}
        if fault == "type"
        else replace(
            constraints,
            **{
                "instrument_id"
                if fault == "identity"
                else "market_type"
                if fault == "market"
                else "contract_kind": "foreign"
            },
        )
    )
    with pytest.raises(ValueError, match="explicit_instrument_constraints_invalid"):
        build_mv2_dynamic_boundary_capital_context_v1(
            state_file=replace(boundary, instrument_quantity_constraints=changed),
            dynamic_price_context=build_mv2_offline_boundary_dynamic_price_context_v1(
                mark_price=market.mark,
                selected_side="long",
                adverse_exit_distance=market.mark / 10,
            ),
        )


def test_native_maximum_is_consumed_by_original_sizing():
    market, state, source = setup_market()
    context, _ = context_for(state, market, source(market=market, now=market.observed_unix))
    # Explicit mechanism counterfactual: the same original owner must consume
    # the supplied native maximum rather than the legacy dynamic None.
    context = replace(context, instrument=replace(context.instrument, maximum_quantity=D(3)))
    sizing = bind_capital_risk_sizing_offline_replay_evidence_v0(
        scenario_evidence("long", "enter_long"), capital_context=context
    )
    assert sizing.sizing_decision.final_quantity == 3


def _regular_card_tick(state, market, budget, *, sequence):
    from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
        ObservationMarketTickV1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
        run_hardened_wallclock_bridge_observation_cycle_v2,
    )
    from tests.ops.test_instrument_card_stream_v1 import bound

    tick = ObservationMarketTickV1(
        SOPH.instrument_id,
        "OKX",
        "FUTURES",
        sequence,
        market.market_event_unix,
        market.observed_unix,
        0.0,
        float(market.mark),
    )
    return run_hardened_wallclock_bridge_observation_cycle_v2(
        bridge_state=state,
        ticks=[tick],
        reference_price=market.mark,
        wall_now_unix=market.observed_unix,
        session_id="minimum-lot",
        instrument_card_market=market,
        instrument_card_bound=bound(market),
        instrument_card_budget=budget,
    )


def test_flat_card_requires_a_bound_distance_before_confirmation():
    market, state, source = setup_market()
    outcome = _regular_card_tick(
        state, market, source(market=market, now=market.observed_unix), sequence=1
    )
    assert outcome.ok and outcome.bridge_cycle is None
    assert outcome.labels["deferred_card"]["reasons"] == ["CARD_BOUND_STOP_DISTANCE_UNAVAILABLE"]
    assert state.card_confirmation is None and state.cycle_index == 0


@pytest.mark.parametrize(
    "free,cap,floor,admitted,entry_limit",
    [
        ("0.33570", "0.003", "-0.0001", {"SELL"}, None),
        ("0.33570", "0.0001", "-0.003", {"BUY"}, None),
        ("0.33570", "0.003", "-0.003", set(), None),
        ("0.34000", "0.003", "-0.003", {"BUY", "SELL"}, None),
        ("0.33505", "0.003", "-0.0001", set(), None),
        ("25", "0.003", "-0.0001", {"SELL"}, "0.33570"),
        ("25", "0.0001", "-0.003", {"BUY"}, "0.33570"),
        ("25", "0.003", "-0.003", set(), "0"),
        ("25", "0.003", "-0.003", set(), "0.30"),
    ],
)
@pytest.mark.parametrize("side", ["BUY", "SELL"])
def test_regular_flat_card_minimum_cost_precedes_confirmation(
    tmp_path, free, cap, floor, admitted, side, entry_limit
):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from src.ops.instrument_card_input_observation_v1 import observe_instrument_card_input_v1
    from tests.ops.test_instrument_card_stream_v1 import bound
    from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
    )

    price = D("0.03350")
    earlier = price + (D("-0.00001") if side == "BUY" else D("0.00001"))
    state = HardenedBridgeSessionStateV2(
        instrument_id=SOPH.instrument_id, venue_instrument_id=SOPH.native_id
    )
    source = shadow_budget_source_v1(state, repo=REPO)
    inputs = []
    for step, mark in enumerate((earlier, price)):
        observations, policy, now = _observations(step, slot=SOPH, price=mark, depth=10000)
        receipt = observations["funding"]
        payload = deepcopy(receipt.payload)
        payload["data"][0].update(maxFundingRate=cap, minFundingRate=floor)
        observations["funding"] = replace(
            receipt, payload=payload, body_sha256=sha256(json.dumps(payload).encode()).hexdigest()
        )
        market = bind_zkp_paper_market_v1(observations, policy=policy, observed_unix=now, slot=SOPH)
        if step == 0:
            g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
                evidence_store_root=tmp_path,
                bound_instrument=bound(market),
                mark_candles_payload=market.g17_payload,
                receive_or_capture_timestamp=market.g17_acquired_at,
            )
            assert g17.estimate_present
            state.typed_volatility_cmc_binding_host = (
                CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1(producer=g17.producer)
            )
        else:
            state.soph_entry_cost_limit_usdc = None if entry_limit is None else D(entry_limit)
            state.portfolio.model.state.cash = D(free)
        budget = source(market=market, now=now)
        with observe_instrument_card_input_v1(inputs.append):
            outcome = _regular_card_tick(state, market, budget, sequence=step + 1)
        assert outcome.ok
        if step == 0:
            assert outcome.bridge_cycle and len(inputs) == 1
            first_epoch = state.card_observations.market_observation_epoch
    assert state.card_observations.market_observation_epoch != first_epoch
    if side in admitted:
        assert len(inputs) == state.cycle_index == len(state.mid_prices) == 2
        assert (
            inputs[-1].side_state.name
            == {"BUY": "LONG_ARMED_NEUTRAL_START", "SELL": "SHORT_ARMED_NEUTRAL_START"}[side]
        )
        review = outcome.bridge_cycle["instrument_card_entry_review"]
        assert outcome.bridge_cycle["fill"] is None
    else:
        assert len(inputs) == state.cycle_index == len(state.mid_prices) == 1
        review = outcome.labels["deferred_card"]
        assert state.card_confirmation is None
    assert state.card_position_scope is None and review["observed_side"] == side
    assert D(review["available_usdc"]) == D(free)
    if not review["sides"][side]["eligible"]:
        assert review["reasons"] == ["CARD_MARKET_SIDE_NOT_RELEASED"]
        return
    measurement = review["minimum_lot_cost"]
    assert (
        measurement["instrument_id"] == SOPH.instrument_id
        and measurement["venue_native_id"] == SOPH.native_id
    )
    assert D(measurement["minimum_contracts"]) == 1 and D(measurement["quantity_base"]) == 10
    assert {s for s, row in measurement["sides"].items() if row["measurement_admitted"]} == admitted
    if side not in admitted:
        assert review["reasons"] == ["CARD_MINIMUM_LOT_COST_NOT_ADMITTED"]
    assert D(measurement["sides"][side]["stop_distance"]) == abs(
        price - D(measurement["sides"][side]["protective_stop_price"])
    )


@pytest.mark.parametrize(
    "fx,free,requested,expected",
    [("0.8", "25", "10", "8"), ("2", "7", "10", "14"), ("1", "25", "100", "25")],
)
def test_independent_entry_limit_uses_current_fx_and_free_amount(fx, free, requested, expected):
    market, state, source = setup_market(fx=fx)
    source(market=market, now=market.observed_unix)
    state.portfolio.model.state.cash = D(free) * market.usd_per_usdc
    budget = source(market=market, now=market.observed_unix)
    check = soph_shadow_cost_check_v1(
        state=state,
        market=market,
        budget=budget,
        side="SELL",
        quantity=market.native_contract.min_qty * market.native_contract.contract_size,
        stop_distance=market.mark / 10,
        entry_cost_limit_usdc=D(requested),
    )
    assert D(budget["available_for_new_entry"]) == D(free)
    assert check["measurement_admitted"] and D(check["model_costs"]["notional_limit"]) == D(
        expected
    )


def test_cli_entry_limit_is_optional_and_accepts_only_nonnegative_finite_amounts():
    from scripts.ops.run_integrated_paper_shadow_observation_wallclock_session_v1 import (
        build_parser,
    )

    parser = build_parser()
    assert parser.parse_args(["run"]).soph_entry_cost_limit_usdc is None
    assert parser.parse_args(
        ["run", "--soph-entry-cost-limit-usdc", "10.01"]
    ).soph_entry_cost_limit_usdc == D("10.01")
    for invalid in ("NaN", "Infinity", "-0.01", "invalid"):
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--soph-entry-cost-limit-usdc", invalid])


def test_lower_nominal_policy_does_not_reallocate_slot_or_lower_loss_budget(monkeypatch):
    from src.ops.portfolio_capital_reservation_budget_v1 import test_phase_limits_v1 as limits
    from src.ops import soph_shadow_capital_risk_binding_v1 as capital

    original = limits.load_slot_entry_budget_v1(
        REPO / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    policy = replace(original, per_entry_notional_limit=D("7"))
    policy.validate_v1()
    monkeypatch.setattr(limits, "load_slot_entry_budget_v1", lambda path: policy)
    monkeypatch.setattr(capital, "load_slot_entry_budget_v1", lambda path: policy)
    market, state, source = setup_market(fx="0.8")
    budget = source(market=market, now=market.observed_unix)
    boundary, _, _ = soph_shadow_capital_binding_v1(
        state=state, market=market, budget=budget, now=market.observed_unix
    )
    assert D(budget["available_for_new_entry"]) == 25
    assert (
        D(boundary.account_equity)
        == D(boundary.total_capital_limit)
        == D(boundary.per_trade_risk_limit)
        == 20
    )
    assert D(boundary.scope_capital_limit) == D("5.6")
