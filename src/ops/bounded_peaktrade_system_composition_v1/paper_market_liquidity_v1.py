"""Public market liquidity measured for the instrument selected for Paper."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from hashlib import sha256
from math import isfinite
from pathlib import Path
from time import time
from urllib.parse import urlencode

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
    public_instrument_ref_for_binding_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

_DAY_MS = 86_400_000


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
class PaperLiquiditySnapshotV1:
    minimum_contracts: Decimal
    maximum_contracts: Decimal
    lot_size: Decimal
    tick_size: Decimal
    contract_size: Decimal
    mark: Decimal
    book: PaperBookV1
    book_event_unix: float
    adv_quote: Decimal
    policy: PaperLiquidityPolicyV1
    source_hashes: dict[str, str]

    def assess_quantity_v1(self, *, side: str, quantity: Decimal) -> dict:
        tick = self.tick_size
        if (
            side not in {"BUY", "SELL"}
            or not quantity.is_finite()
            or not self.minimum_contracts <= quantity <= self.maximum_contracts
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
        base = quantity * self.contract_size
        participation = base * max(self.mark, open_price or self.mark) / self.adv_quote
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
            "open_price_quote": str(open_price) if open_price is not None else None,
            "close_price_quote": str(close_price) if close_price is not None else None,
            "spread_bps": str(spread),
            "slippage_bps": str(slippage) if slippage is not None else None,
            "adv_quote": str(self.adv_quote),
            "adv_days": self.policy.adv_days,
            "adv_participation": str(participation),
            "book_event_unix": self.book_event_unix,
            "book_sha256": self.source_hashes["book"],
            "adv_sha256": self.source_hashes["adv"],
        }

    def assess_opening_liquidity_v1(self, *, side: str) -> dict:
        minimum = self.minimum_contracts
        check = self.assess_quantity_v1(side=side, quantity=minimum)
        quantity_cap = None
        if check["risk_admitted"]:
            # Bound ADV using an upper price for all admissible opening fills.
            # Inside that bound, only adverse VWAP can worsen as size increases.
            adv_price = (
                self.mark * (1 + self.policy.slippage_limit_bps / 10000)
                if side == "BUY"
                else max(self.mark, self.book.bids[0][0])
            )
            adv_cap = (
                self.adv_quote
                * self.policy.adv_participation_limit
                / (adv_price * self.contract_size)
            )
            lot = self.lot_size
            lower = int(minimum // lot)
            upper = int(
                min(
                    self.maximum_contracts,
                    Decimal(check["bid_contracts"]),
                    Decimal(check["ask_contracts"]),
                    max(minimum, adv_cap),
                )
                // lot
            )
            while lower < upper:
                units = (lower + upper + 1) // 2
                if self.assess_quantity_v1(side=side, quantity=units * lot)["risk_admitted"]:
                    lower = units
                else:
                    upper = units - 1
            quantity_cap = str(lower * lot)
        return {
            **check,
            "spread_limit_bps": str(self.policy.spread_limit_bps),
            "slippage_limit_bps": str(self.policy.slippage_limit_bps),
            "adv_participation_limit": str(self.policy.adv_participation_limit),
            "quantity_cap_contracts": quantity_cap,
        }


@contextmanager
def retain_public_paper_sources_v1(output):
    """Retain original receipts even when collection or admission fails closed."""
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
        durable_bytes_v1,
        immutable_json_v1,
    )

    records = {}

    def retain(name, result, body):
        if output is None:
            return
        path = Path(output) / f"{name}.json"
        durable_bytes_v1(path, body)
        record = asdict(result)
        del record["payload"]
        records[name] = {"file": str(path), **record}

    try:
        yield retain
    finally:
        if output is not None:
            immutable_json_v1(Path(output) / "receipts.json", records)


def collect_public_paper_sources_v1(transport, *, queries, capture_id, retain=None):
    observations = {}
    for label, (path, query) in queries.items():
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
    return observations


def validate_public_paper_sources_v1(observations, *, queries, observed_unix):
    if not isfinite(observed_unix) or observed_unix <= 0 or observations.keys() != queries.keys():
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
    return payloads, acquired, hashes


@dataclass(frozen=True)
class BoundPaperLiquidityV1:
    bound: BoundInstrumentV1
    quote_asset: str
    observed_unix: float
    mark_event_unix: float
    snapshot: PaperLiquiditySnapshotV1

    def is_fresh_v1(self, now: float) -> bool:
        return (
            self.observed_unix <= now
            and classify_live_mark_price_freshness_v1(
                age_seconds=now - self.mark_event_unix
            ).publishable
            and classify_live_best_bid_ask_freshness_v1(
                age_seconds=now - self.snapshot.book_event_unix
            ).publishable
        )

    def to_preflight_v1(self) -> dict:
        return {
            "instrument_id": self.bound.instrument_id,
            "native_instrument_id": self.bound.venue_native_id,
            "selection_id": self.bound.selection_id,
            "selection_integrity_digest": self.bound.selection_integrity_digest,
            "quote_asset": self.quote_asset,
            "mark_price_quote": str(self.snapshot.mark),
            "mark_event_unix": self.mark_event_unix,
            "observed_unix": self.observed_unix,
            "source_hashes": self.snapshot.source_hashes,
            "liquidity_at_minimum_quantity": {
                side: self.snapshot.assess_opening_liquidity_v1(side=side)
                for side in ("BUY", "SELL")
            },
        }


@dataclass(frozen=True)
class PaperEntryLiquiditySourceV1:
    policy: PaperLiquidityPolicyV1
    transport_factory: Callable[[], FullCoreFreshPretradeGetTransportV1]

    def observe_v1(self, *, bound, capture_id, clock) -> BoundPaperLiquidityV1:
        return collect_bound_paper_liquidity_v1(
            self.transport_factory(),
            bound=bound,
            policy=self.policy,
            capture_id=capture_id,
            clock=clock,
        )


def collect_bound_paper_liquidity_v1(
    transport,
    *,
    bound: BoundInstrumentV1,
    policy: PaperLiquidityPolicyV1,
    capture_id: str,
    retain=None,
    clock=time,
) -> BoundPaperLiquidityV1:
    """Measure both sides of the selected OKX linear future with fresh public GETs."""
    ref = public_instrument_ref_for_binding_v1(bound)
    native = ref.venue_native_id
    _, _, base, quote, settlement, _ = ref.canonical_instrument_id.split(":")
    exact = {"instType": ref.instrument_type, "instId": native}
    queries = {
        "instrument": ("/api/v5/public/instruments", exact),
        "adv": (
            "/api/v5/market/candles",
            {"instId": native, "bar": "1Dutc", "limit": str(policy.adv_days + 1)},
        ),
        "book": ("/api/v5/market/books", {"instId": native, "sz": "50"}),
        "mark": ("/api/v5/public/mark-price", exact),
    }
    capture = f"{capture_id}:{ref.mapping_provenance_digest}"
    observations = collect_public_paper_sources_v1(
        transport, queries=queries, capture_id=capture, retain=retain
    )
    if any(row.pretrade_decision_id != f"{capture}:{name}" for name, row in observations.items()):
        raise ValueError("PAPER_LIQUIDITY_CAPTURE_BINDING_MISMATCH")
    observed = clock()
    payloads, acquired, hashes = validate_public_paper_sources_v1(
        observations, queries=queries, observed_unix=observed
    )
    instrument = _one(payloads["instrument"], native)
    if (
        instrument["instType"],
        instrument["ctType"],
        instrument["ctValCcy"],
        instrument["settleCcy"],
        instrument["state"],
    ) != (ref.instrument_type, "linear", base, settlement, "live"):
        raise ValueError("PAPER_LIQUIDITY_LINEAR_CONTRACT_METADATA_MISMATCH")
    lot, minimum, maximum, tick = (
        _decimal(instrument[key], positive=True) for key in ("lotSz", "minSz", "maxMktSz", "tickSz")
    )
    if minimum % lot or maximum < minimum:
        raise ValueError("PAPER_LIQUIDITY_INVALID_CONTRACT_GRID")
    size = _decimal(instrument["ctVal"], positive=True) * _decimal(
        instrument["ctMult"], positive=True
    )
    mark = _one(payloads["mark"], native)
    if mark.get("instType", ref.instrument_type) != ref.instrument_type:
        raise ValueError("PAPER_LIQUIDITY_MARK_CONTRACT_TYPE_MISMATCH")
    book = _one(payloads["book"])
    if book.get("instId", native) != native:
        raise ValueError("PAPER_LIQUIDITY_BOOK_INSTRUMENT_MISMATCH")
    _fresh(mark, acquired["mark"], observed, classify_live_mark_price_freshness_v1)
    _fresh(book, acquired["book"], observed, classify_live_best_bid_ask_freshness_v1)
    snapshot = PaperLiquiditySnapshotV1(
        minimum_contracts=minimum,
        maximum_contracts=maximum,
        lot_size=lot,
        tick_size=tick,
        contract_size=size,
        mark=_decimal(mark["markPx"], positive=True),
        book=PaperBookV1.from_okx_v1(book, tick=tick, lot=lot),
        book_event_unix=_timestamp(book) / 1000,
        adv_quote=_adv(payloads["adv"], now=observed, days=policy.adv_days, contract_size=size),
        policy=policy,
        source_hashes=hashes,
    )
    return BoundPaperLiquidityV1(bound, quote, observed, _timestamp(mark) / 1000, snapshot)
