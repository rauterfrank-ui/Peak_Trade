"""Public OKX inputs and quantity-bound liquidity for isolated XPERP Paper slots."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from decimal import Decimal
from time import time

from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperBookV1,
    PaperLiquidityPolicyV1,
    PaperLiquiditySnapshotV1,
    _adv,
    _decimal,
    _fresh,
    _one,
    _timestamp,
    collect_public_paper_sources_v1,
    load_paper_liquidity_policy_v1 as load_paper_liquidity_policy_v1,
    validate_public_paper_sources_v1,
)

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
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import ContractMetadataV1


@dataclass(frozen=True)
class XperpPaperSlotV1:
    lane_id: str
    base_currency: str
    expiry_code: str

    @property
    def index_id(self):
        return f"{self.base_currency}-USD"

    @property
    def family(self):
        return f"{self.index_id}_UM_XPERP"

    @property
    def native_id(self):
        return f"{self.family}-{self.expiry_code}"

    @property
    def instrument_id(self):
        return f"okx_eea:linear_dated_future:{self.base_currency}:USD:USD:{self.native_id.lower()}"


ZKP_PAPER_SLOT = XperpPaperSlotV1("LANE_1", "ZKP", "310905")
UP_PAPER_SLOT = XperpPaperSlotV1("LANE_5", "UP", "310919")
UP_PAPER_ARCHIVED_SLOT2 = XperpPaperSlotV1("LANE_2", "UP", "310919")
IRYS_PAPER_SLOT = XperpPaperSlotV1("LANE_4", "IRYS", "310530")
NATIVE_ID = ZKP_PAPER_SLOT.native_id
INSTRUMENT_ID = ZKP_PAPER_SLOT.instrument_id
FAMILY = ZKP_PAPER_SLOT.family
INDEX_ID = ZKP_PAPER_SLOT.index_id
PAPER_FEE_RATE = Decimal("0.0005")
PAPER_ALLOCATION_USDC = Decimal("25")
_TOP = classify_live_best_bid_ask_freshness_v1
_MARK = classify_live_mark_price_freshness_v1


@dataclass(frozen=True)
class ZkpPaperFundingSettlementV1:
    event_unix: float
    realized_rate: Decimal
    preceding_mark_close_usd: Decimal


def _settled_funding(payload, mark_candles, *, native_id, previous, acquired_unix):
    rows = payload["data"]
    if not isinstance(rows, list):
        raise ValueError("ZKP_PAPER_FUNDING_HISTORY_INVALID")
    candles = {}
    for row in mark_candles["data"]:
        if row[5] == "1":
            candles.setdefault(row[0], []).append(row[4])
    seen, times, settlements = set(), [], []
    for row in rows:
        stamp = _timestamp(row, "fundingTime")
        event = stamp / 1000
        if row["instId"] != native_id or row["instType"] != "FUTURES" or stamp in seen:
            raise ValueError("ZKP_PAPER_FUNDING_HISTORY_IDENTITY_INVALID")
        seen.add(stamp)
        if event > previous:
            continue
        times.append(event)
        raw_rate = row["realizedRate"]
        if raw_rate == "":
            continue
        if not isinstance(raw_rate, str) or event > acquired_unix:
            raise ValueError("ZKP_PAPER_FUNDING_HISTORY_UNAVAILABLE_AT_CAPTURE")
        rate = _decimal(raw_rate)
        # The public rate history does not include OKX's account assessment mark.
        # Model the boundary mark with the exact preceding finalized minute close.
        prices = candles.get(str(stamp - 60_000), [])
        if stamp % 60_000 == 0 and len(prices) == 1:
            settlements.append(
                ZkpPaperFundingSettlementV1(event, rate, _decimal(prices[0], positive=True))
            )
    return tuple(sorted(times)), tuple(sorted(settlements, key=lambda row: row.event_unix))


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
    previous_funding_unix: float
    funding_history_times: tuple[float, ...]
    funding_settlements: tuple[ZkpPaperFundingSettlementV1, ...]
    slot: XperpPaperSlotV1 = ZKP_PAPER_SLOT
    source_observations: dict | None = None
    original_bodies: dict[str, bytes] | None = None

    def _liquidity_snapshot(self) -> PaperLiquiditySnapshotV1:
        return PaperLiquiditySnapshotV1(
            minimum_contracts=self.native_contract.min_qty,
            maximum_contracts=self.maximum_contracts,
            lot_size=self.lot_size,
            tick_size=self.native_contract.tick_size,
            contract_size=self.native_contract.contract_size,
            mark=self.mark,
            book=self.book,
            book_event_unix=self.book_event_unix,
            adv_quote=self.adv_usd,
            policy=self.policy,
            source_hashes=self.source_hashes,
        )

    def assess_quantity_v1(self, *, side: str, quantity: Decimal) -> dict:
        return _zkp_usd_liquidity_v1(
            self._liquidity_snapshot().assess_quantity_v1(side=side, quantity=quantity)
        )

    def assess_opening_liquidity_v1(self, *, side: str) -> dict:
        return _zkp_usd_liquidity_v1(
            self._liquidity_snapshot().assess_opening_liquidity_v1(side=side)
        )


def _zkp_usd_liquidity_v1(check):
    for field in ("open_price", "close_price", "adv"):
        check[f"{field}_usd"] = check.pop(f"{field}_quote")
    return check


def zkp_public_queries_v1(days, *, slot=ZKP_PAPER_SLOT):
    exact = {"instType": "FUTURES", "instId": slot.native_id}
    return {
        "instrument": ("/api/v5/public/instruments", exact),
        "tiers": (
            "/api/v5/public/position-tiers",
            {"instType": "FUTURES", "tdMode": "cross", "instFamily": slot.family},
        ),
        "adv": (
            "/api/v5/market/candles",
            {"instId": slot.native_id, "bar": "1Dutc", "limit": str(days + 1)},
        ),
        "funding": ("/api/v5/public/funding-rate", {"instId": slot.native_id}),
        "funding-history": (
            "/api/v5/public/funding-rate-history",
            {"instId": slot.native_id, "limit": "20"},
        ),
        "trade-candles": (
            "/api/v5/market/candles",
            {"instId": slot.native_id, "bar": "1m", "limit": "105"},
        ),
        "mark-candles": (
            "/api/v5/market/history-mark-price-candles",
            mark_history_get_query_v1(venue_native_id=slot.native_id),
        ),
        "open-interest": ("/api/v5/public/open-interest", exact),
        "ticker": ("/api/v5/market/ticker", {"instId": slot.native_id}),
        "usdc-index": ("/api/v5/market/index-tickers", {"instId": "USDC-USD"}),
        "index": ("/api/v5/market/index-tickers", {"instId": slot.index_id}),
        "book": ("/api/v5/market/books", {"instId": slot.native_id, "sz": "50"}),
        "mark": ("/api/v5/public/mark-price", exact),
    }


def collect_zkp_paper_market_v1(
    transport, *, policy, capture_id, retain=None, clock=time, slot=ZKP_PAPER_SLOT
):
    original_bodies = {}

    def retained(label, result, raw):
        original_bodies[label] = raw
        if retain is not None:
            retain(label, result, raw)

    observations = collect_public_paper_sources_v1(
        transport,
        queries=zkp_public_queries_v1(policy.adv_days, slot=slot),
        capture_id=capture_id,
        retain=retained,
    )
    return bind_zkp_paper_market_v1(
        observations,
        policy=policy,
        observed_unix=clock(),
        slot=slot,
        original_bodies=original_bodies,
    )


def bind_zkp_paper_market_v1(
    observations, *, policy, observed_unix, slot=ZKP_PAPER_SLOT, original_bodies=None
):
    payloads, acquired, hashes = validate_public_paper_sources_v1(
        observations,
        queries=zkp_public_queries_v1(policy.adv_days, slot=slot),
        observed_unix=observed_unix,
    )

    inst = _one(payloads["instrument"], slot.native_id)
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
        slot.family,
        slot.index_id,
        "linear",
        slot.base_currency,
        "USD",
        "live",
    ):
        raise ValueError("ZKP_PAPER_CONTRACT_SCOPE_INVALID")
    (tier,) = [
        row
        for row in payloads["tiers"]["data"]
        if row["instFamily"] == slot.family and row["tier"] == "1"
    ]
    size = _decimal(inst["ctVal"], positive=True) * _decimal(inst["ctMult"], positive=True)
    lot, minimum, tick = (
        _decimal(inst[key], positive=True) for key in ("lotSz", "minSz", "tickSz")
    )
    if lot != minimum:
        raise ValueError("ZKP_PAPER_ACCOUNTING_LOT_MISMATCH")
    contract = ContractMetadataV1(
        slot.native_id,
        size,
        tick,
        minimum,
        "USD",
        _decimal(tier["imr"], positive=True),
        _decimal(tier["mmr"], positive=True),
        _decimal(tier["maxLever"], positive=True),
    )
    maximum = min(_decimal(inst["maxMktSz"], positive=True), _decimal(tier["maxSz"], positive=True))

    funding = _one(payloads["funding"], slot.native_id)
    floor, rate, cap = (
        _decimal(funding[key]) for key in ("minFundingRate", "fundingRate", "maxFundingRate")
    )
    funding_time = _timestamp(funding, "fundingTime") / 1000
    previous_funding = _timestamp(funding, "prevFundingTime") / 1000
    if (
        funding["instType"] != "FUTURES"
        or funding["method"] != "current_period"
        or not floor <= min(rate, Decimal(0)) <= max(rate, Decimal(0)) <= cap
        or not previous_funding < funding_time
        or not previous_funding <= observed_unix < funding_time
        or _timestamp(funding, "nextFundingTime") / 1000 <= funding_time
        or not 0 <= acquired["funding"] - _timestamp(funding) / 1000 <= 180
    ):
        raise ValueError("ZKP_PAPER_FUNDING_CLOCK_OR_BOUNDS_INVALID")

    book = _one(payloads["book"])
    if book.get("instId", slot.native_id) != slot.native_id:
        raise ValueError("ZKP_PAPER_BOOK_IDENTITY_MISMATCH")
    _fresh(book, acquired["book"], observed_unix, _TOP)
    depth = PaperBookV1.from_okx_v1(book, tick=tick, lot=lot)
    for name, native in (
        ("index", slot.index_id),
        ("usdc-index", "USDC-USD"),
        ("ticker", slot.native_id),
        ("open-interest", slot.native_id),
    ):
        row = _one(payloads[name], native)
        _fresh(row, acquired[name], observed_unix, _MARK)
    fx = _decimal(_one(payloads["usdc-index"])["idxPx"], positive=True)
    mark_payload = payloads["mark"]
    mark = _decimal(_one(mark_payload, slot.native_id)["markPx"], positive=True)
    prices = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=mark_payload,
        venue_native_id=slot.native_id,
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
        canonical_instrument_id=slot.instrument_id,
        venue_instrument_id=slot.native_id,
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
    funding_history_times, funding_settlements = _settled_funding(
        payloads["funding-history"],
        mark_candles,
        native_id=slot.native_id,
        previous=previous_funding,
        acquired_unix=acquired["funding-history"],
    )
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
        previous_funding,
        funding_history_times,
        funding_settlements,
        slot,
        deepcopy(dict(observations)),
        None if original_bodies is None else dict(original_bodies),
    )
