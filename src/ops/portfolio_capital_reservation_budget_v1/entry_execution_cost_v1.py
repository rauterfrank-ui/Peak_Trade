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


@dataclass(frozen=True)
class OpenSlotLossObservationV1:
    """A point-in-time simulated accounting source and independent current mark/FX."""

    identity_json: str
    initial_source_ref: str
    current_source_ref: str
    mark_source_json: str
    valuation_epoch: str
    index_tickers_json: str = "null"
    pair_instruments_json: str = "null"
    fx_acquired_at_utc: str = ""
    cost_sources_json: str = "null"
    renewal_context_json: str = "null"
    cost_reserve_ref: str = ""

    @classmethod
    def capture_v1(
        cls,
        *,
        episode,
        mark_source,
        valuation_epoch,
        index_tickers_payload=None,
        pair_instruments_payload=None,
        fx_acquired_at_utc="",
        cost_sources=None,
        renewal_context=None,
    ):
        if type(mark_source) is not FreshPretradeGetTransportResultV1:
            raise ValueError("OPEN_SLOT_ORIGINAL_MARK_SOURCE_REQUIRED")
        if renewal_context is not None:
            from .open_slot_cost_renewal_v1 import OpenSlotCostRenewalContextV1

            if type(renewal_context) is not OpenSlotCostRenewalContextV1:
                raise ValueError("OPEN_SLOT_ORIGINAL_RENEWAL_CONTEXT_REQUIRED")
        if cost_sources is not None and (
            type(cost_sources) is not dict
            or set(cost_sources) != {"account", "instruments", "fees", "book", "funding"}
            or any(type(s) is not FreshPretradeGetTransportResultV1 for s in cost_sources.values())
        ):
            raise ValueError("OPEN_SLOT_ORIGINAL_COST_GET_RESULTS_REQUIRED")
        progress = episode.binding.simulated_accounting_progress
        return cls(
            canonical(asdict(episode.identity)),
            episode.entry_source_ref,
            episode.entry_source_ref if progress is None else progress["current_source_ref"],
            canonical(asdict(mark_source)),
            valuation_epoch,
            canonical(index_tickers_payload),
            canonical(pair_instruments_payload),
            fx_acquired_at_utc,
            "null"
            if cost_sources is None
            else canonical({k: asdict(v) for k, v in cost_sources.items()}),
            "null" if renewal_context is None else canonical(renewal_context.to_dict_v1()),
        )

    def to_dict_v1(self):
        body = asdict(self)
        if self.renewal_context_json != "null" or self.cost_reserve_ref:
            return dict(schema="open_slot_loss_observation.v3", **body)
        body.pop("renewal_context_json")
        body.pop("cost_reserve_ref")
        if self.cost_sources_json == "null":
            body.pop("cost_sources_json")
            return dict(schema="open_slot_loss_observation.v1", **body)
        return dict(schema="open_slot_loss_observation.v2", **body)

    @classmethod
    def from_dict_v1(cls, raw):
        names = {f.name for f in fields(cls)}
        if isinstance(raw, dict) and raw.get("schema") in {
            "open_slot_loss_observation.v1",
            "open_slot_loss_observation.v2",
        }:
            names -= {"renewal_context_json", "cost_reserve_ref"}
        if isinstance(raw, dict) and raw.get("schema") == "open_slot_loss_observation.v1":
            names.remove("cost_sources_json")
        if (
            type(raw) is not dict
            or set(raw) != {"schema", *names}
            or raw["schema"]
            not in {
                "open_slot_loss_observation.v1",
                "open_slot_loss_observation.v2",
                "open_slot_loss_observation.v3",
            }
        ):
            raise ValueError("OPEN_SLOT_LOSS_OBSERVATION_SCHEMA_INVALID")
        return cls(**{k: v for k, v in raw.items() if k != "schema"})


def open_slot_mark_acquisition_id_v1(identity, valuation_epoch):
    # This is an observation context, never a fabricated trading decision.
    return "open-slot-loss:" + digest(
        dict(identity=asdict(identity), valuation_epoch=valuation_epoch)
    )


