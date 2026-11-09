"""Decision-bound native initial margin, retained by the original budget owner.

Only acctLv=2, cross, net-mode linear USDT/USDC contracts are supported. A
valuation FX edge never supplies collateral. Public tiers, liquidation estimates,
cost cover and future margin changes are not inferred from this admission.
"""

from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from fractions import Fraction
import json
import re

from .durable_store_v1 import canonical, digest
from . import entry_execution_cost_v1 as cost
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductiveUsdcFreeMarginObservationV1,
    OBSERVATION_FACT_ID,
    OBSERVATION_SURFACE,
)


def _number(value, *, positive=False):
    result = cost._money(value, positive=positive)
    if result < 0:
        raise ValueError("NATIVE_INITIAL_MARGIN_NEGATIVE_VALUE")
    return result


@dataclass(frozen=True)
class NativeInitialMarginObservationV1:
    sources_json: str
    opening_observation_digest: str
    evaluated_at_utc: str

    @classmethod
    def capture_v1(cls, *, sources, opening_observation, evaluated_at_utc):
        if (
            set(sources) != {"balance", "leverage"}
            or any(type(r) is not cost.FreshPretradeGetTransportResultV1 for r in sources.values())
            or type(opening_observation) is not cost.EntryExecutionCostObservationV1
        ):
            raise ValueError("NATIVE_INITIAL_MARGIN_ORIGINAL_GETS_REQUIRED")
        return cls(
            canonical({k: asdict(r) for k, r in sources.items()}),
            digest(opening_observation.to_dict_v1()),
            evaluated_at_utc,
        )

    def to_dict_v1(self):
        return dict(schema="native_initial_margin_observation.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema", *(f.name for f in fields(cls))}
            or raw["schema"] != "native_initial_margin_observation.v1"
        ):
            raise ValueError("NATIVE_INITIAL_MARGIN_OBSERVATION_SCHEMA_INVALID")
        return cls(**{k: v for k, v in raw.items() if k != "schema"})


