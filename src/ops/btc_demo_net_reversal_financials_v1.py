"""Bind original TESTNET sizing/cost owners to one retained net reversal."""

from dataclasses import asdict, replace
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json

from src.ops.btc_demo_entry_financial_inputs_v1 import build_btc_demo_capital_inputs_v1
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
    request_digest_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.native_initial_margin_v1 import (
    bind_native_initial_margin_v1,
    require_native_margin_locked_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.absolute_movement_cost_v1 import (
    bind_absolute_movement_cost_v1,
)


def original_reversal_sources_v1(injected, *, account, epoch, now):
    rows = json.loads(injected.testnet_original_sources_json)
    bodies = json.loads(injected.testnet_original_bodies_json)
    expected = {
        "account",
        "instruments",
        "fees",
        "book",
        "balance",
        "leverage",
        "funding",
        "positions",
        "pending",
        "quantity_public",
        "quantity_private",
    }
    if rows.keys() != expected or bodies.keys() != expected:
        raise ValueError("TESTNET_REVERSAL_ORIGINAL_SOURCES_REQUIRED")
    sources = {k: cost.FreshPretradeGetTransportResultV1(**v) for k, v in rows.items()}
    for key, source in sources.items():
        body = bytes.fromhex(bodies[key])
        if (
            source.transport_class != "OKX_EEA_DEMO_READ_ONLY_GET"
            or source.method != "GET"
            or source.get_performed is not True
            or source.http_status != 200
            or source.historical_reuse is not False
            or source.error_class
            or source.body_sha256 != sha256(body).hexdigest()
            or source.payload != json.loads(body)
            or source.auth_header_sent is not (key not in {"book", "funding", "quantity_public"})
            or source.pretrade_decision_id != injected.acquisition_decision_id
        ):
            raise ValueError("TESTNET_REVERSAL_ORIGINAL_SOURCE_CHANGED:" + key)
        cost.acquisition_age_seconds_v1(acquired_at_utc=epoch, now_utc=source.acquired_at_utc)
        cost.acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now)
    config = cost._rows(sources["account"].payload)
    if (
        len(config) != 1
        or config[0].get("uid") != account
        or config[0].get("posMode") != "net_mode"
    ):
        raise ValueError("TESTNET_REVERSAL_ACCOUNT_MISMATCH")
    if (
        sources["balance"].payload != injected.payload
        or sources["balance"].body_sha256 != injected.body_sha256
        or sources["instruments"].payload != injected.instruments_payload
        or sources["pending"].payload["data"] != []
    ):
        raise ValueError("TESTNET_REVERSAL_CAPITAL_OR_PENDING_MISMATCH")
    margin, output, _, _ = build_btc_demo_capital_inputs_v1(
        sources,
        account=account,
        epoch=epoch,
        now=now,
        config=config[0],
        minimum_available=Decimal(0),
    )
    return sources, margin, output


def bind_reversal_financials_v1(
    *, owner, injected, applied, decision, monetary, margin, basis, current_contracts, epoch, now
):
    sources, _, _ = original_reversal_sources_v1(
        injected, account=basis.account_identity, epoch=epoch, now=now
    )
    cycle = json.loads(injected.acquisition_decision_id)["cycle_id"]
    args = dict(
        applied_input=applied, decision=decision, monetary_source=monetary, evaluated_at_utc=now
    )
    opening = cost.bind_entry_execution_cost_v1(
        injected.opening_cost_observation,
        account_identity=basis.account_identity,
        slot_id=basis.slot_id,
        cycle_id=cycle,
        **args,
    )
    closing = cost.bind_closing_execution_cost_v1(opening, **args)
    funding = cost.bind_next_funding_cost_v1(
        injected.funding_cost_observation, entry_binding=opening, close_binding=closing, **args
    )
    native = bind_native_initial_margin_v1(
        injected.native_initial_margin_observation,
        original_margin=margin,
        entry_binding=opening,
        **args,
    )
    sizing = ReservationSizingBindingV1(
        request_digest=request_digest_v1(applied),
        applied_input=applied,
        decision=decision,
        monetary_source=monetary,
        entry_cost_binding=opening,
        close_cost_binding=closing,
        funding_cost_binding=funding,
        native_initial_margin_binding=native,
    )
    movement = bind_absolute_movement_cost_v1(
        injected.absolute_movement_cost_observation, sizing=sizing, evaluated_at_utc=now
    )
    sizing = replace(sizing, absolute_movement_cost_binding=movement)
    sizing.validate_v1(
        amount=decision.canonical_position_sizing.resulting_notional,
        decision_id=applied.decision_id,
    )
    with owner._lock:
        require_native_margin_locked_v1(owner, sizing, evaluated_at_utc=now)
    net = cost.assess_net_reversal_execution_cost_v1(
        injected.opening_cost_observation,
        current_contracts=current_contracts,
        account_identity=basis.account_identity,
        slot_id=basis.slot_id,
        cycle_id=cycle,
        **args,
    )
    result = dict(
        schema="btc_demo_net_reversal_financials.v1",
        account=basis.account_identity,
        lane_id=basis.slot_id,
        decision_epoch=epoch,
        evaluated_at_utc=now,
        slot_basis=basis.to_dict(),
        sizing=sizing.to_dict_v1(),
        net_order_cost=net,
        original_sources={k: asdict(v) for k, v in sources.items()},
        original_bodies=json.loads(injected.testnet_original_bodies_json),
    )
    _require_cost_cover_v1(result)
    return cost.canonical(result)


