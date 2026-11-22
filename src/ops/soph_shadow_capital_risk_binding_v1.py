"""SOPH analytical capital input for the original CRS boundary, never account authority.

The original CRS and intent count native contracts. The legacy Shadow portfolio
counts base units and USD; only its consumer projects the native intent quantity.
No historical fixture limits or implicit account authority.
"""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
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
from src.ops.single_selected_future_policy_v1.constants_v1 import MAX_POSITIONS_EFFECTIVE
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
    capture_productive_offline_simulated_portfolio_position_observation_v1,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
)

REPO = Path(__file__).resolve().parents[2]
_ZERO = Decimal(0)


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
        policy.per_entry_notional_limit,
        policy.per_slot_reserved_notional_limit,
    )
    available = max(_ZERO, min(cap_usdc, equity / market.usd_per_usdc))
    position = capture_productive_offline_simulated_portfolio_position_observation_v1(
        portfolio=state.portfolio.model,
        instrument_id=state.instrument_id,
        mark_price=market.mark,
        feedback_source_bar_epoch=state.trading_epoch,
    )
    free = available if position.venue_flat else _ZERO
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
        scope_capital_limit=str(available * market.usd_per_usdc),
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


def soph_shadow_cost_check_v1(*, state, market, budget, side, quantity, stop_distance):
    """Extra model-cost admission after original sizing; no quantity adjustment."""
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
    admitted = quantity * market.mark + reserve <= limit and quantity * distance + reserve <= min(
        limit, policy_loss
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
            notional_limit=str(limit),
            loss_with_costs=str(quantity * distance + reserve),
            funding_booking="ORIGINAL_ANALYTICAL_MODEL_UNCHANGED",
        ),
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
    projected = replace(native, intended_quantity=native.intended_quantity * multiplier)
    receipt = dict(
        mapper_quantity_contracts=str(native.intended_quantity),
        contract_size=str(multiplier),
        portfolio_quantity_base=str(projected.intended_quantity),
        portfolio_quantity_unit=market.slot.base_currency,
        source=native.quantity_source,
    )
    return projected, receipt