def assess_native_initial_margin_v1(
    observation,
    *,
    original_margin,
    entry_binding,
    monetary_source,
    applied_input,
    decision,
    evaluated_at_utc=None,
):
    if type(observation) is not NativeInitialMarginObservationV1 or any(
        type(getattr(observation, f.name)) is not str or not getattr(observation, f.name)
        for f in fields(observation)
    ):
        raise ValueError("NATIVE_INITIAL_MARGIN_TYPED_OBSERVATION_REQUIRED")
    if type(original_margin) is not CurrentProductiveUsdcFreeMarginObservationV1:
        raise ValueError("NATIVE_INITIAL_MARGIN_ORIGINAL_29P_OBSERVATION_REQUIRED")
    if type(entry_binding) is not cost.EntryExecutionCostBindingV1:
        raise ValueError("NATIVE_INITIAL_MARGIN_ORIGINAL_ENTRY_BINDING_REQUIRED")
    opening = cost.EntryExecutionCostObservationV1.from_dict_v1(
        json.loads(entry_binding.observation_json)
    )
    entry = entry_binding.validate_v1(
        monetary_source=monetary_source, applied_input=applied_input, decision=decision
    )
    if observation.opening_observation_digest != digest(opening.to_dict_v1()):
        raise ValueError("NATIVE_INITIAL_MARGIN_ENTRY_SOURCE_MISMATCH")
    now = evaluated_at_utc or observation.evaluated_at_utc
    cost.acquisition_age_seconds_v1(acquired_at_utc=observation.evaluated_at_utc, now_utc=now)
    sources = json.loads(observation.sources_json)
    if set(sources) != {"balance", "leverage"}:
        raise ValueError("NATIVE_INITIAL_MARGIN_COMPLETE_SOURCES_REQUIRED")
    parsed = {}
    for key, raw in sources.items():
        result = cost.FreshPretradeGetTransportResultV1(**raw)
        if (
            result.get_performed is not True
            or result.method != "GET"
            or result.http_status != 200
            or result.auth_header_sent is not True
            or result.historical_reuse is not False
            or result.error_class
            or result.pretrade_decision_id != opening.acquisition_decision_id
            or not re.fullmatch("[0-9a-f]{64}", result.body_sha256)
        ):
            raise ValueError("NATIVE_INITIAL_MARGIN_FRESH_BOUND_PRIVATE_GET_REQUIRED:" + key)
        cost.acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now)
        cost.acquisition_age_seconds_v1(
            acquired_at_utc=result.acquired_at_utc, now_utc=observation.evaluated_at_utc
        )
        parsed[key] = result
    config = cost._rows(json.loads(opening.sources_json)["account"]["payload"])[0]
    if config.get("acctLv") != "2" or config.get("posMode") != "net_mode":
        raise ValueError("NATIVE_INITIAL_MARGIN_FUTURES_CROSS_NET_SCOPE_REQUIRED")
    # Revalidate the original config/instrument acquisitions at the late clock.
    cost.assess_opening_execution_cost_v1(
        opening,
        monetary_source=monetary_source,
        applied_input=applied_input,
        decision=decision,
        account_identity=entry["account_identity"],
        slot_id=entry["slot_id"],
        cycle_id=entry["cycle_id"],
        evaluated_at_utc=now,
    )
    context, identity, _ = monetary_source.rebuild_v1()
    currency = identity.settle_currency
    if identity.ct_val_currency != identity.base_currency:
        raise ValueError("NATIVE_INITIAL_MARGIN_CONTRACT_VALUE_UNIT_UNPROVEN")
    if (
        currency not in {"USDT", "USDC"}
        or identity.quote_currency != currency
        or context.native_reference_price.currency != currency
        or entry["quote_currency"] != currency
    ):
        raise ValueError("NATIVE_INITIAL_MARGIN_SETTLEMENT_ROUTE_UNPROVEN")
    balance, leverage = (parsed[k] for k in ("balance", "leverage"))
    if cost._query(balance.endpoint, "/api/v5/account/balance") != {}:
        raise ValueError("NATIVE_INITIAL_MARGIN_UNFILTERED_BALANCE_REQUIRED")
    balances = cost._rows(balance.payload)
    if len(balances) != 1:
        raise ValueError("NATIVE_INITIAL_MARGIN_BALANCE_NOT_UNIQUE")
    row = balances[0]
    if row.get("uid", entry["account_identity"]) != entry["account_identity"]:
        raise ValueError("NATIVE_INITIAL_MARGIN_ACCOUNT_MISMATCH")
    details = row.get("details")
    if not isinstance(details, list) or any(not isinstance(r, dict) for r in details):
        raise ValueError("NATIVE_INITIAL_MARGIN_CURRENCY_DETAILS_REQUIRED")
    usdc = cost._one(details, "ccy", "USDC")
    if (
        original_margin.value != usdc.get("availEq")
        or original_margin.fact_id != OBSERVATION_FACT_ID
        or original_margin.surface != OBSERVATION_SURFACE
        or original_margin.already_net_of_in_use != "true"
        or original_margin.account_level_avail_eq_used != "false"
        or original_margin.fallback_chain_used != "false"
        or original_margin.bound_venue_identity != "okx"
        or original_margin.selected_ccy != "USDC"
        or original_margin.settlement_currency != "USDC"
        or original_margin.bound_account_identity != entry["account_identity"]
        or original_margin.bound_td_mode != "cross"
        or original_margin.decision_epoch != opening.decision_epoch
        or original_margin.observed_at_as_of != balance.acquired_at_utc
        or original_margin.provenance_digest != balance.body_sha256
    ):
        raise ValueError("NATIVE_INITIAL_MARGIN_ORIGINAL_CAPITAL_SOURCE_MISMATCH")
    if applied_input.account_equity > _number(usdc.get("availEq"), positive=True):
        raise ValueError("NATIVE_INITIAL_MARGIN_ORIGINAL_CAPITAL_BASIS_EXCEEDS_SOURCE")
    available = _number(cost._one(details, "ccy", currency).get("availEq"))
    native = monetary_source.venue_native_id
    if cost._query(leverage.endpoint, "/api/v5/account/leverage-info") != {
        "instId": [native],
        "mgnMode": ["cross"],
    }:
        raise ValueError("NATIVE_INITIAL_MARGIN_LEVERAGE_QUERY_MISMATCH")
    levers = cost._rows(leverage.payload)
    if len(levers) != 1 or any(
        levers[0].get(k) != v
        for k, v in (("instId", native), ("mgnMode", "cross"), ("posSide", "net"))
    ):
        raise ValueError("NATIVE_INITIAL_MARGIN_LEVERAGE_SCOPE_MISMATCH")
    lever = _number(levers[0].get("lever"), positive=True)
    # Exact rational arithmetic: a repeating 1/lever must never round down to
    # allow an otherwise insufficient balance. These are native money units.
    reference = _number(monetary_source.native_reference_price, positive=True)
    # Reuse the validated book levels, retaining exact fractional quote value;
    # the displayed VWAP can be a repeating rounded decimal.
    book = cost._rows(json.loads(opening.sources_json)["book"]["payload"])[0]
    remaining, quote_value = Fraction(decision.final_quantity), Fraction(0)
    for price, size, *_ in book["asks" if entry["side"] == "LONG" else "bids"]:
        take = min(remaining, Fraction(Decimal(size)))
        quote_value += take * Fraction(Decimal(price))
        remaining -= take
    if remaining:
        raise ValueError("NATIVE_INITIAL_MARGIN_EXECUTABLE_DEPTH_INSUFFICIENT")
    quote_value = max(quote_value, Fraction(decision.final_quantity) * Fraction(reference))
    notional = quote_value * Fraction(identity.ct_val)
    required = notional / Fraction(lever)
    if required > Fraction(available):
        raise ValueError("NATIVE_INITIAL_MARGIN_INSUFFICIENT")
    result = dict(
        schema="native_initial_margin.v1",
        account_identity=entry["account_identity"],
        slot_id=entry["slot_id"],
        cycle_id=entry["cycle_id"],
        decision_id=entry["decision_id"],
        native_id=native,
        side=entry["side"],
        quantity=entry["quantity"],
        td_mode="cross",
        settlement_currency=currency,
        available_native=str(available),
        observed_leverage=str(lever),
        reference_price=str(reference),
        notional_numerator=str(notional.numerator),
        notional_denominator=str(notional.denominator),
        required_numerator=str(required.numerator),
        required_denominator=str(required.denominator),
        observation_digest=digest(observation.to_dict_v1()),
        original_capital_observation_digest=digest(asdict(original_margin)),
        entry_receipt_digest=entry["digest"],
        evaluated_at_utc=observation.evaluated_at_utc,
        role="INITIAL_MARGIN_ONLY_NO_MARGIN_CREDIT_FOR_LOCAL_HOLDS",
        liquidation_cover_proven=False,
        future_margin_guaranteed=False,
        native_cost_cover_proven=False,
        runtime_authorization_effect="NONE",
    )
    return dict(**result, digest=digest(result))


