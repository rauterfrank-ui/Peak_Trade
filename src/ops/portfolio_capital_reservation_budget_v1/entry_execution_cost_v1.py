"""Observed order costs, retained by the original reservation owner.

No implicit GET, order, profit forecast, future-fee guarantee or margin model.
The fee schedule and immediately executable book are inputs, not constants.
"""

from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from decimal import Decimal
import json
import re
from urllib.parse import parse_qs, urlsplit

from .durable_store_v1 import canonical, digest
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_acquisition_v1 import (
    acquisition_age_seconds_v1,
    utc_now_iso_v1,
)


def _money(value, *, positive=False):
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("ENTRY_COST_DECIMAL_STRING_REQUIRED")
    result = Decimal(value)
    if not result.is_finite() or positive and result <= 0:
        raise ValueError("ENTRY_COST_NUMERIC_DOMAIN_INVALID")
    return result


def _rows(payload):
    if (
        not isinstance(payload, dict)
        or payload.get("code") != "0"
        or not isinstance(payload.get("data"), list)
        or any(not isinstance(r, dict) for r in payload["data"])
    ):
        raise ValueError("ENTRY_COST_RESPONSE_INVALID")
    return payload["data"]


def _one(rows, key, value):
    found = [row for row in rows if row.get(key) == value]
    if len(found) != 1:
        raise ValueError("ENTRY_COST_SOURCE_ROW_NOT_UNIQUE:" + key)
    return found[0]


def _query(endpoint, path):
    parsed = urlsplit(endpoint)
    if parsed.scheme or parsed.netloc or parsed.fragment or parsed.path != path:
        raise ValueError("ENTRY_COST_ENDPOINT_SCOPE_MISMATCH")
    return parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)


def _event_clock(value, acquired, evaluated):
    if type(value) is not str or not value.isdigit() or int(value) <= 0:
        raise ValueError("ENTRY_COST_EVENT_TIME_REQUIRED")
    event = datetime.fromtimestamp(int(value) / 1000, timezone.utc).isoformat()
    acquisition_age_seconds_v1(acquired_at_utc=event, now_utc=acquired)
    acquisition_age_seconds_v1(acquired_at_utc=event, now_utc=evaluated)


@dataclass(frozen=True)
class EntryExecutionCostObservationV1:
    account_identity: str
    bound_instrument_json: str
    decision_epoch: str
    cycle_id: str
    acquisition_decision_id: str
    sources_json: str
    evaluated_at_utc: str
    order_type: str = "market"

    @classmethod
    def capture_v1(
        cls,
        *,
        account_identity,
        bound_instrument,
        decision_epoch,
        cycle_id,
        sources,
        evaluated_at_utc,
    ):
        if set(sources) != {"account", "instruments", "fees", "book"} or any(
            type(r) is not FreshPretradeGetTransportResultV1 for r in sources.values()
        ):
            raise ValueError("ENTRY_COST_ORIGINAL_GET_RESULTS_REQUIRED")
        acquisition = canonical(dict(decision_epoch=decision_epoch, cycle_id=cycle_id))
        return cls(
            account_identity,
            canonical(bound_instrument.to_dict()),
            decision_epoch,
            cycle_id,
            acquisition,
            canonical({k: asdict(v) for k, v in sources.items()}),
            evaluated_at_utc,
        )

    def to_dict_v1(self):
        return dict(schema="entry_execution_cost_observation.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            not isinstance(raw, dict)
            or raw.get("schema") != "entry_execution_cost_observation.v1"
            or set(raw) != {"schema", *(f.name for f in fields(cls))}
        ):
            raise ValueError("ENTRY_COST_OBSERVATION_SCHEMA_INVALID")
        return cls(**{k: v for k, v in raw.items() if k != "schema"})


