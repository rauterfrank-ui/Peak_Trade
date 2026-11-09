"""Native coverage of existing obligations; no new balance or reservation writer.

Exact native cost arithmetic follows the original cost owner's formulas. FX may
measure a retained USDC provision, never create collateral. Original IM/opening
commitments remain charged even after a fill; no unproven venue credit is given.
"""

from dataclasses import asdict
from decimal import Decimal
from fractions import Fraction
import json
import re

from . import entry_execution_cost_v1 as cost
from .durable_store_v1 import digest
from .sizing_binding_v1 import ReservationSizingBindingV1


def _f(value):
    return Fraction(cost._money(str(value)))


def _pack(value):
    return dict(numerator=str(value.numerator), denominator=str(value.denominator))


def _unpack(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def _quote(book, side, quantity):
    remaining, total = quantity, Fraction(0)
    for price, size, *_ in book[side]:
        take = min(remaining, _f(size))
        total += take * _f(price)
        remaining -= take
    if remaining:
        raise ValueError("NATIVE_COST_COVER_EXECUTABLE_DEPTH_INSUFFICIENT")
    return total


def original_costs_v1(sizing):
    """Rebuild original costs from retained validated inputs, without VWAP rounding."""
    sizing.validate_v1(
        amount=sizing.decision.canonical_position_sizing.resulting_notional,
        decision_id=sizing.applied_input.decision_id,
    )
    if any(
        v is None
        for v in (
            sizing.native_initial_margin_binding,
            sizing.entry_cost_binding,
            sizing.close_cost_binding,
            sizing.funding_cost_binding,
        )
    ):
        raise ValueError("NATIVE_COST_COVER_ORIGINAL_BINDINGS_REQUIRED")
    margin = json.loads(sizing.native_initial_margin_binding.receipt_json)
    opening = json.loads(sizing.entry_cost_binding.receipt_json)
    closing = json.loads(sizing.close_cost_binding.receipt_json)
    funding = json.loads(sizing.funding_cost_binding.receipt_json)
    sources = json.loads(json.loads(sizing.entry_cost_binding.observation_json)["sources_json"])
    book = cost._rows(sources["book"]["payload"])[0]
    quantity = _f(sizing.decision.final_quantity)
    reference = _f(sizing.monetary_source.native_reference_price)
    stop = _f(sizing.monetary_source.native_protective_stop_price)
    multiplier = _f(sizing.applied_input.instrument.contract_multiplier)
    long = opening["side"] == "LONG"
    direction = 1 if long else -1
    entry_quote = _quote(book, "asks" if long else "bids", quantity)
    close_quote = _quote(book, "bids" if long else "asks", quantity)
    fee_basis = max(reference * quantity, stop * quantity, close_quote) * multiplier
    fx = _f(sizing.applied_input.reference_price) / reference
    # Keep both the exact native formula and the existing USDC provision's
    # measured native equivalent. Decimal projection must not understate either.
    opening_cost = max(
        entry_quote * multiplier * _f(opening["charged_rate"])
        + max(Fraction(0), direction * (entry_quote - reference * quantity)) * multiplier,
        _f(opening["total_opening_cost_usdc"]) / fx,
    )
    close_cost = max(
        fee_basis * _f(closing["charged_rate"])
        + max(Fraction(0), direction * (reference * quantity - close_quote)) * multiplier,
        _f(closing["reserved_close_cost_usdc"]) / fx,
    )
    funding_cost = max(
        fee_basis * _f(funding["adverse_rate_allowance"]),
        _f(funding["funding_allowance_usdc"]) / fx,
    )
    return margin, dict(
        initial_margin=Fraction(
            int(margin["required_numerator"]), int(margin["required_denominator"])
        ),
        opening=opening_cost,
        closing=close_cost,
        funding=funding_cost,
    )


def _effective_costs(sizing, history):
    margin, values = original_costs_v1(sizing)
    if history:
        native = history[-1].get("native_cost_cover")
        if native is None or native["settlement_currency"] != margin["settlement_currency"]:
            raise ValueError("NATIVE_COST_COVER_RENEWED_RESERVE_REQUIRED")
        values.update({k: _unpack(native["target_costs"][k]) for k in ("closing", "funding")})
    return margin, values


def require_native_cost_cover_locked_v1(owner, sizing, *, exclude_reservation_id=None):
    """Called inside the original IM gate and original owner lock, early and late."""
    candidate, values = original_costs_v1(sizing)
    required = sum(values.values(), Fraction(0))
    for key, hold in owner._by_key.items():
        if not hold.counts_against_budget or str(hold.reservation_id) == exclude_reservation_id:
            continue
        prior, costs = _effective_costs(
            owner._sizing_bindings[key], owner._open_slot_cost_reserves.get(key, [])
        )
        if prior["account_identity"] != candidate["account_identity"]:
            raise ValueError("NATIVE_COST_COVER_ACCOUNT_MISMATCH")
        if prior["settlement_currency"] == candidate["settlement_currency"]:
            required += sum(costs.values(), Fraction(0))
    if required > _f(candidate["available_native"]):
        raise ValueError("NATIVE_COST_COVER_LOCAL_OBLIGATIONS_UNCOVERED")


def assess_renewed_native_cover_v1(owner, rid, observation, current, context, prior, output):
    """Pure reconstruction from the preceding durable revision and current sources."""
    if context.native_balance_source_json == "null":
        raise ValueError("NATIVE_COST_COVER_CURRENT_BALANCE_REQUIRED")
    source = cost.FreshPretradeGetTransportResultV1(
        **json.loads(context.native_balance_source_json)
    )
    sources = json.loads(observation.cost_sources_json)
    account = cost._rows(sources["account"]["payload"])[0]
    if account.get("acctLv") != "2" or account.get("posMode") != "net_mode":
        raise ValueError("NATIVE_COST_COVER_FUTURES_CROSS_NET_REQUIRED")
    if (
        source.get_performed is not True
        or source.method != "GET"
        or source.http_status != 200
        or source.auth_header_sent is not True
        or source.historical_reuse is not False
        or source.error_class
        or not re.fullmatch("[0-9a-f]{64}", source.body_sha256)
        or source.pretrade_decision_id != sources["account"]["pretrade_decision_id"]
        or cost._query(source.endpoint, "/api/v5/account/balance") != {}
        or source.acquired_at_utc != output.observed_at_as_of
    ):
        raise ValueError("NATIVE_COST_COVER_CURRENT_BOUND_BALANCE_REQUIRED")
    cost.acquisition_age_seconds_v1(
        acquired_at_utc=source.acquired_at_utc, now_utc=observation.valuation_epoch
    )
    rows = cost._rows(source.payload)
    if len(rows) != 1 or rows[0].get("uid", owner._account_identity) != owner._account_identity:
        raise ValueError("NATIVE_COST_COVER_BALANCE_ACCOUNT_MISMATCH")
    details = rows[0].get("details")
    if type(details) is not list or any(type(r) is not dict for r in details):
        raise ValueError("NATIVE_COST_COVER_CURRENCY_DETAILS_REQUIRED")
    usdc = cost._money(cost._one(details, "ccy", "USDC").get("availEq"), positive=True)
    if Decimal(output.value) > usdc:
        raise ValueError("NATIVE_COST_COVER_CAPITAL_EXCEEDS_CURRENT_SOURCE")
    binding = ReservationSizingBindingV1.from_dict_v1(prior["sizing_bindings"][rid])
    margin, original = original_costs_v1(binding)
    quantity = _f(current["quantity"])
    mark = _f(current["native_mark_price"])
    multiplier = _f(binding.applied_input.instrument.contract_multiplier)
    book = cost._rows(sources["book"]["payload"])[0]
    long = current["position_side"] == "LONG"
    quote = _quote(book, "bids" if long else "asks", quantity)
    basis = (
        max(
            mark * quantity,
            _f(binding.monetary_source.native_protective_stop_price) * quantity,
            quote,
        )
        * multiplier
    )
    fx, _ = cost._open_slot_fx_v1(margin["settlement_currency"], observation)
    closing = max(
        basis * _f(current["charged_rate"])
        + max(Fraction(0), (1 if long else -1) * (mark * quantity - quote)) * multiplier,
        _f(current["close_provision_usdc"]) / _f(fx),
    )
    funding = max(
        basis * _f(current["adverse_funding_rate"]),
        _f(current["funding_provision_usdc"]) / _f(fx),
    )
    target = {**original, "closing": closing, "funding": funding}
    totals = {}
    for record in prior["reservations"]:
        if record["state"] not in {"RESERVED", "COMMITTED"}:
            continue
        key = record["reservation_id"]
        row, values = (
            (margin, target)
            if key == rid
            else _effective_costs(
                ReservationSizingBindingV1.from_dict_v1(prior["sizing_bindings"][key]),
                prior.get("open_slot_cost_reserves", {}).get(key, []),
            )
        )
        if row["account_identity"] != owner._account_identity:
            raise ValueError("NATIVE_COST_COVER_ACCOUNT_MISMATCH")
        ccy = row["settlement_currency"]
        totals[ccy] = totals.get(ccy, Fraction(0)) + sum(values.values(), Fraction(0))
    available = {}
    for ccy, required in totals.items():
        value = cost._money(cost._one(details, "ccy", ccy).get("availEq"))
        if value < 0:
            raise ValueError("NATIVE_COST_COVER_NEGATIVE_AVAILABLE_EQUITY")
        available[ccy] = str(value)
    body = dict(
        schema="renewed_native_cost_cover.v1",
        settlement_currency=margin["settlement_currency"],
        target_costs={k: _pack(v) for k, v in target.items()},
        required_by_currency={k: _pack(v) for k, v in totals.items()},
        available_by_currency=available,
        covered=all(v <= _f(available[k]) for k, v in totals.items()),
        balance_source_digest=digest(asdict(source)),
        preceding_budget_digest=context.budget_digest,
        role="CONSERVATIVE_LOCAL_OBLIGATIONS_NO_VENUE_MARGIN_OR_PAID_COST_CREDIT",
        liquidation_cover_proven=False,
        future_margin_guaranteed=False,
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": digest(body)}