def _open_slot_fx_v1(currency, observation):
    from src.ops.governed_productive_monetary_normalization_v1.instrument_monetary_identity_v1 import (
        conversion_pair_monetary_identity_from_okx_payload_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
        build_usdt_usdc_conversion_edge_from_index_tickers_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
        USDT_USDC_PAIR_NATIVE_ID,
    )

    if currency == "USDC":
        return Decimal(1), None
    if currency != "USDT":
        raise ValueError("OPEN_SLOT_CURRENCY_UNSUPPORTED")
    acquisition_age_seconds_v1(
        acquired_at_utc=observation.fx_acquired_at_utc, now_utc=observation.valuation_epoch
    )
    base, quote = conversion_pair_monetary_identity_from_okx_payload_v1(
        json.loads(observation.pair_instruments_json), pair_native_id=USDT_USDC_PAIR_NATIVE_ID
    )
    edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
        index_tickers_payload=json.loads(observation.index_tickers_json),
        decision_epoch=observation.valuation_epoch,
        observed_at=observation.fx_acquired_at_utc,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        pair_base_currency=base,
        pair_quote_currency=quote,
    )
    _event_clock(edge.source_timestamp, observation.fx_acquired_at_utc, observation.valuation_epoch)
    return edge.normalized_rate, edge.payload_digest


