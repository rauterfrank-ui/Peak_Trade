"""SOPH analytical capital input for the original CRS boundary, never account authority.

The original CRS and intent count native contracts. The legacy Shadow portfolio
counts base units and USD; only its consumer projects the native intent quantity.
No historical fixture limits or implicit account authority.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path

from src.governance.capital_risk_sizing_v1 import CONTRACT_VERSION
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.instrument_card_stream_v1 import plain
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import opening_order_side_v1
from src.ops.single_selected_future_policy_v1.constants_v1 import MAX_POSITIONS_EFFECTIVE
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
    capture_productive_offline_simulated_portfolio_position_observation_v1,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    build_mv2_offline_boundary_dynamic_price_context_v1,
)

REPO = Path(__file__).resolve().parents[2]
_ZERO = Decimal(0)


def parse_soph_entry_cost_limit_usdc_v1(value):
    """Optional all-in Shadow entry ceiling. Zero explicitly disables flat entries."""
    if value is None:
        return None
    if not isinstance(value, (str, Decimal)):
        raise ValueError("SOPH_SHADOW_ENTRY_COST_LIMIT_INVALID")
    try:
        limit = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("SOPH_SHADOW_ENTRY_COST_LIMIT_INVALID") from exc
    if not limit.is_finite() or limit < 0:
        raise ValueError("SOPH_SHADOW_ENTRY_COST_LIMIT_INVALID")
    return limit


def soph_shadow_capital_binding_v1(*, state, market, budget, now):
    """Validate a current original budget and build an in-memory original boundary."""
    try:
        return _current_binding(state=state, market=market, budget=budget, now=now)
    except (KeyError, TypeError, ArithmeticError) as exc:
        raise ValueError("SOPH_SHADOW_CAPITAL_SOURCE_INVALID") from exc


def _current_binding(*, state, market, budget, now):
    if (
        state.instrument_id != SOPH_I17.canonical_id
        or state.venue_instrument_id != SOPH_I17.native_id
        or market.slot.instrument_id != state.instrument_id
        or market.slot.native_id != state.venue_instrument_id
        or market.slot.lane_id != SOPH_I17.lane_id
        or not isinstance(budget, dict)
        or budget.get("status") != "BOUND"
        or budget.get("owner") != "I17_ORIGINAL_ANALYTICAL_PORTFOLIO_AND_SLOT_TEST_POLICY"
        or budget.get("currency") != "USDC"
        or budget.get("lane_id") != SOPH_I17.lane_id
        or budget.get("instrument_id") != state.instrument_id
        or budget.get("reservation_scope") != "ANALYTICAL_MODEL_WITHOUT_PORTFOLIO_HOLD"
        or budget.get("reserved_amount") is not None
        or type(budget.get("observed_unix")) not in (int, float)
        or not isfinite(budget["observed_unix"])
        or not market.observed_unix <= budget["observed_unix"] <= now < market.funding_time_unix
    ):
        raise ValueError("SOPH_SHADOW_CAPITAL_SOURCE_OR_IDENTITY_MISMATCH")
    snapshot = budget["original_snapshot"]
    policy = load_slot_entry_budget_v1(
        REPO / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    if (
        budget["source_digest"] != canonical_digest_v1(snapshot)
        or snapshot["policy"] != policy.to_dict_v1()
        or snapshot["original_portfolio"] != plain(state.portfolio.snapshot())
        or snapshot["usd_per_usdc"] != str(market.usd_per_usdc)
        or any(
            instrument != state.instrument_id and Decimal(position["quantity"]) != 0
            for instrument, position in snapshot["original_portfolio"]["state"]["positions"].items()
        )
    ):
        raise ValueError("SOPH_SHADOW_CAPITAL_CURRENT_READBACK_MISMATCH")
    marked = deepcopy(state.portfolio.model)
    marked.apply_intended_action(
        instrument_id=state.instrument_id, side="HOLD", quantity=_ZERO, mark_price=market.mark
    )
    if snapshot["marked_portfolio"] != plain(marked.snapshot()):
        raise ValueError("SOPH_SHADOW_CAPITAL_MARKED_READBACK_MISMATCH")
    equity = marked.economic_metrics().equity
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
        PAPER_ALLOCATION_USDC,
    )
    from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import (
        paper_constraints_v1,
    )

    cap_usdc = min(
        PAPER_ALLOCATION_USDC,
        policy.per_slot_reserved_notional_limit,
    )
    available = max(_ZERO, min(cap_usdc, equity / market.usd_per_usdc))
    position = capture_productive_offline_simulated_portfolio_position_observation_v1(
        portfolio=state.portfolio.model,
        instrument_id=state.instrument_id,
        mark_price=market.mark,
        feedback_source_bar_epoch=state.trading_epoch,
    )
    if snapshot.get("confirmed_entry_budget") != state.soph_confirmed_entry_budget:
        raise ValueError("SOPH_SHADOW_ENTRY_BUDGET_READBACK_MISMATCH")
    free = available if position.venue_flat and state.soph_confirmed_entry_budget is None else _ZERO
    if (Decimal(budget["available_amount"]), Decimal(budget["available_for_new_entry"])) != (
        available,
        free,
    ):
        raise ValueError("SOPH_SHADOW_CAPITAL_AMOUNT_MISMATCH")
    if equity <= 0 or available <= 0:
        raise ValueError("SOPH_SHADOW_ANALYTICAL_CAPITAL_EXHAUSTED")
    contract = market.native_contract
    if contract.quote_currency != "USD" or contract.contract_type != "linear":
        raise ValueError("SOPH_SHADOW_USD_LINEAR_CONTRACT_REQUIRED")
    # Same bounded test-loss envelope as the existing Paper owner; not a claim
    # of a private account's daily-loss balance. USD at this captured FX only.
    loss_limit = min(equity, policy.per_slot_test_loss_limit * market.usd_per_usdc)
    native_position = replace(
        position,
        signed_quantity=position.signed_quantity / contract.contract_size,
        reconciled_open_position_quantity=position.reconciled_open_position_quantity
        / contract.contract_size,
    )
    constraints = paper_constraints_v1(market)
    material = dict(
        schema="soph_shadow_capital_binding.v1",
        authority="NONE",
        capital_risk_mode="OFFLINE_ALGEBRA",
        price_currency="USD",
        capital_source_currency="USDC",
        core_quantity_unit="CONTRACTS",
        analytical_portfolio_quantity_unit=market.slot.base_currency,
        contract_size=str(contract.contract_size),
        market_source_hashes=dict(market.source_hashes),
        budget_source_digest=budget["source_digest"],
        observed_unix=budget["observed_unix"],
        marked_equity_usd=str(equity),
        available_usdc=str(available),
        available_usd=str(available * market.usd_per_usdc),
        loss_envelope_usd=str(loss_limit),
        loss_scope=snapshot["policy"]["loss_limit_scope"],
        daily_loss_field_lineage="BOUNDED_SHADOW_TEST_LOSS_ENVELOPE_NOT_ACCOUNT_DAILY_BALANCE",
        portfolio_position_base=plain(position),
        crs_position_contracts=plain(native_position),
        native_constraints=plain(contract),
        native_lot_size=str(market.lot_size),
        native_maximum_contracts=str(market.maximum_contracts),
        original_snapshot=snapshot,
    )
    boundary = CapitalRiskSizingBacktestStateFileRecordV0(
        instrument_id=state.instrument_id,
        reference_price="",
        protective_stop_price="",
        account_equity=str(equity),
        scope_capital_limit=str(
            min(available, policy.per_entry_notional_limit) * market.usd_per_usdc
        ),
        per_trade_risk_limit=str(loss_limit),
        total_capital_limit=str(cap_usdc * market.usd_per_usdc),
        daily_loss_remaining_budget=str(loss_limit),
        current_reconciled_exposure=str(position.current_reconciled_exposure),
        lot_size=str(market.lot_size),
        minimum_quantity=str(contract.min_qty),
        maximum_quantity="",
        minimum_notional=str(contract.min_qty * contract.contract_size * market.mark),
        tick_size=str(contract.tick_size),
        maximum_positions=MAX_POSITIONS_EFFECTIVE,
        current_open_positions_count=position.current_open_positions_count,
        reconciliation_status="RECONCILED",
        capital_risk_sizing_owner_digest_ref=CONTRACT_VERSION,
        state_file_digest_ref=canonical_digest_v1(material),
        dynamic_price_context_binding_ref=MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
        raw_payload=material,
        instrument_quantity_constraints=constraints,
    )
    return boundary, native_position, material


def soph_shadow_cost_check_v1(
    *, state, market, budget, side, quantity, stop_distance, entry_cost_limit_usdc=None
):
    """Measure the supplied base quantity against the shadow cost and loss limits."""
    from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1

    measurement = assess_instrument_budget_v1(
        market=market,
        available_usdc=budget["available_for_new_entry"],
        side=side,
        quantity_contracts=quantity / market.native_contract.contract_size,
    )
    if not measurement["measurement_admitted"]:
        return measurement
    params = state.portfolio.model.params
    fee = params.fee_rate_bps / Decimal(10000)
    slip = params.slippage_bps / Decimal(10000)
    if any(not value.is_finite() or value < 0 for value in (fee, slip)) or slip >= 1:
        raise ValueError("SOPH_SHADOW_COST_MODEL_INVALID")
    distance = Decimal(str(stop_distance))
    if not distance.is_finite() or distance <= 0:
        raise ValueError("SOPH_SHADOW_DYNAMIC_SCOPE_REQUIRED")
    worst = max(
        market.mark + distance,
        Decimal(measurement["liquidity"]["open_price_usd"]),
        Decimal(measurement["liquidity"]["close_price_usd"]),
    )
    opening_slip = quantity * market.mark * slip
    opening_fee = quantity * market.mark * (1 + slip) * fee
    closing_slip = quantity * worst * slip
    closing_fee = quantity * worst * (1 + slip) * fee
    funding = (
        quantity
        * worst
        * max(_ZERO, market.funding_cap if side == "BUY" else -market.funding_floor)
    )
    reserve = opening_slip + opening_fee + closing_slip + closing_fee + funding
    limit = Decimal(budget["available_for_new_entry"]) * market.usd_per_usdc
    policy_loss = (
        Decimal(budget["original_snapshot"]["policy"]["per_slot_test_loss_limit"])
        * market.usd_per_usdc
    )
    entry_limit = parse_soph_entry_cost_limit_usdc_v1(entry_cost_limit_usdc)
    spend_limit = limit if entry_limit is None else min(limit, entry_limit * market.usd_per_usdc)
    policy_notional = (
        Decimal(budget["original_snapshot"]["policy"]["per_entry_notional_limit"])
        * market.usd_per_usdc
    )
    admitted = (
        quantity * market.mark <= policy_notional
        and Decimal(measurement["book_notional_usd"]) <= spend_limit
        and quantity * market.mark + reserve <= spend_limit
        and quantity * distance + reserve <= min(limit, policy_loss)
    )
    return dict(
        measurement,
        measurement_admitted=admitted,
        fees_and_funding_included=True,
        reason_codes=[] if admitted else ["SOPH_SHADOW_MODEL_COST_ENVELOPE_EXCEEDED"],
        model_costs=dict(
            currency="USD",
            opening_fee=str(opening_fee),
            opening_slippage=str(opening_slip),
            closing_fee_allowance=str(closing_fee),
            closing_slippage_allowance=str(closing_slip),
            next_funding_allowance=str(funding),
            total_reserve=str(reserve),
            next_funding_unix=market.funding_time_unix,
            notional_limit=str(spend_limit),
            loss_with_costs=str(quantity * distance + reserve),
            funding_booking="ORIGINAL_ANALYTICAL_MODEL_UNCHANGED",
        ),
    )


def soph_shadow_minimum_lot_cost_v1(*, state, market, budget, context, adverse_exit_distance):
    """Price the first opening order on the executable book for each direction."""
    event_time = datetime.fromtimestamp(market.market_event_unix, tz=timezone.utc).isoformat()
    if (
        context.instrument_id != market.slot.instrument_id
        or context.mark_price != float(market.mark)
        or context.market_event_time != event_time
    ):
        raise ValueError("SOPH_SHADOW_MINIMUM_LOT_MARK_BINDING_MISMATCH")

    contract = market.native_contract
    quantity = contract.min_qty * contract.contract_size
    by_direction = {}
    for direction in ("long", "short"):
        price = build_mv2_offline_boundary_dynamic_price_context_v1(
            mark_price=Decimal(str(context.mark_price)),
            selected_side=direction.upper(),
            adverse_exit_distance=adverse_exit_distance,
        )
        if price.protective_stop_price is None:
            by_direction[direction] = {
                "measurement_admitted": False,
                "reason_codes": ["SOPH_SHADOW_PROTECTIVE_STOP_UNAVAILABLE"],
            }
            continue
        distance = abs(price.reference_price - price.protective_stop_price)
        by_direction[direction] = dict(
            soph_shadow_cost_check_v1(
                state=state,
                market=market,
                budget=budget,
                side=opening_order_side_v1(direction),
                quantity=quantity,
                stop_distance=distance,
                entry_cost_limit_usdc=state.soph_entry_cost_limit_usdc,
            ),
            quantity_source="NATIVE_MINIMUM_ENTRY_LOT",
            protective_stop_price=str(price.protective_stop_price),
            stop_distance=str(distance),
        )
    return dict(
        instrument_id=context.instrument_id,
        venue_native_id=market.slot.native_id,
        market_event_time=context.market_event_time,
        context_digest=context.input_digest,
        mark_price=str(context.mark_price),
        price_unit=f"USD/{market.slot.base_currency}",
        minimum_contracts=str(contract.min_qty),
        quantity_base=str(quantity),
        configured_entry_cost_limit_usdc=None
        if state.soph_entry_cost_limit_usdc is None
        else str(state.soph_entry_cost_limit_usdc),
        by_direction=by_direction,
    )


def soph_shadow_entry_sizing_boundary_v1(*, state, market, budget, boundary, review):
    """Bind a positive, side-specific mark notional to CRS before its own lot/risk sizing."""
    direction = review["market_direction"]
    minimum = review["minimum_lot_cost"]
    cost = minimum["by_direction"][direction]
    if not cost["measurement_admitted"]:
        raise ValueError("SOPH_SHADOW_MINIMUM_LOT_REQUIRED")
    order_side = opening_order_side_v1(direction)
    if cost["side"] != order_side:
        raise ValueError("SOPH_SHADOW_ENTRY_BUDGET_BINDING_MISMATCH")
    lot = market.lot_size
    base_per_lot = lot * market.native_contract.contract_size
    mark_per_lot = base_per_lot * market.mark
    lower = int(market.native_contract.min_qty // lot)
    upper = int(
        min(
            Decimal(boundary.scope_capital_limit) / mark_per_lot,
            Decimal(cost["model_costs"]["notional_limit"]) / mark_per_lot,
            market.maximum_contracts / lot,
        )
    )
    if lower < 1 or lower > upper:
        raise ValueError("SOPH_SHADOW_ENTRY_LOT_BOUNDS_INVALID")
    # Start at the admitted native minimum. Probe complete lots on the same book,
    # FX, stop, loss and funding snapshot. The probe only limits CRS.
    while lower < upper:
        candidate = (lower + upper + 1) // 2
        probe = soph_shadow_cost_check_v1(
            state=state,
            market=market,
            budget=budget,
            side=order_side,
            quantity=candidate * base_per_lot,
            stop_distance=cost["stop_distance"],
            entry_cost_limit_usdc=state.soph_entry_cost_limit_usdc,
        )
        if probe["measurement_admitted"]:
            lower = candidate
        else:
            upper = candidate - 1
    nominal = lower * mark_per_lot
    receipt = dict(
        instrument_id=minimum["instrument_id"],
        venue_native_id=minimum["venue_native_id"],
        lane_id=review["lane_id"],
        market_direction=direction,
        side=order_side,
        market_event_time=minimum["market_event_time"],
        decision_time_unix=review["observed_unix"],
        market_context_digest=minimum["context_digest"],
        budget_source_digest=budget["source_digest"],
        available_usdc=budget["available_for_new_entry"],
        configured_entry_cost_limit_usdc=minimum["configured_entry_cost_limit_usdc"],
        effective_entry_cost_limit_usd=cost["model_costs"]["notional_limit"],
        stop_distance=cost["stop_distance"],
        maximum_contracts=str(lower * lot),
        maximum_mark_notional_usd=str(nominal),
    )
    material = dict(boundary.raw_payload, flat_entry_cost_bound=receipt)
    return replace(
        boundary,
        scope_capital_limit=str(nominal),
        raw_payload=material,
        state_file_digest_ref=canonical_digest_v1(material),
    )


def soph_shadow_confirm_entry_budget_v1(*, replay, state, market, budget, review, limit, cycle_id):
    """Bind the original directional assessment and final sizing at decision time."""
    inter = replay.intermediate
    sizing = inter.capital_risk_sizing_decision
    direction = review["market_direction"]
    order_side = opening_order_side_v1(direction)
    assessment = inter.bull_assessment if direction == "long" else inter.bear_assessment
    intent = inter.canonical_order_intent
    if assessment is None or sizing is None or intent is None or limit is None:
        raise ValueError("SOPH_SHADOW_ENTRY_BUDGET_ORIGINAL_REQUIRED")
    qty = sizing.final_quantity
    nominal = sizing.post_sizing_risk.resulting_notional
    minimum = review["minimum_lot_cost"]["by_direction"][direction]
    if (
        not replay.replay_pass
        or assessment.status.value != "confirmed"
        or assessment.side.value != direction
        or assessment.instrument_id != market.slot.instrument_id
        or sizing.outcome.value != "PASS"
        or sizing.selected_side.lower() != direction
        or intent.side.lower() != direction
        or intent.intent_action != f"ENTER_{direction.upper()}"
        or intent.instrument_id != market.slot.instrument_id
        or intent.decision_id != sizing.canonical_position_sizing.decision_id
        or intent.quantity != qty
        or not _ZERO < qty <= Decimal(limit["maximum_contracts"])
        or limit["market_direction"] != direction
        or minimum["side"] != order_side
        or limit["side"] != order_side
        or limit["budget_source_digest"] != budget["source_digest"]
        or limit["configured_entry_cost_limit_usdc"]
        != (
            None
            if state.soph_entry_cost_limit_usdc is None
            else str(state.soph_entry_cost_limit_usdc)
        )
        or not minimum["measurement_admitted"]
        or sizing.pre_sizing_risk.stop_or_risk_distance != Decimal(minimum["stop_distance"])
        or nominal != qty * market.native_contract.contract_size * market.mark
    ):
        raise ValueError("SOPH_SHADOW_ENTRY_BUDGET_BINDING_MISMATCH")
    cost = soph_shadow_cost_check_v1(
        state=state,
        market=market,
        budget=budget,
        side=order_side,
        quantity=qty * market.native_contract.contract_size,
        stop_distance=sizing.pre_sizing_risk.stop_or_risk_distance,
        entry_cost_limit_usdc=state.soph_entry_cost_limit_usdc,
    )
    if not cost["measurement_admitted"]:
        return None
    return dict(
        status="CONFIRMED",
        session_id=state.session_id,
        cycle_id=cycle_id,
        lane_id=market.slot.lane_id,
        instrument_id=market.slot.instrument_id,
        venue_native_id=market.slot.native_id,
        selection_id=review["binding"]["selection_id"],
        selection_integrity_digest=review["binding"]["selection_integrity_digest"],
        direction=direction,
        entry_action="FIRST_PURCHASE",
        first_purchase_side=cost["side"],
        market_event_unix=market.market_event_unix,
        decision_unix=review["observed_unix"],
        assessment_id=assessment.assessment_id,
        decision_id=intent.decision_id,
        sizing_ref=sizing.quantity_provenance.sizing_ref,
        budget_source_digest=budget["source_digest"],
        quantity_contracts=str(qty),
        nominal_usd=str(nominal),
        nominal_usdc=str(nominal / market.usd_per_usdc),
        usd_per_usdc=str(market.usd_per_usdc),
        cost_allowance_usd=cost["model_costs"]["total_reserve"],
        budget_owner=budget["owner"],
        binding_scope="ANALYTICAL_SLOT_ENTRY",
    )


def soph_shadow_portfolio_action_v1(*, replay, state, market):
    """Original intent/mapper in contracts, explicit projection at model consumer."""
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
        map_replay_result_to_intended_analytical_action_v1,
    )

    portfolio = deepcopy(state.portfolio.snapshot())
    multiplier = market.native_contract.contract_size
    for position in portfolio["state"]["positions"].values():
        position["quantity"] = str(Decimal(position["quantity"]) / multiplier)
    native = map_replay_result_to_intended_analytical_action_v1(
        replay, instrument_id=state.instrument_id, portfolio_snapshot=portfolio
    )
    # Preserve the original mapper label in the receipt. A portfolio close
    # without a canonical order intent is still an analytical exit or reduction.
    action = native.intent_action
    if native.quantity_source == "exit_or_reduce" and native.decision_outcome in {"exit", "reduce"}:
        action = native.decision_outcome.upper()
    elif native.quantity_source == "exit_flat":
        action = "NONE"
    projected = replace(
        native,
        intent_action=action,
        intended_quantity=native.intended_quantity * multiplier,
    )
    receipt = dict(
        mapper_intent_action=native.intent_action,
        mapper_quantity_contracts=str(native.intended_quantity),
        contract_size=str(multiplier),
        portfolio_quantity_base=str(projected.intended_quantity),
        portfolio_quantity_unit=market.slot.base_currency,
        source=native.quantity_source,
    )
    return projected, receipt