def assess_opening_execution_cost_v1(
    observation,
    *,
    monetary_source,
    applied_input,
    decision,
    account_identity,
    slot_id,
    cycle_id,
    evaluated_at_utc=None,
):
    if type(observation) is not EntryExecutionCostObservationV1 or any(
        type(getattr(observation, f.name)) is not str or not getattr(observation, f.name)
        for f in fields(observation)
    ):
        raise ValueError("ENTRY_COST_TYPED_COMPLETE_OBSERVATION_REQUIRED")
    bound = json.loads(observation.bound_instrument_json)
    expected = canonical(dict(decision_epoch=observation.decision_epoch, cycle_id=cycle_id))
    if (
        observation.account_identity != account_identity
        or observation.cycle_id != cycle_id
        or observation.decision_epoch != monetary_source.decision_epoch
        or observation.acquisition_decision_id != expected
        or bound["instrument_id"] != applied_input.instrument_id
        or bound["venue_native_id"] != monetary_source.venue_native_id
    ):
        raise ValueError("ENTRY_COST_ACCOUNT_DECISION_OR_INSTRUMENT_MISMATCH")
    now = evaluated_at_utc or observation.evaluated_at_utc
    # The financial observation clock is distinct from the Core decision epoch.
    acquisition_age_seconds_v1(acquired_at_utc=observation.evaluated_at_utc, now_utc=now)
    sources = json.loads(observation.sources_json)
    if set(sources) != {"account", "instruments", "fees", "book"}:
        raise ValueError("ENTRY_COST_COMPLETE_SOURCES_REQUIRED")
    parsed = {}
    for key, raw in sources.items():
        result = FreshPretradeGetTransportResultV1(**raw)
        if (
            result.get_performed is not True
            or result.method != "GET"
            or result.http_status != 200
            or result.historical_reuse is not False
            or result.error_class
            or result.pretrade_decision_id != expected
            or key in {"account", "fees"}
            and result.auth_header_sent is not True
            or not re.fullmatch("[0-9a-f]{64}", result.body_sha256)
        ):
            raise ValueError("ENTRY_COST_CURRENT_ACCOUNT_BOUND_GET_REQUIRED:" + key)
        acquisition_age_seconds_v1(acquired_at_utc=result.acquired_at_utc, now_utc=now)
        # Retained acquisition cannot postdate the original financial assessment.
        acquisition_age_seconds_v1(
            acquired_at_utc=result.acquired_at_utc, now_utc=observation.evaluated_at_utc
        )
        parsed[key] = result
    account, public, fee, book = (parsed[k] for k in ("account", "instruments", "fees", "book"))
    if _query(account.endpoint, "/api/v5/account/config") != {}:
        raise ValueError("ENTRY_COST_ACCOUNT_QUERY_INVALID")
    accounts = _rows(account.payload)
    if len(accounts) != 1:
        raise ValueError("ENTRY_COST_ACCOUNT_SOURCE_NOT_UNIQUE")
    _one(accounts, "uid", account_identity)
    native = monetary_source.venue_native_id
    instrument = _one(_rows(public.payload), "instId", native)
    retained = _one(_rows(json.loads(monetary_source.instruments_json)), "instId", native)
    kind, family, group = (instrument.get(k) for k in ("instType", "instFamily", "groupId"))
    if (
        instrument != retained
        or kind not in {"SWAP", "FUTURES"}
        or any(type(s) is not str or not s or s.strip() != s for s in (family, group))
        or _query(public.endpoint, "/api/v5/public/instruments")
        != {"instType": [kind], "instId": [native]}
    ):
        raise ValueError("ENTRY_COST_INSTRUMENT_FEE_GROUP_UNPROVEN")
    # Family-specific request also covers incentive fee accounts. Never fall
    # back to deprecated top-level maker/taker(U/USDC) or another product group.
    if _query(fee.endpoint, "/api/v5/account/trade-fee") != {
        "instType": [kind],
        "instFamily": [family],
    }:
        raise ValueError("ENTRY_COST_FEE_QUERY_SCOPE_MISMATCH")
    rate_row = _one(_rows(fee.payload), "instType", kind)
    _event_clock(rate_row.get("ts"), fee.acquired_at_utc, now)
    groups = rate_row.get("feeGroup")
    if not isinstance(groups, list) or any(not isinstance(r, dict) for r in groups):
        raise ValueError("ENTRY_COST_CURRENT_FEE_GROUP_REQUIRED")
    rates = _one(groups, "groupId", group)
    maker, taker = (_money(rates.get(k)) for k in ("maker", "taker"))
    # A possible rebate never funds this reservation. Current market orders
    # consume liquidity; maker fills are not promised by a limit price.
    if observation.order_type != "market":
        raise ValueError("ENTRY_COST_MARKET_ORDER_ONLY")
    charged_rate = max(Decimal(0), -taker)
    query = _query(book.endpoint, "/api/v5/market/books")
    if (
        set(query) - {"instId", "sz"}
        or query.get("instId") != [native]
        or "sz" in query
        and (
            len(query["sz"]) != 1
            or not query["sz"][0].isdigit()
            or not 1 <= int(query["sz"][0]) <= 400
        )
    ):
        raise ValueError("ENTRY_COST_BOOK_QUERY_SCOPE_MISMATCH")
    rows = _rows(book.payload)
    if len(rows) != 1:
        raise ValueError("ENTRY_COST_BOOK_ROW_NOT_UNIQUE")
    row = rows[0]
    if row.get("instId", native) != native:
        raise ValueError("ENTRY_COST_BOOK_INSTRUMENT_MISMATCH")
    _event_clock(row.get("ts"), book.acquired_at_utc, now)
    levels = {}
    for side, descending in (("bids", True), ("asks", False)):
        values = row.get(side)
        if not isinstance(values, list) or not values:
            raise ValueError("ENTRY_COST_BOTH_BOOK_SIDES_REQUIRED")
        levels[side] = [
            (_money(v[0], positive=True), _money(v[1], positive=True))
            for v in values
            if isinstance(v, list) and len(v) >= 2
        ]
        if len(levels[side]) != len(values) or any(
            (a[0] <= b[0] if descending else a[0] >= b[0])
            for a, b in zip(levels[side], levels[side][1:])
        ):
            raise ValueError("ENTRY_COST_BOOK_ORDER_OR_LEVEL_INVALID")
    if levels["bids"][0][0] >= levels["asks"][0][0]:
        raise ValueError("ENTRY_COST_LOCKED_OR_CROSSED_BOOK")
    context = monetary_source.validate_sizing_v1(applied_input)
    if (
        applied_input.instrument.contract_kind != "LINEAR"
        or instrument.get("ctType") != "linear"
        or _money(instrument.get("ctMult"), positive=True) != 1
        or instrument.get("settleCcy") != context.native_reference_price.currency
    ):
        raise ValueError("ENTRY_COST_SUPPORTED_LINEAR_CONTRACT_REQUIRED")
    if context.usdt_usdc_edge is not None:
        _event_clock(context.usdt_usdc_edge.source_timestamp, monetary_source.observed_at, now)
    quantity = decision.final_quantity
    remaining, price_sum = quantity, Decimal(0)
    side = applied_input.selected_side.upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("ENTRY_COST_DIRECTION_INVALID")
    for price, count in levels["asks" if side == "LONG" else "bids"]:
        take = min(remaining, count)
        price_sum += take * price
        remaining -= take
    if remaining:
        raise ValueError("ENTRY_COST_EXECUTABLE_BOOK_DEPTH_INSUFFICIENT")
    reference = _money(monetary_source.native_reference_price, positive=True)
    fx = context.reference_price.amount / reference
    multiplier = applied_input.instrument.contract_multiplier
    fee_usdc = price_sum * multiplier * charged_rate * fx
    adverse = (
        max(Decimal(0), (price_sum - reference * quantity) * (1 if side == "LONG" else -1))
        * multiplier
        * fx
    )
    result = dict(
        schema="opening_execution_cost.v1",
        account_identity=account_identity,
        slot_id=str(slot_id),
        cycle_id=cycle_id,
        decision_id=applied_input.decision_id,
        canonical_id=applied_input.instrument_id,
        native_id=native,
        side=side,
        quantity=str(quantity),
        currency="USDC",
        fee_group=group,
        maker_rate=str(maker),
        taker_rate=str(taker),
        charged_rate=str(charged_rate),
        order_type=observation.order_type,
        quote_currency=context.native_reference_price.currency,
        fee_quote=str(price_sum * multiplier * charged_rate),
        fee_usdc=str(fee_usdc),
        adverse_entry_cost_usdc=str(adverse),
        total_opening_cost_usdc=str(fee_usdc + adverse),
        book_vwap=str(price_sum / quantity),
        basis="CURRENT_OPENING_ORDER_BOOK_AND_ACCOUNT_FEE_NOT_EXECUTION_GUARANTEE",
        future_close_fees_and_funding="NOT_INCLUDED",
        evaluated_at_utc=observation.evaluated_at_utc,
        observation_digest=digest(observation.to_dict_v1()),
    )
    return dict(**result, digest=digest(result))