def assess_current_open_slot_cost_v1(
    owner, reservation_id, observation, loss_proof, *, funding_horizon_ms=None
):
    """Protection-only repricing within the original next-settlement horizon.

    The original reservation, quantity authority and payment ledger are not
    rewritten. A changed funding period requires its own settlement contract.
    """
    binding = owner._sizing_bindings[reservation_id]
    original = json.loads(binding.monetary_source.instruments_json)
    native = loss_proof["identity"]["venue_native_id"]
    retained = _one(_rows(original), "instId", native)
    kind = retained["instType"]
    identity = loss_proof["identity"]
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )

    episode_identity = PositionEpisodeIdentityV1(
        **{**identity, "account_scope": PositionEpisodeScopeV1(**identity["account_scope"])}
    )
    context = open_slot_mark_acquisition_id_v1(episode_identity, observation.valuation_epoch)
    raw_sources = json.loads(observation.cost_sources_json)
    if type(raw_sources) is not dict or set(raw_sources) != {
        "account",
        "instruments",
        "fees",
        "book",
        "funding",
    }:
        raise ValueError("OPEN_SLOT_CURRENT_COST_SOURCES_REQUIRED")
    sources = {}
    for name, raw in raw_sources.items():
        source = FreshPretradeGetTransportResultV1(**raw)
        if (
            source.get_performed is not True
            or source.method != "GET"
            or source.http_status != 200
            or source.historical_reuse is not False
            or source.auth_header_sent is not (name in {"account", "fees"})
            or source.error_class
            or source.pretrade_decision_id != context
            or not re.fullmatch("[0-9a-f]{64}", source.body_sha256)
        ):
            raise ValueError("OPEN_SLOT_CURRENT_COST_GET_CONTEXT_INVALID:" + name)
        acquisition_age_seconds_v1(
            acquired_at_utc=source.acquired_at_utc, now_utc=observation.valuation_epoch
        )
        sources[name] = source
    account, instruments, fee, book, funding = (
        sources[k] for k in ("account", "instruments", "fees", "book", "funding")
    )
    account_rows = _rows(account.payload)
    if _query(account.endpoint, "/api/v5/account/config") != {} or len(account_rows) != 1:
        raise ValueError("OPEN_SLOT_CURRENT_COST_ACCOUNT_UNPROVEN")
    _one(account_rows, "uid", owner._account_identity)
    if (
        _query(instruments.endpoint, "/api/v5/public/instruments")
        != {"instType": [kind], "instId": [native]}
        or _one(_rows(instruments.payload), "instId", native) != retained
    ):
        raise ValueError("OPEN_SLOT_CURRENT_COST_ORIGINAL_CONTRACT_MISMATCH")
    if _query(fee.endpoint, "/api/v5/account/trade-fee") != {
        "instType": [kind],
        "instFamily": [retained["instFamily"]],
    }:
        raise ValueError("OPEN_SLOT_CURRENT_COST_FEE_SCOPE_INVALID")
    fee_row = _one(_rows(fee.payload), "instType", kind)
    _event_clock(fee_row.get("ts"), fee.acquired_at_utc, observation.valuation_epoch)
    groups = fee_row.get("feeGroup")
    if type(groups) is not list or any(type(g) is not dict for g in groups):
        raise ValueError("OPEN_SLOT_CURRENT_COST_FEE_GROUP_REQUIRED")
    fee_group = _one(groups, "groupId", retained["groupId"])
    _money(fee_group.get("maker"))
    charged_rate = max(Decimal(0), -_money(fee_group.get("taker")))
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
        raise ValueError("OPEN_SLOT_CURRENT_COST_BOOK_SCOPE_INVALID")
    books = _rows(book.payload)
    if len(books) != 1 or books[0].get("instId", native) != native:
        raise ValueError("OPEN_SLOT_CURRENT_COST_BOOK_INSTRUMENT_MISMATCH")
    row = books[0]
    _event_clock(row.get("ts"), book.acquired_at_utc, observation.valuation_epoch)
    levels = {}
    for side, descending in (("bids", True), ("asks", False)):
        values = row.get(side)
        if type(values) is not list or not values:
            raise ValueError("OPEN_SLOT_CURRENT_COST_BOTH_BOOK_SIDES_REQUIRED")
        levels[side] = [
            (_money(v[0], positive=True), _money(v[1], positive=True))
            for v in values
            if type(v) is list and len(v) >= 2
        ]
        if len(levels[side]) != len(values) or any(
            (a[0] <= b[0] if descending else a[0] >= b[0])
            for a, b in zip(levels[side], levels[side][1:])
        ):
            raise ValueError("OPEN_SLOT_CURRENT_COST_BOOK_ORDER_INVALID")
    if levels["bids"][0][0] >= levels["asks"][0][0]:
        raise ValueError("OPEN_SLOT_CURRENT_COST_CROSSED_BOOK")
    quantity = _money(loss_proof["quantity"], positive=True)
    remaining, price_sum = quantity, Decimal(0)
    position_side = identity["position_side"].upper()
    for price, count in levels["bids" if position_side == "LONG" else "asks"]:
        take = min(remaining, count)
        price_sum += take * price
        remaining -= take
    if remaining:
        raise ValueError("OPEN_SLOT_CURRENT_CLOSE_DEPTH_INSUFFICIENT")
    mark = _money(loss_proof["native_mark_price"], positive=True)
    multiplier = binding.applied_input.instrument.contract_multiplier
    fx, fx_digest = _open_slot_fx_v1(retained["settleCcy"], observation)
    vwap = price_sum / quantity
    fee_price = max(
        mark, vwap, _money(binding.monetary_source.native_protective_stop_price, positive=True)
    )
    close_fee = fee_price * quantity * multiplier * charged_rate * fx
    adverse = (
        max(Decimal(0), (mark * quantity - price_sum) * (1 if position_side == "LONG" else -1))
        * multiplier
        * fx
    )
    if _query(funding.endpoint, "/api/v5/public/funding-rate") != {"instId": [native]}:
        raise ValueError("OPEN_SLOT_CURRENT_COST_FUNDING_SCOPE_INVALID")
    funding_row = _one(_rows(funding.payload), "instId", native)
    if (
        funding_row.get("instType") != kind
        or funding_row.get("method") != "current_period"
        or funding_row.get("settState") != "settled"
    ):
        raise ValueError("OPEN_SLOT_CURRENT_COST_FUNDING_STATE_UNPROVEN")
    _event_clock(funding_row.get("ts"), funding.acquired_at_utc, observation.valuation_epoch)
    predicted, floor, ceiling = (
        _money(funding_row.get(k)) for k in ("fundingRate", "minFundingRate", "maxFundingRate")
    )
    if not floor <= predicted <= ceiling or floor > 0 or ceiling < 0:
        raise ValueError("OPEN_SLOT_CURRENT_COST_FUNDING_LIMITS_INVALID")
    times = [funding_row.get(k) for k in ("fundingTime", "nextFundingTime")]
    if any(type(t) is not str or not t.isdigit() or int(t) <= 0 for t in times):
        raise ValueError("OPEN_SLOT_CURRENT_COST_FUNDING_CLOCK_INVALID")
    original_horizon = json.loads(binding.funding_cost_binding.receipt_json)[
        "upcoming_funding_time_ms"
    ]
    if funding_horizon_ms is not None:
        original_horizon = funding_horizon_ms
    now_ms = int(
        datetime.fromisoformat(observation.valuation_epoch.replace("Z", "+00:00")).timestamp()
        * 1000
    )
    if not now_ms < int(times[0]) < int(times[1]) or int(times[0]) != original_horizon:
        raise ValueError("OPEN_SLOT_FUNDING_PERIOD_ROLLOVER_NOT_ADMITTED")
    funding_rate = ceiling if position_side == "LONG" else -floor
    funding_allowance = fee_price * quantity * multiplier * fx * funding_rate
    body = dict(
        schema="current_open_slot_cost_protection.v1",
        reservation_id=reservation_id,
        slot_id=identity["lane_id"],
        account_identity=owner._account_identity,
        native_id=native,
        position_side=position_side,
        quantity=str(quantity),
        currency="USDC",
        valuation_epoch=observation.valuation_epoch,
        native_mark_price=str(mark),
        closing_order_side="SELL" if position_side == "LONG" else "BUY",
        current_close_book_vwap=str(vwap),
        charged_rate=str(charged_rate),
        fee_group=retained["groupId"],
        fee_price_basis_native=str(fee_price),
        close_fee_usdc=str(close_fee),
        adverse_close_cost_usdc=str(adverse),
        close_provision_usdc=str(close_fee + adverse),
        funding_provision_usdc=str(funding_allowance),
        total_future_cost_provision_usdc=str(close_fee + adverse + funding_allowance),
        adverse_funding_rate=str(funding_rate),
        predicted_funding_rate=str(predicted),
        upcoming_funding_time_ms=original_horizon,
        following_funding_time_forecast_ms=int(times[1]),
        sources_digest=digest(raw_sources),
        fx_payload_digest=fx_digest,
        accounting_source_ref=observation.current_source_ref,
        actual_funding_payment=False,
        reservation_rewritten=False,
        positive_financial_admission=False,
        runtime_authorization_effect="NONE",
    )
    return {**body, "digest": digest(body)}