@dataclass(frozen=True)
class NativeInitialMarginBindingV1:
    observation_json: str
    original_margin_json: str
    receipt_json: str

    def validate_v1(
        self, *, entry_binding, monetary_source, applied_input, decision, evaluated_at_utc=None
    ):
        receipt = json.loads(self.receipt_json)
        rebuilt = assess_native_initial_margin_v1(
            NativeInitialMarginObservationV1.from_dict_v1(json.loads(self.observation_json)),
            original_margin=CurrentProductiveUsdcFreeMarginObservationV1(
                **json.loads(self.original_margin_json)
            ),
            entry_binding=entry_binding,
            monetary_source=monetary_source,
            applied_input=applied_input,
            decision=decision,
            evaluated_at_utc=evaluated_at_utc,
        )
        if receipt != rebuilt:
            raise ValueError("NATIVE_INITIAL_MARGIN_RECEIPT_SOURCE_OR_QUANTITY_MISMATCH")
        return receipt

    def to_dict_v1(self):
        return dict(
            schema="native_initial_margin_binding.v1",
            observation=json.loads(self.observation_json),
            original_margin=json.loads(self.original_margin_json),
            receipt=json.loads(self.receipt_json),
        )

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema", "observation", "original_margin", "receipt"}
            or raw["schema"] != "native_initial_margin_binding.v1"
        ):
            raise ValueError("NATIVE_INITIAL_MARGIN_BINDING_SCHEMA_INVALID")
        return cls(*(canonical(raw[k]) for k in ("observation", "original_margin", "receipt")))


