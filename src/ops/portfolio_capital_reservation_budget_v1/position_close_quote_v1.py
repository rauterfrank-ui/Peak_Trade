"""Current full-position close quote; no sizing, payment or exit decision.

The private linear contract supplies its settlement unit. Native USD prices
remain prices; no market USD/USDC exchange rate or cash-parity claim is made.
"""

from decimal import Decimal, localcontext
import json

from . import entry_execution_cost_v1 as cost
from .durable_store_v1 import digest


def quote_btc_demo_position_close_v1(
    owner, *, reservation_id, sources, acquisition_id, quantity, position_side, now_utc
):
    if set(sources) != {"account", "instruments", "fees", "book"}:
        raise ValueError("SESSION_CLOSE_COST_ORIGINAL_SOURCES_REQUIRED")
    binding = owner._sizing_bindings[reservation_id]
    native = owner._reservation_bindings[reservation_id]["bound"]["venue_native_id"]
    retained = cost._one(
        cost._rows(json.loads(binding.monetary_source.instruments_json)), "instId", native
    )
    for key, source in sources.items():
        if (
            type(source) is not cost.FreshPretradeGetTransportResultV1
            or source.get_performed is not True
            or source.method != "GET"
            or source.http_status != 200
            or source.historical_reuse is not False
            or source.venue_live_contact is not True
            or source.auth_header_sent is not (key != "book")
            or source.error_class
            or source.pretrade_decision_id != acquisition_id
            or source.transport_class != "OKX_EEA_DEMO_READ_ONLY_GET"
        ):
            raise ValueError("SESSION_CLOSE_COST_CURRENT_GET_REQUIRED:" + key)
        cost.acquisition_age_seconds_v1(acquired_at_utc=source.acquired_at_utc, now_utc=now_utc)
    account, instruments, fees, book = (
        sources[k] for k in ("account", "instruments", "fees", "book")
    )
    accounts = cost._rows(account.payload)
    if cost._query(account.endpoint, "/api/v5/account/config") or len(accounts) != 1:
        raise ValueError("SESSION_CLOSE_COST_ACCOUNT_UNPROVEN")
    config = cost._one(accounts, "uid", owner._account_identity)
    path = cost._instrument_source_path_v1(instruments, retained, config)
    current = cost._one(cost._rows(instruments.payload), "instId", native)
    if (
        current != retained
        or cost._query(instruments.endpoint, path) != {"instType": ["FUTURES"], "instId": [native]}
        or retained["settleCcy"] != "USDC"
        or native != "BTC-USD_UM_XPERP-310328"
        or retained.get("ctType") != "linear"
        or cost._money(retained["ctMult"], positive=True) != 1
        or owner.execution_environment_v1() != "TESTNET"
    ):
        raise ValueError("SESSION_CLOSE_COST_ORIGINAL_USDC_CONTRACT_REQUIRED")
    # Rebuild the original native linear settlement rule before consuming its
    # multiplier. A price unit is not used as an observed cash balance.
    _, money, _ = binding.monetary_source.rebuild_v1()
    if money.settle_currency != "USDC":
        raise ValueError("SESSION_CLOSE_COST_SETTLEMENT_CURRENCY_MISMATCH")
    size = cost._money(quantity, positive=True)
    lot = cost._money(retained["lotSz"], positive=True)
    if size % lot or size < cost._money(retained["minSz"], positive=True):
        raise ValueError("SESSION_CLOSE_NATIVE_QUANTITY_INVALID")
    if cost._query(fees.endpoint, "/api/v5/account/trade-fee") != {
        "instType": ["FUTURES"],
        "instFamily": [retained["instFamily"]],
    }:
        raise ValueError("SESSION_CLOSE_FEE_SCOPE_MISMATCH")
    fee = cost._one(cost._rows(fees.payload), "instType", "FUTURES")
    cost._event_clock(fee["ts"], fees.acquired_at_utc, now_utc)
    group = cost._one(fee["feeGroup"], "groupId", retained["groupId"])
    cost._money(group["maker"])
    rate = max(Decimal(0), -cost._money(group["taker"]))
    if cost._query(book.endpoint, "/api/v5/market/books") != {"instId": [native], "sz": ["20"]}:
        raise ValueError("SESSION_CLOSE_BOOK_SCOPE_MISMATCH")
    books = cost._rows(book.payload)
    if len(books) != 1 or books[0].get("instId", native) != native:
        raise ValueError("SESSION_CLOSE_BOOK_INSTRUMENT_MISMATCH")
    row, levels = books[0], {}
    cost._event_clock(row["ts"], book.acquired_at_utc, now_utc)
    for side, descending in (("bids", True), ("asks", False)):
        raw = row.get(side)
        if type(raw) is not list or not raw or any(type(v) is not list or len(v) < 2 for v in raw):
            raise ValueError("SESSION_CLOSE_BOOK_LEVEL_INVALID")
        values = [(cost._money(v[0], positive=True), cost._money(v[1], positive=True)) for v in raw]
        if any((a[0] <= b[0] if descending else a[0] >= b[0]) for a, b in zip(values, values[1:])):
            raise ValueError("SESSION_CLOSE_BOOK_ORDER_INVALID")
        levels[side] = values
    if levels["bids"][0][0] >= levels["asks"][0][0] or position_side not in {"long", "short"}:
        raise ValueError("SESSION_CLOSE_BOOK_OR_SIDE_INVALID")
    with localcontext() as ctx:
        ctx.prec = 96
        remaining, total = size, Decimal(0)
        for price, count in levels["bids" if position_side == "long" else "asks"]:
            take = min(count, remaining)
            remaining -= take
            total += take * price
        if remaining:
            raise ValueError("SESSION_CLOSE_DEPTH_INSUFFICIENT")
        fee_usdc = total * binding.applied_input.instrument.contract_multiplier * rate
        result = dict(
            schema="current_native_position_close_quote.v1",
            reservation_id=reservation_id,
            native_id=native,
            position_side=position_side,
            quantity=quantity,
            book_vwap=str(total / size),
            charged_rate=str(rate),
            estimated_fee_usdc=str(fee_usdc),
            settlement_currency="USDC",
            native_price_currency="USD",
            acquisition_id=acquisition_id,
            sources_digest=digest({k: v.body_sha256 for k, v in sources.items()}),
            evaluated_at_utc=now_utc,
            actual_payment=False,
            funding_included=False,
        )
    return {**result, "digest": digest(result)}
