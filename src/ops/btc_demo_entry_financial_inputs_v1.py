"""Pure BTC Demo financial inputs for the original risk and cost consumers."""

from decimal import Decimal

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1 as acquisition
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    resolve_current_productive_live_29p_adverse_exit_distance_v1,
    resolve_protective_stop_sizing_side_for_live_29p_join_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
    CurrentProductiveUsdcFreeMarginObservationV1,
    produce_current_productive_29p_risk_capital_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u01_account_mode_adapter_v1 import (
    adapt_current_productive_u01_account_mode_v1,
    build_current_productive_u01_eligibility_fact_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    bind_current_productive_p01_fact_for_ct_sizing_produce_v1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.normalize_v1 import (
    build_capital_risk_sizing_monetary_context_v1,
    crs_operands_from_monetary_context_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
    instrument_monetary_identity_from_okx_payload_v1,
)
from src.ops.governed_productive_monetary_normalization_v1.sizing_source_v1 import (
    build_sizing_monetary_source_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
    default_offline_replay_capital_context_v0,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    build_capital_risk_sizing_input_from_decision_v0,
)


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def build_btc_demo_capital_inputs_v1(rows, *, account, epoch, now, config):
    balance = rows["balance"]
    detail = cost._one(demo._only(balance.payload)["details"], "ccy", "USDC")
    value = cost._money(detail.get("availEq"), positive=True)
    _need(value >= demo._BUDGET_USDC, "BTC_TESTNET_DECLARED_BUDGET_UNCOVERED")
    age = acquisition.acquisition_age_seconds_v1(
        acquired_at_utc=balance.acquired_at_utc, now_utc=now
    )
    scope = dict(
        bound_account_identity=account,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=epoch,
    )
    margin = CurrentProductiveUsdcFreeMarginObservationV1(
        **scope,
        fact_id=OBSERVATION_FACT_ID,
        surface=OBSERVATION_SURFACE,
        value=detail["availEq"],
        settlement_currency="USDC",
        selected_ccy="USDC",
        observed_at_as_of=balance.acquired_at_utc,
        age_seconds=age,
        freshness_max_age=str(acquisition.NUMERIC_EQUITY_TTL_SECONDS),
        provenance_digest=balance.body_sha256,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )
    p01 = bind_current_productive_p01_fact_for_ct_sizing_produce_v1(
        base=margin, age_seconds=age, freshness_max_age=margin.freshness_max_age
    )
    eligibility = build_current_productive_u01_eligibility_fact_v1(
        **scope,
        adaptation=adapt_current_productive_u01_account_mode_v1(config["acctLv"]),
        provenance_digest=rows["account"].body_sha256,
    )
    output = produce_current_productive_29p_risk_capital_v1(
        observation=margin, p01=p01, eligibility=eligibility
    )
    _need(
        output.produced == "true" and Decimal(output.value) >= demo._BUDGET_USDC,
        "BTC_TESTNET_CAPITAL_NOT_ADMISSIBLE",
    )
    return margin, output, p01, eligibility


def build_btc_demo_sizing_inputs_v1(
    cycle,
    bound,
    instruments,
    equity,
    observed_at,
    policy,
    source_digest,
    *,
    capital_risk_mode,
    native_price_currency,
    contract_settlement_sources_json="",
):
    replay = cycle.replay
    reference = Decimal(str(replay.intermediate.market_context.mark_price))
    distance, _ = resolve_current_productive_live_29p_adverse_exit_distance_v1(replay)
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=resolve_protective_stop_sizing_side_for_live_29p_join_v1(replay),
        reference_price=reference,
        adverse_exit_distance=distance,
    )
    _need(stop is not None, "BTC_TESTNET_ORIGINAL_STOP_REQUIRED")
    meta = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=bound.venue_native_id,
        instruments_payload=instruments,
        observed_at_as_of=observed_at,
        bound_instrument_id=bound.instrument_id,
    )
    _need(meta.produced and meta.constraints is not None, "BTC_TESTNET_NATIVE_METADATA_REQUIRED")
    money_args = dict(
        decision_epoch=replay.intermediate.market_context.decision_time,
        observed_at=observed_at,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        native_reference_price=reference,
        native_protective_stop_price=stop,
        instruments_payload=instruments,
        venue_native_id=bound.venue_native_id,
        index_tickers_payload=None,
        conversion_pair_instruments_payload=None,
        contract_settlement_sources_json=contract_settlement_sources_json,
    )
    identity = instrument_monetary_identity_from_okx_payload_v1(
        instruments,
        venue_native_id=bound.venue_native_id,
    )
    if contract_settlement_sources_json:
        from src.ops.governed_productive_monetary_normalization_v1.xperp_settlement_v1 import (
            bind_xperp_settlement_rule_v1,
        )

        _, identity = bind_xperp_settlement_rule_v1(
            contract_settlement_sources_json,
            instruments_payload=instruments,
            venue_native_id=bound.venue_native_id,
            decision_epoch=money_args["decision_epoch"],
            evaluated_at_utc=observed_at,
        )
    _need(
        identity.instrument_money_unit == native_price_currency,
        "BTC_DEMO_NATIVE_PRICE_UNIT_REQUIRES_EXPLICIT_VALUATION",
    )
    money = build_capital_risk_sizing_monetary_context_v1(
        **money_args, account_equity_amount=equity, account_equity_currency="USDC"
    )
    source = build_sizing_monetary_source_v1(
        **money_args,
        canonical_instrument_id=bound.instrument_id,
        account_equity_usdc=equity,
        normalization_digest=money.normalization_digest,
    )
    amount, price, protection = crs_operands_from_monetary_context_v1(money)
    context = default_offline_replay_capital_context_v0(
        instrument_id=bound.instrument_id,
        reference_price=price,
        protective_stop_price=protection,
        account_equity=amount,
        scope_capital_limit=min(amount, policy.per_entry_notional_limit),
        per_trade_risk_limit=amount,
        total_capital_limit=min(amount, policy.aggregate_reserved_notional_limit),
        daily_loss_remaining_budget=amount,
        instrument=meta.constraints,
        config_digest=source_digest,
        capital_risk_mode=capital_risk_mode,
    )
    sizing, reasons = build_capital_risk_sizing_input_from_decision_v0(
        decision=replay.evidence, capital_context=context
    )
    _need(sizing is not None, "BTC_TESTNET_SIZING_INPUT_REQUIRED:" + ",".join(reasons))
    return sizing, source