def _assess_open_slot_loss_base_v1(owner, reservation_id, observation):
    """Original-kernel valuation; no fill, fee, funding payment or balance writer."""
    from .slot_economic_source_v1 import _fill
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
        _source,
        _same_accounting_domain,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        bind_simulated_accounting_episode_identity_v1,
        economic_journal_events_v1,
        require_economic_history_extension_v1,
        latest_economic_event_time_v1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )

    if type(observation) is not OpenSlotLossObservationV1 or any(
        type(getattr(observation, f.name)) is not str for f in fields(observation)
    ):
        raise ValueError("OPEN_SLOT_TYPED_OBSERVATION_REQUIRED")
    policy = owner._entry_budget_policy
    if not policy or not policy.enforce_open_slot_loss_protection:
        raise ValueError("OPEN_SLOT_EXPLICIT_TEST_POLICY_REQUIRED")
    record = owner._by_key.get(owner._by_id.get(reservation_id))
    binding = owner._sizing_bindings.get(reservation_id)
    link = owner._execution_links.get(reservation_id)
    if record is None or binding is None or link is None or binding.monetary_source is None:
        raise ValueError("OPEN_SLOT_ORIGINAL_RESERVATION_REQUIRED")
    binding.validate_v1(amount=record.amount, decision_id=record.decision_id)
    data = json.loads(observation.identity_json)
    identity = PositionEpisodeIdentityV1(
        **{**data, "account_scope": PositionEpisodeScopeV1(**data["account_scope"])}
    )
    identity.validate_v1()
    bound = owner._reservation_bindings[reservation_id]["bound"]
    if identity.account_scope.execution_environment != "INTERNAL_SIMULATED_EXECUTION" or (
        identity.lane_id,
        identity.account_scope.account_identity,
        identity.instrument_id,
        identity.venue_native_id,
    ) != (
        str(record.slot_id),
        owner._account_identity,
        bound["instrument_id"],
        bound["venue_native_id"],
    ):
        raise ValueError("OPEN_SLOT_ACCOUNT_INSTRUMENT_OR_SLOT_MISMATCH")
    initial, _ = _source(observation.initial_source_ref, identity)
    current, anchors = _source(observation.current_source_ref, identity)
    _same_accounting_domain(initial, current)
    require_economic_history_extension_v1(initial, current)
    valuation = datetime.fromisoformat(observation.valuation_epoch.replace("Z", "+00:00"))
    if valuation.utcoffset() is None or valuation.timestamp() < latest_economic_event_time_v1(
        current
    ):
        raise ValueError("OPEN_SLOT_ACCOUNTING_AFTER_VALUATION")
    frozen = ProductiveFuturesAccountingSessionV1.from_durable_dict(
        current["accounting_checkpoint"]
    )
    _, money_identity, constraints = binding.monetary_source.rebuild_v1()
    if (
        frozen.contract.quote_currency != money_identity.settle_currency
        or money_identity.quote_currency != money_identity.settle_currency
        or frozen.contract.contract_size != constraints.contract_multiplier
        or frozen.contract.tick_size != constraints.tick_size
        or frozen.contract.min_qty != constraints.minimum_quantity
        or frozen.position is None
        or frozen.position.qty <= 0
        or frozen.position.side.value != identity.position_side
        or frozen.position.qty > Decimal(link["envelope"]["quantity"])
        or anchors["entry_event_time"] > valuation.timestamp()
    ):
        raise ValueError("OPEN_SLOT_ORIGINAL_OPEN_CONTRACT_OR_QUANTITY_MISMATCH")
    opening_equity = None
    replay = ProductiveFuturesAccountingSessionV1(
        contract=frozen.contract,
        initial_equity=frozen.initial_equity,
        writer_identity=frozen.writer_identity,
    )
    for event in economic_journal_events_v1(initial):
        row = event["value"]
        if event["kind"] == "FUNDING":
            replay.apply_funding_observation_v1(
                event_id=event["event_id"],
                amount=row["amount"],
                currency=row["currency"],
                instrument_id=row["instrument_id"],
                event_time_unix=row["event_time_unix"],
            )
            continue
        fill = _fill(row)
        before = replay.portfolio_state().equity
        result = replay.apply_fill(fill)
        if (
            result.action_code in {"LONG_OPEN", "SHORT_OPEN"}
            and bind_simulated_accounting_episode_identity_v1(identity=identity, opening_fill=fill)
            == identity
        ):
            if (
                fill.fill_id
                not in {
                    p + link["envelope"]["envelope_digest"]
                    for p in ("original-plan:", "next-original-plan:", "offline-envelope:")
                }
                or fill.side.lower() != link["envelope"]["side"]
            ):
                raise ValueError("OPEN_SLOT_ORIGINAL_ENTRY_FILL_REQUIRED")
            opening_equity = before
    if opening_equity is None:
        raise ValueError("OPEN_SLOT_ORIGINAL_EPISODE_OPENING_REQUIRED")
    mark_source = FreshPretradeGetTransportResultV1(**json.loads(observation.mark_source_json))
    kind = _one(
        _rows(json.loads(binding.monetary_source.instruments_json)),
        "instId",
        identity.venue_native_id,
    )["instType"]
    if (
        mark_source.get_performed is not True
        or mark_source.method != "GET"
        or mark_source.http_status != 200
        or mark_source.auth_header_sent is not False
        or mark_source.historical_reuse is not False
        or mark_source.error_class
        or mark_source.pretrade_decision_id
        != open_slot_mark_acquisition_id_v1(identity, observation.valuation_epoch)
        or not re.fullmatch("[0-9a-f]{64}", mark_source.body_sha256)
        or _query(mark_source.endpoint, "/api/v5/public/mark-price")
        != {"instType": [kind], "instId": [identity.venue_native_id]}
    ):
        raise ValueError("OPEN_SLOT_CURRENT_PUBLIC_MARK_REQUIRED")
    acquisition_age_seconds_v1(
        acquired_at_utc=mark_source.acquired_at_utc, now_utc=observation.valuation_epoch
    )
    mark = _one(_rows(mark_source.payload), "instId", identity.venue_native_id)
    if mark.get("instType") != kind:
        raise ValueError("OPEN_SLOT_MARK_PRODUCT_MISMATCH")
    _event_clock(mark.get("ts"), mark_source.acquired_at_utc, observation.valuation_epoch)
    price = _money(mark.get("markPx"), positive=True)
    frozen.mark_to_market(price)
    native_result = frozen.portfolio_state().equity - opening_equity
    rate, fx_digest = _open_slot_fx_v1(frozen.contract.quote_currency, observation)
    prior = [
        r
        for r in owner._slot_test_economics[identity.lane_id]["records"]
        if r["reservation_id"] != reservation_id
        and datetime.fromisoformat(r["valuation_epoch"].replace("Z", "+00:00")) <= valuation
    ]
    closed_net = sum((Decimal(r["net_result_usdc"]) for r in prior), Decimal(0))
    limit = policy.per_slot_test_loss_limit
    allowance = min(limit, max(Decimal(0), limit + closed_net)) + native_result * rate
    close_cost = reserved_closing_cost_v1(binding)
    funding = json.loads(binding.funding_cost_binding.receipt_json)
    horizon_valid = int(valuation.timestamp() * 1000) < funding["upcoming_funding_time_ms"]
    original_funding_provision = reserved_funding_cost_v1(binding)
    if policy.renew_open_slot_cost_reserves:
        from .open_slot_cost_renewal_v1 import effective_reserve_v1

        close_cost, original_funding_provision, horizon = effective_reserve_v1(
            owner, reservation_id, observation.cost_reserve_ref
        )
        horizon_valid = int(valuation.timestamp() * 1000) < horizon
    exhausted = allowance <= 0
    close_required = (
        exhausted
        or (horizon_valid or policy.renew_open_slot_cost_reserves)
        and allowance <= close_cost + original_funding_provision
    )
    body = dict(
        schema="open_slot_loss_protection.v1",
        reservation_id=reservation_id,
        slot_id=identity.lane_id,
        identity=asdict(identity),
        quantity=str(frozen.position.qty),
        native_mark_price=str(price),
        currency="USDC",
        native_net_result=str(native_result),
        mark_valued_open_net_result_usdc=str(native_result * rate),
        prior_closed_net_result_usdc=str(closed_net),
        prior_closed_records_digest=digest(prior),
        remaining_allowance_before_future_costs_usdc=str(allowance),
        original_close_provision_usdc=str(reserved_closing_cost_v1(binding)),
        original_next_funding_provision_usdc=str(reserved_funding_cost_v1(binding)),
        original_funding_horizon_valid=int(valuation.timestamp() * 1000)
        < funding["upcoming_funding_time_ms"],
        actual_loss_allowance_exhausted=exhausted,
        close_required=bool(close_required),
        reason="TEST_SLOT_MARK_VALUED_LOSS_ALLOWANCE_EXHAUSTED"
        if exhausted
        else "TEST_SLOT_ORIGINAL_COST_PROVISIONS_UNCOVERED"
        if close_required
        else "NO_OBSERVED_LOSS_CLOSE_TRIGGER",
        valuation_epoch=observation.valuation_epoch,
        observation=observation.to_dict_v1(),
        fx_payload_digest=fx_digest,
        accounting_basis="ORIGINAL_SIMULATED_KERNEL_EQUITY_SINCE_TARGET_OPEN_INCLUDES_OBSERVED_FEES_AND_FUNDING_NO_EXTRA_SLIPPAGE_DEBIT",
        future_liability_basis="ORIGINAL_ENTRY_PROVISIONS_NOT_RENEWED",
        funding_or_cost_rollover_admitted=False,
        private_venue_cash_observed=False,
        runtime_authorization_effect="NONE",
        policy_digest=policy.digest_v1(),
    )
    if policy.refresh_open_slot_cost_protection and not policy.renew_open_slot_cost_reserves:
        body.update(
            schema="open_slot_loss_protection.v2",
            current_cost_provision=None,
            current_cost_status="UNPROVEN_ORIGINAL_PROTECTION_RETAINED",
            current_cost_reasons=[],
        )
        try:
            current_cost = assess_current_open_slot_cost_v1(
                owner, reservation_id, observation, body
            )
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            body["current_cost_reasons"] = [str(exc)]
        else:
            body.update(
                current_cost_provision=current_cost,
                current_cost_status="OBSERVED_PROTECTION_ONLY",
                future_liability_basis="MAX_ORIGINAL_AND_CURRENT_SAME_SETTLEMENT_COSTS_PROTECTION_ONLY",
            )
            required = max(
                close_cost + original_funding_provision,
                Decimal(current_cost["total_future_cost_provision_usdc"]),
            )
            if allowance <= required and not body["close_required"]:
                body.update(
                    close_required=True, reason="TEST_SLOT_CURRENT_COST_PROVISIONS_UNCOVERED"
                )
    return {**body, "digest": digest(body)}