@dataclass(frozen=True)
class EntryExecutionCostBindingV1:
    observation_json: str
    receipt_json: str

    def validate_v1(self, *, monetary_source, applied_input, decision):
        receipt = json.loads(self.receipt_json)
        observation = EntryExecutionCostObservationV1.from_dict_v1(
            json.loads(self.observation_json)
        )
        rebuilt = assess_opening_execution_cost_v1(
            observation,
            monetary_source=monetary_source,
            applied_input=applied_input,
            decision=decision,
            account_identity=receipt["account_identity"],
            slot_id=receipt["slot_id"],
            cycle_id=receipt["cycle_id"],
        )
        if receipt != rebuilt:
            raise ValueError("ENTRY_COST_RECEIPT_OR_QUANTITY_MISMATCH")
        return receipt

    def to_dict_v1(self):
        return dict(
            schema="entry_execution_cost_binding.v1",
            observation=json.loads(self.observation_json),
            receipt=json.loads(self.receipt_json),
        )

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            not isinstance(raw, dict)
            or set(raw) != {"schema", "observation", "receipt"}
            or raw["schema"] != "entry_execution_cost_binding.v1"
        ):
            raise ValueError("ENTRY_COST_BINDING_SCHEMA_INVALID")
        return cls(canonical(raw["observation"]), canonical(raw["receipt"]))