def _require_cost_cover_v1(record):
    sizing = ReservationSizingBindingV1.from_dict_v1(record["sizing"])
    target = sizing.decision.canonical_position_sizing.resulting_notional
    sizing.validate_v1(amount=target, decision_id=sizing.applied_input.decision_id)
    net = record["net_order_cost"]["order_cost"]
    future = cost.reserved_closing_cost_v1(sizing) + cost.reserved_funding_cost_v1(sizing)
    capital = Decimal(record["slot_basis"]["net_basis_usdc"])
    order = Decimal(net["total_opening_cost_usdc"])
    if target + order + future > capital:
        raise ValueError("TESTNET_REVERSAL_CAPITAL_WITH_NET_FEES_EXCEEDED")
    if sizing.decision.post_sizing_risk.resulting_max_loss + order + future > min(
        Decimal(25), capital
    ):
        raise ValueError("TESTNET_REVERSAL_REMAINING_LOSS_EXCEEDED")
    movement = json.loads(sizing.absolute_movement_cost_binding.receipt_json)[
        "observed_amplitude_native_money"
    ]
    if Fraction(int(movement["numerator"]), int(movement["denominator"])) <= Fraction(
        order + future
    ):
        raise ValueError("TESTNET_REVERSAL_MOVEMENT_DOES_NOT_COVER_NET_COSTS")
    return sizing


def verify_reversal_financials_v1(plan):
    record = json.loads(plan.financial_receipt_json)
    sizing = _require_cost_cover_v1(record)
    money, identity, _ = sizing.monetary_source.rebuild_v1()
    source = sizing.entry_cost_binding
    opening = cost.EntryExecutionCostObservationV1.from_dict_v1(json.loads(source.observation_json))
    originals = record["original_sources"]
    retained = json.loads(opening.sources_json)
    retained.update(
        json.loads(
            json.loads(sizing.native_initial_margin_binding.observation_json)["sources_json"]
        )
    )
    retained["funding"] = json.loads(
        json.loads(sizing.funding_cost_binding.observation_json)["source_json"]
    )
    if any(originals.get(key) != raw for key, raw in retained.items()):
        raise ValueError("TESTNET_REVERSAL_RETAINED_COST_SOURCE_MISMATCH")
    position = originals["positions"]["payload"]["data"]
    if (
        len(position) != 1
        or position[0].get("instId") != plan.episode.venue_native_id
        or position[0].get("posSide") != "net"
        or Decimal(position[0]["pos"]) != plan.current_contracts
        or originals["pending"]["payload"]["data"] != []
    ):
        raise ValueError("TESTNET_REVERSAL_RETAINED_POSITION_MISMATCH")
    rebuilt = cost.assess_net_reversal_execution_cost_v1(
        opening,
        current_contracts=plan.current_contracts,
        monetary_source=sizing.monetary_source,
        applied_input=sizing.applied_input,
        decision=sizing.decision,
        account_identity=record["account"],
        slot_id=record["lane_id"],
        cycle_id=opening.cycle_id,
        evaluated_at_utc=record["evaluated_at_utc"],
    )
    if (
        record["schema"] != "btc_demo_net_reversal_financials.v1"
        or identity.settle_currency != "USDC"
        or money.contract_settlement_rule is None
        or plan.quote_to_usdc != money.reference_price.amount / money.native_reference_price.amount
        or rebuilt != record["net_order_cost"]
        or record["account"] != plan.episode.account_scope.account_identity
        or record["lane_id"] != plan.episode.lane_id
        or record["decision_epoch"] != plan.decision_epoch
        or cost.digest(record["slot_basis"]) != plan.funding_digest
        or Decimal(rebuilt["target_contracts"]) != plan.target_contracts
        or sizing.decision.canonical_position_sizing.resulting_notional != plan.target_notional_usdc
        or sizing.monetary_source.native_reference_price != str(plan.reference_mark)
        or sizing.monetary_source.native_protective_stop_price != str(plan.protective_stop)
    ):
        raise ValueError("TESTNET_REVERSAL_FINANCIAL_BINDING_MISMATCH")
    for key, raw in record["original_sources"].items():
        body = bytes.fromhex(record["original_bodies"][key])
        if raw["body_sha256"] != sha256(body).hexdigest() or raw["payload"] != json.loads(body):
            raise ValueError("TESTNET_REVERSAL_RETAINED_ORIGINAL_CHANGED")
    return record