def assess_open_slot_loss_v1(owner, reservation_id, observation):
    """Public valuation path shared by the original owner and cold readback."""
    base = _assess_open_slot_loss_base_v1(owner, reservation_id, observation)
    if owner._entry_budget_policy.renew_open_slot_cost_reserves:
        from .open_slot_cost_renewal_v1 import assess_renewal_v1

        return assess_renewal_v1(owner, reservation_id, observation, base)
    return base


def restore_open_slot_protection_v1(owner, raw):
    policy = owner._entry_budget_policy
    if policy is None or not policy.enforce_open_slot_loss_protection:
        if raw is not None:
            raise ValueError("OPEN_SLOT_PROTECTION_OUTSIDE_EXPLICIT_POLICY")
        return {}
    if type(raw) is not dict or set(raw) != set(policy.allowed_slot_ids):
        raise ValueError("OPEN_SLOT_PROTECTION_STATE_REQUIRED")
    for slot, row in raw.items():
        if row is None:
            continue
        if (
            type(row) is not dict
            or set(row) != {"latest", "pending_close", "exhaustion"}
            or row["latest"] is None
        ):
            raise ValueError("OPEN_SLOT_PROTECTION_STATE_INVALID")
        latest = datetime.fromisoformat(row["latest"]["valuation_epoch"].replace("Z", "+00:00"))
        if (
            row["latest"]["close_required"]
            and row["pending_close"] is None
            or (
                row["exhaustion"] is None
                and any(
                    proof is not None and proof["actual_loss_allowance_exhausted"]
                    for proof in row.values()
                )
            )
        ):
            raise ValueError("OPEN_SLOT_PROTECTION_LATCH_MISSING")
        for key, proof in row.items():
            if proof is None:
                continue
            rebuilt = assess_open_slot_loss_v1(
                owner,
                proof["reservation_id"],
                OpenSlotLossObservationV1.from_dict_v1(proof["observation"]),
            )
            if (
                proof != rebuilt
                or proof["slot_id"] != slot
                or datetime.fromisoformat(proof["valuation_epoch"].replace("Z", "+00:00")) > latest
                or key == "pending_close"
                and proof["close_required"] is not True
                or key == "exhaustion"
                and proof["actual_loss_allowance_exhausted"] is not True
            ):
                raise ValueError("OPEN_SLOT_PROTECTION_SOURCE_OR_SUMMARY_MISMATCH")
            if policy.renew_open_slot_cost_reserves:
                history = owner._open_slot_cost_reserves.get(proof["reservation_id"], [])
                renewal = proof["reserve_renewal"]
                if renewal is not None and renewal not in history:
                    raise ValueError("OPEN_SLOT_PROTECTION_RENEWAL_HOLD_MISSING")
                if key == "latest" and (
                    renewal is not None
                    and history[-1] != renewal
                    or renewal is None
                    and proof["observation"]["cost_reserve_ref"]
                    != (history[-1]["digest"] if history else "")
                ):
                    raise ValueError("OPEN_SLOT_PROTECTION_CURRENT_RESERVE_MISMATCH")
    return json.loads(canonical(raw))


@dataclass(frozen=True)
class SlotLossExitRequestV1:
    """Reference to a durable original budget fact, never a free safety boolean."""

    owner: object
    reservation_id: str
    proof_digest: str

    def validate_v1(self, *, episode, bound, observed_unix):
        from .contract_v1 import PortfolioCapitalReservationBudgetOwnerV1

        if type(self.owner) is not PortfolioCapitalReservationBudgetOwnerV1 or episode is None:
            raise ValueError("OPEN_SLOT_ORIGINAL_BUDGET_CLOSE_REQUEST_REQUIRED")
        return self.owner.inspect_open_slot_loss_exit_v1(
            reservation_id=self.reservation_id,
            proof_digest=self.proof_digest,
            episode=episode,
            bound=bound,
            observed_unix=observed_unix,
        )