def bind_entry_execution_cost_v1(observation, **kwargs):
    result = assess_opening_execution_cost_v1(observation, **kwargs)
    return EntryExecutionCostBindingV1(canonical(observation.to_dict_v1()), canonical(result))


def reserved_opening_fee_v1(sizing):
    if sizing is None or sizing.entry_cost_binding is None:
        return Decimal(0)
    value = _money(json.loads(sizing.entry_cost_binding.receipt_json)["fee_usdc"])
    if value < 0:
        raise ValueError("ENTRY_COST_NEGATIVE_FEE_RESERVE")
    return value


def collect_entry_execution_cost_observation_v1(
    *, transport, account_identity, bound_instrument, inst_type, decision_epoch, cycle_id
):
    """Four decision-bound GETs through a supplied original read-only port.

    No transport construction, credentials, retries or allowlist expansion.
    The port's own capabilities and shared request budget still apply.
    """
    from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
        GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    from urllib.parse import urlencode

    if inst_type not in {"SWAP", "FUTURES"}:
        raise ValueError("ENTRY_COST_SUPPORTED_FUTURES_TYPE_REQUIRED")
    native = bound_instrument.venue_native_id
    acquisition = canonical(dict(decision_epoch=decision_epoch, cycle_id=cycle_id))
    sources = {}

    def get(key, path, query, private):
        endpoint = path + ("?" + urlencode(query) if query else "")
        result = transport.get(
            endpoint=endpoint,
            auth_required=private,
            pretrade_decision_id=acquisition,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
        if type(result) is not FreshPretradeGetTransportResultV1:
            raise ValueError("ENTRY_COST_ORIGINAL_GET_RESULT_REQUIRED")
        sources[key] = result
        return result

    get("account", "/api/v5/account/config", {}, True)
    public = get(
        "instruments", "/api/v5/public/instruments", dict(instType=inst_type, instId=native), False
    )
    row = _one(_rows(public.payload), "instId", native)
    family = row.get("instFamily")
    if type(family) is not str or not family or family.strip() != family:
        raise ValueError("ENTRY_COST_INSTRUMENT_FAMILY_REQUIRED")
    get("fees", "/api/v5/account/trade-fee", dict(instType=inst_type, instFamily=family), True)
    get("book", "/api/v5/market/books", dict(instId=native, sz="20"), False)
    return EntryExecutionCostObservationV1.capture_v1(
        account_identity=account_identity,
        bound_instrument=bound_instrument,
        decision_epoch=decision_epoch,
        cycle_id=cycle_id,
        sources=sources,
        evaluated_at_utc=utc_now_iso_v1(),
    )


def assess_closing_execution_cost_v1(
    entry_binding, *, monetary_source, applied_input, decision, evaluated_at_utc=None
):
    if type(entry_binding) is not EntryExecutionCostBindingV1:
        raise ValueError("CLOSE_COST_ORIGINAL_ENTRY_COST_BINDING_REQUIRED")
    opening = entry_binding.validate_v1(
        monetary_source=monetary_source, applied_input=applied_input, decision=decision
    )
    side = applied_input.selected_side.upper()
    if side not in {"LONG", "SHORT"} or decision.selected_side.upper() != side:
        raise ValueError("CLOSE_COST_ORIGINAL_POSITION_SIDE_MISMATCH")
    observation = EntryExecutionCostObservationV1.from_dict_v1(
        json.loads(entry_binding.observation_json)
    )
    # Reuse the original source parser and quantity/depth algorithm. This
    # side-flipped pricing request is not a sizing or opposite-entry decision.
    close_quote = assess_opening_execution_cost_v1(
        observation,
        monetary_source=monetary_source,
        applied_input=replace(applied_input, selected_side="SHORT" if side == "LONG" else "LONG"),
        decision=decision,
        account_identity=opening["account_identity"],
        slot_id=opening["slot_id"],
        cycle_id=opening["cycle_id"],
        evaluated_at_utc=evaluated_at_utc,
    )
    reference = _money(monetary_source.native_reference_price, positive=True)
    stop = _money(monetary_source.native_protective_stop_price, positive=True)
    # Fee planning also covers the original modeled adverse stop price. This
    # remains a conditional price basis, not guaranteed stop execution.
    fee_price = max(reference, stop, _money(close_quote["book_vwap"], positive=True))
    fx = applied_input.reference_price / reference
    fee = (
        fee_price
        * applied_input.instrument.contract_multiplier
        * decision.final_quantity
        * _money(close_quote["charged_rate"])
        * fx
    )
    adverse = _money(close_quote["adverse_entry_cost_usdc"])
    body = dict(
        schema="closing_execution_cost_provision.v1",
        account_identity=opening["account_identity"],
        slot_id=opening["slot_id"],
        cycle_id=opening["cycle_id"],
        decision_id=opening["decision_id"],
        canonical_id=opening["canonical_id"],
        native_id=opening["native_id"],
        position_side=side,
        closing_order_side="SELL" if side == "LONG" else "BUY",
        quantity=str(decision.final_quantity),
        currency="USDC",
        fee_group=opening["fee_group"],
        charged_rate=close_quote["charged_rate"],
        current_close_book_vwap=close_quote["book_vwap"],
        fee_price_basis_native=str(fee_price),
        fee_allowance_usdc=str(fee),
        current_adverse_close_cost_usdc=str(adverse),
        reserved_close_cost_usdc=str(fee + adverse),
        total_roundtrip_cost_allowance_usdc=str(
            _money(opening["total_opening_cost_usdc"]) + fee + adverse
        ),
        opening_observation_digest=opening["observation_digest"],
        opposite_book_quote_digest=close_quote["digest"],
        evaluated_at_utc=opening["evaluated_at_utc"],
        basis="CURRENT_BOOK_AND_ACCOUNT_FEE_PLUS_ORIGINAL_MODELED_STOP_PRICE",
        future_execution_or_fee_guaranteed=False,
        funding_included=False,
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": digest(body)}


@dataclass(frozen=True)
class CloseExecutionCostBindingV1:
    receipt_json: str

    def validate_v1(self, *, entry_binding, monetary_source, applied_input, decision):
        receipt = json.loads(self.receipt_json)
        rebuilt = assess_closing_execution_cost_v1(
            entry_binding,
            monetary_source=monetary_source,
            applied_input=applied_input,
            decision=decision,
        )
        if receipt != rebuilt:
            raise ValueError("CLOSE_COST_SOURCE_OR_PROVISION_MISMATCH")
        return rebuilt

    def to_dict_v1(self):
        return dict(
            schema="closing_execution_cost_binding.v1", receipt=json.loads(self.receipt_json)
        )

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or set(raw) != {"schema", "receipt"}
            or raw["schema"] != "closing_execution_cost_binding.v1"
        ):
            raise ValueError("CLOSE_COST_BINDING_SCHEMA_INVALID")
        return cls(canonical(raw["receipt"]))


def bind_closing_execution_cost_v1(entry_binding, **kwargs):
    return CloseExecutionCostBindingV1(
        canonical(assess_closing_execution_cost_v1(entry_binding, **kwargs))
    )


def reserved_closing_cost_v1(sizing):
    if sizing is None or sizing.close_cost_binding is None:
        return Decimal(0)
    result = _money(json.loads(sizing.close_cost_binding.receipt_json)["reserved_close_cost_usdc"])
    if result < 0:
        raise ValueError("CLOSE_COST_NEGATIVE_RESERVE")
    return result


@dataclass(frozen=True)
class FundingCostObservationV1:
    """A separately supplied public funding source, not an accounting debit."""

    bound_instrument_json: str
    decision_epoch: str
    cycle_id: str
    source_json: str
    evaluated_at_utc: str

    @classmethod
    def capture_v1(cls, *, bound_instrument, decision_epoch, cycle_id, source, evaluated_at_utc):
        if type(source) is not FreshPretradeGetTransportResultV1:
            raise ValueError("FUNDING_COST_ORIGINAL_GET_SOURCE_REQUIRED")
        return cls(
            canonical(bound_instrument.to_dict()),
            decision_epoch,
            cycle_id,
            canonical(asdict(source)),
            evaluated_at_utc,
        )

    def to_dict_v1(self):
        return dict(schema="funding_cost_observation.v1", **asdict(self))

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or raw.get("schema") != "funding_cost_observation.v1"
            or set(raw) != {"schema", *(f.name for f in fields(cls))}
        ):
            raise ValueError("FUNDING_COST_OBSERVATION_SCHEMA_INVALID")
        return cls(**{k: v for k, v in raw.items() if k != "schema"})