def bind_native_initial_margin_v1(observation, **kwargs):
    receipt = assess_native_initial_margin_v1(observation, **kwargs)
    return NativeInitialMarginBindingV1(
        canonical(observation.to_dict_v1()),
        canonical(asdict(kwargs["original_margin"])),
        canonical(receipt),
    )


def require_native_margin_locked_v1(
    owner, sizing, *, exclude_reservation_id=None, evaluated_at_utc=None
):
    """Original owner lock; compare exact native obligations without venue credit.

    Old local IM commitments remain charged after a fill/unknown submit. A fresh
    balance already net of venue use never proves how much local credit to grant.
    Released records no longer count. This creates no second durable ledger.
    """
    binding = sizing.native_initial_margin_binding if sizing is not None else None
    if type(binding) is not NativeInitialMarginBindingV1:
        raise ValueError("NATIVE_INITIAL_MARGIN_BINDING_REQUIRED")
    receipt = binding.validate_v1(
        entry_binding=sizing.entry_cost_binding,
        monetary_source=sizing.monetary_source,
        applied_input=sizing.applied_input,
        decision=sizing.decision,
        evaluated_at_utc=evaluated_at_utc,
    )
    required = Fraction(int(receipt["required_numerator"]), int(receipt["required_denominator"]))
    for key, hold in owner._by_key.items():
        if not hold.counts_against_budget or str(hold.reservation_id) == exclude_reservation_id:
            continue
        prior = owner._sizing_bindings.get(key)
        if (
            prior is None
            or type(prior.native_initial_margin_binding) is not NativeInitialMarginBindingV1
        ):
            raise ValueError("NATIVE_INITIAL_MARGIN_ACTIVE_OBLIGATION_UNPROVEN")
        row = prior.native_initial_margin_binding.validate_v1(
            entry_binding=prior.entry_cost_binding,
            monetary_source=prior.monetary_source,
            applied_input=prior.applied_input,
            decision=prior.decision,
        )
        if row["account_identity"] != receipt["account_identity"]:
            raise ValueError("NATIVE_INITIAL_MARGIN_OBLIGATION_ACCOUNT_MISMATCH")
        if row["settlement_currency"] == receipt["settlement_currency"]:
            required += Fraction(int(row["required_numerator"]), int(row["required_denominator"]))
    if required > Fraction(Decimal(receipt["available_native"])):
        raise ValueError("NATIVE_INITIAL_MARGIN_LOCAL_OBLIGATIONS_UNCOVERED")
    return receipt


def collect_native_initial_margin_observation_v1(*, transport, opening_observation, balance_source):
    """Explicit port only: reuse original 29P balance, request one leverage GET.

    No credentials, default transport, writes or automatic acquisition on import.
    The account/instrument sources remain owned by the original cost collector.
    """
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )

    native = json.loads(opening_observation.bound_instrument_json)["venue_native_id"]
    leverage = transport.get(
        endpoint=f"/api/v5/account/leverage-info?instId={native}&mgnMode=cross",
        auth_required=True,
        pretrade_decision_id=opening_observation.acquisition_decision_id,
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    return NativeInitialMarginObservationV1.capture_v1(
        sources=dict(balance=balance_source, leverage=leverage),
        opening_observation=opening_observation,
        evaluated_at_utc=cost.utc_now_iso_v1(),
    )
