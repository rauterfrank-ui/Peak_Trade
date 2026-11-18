"""Public OKX inputs and quantity-bound liquidity for the ZKP Paper opening."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from hashlib import sha256
import math
from pathlib import Path
from time import time
from urllib.parse import urlencode

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from src.ops.full_core_live_path_composition_root_v1.current_productive_candidate_input_gate_v1 import (
    finalized_candidate_candle_history_rejection_codes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    extract_full_core_g17_pt1m_mark_ingest_fields_v1,
    mark_history_get_query_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_finalized_candle_closes_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import ContractMetadataV1

NATIVE_ID = "ZKP-USD_UM_XPERP-310905"
INSTRUMENT_ID = "okx_eea:linear_dated_future:ZKP:USD:USD:zkp-usd_um_xperp-310905"
FAMILY = "ZKP-USD_UM_XPERP"
INDEX_ID = "ZKP-USD"
PAPER_FEE_RATE = Decimal("0.0005")
PAPER_ALLOCATION_USDC = Decimal("25")
_DAY_MS = 86_400_000
_TOP = classify_live_best_bid_ask_freshness_v1
_MARK = classify_live_mark_price_freshness_v1


@dataclass(frozen=True)
class PaperLiquidityPolicyV1:
    spread_limit_bps: Decimal
    slippage_limit_bps: Decimal
    adv_participation_limit: Decimal
    adv_days: int


def load_paper_liquidity_policy_v1(repo: Path) -> PaperLiquidityPolicyV1:
    with (repo / "config/risk_liquidity_gate_paper.toml").open("rb") as source:
        paper = tomllib.load(source)["risk"]["liquidity_gate"]["paper"]
    with (repo / "config/risk/slippage.toml").open("rb") as source:
        slippage = tomllib.load(source)["slippage"]
    if paper["enabled"] is not True:
        raise ValueError("ZKP_PAPER_LIQUIDITY_MUST_BE_ENABLED")
    days = paper["adv_lookback_days"]
    participation = _decimal(paper["max_order_size_pct_adv"], positive=True)
    if type(days) is not int or not 1 <= days <= 299 or participation > 1:
        raise ValueError("ZKP_PAPER_LIQUIDITY_POLICY_INVALID")
    return PaperLiquidityPolicyV1(
        _decimal(paper["max_spread_bps"], positive=True),
        _decimal(slippage["cap_bps"], positive=True),
        participation,
        days,
    )


def _decimal(value, *, positive=False):
    number = Decimal(str(value))
    if not number.is_finite() or positive and number <= 0:
        raise ValueError("ZKP_PAPER_NUMERIC_INPUT_INVALID")
    return number


def _timestamp(row, name="ts"):
    raw = row[name]
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal() or int(raw) <= 0:
        raise ValueError("ZKP_PAPER_EVENT_TIMESTAMP_INVALID")
    return int(raw)


def _fresh(row, acquired, now, classify):
    event = _timestamp(row) / 1000
    if not all(
        classify(age_seconds=age).publishable
        for age in (acquired - event, now - acquired, now - event)
    ):
        raise ValueError("ZKP_PAPER_SOURCE_STALE_OR_FUTURE")


def _one(payload, native=None):
    (row,) = payload["data"]
    if native is not None and row.get("instId") != native:
        raise ValueError("ZKP_PAPER_INSTRUMENT_MISMATCH")
    return row


@dataclass(frozen=True)
class PaperBookV1:
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]

    @classmethod
    def from_okx_v1(cls, book, *, tick, lot):
        def parse(side):
            levels = tuple(
                (_decimal(row[0], positive=True), _decimal(row[1], positive=True))
                for row in book[side]
            )
            prices = tuple(price for price, _ in levels)
            if (
                not levels
                or any(price % tick or count % lot for price, count in levels)
                or len(set(prices)) != len(prices)
                or prices != tuple(sorted(prices, reverse=side == "bids"))
            ):
                raise ValueError("ZKP_PAPER_BOOK_DEPTH_OR_GRID_INVALID")
            return levels

        bids, asks = parse("bids"), parse("asks")
        if bids[0][0] >= asks[0][0]:
            raise ValueError("ZKP_PAPER_BOOK_LOCKED_OR_CROSSED")
        return cls(bids, asks)

    def executable_price_v1(self, side, quantity, tick):
        levels = self.asks if side == "BUY" else self.bids
        size_left, spent = quantity, Decimal(0)
        for price, available in levels:
            take = min(size_left, available)
            spent += price * take
            size_left -= take
            if size_left == 0:
                vwap = spent / quantity
                rounding = ROUND_CEILING if side == "BUY" else ROUND_FLOOR
                return (vwap / tick).to_integral_value(rounding=rounding) * tick
        return None


def _adv(payload, *, now, days, contract_size):
    midnight = int(now * 1000) // _DAY_MS * _DAY_MS
    required = set(range(midnight - days * _DAY_MS, midnight, _DAY_MS))
    quote_volumes = {}
    for row in payload["data"]:
        if len(row) != 9 or row[8] not in {"0", "1"}:
            raise ValueError("ZKP_PAPER_ADV_CANDLE_INVALID")
        timestamp = _timestamp({"ts": row[0]})
        if row[8] != "1" or timestamp not in required:
            continue
        contracts, base, quote = (_decimal(value) for value in row[5:8])
        if (
            timestamp in quote_volumes
            or min(contracts, base, quote) < 0
            or base != contracts * contract_size
            or (quote > 0) != (base > 0)
        ):
            raise ValueError("ZKP_PAPER_ADV_SOURCE_UNITS_OR_IDENTITY_INVALID")
        quote_volumes[timestamp] = quote
    if set(quote_volumes) != required:
        raise ValueError("ZKP_PAPER_ADV_FINALIZED_DAYS_MISSING")
    return _decimal(sum(quote_volumes.values()) / days, positive=True)


@dataclass(frozen=True)
class ZkpPaperMarketV1:
    observed_unix: float
    market_event_unix: float
    native_contract: ContractMetadataV1
    maximum_contracts: Decimal
    lot_size: Decimal
    candles_payload: dict
    mark_payload: dict
    index_payload: dict
    mark_acquired_at: str
    g17_payload: dict
    g17_acquired_at: str
    g17_c1_open_unix: float
    g17_window_digest: str
    mark: Decimal
    book: PaperBookV1
    book_event_unix: float
    volume_contracts: Decimal
    oi_contracts: Decimal
    funding_rate: Decimal
    funding_floor: Decimal
    funding_cap: Decimal
    funding_time_unix: float
    usd_per_usdc: Decimal
    adv_usd: Decimal
    policy: PaperLiquidityPolicyV1
    source_hashes: dict[str, str]

    def assess_quantity_v1(self, *, side: str, quantity: Decimal) -> dict:
        tick = self.native_contract.tick_size
        if (
            side not in {"BUY", "SELL"}
            or not quantity.is_finite()
            or not self.native_contract.min_qty <= quantity <= self.maximum_contracts
            or quantity % self.lot_size
        ):
            raise ValueError("ZKP_PAPER_LIQUIDITY_QUANTITY_INVALID")
        opposite = "SELL" if side == "BUY" else "BUY"
        open_price = self.book.executable_price_v1(side, quantity, tick)
        close_price = self.book.executable_price_v1(opposite, quantity, tick)
        bid, ask = self.book.bids[0][0], self.book.asks[0][0]
        spread = (ask - bid) / ((bid + ask) / 2) * 10000
        direction = 1 if side == "BUY" else -1
        slippage = (
            max(Decimal(0), direction * (open_price - self.mark) / self.mark * 10000)
            if open_price is not None
            else None
        )
        base = quantity * self.native_contract.contract_size
        participation = base * max(self.mark, open_price or self.mark) / self.adv_usd
        reasons = []
        if open_price is None or close_price is None:
            reasons.append("ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT")
        if spread > self.policy.spread_limit_bps:
            reasons.append("ZKP_PAPER_SPREAD_LIMIT")
        if slippage is not None and slippage > self.policy.slippage_limit_bps:
            reasons.append("ZKP_PAPER_SLIPPAGE_LIMIT")
        if participation > self.policy.adv_participation_limit:
            reasons.append("ZKP_PAPER_ADV_PARTICIPATION_LIMIT")
        return {
            "risk_admitted": not reasons,
            "reason_codes": reasons,
            "side": side,
            "quantity_contracts": str(quantity),
            "bid_contracts": str(sum(q for _, q in self.book.bids)),
            "ask_contracts": str(sum(q for _, q in self.book.asks)),
            "open_price_usd": str(open_price) if open_price is not None else None,
            "close_price_usd": str(close_price) if close_price is not None else None,
            "spread_bps": str(spread),
            "slippage_bps": str(slippage) if slippage is not None else None,
            "adv_usd": str(self.adv_usd),
            "adv_days": self.policy.adv_days,
            "adv_participation": str(participation),
            "book_event_unix": self.book_event_unix,
            "book_sha256": self.source_hashes["book"],
            "adv_sha256": self.source_hashes["adv"],
        }


def zkp_public_queries_v1(days):
    exact = {"instType": "FUTURES", "instId": NATIVE_ID}
    return {
        "instrument": ("/api/v5/public/instruments", exact),
        "tiers": (
            "/api/v5/public/position-tiers",
            {"instType": "FUTURES", "tdMode": "cross", "instFamily": FAMILY},
        ),
        "adv": (
            "/api/v5/market/candles",
            {"instId": NATIVE_ID, "bar": "1Dutc", "limit": str(days + 1)},
        ),
        "funding": ("/api/v5/public/funding-rate", {"instId": NATIVE_ID}),
        "trade-candles": (
            "/api/v5/market/candles",
            {"instId": NATIVE_ID, "bar": "1m", "limit": "105"},
        ),
        "mark-candles": (
            "/api/v5/market/history-mark-price-candles",
            mark_history_get_query_v1(venue_native_id=NATIVE_ID),
        ),
        "open-interest": ("/api/v5/public/open-interest", exact),
        "ticker": ("/api/v5/market/ticker", {"instId": NATIVE_ID}),
        "usdc-index": ("/api/v5/market/index-tickers", {"instId": "USDC-USD"}),
        "index": ("/api/v5/market/index-tickers", {"instId": INDEX_ID}),
        "book": ("/api/v5/market/books", {"instId": NATIVE_ID, "sz": "50"}),
        "mark": ("/api/v5/public/mark-price", exact),
    }


def collect_zkp_paper_market_v1(transport, *, policy, capture_id, retain=None, clock=time):
    observations = {}
    for label, (path, query) in zkp_public_queries_v1(policy.adv_days).items():
        endpoint = f"{path}?{urlencode(query)}"

        def archive(*, result, body, label=label):
            if sha256(body).hexdigest() != result.body_sha256:
                raise ValueError("ZKP_PAPER_PUBLIC_BODY_DIGEST_MISMATCH")
            if retain is not None:
                retain(label, result, body)

        transport.raw_response_sink_v1 = archive
        observations[label] = transport.get(
            endpoint=endpoint,
            auth_required=False,
            pretrade_decision_id=f"{capture_id}:{label}",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
    return bind_zkp_paper_market_v1(observations, policy=policy, observed_unix=clock())


def bind_zkp_paper_market_v1(observations, *, policy, observed_unix):
    queries = zkp_public_queries_v1(policy.adv_days)
    if (
        not math.isfinite(observed_unix)
        or observed_unix <= 0
        or observations.keys() != queries.keys()
    ):
        raise ValueError("ZKP_PAPER_COMPLETE_PUBLIC_INPUTS_REQUIRED")
    payloads, acquired, hashes = {}, {}, {}
    for name, (path, query) in queries.items():
        receipt = observations[name]
        if (
            receipt.endpoint != f"{path}?{urlencode(query)}"
            or receipt.get_performed is not True
            or receipt.method != "GET"
            or receipt.http_status != 200
            or receipt.error_class
            or receipt.auth_header_sent is not False
            or receipt.historical_reuse is not False
            or receipt.venue_live_contact is not True
            or len(receipt.body_sha256) != 64
            or not isinstance(receipt.payload, dict)
            or receipt.payload.get("code") != "0"
        ):
            raise ValueError(f"ZKP_PAPER_PUBLIC_GET_UNPROVEN:{name}")
        moment = datetime.fromisoformat(receipt.acquired_at_utc.replace("Z", "+00:00"))
        if moment.utcoffset() is None or not 0 <= observed_unix - moment.timestamp() <= 15:
            raise ValueError(f"ZKP_PAPER_CAPTURE_OUTSIDE_OBSERVATION:{name}")
        payloads[name] = receipt.payload
        acquired[name] = moment.timestamp()
        hashes[name] = receipt.body_sha256

    inst = _one(payloads["instrument"], NATIVE_ID)
    if (
        inst["instType"],
        inst["instFamily"],
        inst["uly"],
        inst["ctType"],
        inst["ctValCcy"],
        inst["settleCcy"],
        inst["state"],
    ) != (
        "FUTURES",
        FAMILY,
        INDEX_ID,
        "linear",
        "ZKP",
        "USD",
        "live",
    ):
        raise ValueError("ZKP_PAPER_CONTRACT_SCOPE_INVALID")
    (tier,) = [
        row
        for row in payloads["tiers"]["data"]
        if row["instFamily"] == FAMILY and row["tier"] == "1"
    ]
    size = _decimal(inst["ctVal"], positive=True) * _decimal(inst["ctMult"], positive=True)
    lot, minimum, tick = (
        _decimal(inst[key], positive=True) for key in ("lotSz", "minSz", "tickSz")
    )
    if lot != minimum:
        raise ValueError("ZKP_PAPER_ACCOUNTING_LOT_MISMATCH")
    contract = ContractMetadataV1(
        NATIVE_ID,
        size,
        tick,
        minimum,
        "USD",
        _decimal(tier["imr"], positive=True),
        _decimal(tier["mmr"], positive=True),
        _decimal(tier["maxLever"], positive=True),
    )
    maximum = min(_decimal(inst["maxMktSz"], positive=True), _decimal(tier["maxSz"], positive=True))

    funding = _one(payloads["funding"], NATIVE_ID)
    floor, rate, cap = (
        _decimal(funding[key]) for key in ("minFundingRate", "fundingRate", "maxFundingRate")
    )
    funding_time = _timestamp(funding, "fundingTime") / 1000
    if (
        funding["instType"] != "FUTURES"
        or funding["method"] != "current_period"
        or not floor <= min(rate, Decimal(0)) <= max(rate, Decimal(0)) <= cap
        or not _timestamp(funding, "prevFundingTime") / 1000 <= observed_unix < funding_time
        or _timestamp(funding, "nextFundingTime") / 1000 <= funding_time
        or not 0 <= acquired["funding"] - _timestamp(funding) / 1000 <= 180
    ):
        raise ValueError("ZKP_PAPER_FUNDING_CLOCK_OR_BOUNDS_INVALID")

    book = _one(payloads["book"])
    if book.get("instId", NATIVE_ID) != NATIVE_ID:
        raise ValueError("ZKP_PAPER_BOOK_IDENTITY_MISMATCH")
    _fresh(book, acquired["book"], observed_unix, _TOP)
    depth = PaperBookV1.from_okx_v1(book, tick=tick, lot=lot)
    for name, native in (
        ("index", INDEX_ID),
        ("usdc-index", "USDC-USD"),
        ("ticker", NATIVE_ID),
        ("open-interest", NATIVE_ID),
    ):
        row = _one(payloads[name], native)
        _fresh(row, acquired[name], observed_unix, _MARK)
    fx = _decimal(_one(payloads["usdc-index"])["idxPx"], positive=True)
    mark_payload = payloads["mark"]
    mark = _decimal(_one(mark_payload, NATIVE_ID)["markPx"], positive=True)
    prices = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=mark_payload,
        venue_native_id=NATIVE_ID,
        index_from_index_tickers=payloads["index"],
        mark_acquired_at_utc=observations["mark"].acquired_at_utc,
    )
    mark_event = prices.require_current_mark_clock_v1(observed_unix=observed_unix)
    interest = _one(payloads["open-interest"])
    ticker = _one(payloads["ticker"])
    oi = _decimal(interest["oi"], positive=True)
    volume = _decimal(ticker["vol24h"], positive=True)
    if oi * size != _decimal(interest["oiCcy"]) or volume * size != _decimal(ticker["volCcy24h"]):
        raise ValueError("ZKP_PAPER_CONTRACT_VOLUME_UNITS_MISMATCH")

    candles = payloads["trade-candles"]
    if finalized_candidate_candle_history_rejection_codes_v1(candles):
        raise ValueError("ZKP_PAPER_FINALIZED_TRADE_C1_REQUIRED")
    _, c1 = extract_finalized_candle_closes_v1(candles)
    mark_candles = payloads["mark-candles"]
    g17_at = observations["mark-candles"].acquired_at_utc
    g17 = extract_full_core_g17_pt1m_mark_ingest_fields_v1(
        mark_candles,
        venue="okx_eea",
        canonical_instrument_id=INSTRUMENT_ID,
        venue_instrument_id=NATIVE_ID,
        receive_or_capture_timestamp=g17_at,
    )
    if (
        c1 is None
        or c1 % 60
        or not 0 <= mark_event - (c1 + 60) < 60
        or c1 + 60 > acquired["trade-candles"]
        or c1 + 60 > acquired["mark-candles"]
        or g17.failure_codes
        or g17.samples[-1].event_time_unix_seconds != c1
    ):
        raise ValueError("ZKP_PAPER_G17_AND_C1_CLOCK_MISMATCH")
    return ZkpPaperMarketV1(
        observed_unix,
        mark_event,
        contract,
        maximum,
        lot,
        candles,
        mark_payload,
        payloads["index"],
        observations["mark"].acquired_at_utc,
        mark_candles,
        g17_at,
        c1,
        canonical_digest_v1([(row.event_time_unix_seconds, row.mark_price) for row in g17.samples]),
        mark,
        depth,
        _timestamp(book) / 1000,
        volume,
        oi,
        rate,
        floor,
        cap,
        funding_time,
        fx,
        _adv(payloads["adv"], now=observed_unix, days=policy.adv_days, contract_size=size),
        policy,
        hashes,
    )