def assess_next_funding_cost_v1(
    observation,
    *,
    entry_binding,
    close_binding,
    monetary_source,
    applied_input,
    decision,
    evaluated_at_utc=None,
):
    if type(observation) is not FundingCostObservationV1 or any(
        type(getattr(observation, f.name)) is not str or not getattr(observation, f.name)
        for f in fields(observation)
    ):
        raise ValueError("FUNDING_COST_COMPLETE_TYPED_OBSERVATION_REQUIRED")
    if type(close_binding) is not CloseExecutionCostBindingV1:
        raise ValueError("FUNDING_COST_ORIGINAL_CLOSE_PROVISION_REQUIRED")
    closing = close_binding.validate_v1(
        entry_binding=entry_binding,
        monetary_source=monetary_source,
        applied_input=applied_input,
        decision=decision,
    )
    opening_observation = EntryExecutionCostObservationV1.from_dict_v1(
        json.loads(entry_binding.observation_json)
    )
    if (observation.bound_instrument_json, observation.decision_epoch, observation.cycle_id) != (
        opening_observation.bound_instrument_json,
        opening_observation.decision_epoch,
        opening_observation.cycle_id,
    ):
        raise ValueError("FUNDING_COST_ORIGINAL_INSTRUMENT_OR_DECISION_MISMATCH")
    now = evaluated_at_utc or observation.evaluated_at_utc
    acquisition_age_seconds_v1(acquired_at_utc=observation.evaluated_at_utc, now_utc=now)
    # Revalidate the associated market/FX basis at this financial observation,
    # without treating the two streams as one feed or replacing either source.
    assess_closing_execution_cost_v1(
        entry_binding,
        monetary_source=monetary_source,
        applied_input=applied_input,
        decision=decision,
        evaluated_at_utc=now,
    )
    source = FreshPretradeGetTransportResultV1(**json.loads(observation.source_json))
    native = monetary_source.venue_native_id
    acquisition = canonical(
        dict(decision_epoch=observation.decision_epoch, cycle_id=observation.cycle_id)
    )
    if (
        source.get_performed is not True
        or source.method != "GET"
        or source.http_status != 200
        or source.historical_reuse is not False
        or source.auth_header_sent is not False
        or source.error_class
        or source.pretrade_decision_id != acquisition
        or not re.fullmatch("[0-9a-f]{64}", source.body_sha256)
        or _query(source.endpoint, "/api/v5/public/funding-rate") != {"instId": [native]}
    ):
        raise ValueError("FUNDING_COST_CURRENT_PUBLIC_INSTRUMENT_GET_REQUIRED")
    acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now)
    acquisition_age_seconds_v1(
        acquired_at_utc=source.acquired_at_utc, now_utc=observation.evaluated_at_utc
    )
    row = _one(_rows(source.payload), "instId", native)
    instrument = _one(_rows(json.loads(monetary_source.instruments_json)), "instId", native)
    if (
        row.get("instType") not in {"SWAP", "FUTURES"}
        or row.get("instType") != instrument.get("instType")
        or row.get("method") != "current_period"
        or row.get("settState") != "settled"
    ):
        raise ValueError("FUNDING_COST_PRODUCT_OR_SETTLEMENT_STATE_UNPROVEN")
    _event_clock(row.get("ts"), source.acquired_at_utc, now)
    predicted, floor, ceiling = (
        _money(row.get(k)) for k in ("fundingRate", "minFundingRate", "maxFundingRate")
    )
    if not floor <= predicted <= ceiling or floor > 0 or ceiling < 0:
        raise ValueError("FUNDING_COST_RATE_LIMITS_INVALID")
    times = [row.get(k) for k in ("fundingTime", "nextFundingTime")]
    if any(type(t) is not str or not t.isdigit() or int(t) <= 0 for t in times):
        raise ValueError("FUNDING_COST_INSTRUMENT_SETTLEMENT_CLOCK_REQUIRED")
    now_ms = int(datetime.fromisoformat(now.replace("Z", "+00:00")).timestamp() * 1000)
    if not now_ms < int(times[0]) < int(times[1]):
        raise ValueError("FUNDING_COST_NEXT_SETTLEMENT_BOUND_EXPIRED_OR_INVALID")
    exposure = (
        _money(closing["fee_price_basis_native"], positive=True)
        * applied_input.instrument.contract_multiplier
        * decision.final_quantity
        * (
            applied_input.reference_price
            / _money(monetary_source.native_reference_price, positive=True)
        )
    )
    side = applied_input.selected_side.upper()
    allowance_rate = ceiling if side == "LONG" else -floor
    body = dict(
        schema="next_funding_cost_provision.v1",
        account_identity=closing["account_identity"],
        slot_id=closing["slot_id"],
        cycle_id=closing["cycle_id"],
        decision_id=closing["decision_id"],
        canonical_id=closing["canonical_id"],
        native_id=native,
        position_side=side,
        quantity=str(decision.final_quantity),
        currency="USDC",
        exposure_basis_usdc=str(exposure),
        predicted_rate=str(predicted),
        lower_rate_limit=str(floor),
        upper_rate_limit=str(ceiling),
        adverse_rate_allowance=str(allowance_rate),
        funding_allowance_usdc=str(exposure * allowance_rate),
        upcoming_funding_time_ms=int(times[0]),
        following_funding_time_forecast_ms=int(times[1]),
        evaluated_at_utc=observation.evaluated_at_utc,
        source_observation_digest=digest(observation.to_dict_v1()),
        close_provision_digest=closing["digest"],
        basis="CURRENT_INSTRUMENT_RATE_LIMIT_AND_MODELED_PRICE_NEXT_SETTLEMENT_ONLY",
        actual_funding_payment=False,
        future_rate_limit_or_execution_guaranteed=False,
        future_credit_funds_reservation=False,
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": digest(body)}


@dataclass(frozen=True)
class FundingCostBindingV1:
    observation_json: str
    receipt_json: str

    def validate_v1(self, **kwargs):
        receipt = json.loads(self.receipt_json)
        rebuilt = assess_next_funding_cost_v1(
            FundingCostObservationV1.from_dict_v1(json.loads(self.observation_json)), **kwargs
        )
        if receipt != rebuilt:
            raise ValueError("FUNDING_COST_SOURCE_OR_PROVISION_MISMATCH")
        return rebuilt

    def to_dict_v1(self):
        return dict(
            schema="funding_cost_binding.v1",
            observation=json.loads(self.observation_json),
            receipt=json.loads(self.receipt_json),
        )

    @classmethod
    def from_dict_v1(cls, raw):
        if (
            type(raw) is not dict
            or set(raw) != {"schema", "observation", "receipt"}
            or raw["schema"] != "funding_cost_binding.v1"
        ):
            raise ValueError("FUNDING_COST_BINDING_SCHEMA_INVALID")
        return cls(canonical(raw["observation"]), canonical(raw["receipt"]))


def bind_next_funding_cost_v1(observation, **kwargs):
    return FundingCostBindingV1(
        canonical(observation.to_dict_v1())
        if type(observation) is FundingCostObservationV1
        else "null",
        canonical(assess_next_funding_cost_v1(observation, **kwargs)),
    )


def reserved_funding_cost_v1(sizing):
    if sizing is None or sizing.funding_cost_binding is None:
        return Decimal(0)
    result = _money(json.loads(sizing.funding_cost_binding.receipt_json)["funding_allowance_usdc"])
    if result < 0:
        raise ValueError("FUNDING_COST_NEGATIVE_RESERVE")
    return result
