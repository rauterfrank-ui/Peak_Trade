"""Original EEA public facts for a mark-based no-fill I17 swap observation."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from decimal import DecimalException
from pathlib import Path
from src.ops.bounded_peaktrade_system_composition_v1.paper_market_liquidity_v1 import (
    PaperBookV1,
    _decimal,
    _fresh,
    _one,
    _timestamp,
)
from src.ops.peak_trade_public_market_data_runtime_v1.freshness_v1 import (
    classify_live_best_bid_ask_freshness_v1,
    classify_live_mark_price_freshness_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    durable_bytes_v1,
    immutable_json_v1,
)


from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    swap_queries_v1,
)


@dataclass(frozen=True)
class RankedSwapObservationV1:
    canonical_id: str
    native_id: str
    mark: float
    market_event_unix: float
    mark_acquired_unix: float
    receipt_path: Path
    index: float
    volume_contracts: float
    oi_contracts: float
    funding_rate: float | None
    book: PaperBookV1
    book_event_unix: float
    book_acquired_at_utc: str
    source_hashes: dict
    source_observations: dict

    @property
    def decision_blocker(self):
        return "I17_SWAP_FUNDING_OUTSIDE_WINDOW" if self.funding_rate is None else None

    def fetch_mark_price(self, *, venue_instrument_id, inst_type):
        if venue_instrument_id != self.native_id or inst_type != "SWAP":
            raise ValueError("I17_SWAP_MARK_IDENTITY_MISMATCH")
        return self.source_observations["mark"]

    def fetch_ticker(self, *, venue_instrument_id):
        if venue_instrument_id != self.native_id:
            raise ValueError("I17_SWAP_TICKER_IDENTITY_MISMATCH")
        return self.source_observations["ticker"]


def invalid_swap_observation_v1(exc):
    detail = str(exc)
    error_class = {
        "ZKP_PAPER_SOURCE_STALE_OR_FUTURE": "MARKET_DATA_STALE",
        "I17_SWAP_FUNDING_OUTSIDE_WINDOW": "MARKET_DATA_STALE",
        "ZKP_PAPER_EVENT_TIMESTAMP_INVALID": "MARKET_DATA_TIMESTAMP_MISSING",
        "ZKP_PAPER_NUMERIC_INPUT_INVALID": "INVALID_PRICE_VALUE",
        "I17_SWAP_NUMERIC_VALUE_INVALID": "INVALID_PRICE_VALUE",
        "ZKP_PAPER_BOOK_DEPTH_OR_GRID_INVALID": "INVALID_PRICE_VALUE",
        "ZKP_PAPER_BOOK_LOCKED_OR_CROSSED": "INVALID_PRICE_VALUE",
    }.get(detail, "VENUE_INSTRUMENT_RESPONSE_MISMATCH")
    if isinstance(exc, DecimalException):
        error_class = "INVALID_PRICE_VALUE"
    if isinstance(exc, KeyError):
        error_class = (
            "MARKET_DATA_TIMESTAMP_MISSING"
            if exc.args[0] in {"ts", "fundingTime"}
            else "REQUIRED_PRICE_FIELD_MISSING"
        )
    return MarketDataBindingErrorV1(error_class, detail)


def collect_ranked_swap_observation_v1(assignment, output: Path, clock, *, transport):
    i = assignment.instrument
    n = i.venue_native_inst_id
    underlying = f"{i.base_currency}-{i.quote_currency}"
    if (i.instrument_type, i.contract_type, i.quote_currency, i.settlement_currency) != (
        "SWAP",
        "linear_perpetual",
        "USDT",
        "USDT",
    ):
        raise ValueError("I17_SWAP_INSTRUMENT_MISMATCH")
    observations, acquired, hashes, payloads, receipts = {}, {}, {}, {}, {}
    for name, (path, query) in swap_queries_v1(n, underlying).items():
        response = transport.get_json(path, query)
        if (
            response.status != 200
            or response.path != path
            or not isinstance(response.payload, dict)
            or response.payload.get("code") != "0"
            or not isinstance(response.payload.get("data"), list)
            or len(response.payload["data"]) != 1
            or not isinstance(response.payload["data"][0], dict)
            or json.loads(response.body) != response.payload
        ):
            raise ValueError("I17_SWAP_PUBLIC_RESPONSE_INVALID")
        acquired[name] = clock()
        observations[name] = response
        payloads[name] = response.payload
        hashes[name] = sha256(response.body).hexdigest()
        durable_bytes_v1(output / (name + ".json"), response.body)
        receipts[name] = dict(
            path=path, query=query, received_at_unix=acquired[name], sha256=hashes[name]
        )
    immutable_json_v1(output / "receipts.json", receipts)
    now = clock()
    rows = {
        k: _one(v, underlying if k == "index" else None if k == "book" else n)
        for k, v in payloads.items()
    }
    for k in ("mark", "oi", "ticker", "funding"):
        if rows[k].get("instType") != "SWAP":
            raise ValueError("I17_SWAP_PROVIDER_TYPE_MISMATCH")
    if rows["book"].get("instId", n) != n:
        raise ValueError("I17_SWAP_BOOK_IDENTITY_MISMATCH")
    for k in ("mark", "oi", "ticker", "index", "book"):
        _fresh(
            rows[k],
            acquired[k],
            now,
            classify_live_best_bid_ask_freshness_v1
            if k == "book"
            else classify_live_mark_price_freshness_v1,
        )
    funding_current = (
        0 <= now - _timestamp(rows["funding"]) / 1000 <= 180
        and now < _timestamp(rows["funding"], "fundingTime") / 1000
    )
    values = [
        float(_decimal(rows[k][field], positive=k != "funding"))
        for k, field in (
            ("mark", "markPx"),
            ("index", "idxPx"),
            ("ticker", "vol24h"),
            ("oi", "oi"),
            ("funding", "fundingRate"),
        )
    ]
    if not all(isfinite(v) for v in values):
        raise ValueError("I17_SWAP_NUMERIC_VALUE_INVALID")
    mark, index, volume, oi, funding = values
    book = PaperBookV1.from_okx_v1(
        rows["book"],
        tick=_decimal(i.tick_size, positive=True),
        lot=_decimal(i.lot_size, positive=True),
    )
    return RankedSwapObservationV1(
        i.canonical_instrument_id,
        n,
        mark,
        _timestamp(rows["mark"]) / 1000,
        acquired["mark"],
        output / "receipts.json",
        index,
        volume,
        oi,
        funding if funding_current else None,
        book,
        _timestamp(rows["book"]) / 1000,
        datetime.fromtimestamp(acquired["book"], timezone.utc).isoformat(),
        hashes,
        observations,
    )


def observe_ranked_entry_fx_v1(assignment, market, cycle, *, transport, clock):
    """Value the original native mark for this entry decision only. Never mutate a portfolio."""
    from urllib.parse import parse_qs, urlsplit

    from src.ops.governed_productive_monetary_normalization_v1.constants_v1 import (
        USDT_USDC_ENDPOINT,
        USDT_USDC_SOURCE_IDENTITY,
    )
    from src.ops.governed_productive_monetary_normalization_v1.contracts_v1 import (
        MonetaryNormalizationError,
        conversion_edge_digest_v1,
    )
    from src.ops.governed_productive_monetary_normalization_v1.usdt_usdc_index_observation_v1 import (
        build_usdt_usdc_conversion_edge_from_index_tickers_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
        FreshPretradeGetStatusV1,
    )
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
        CANONICAL_HOST,
    )

    if cycle["decision_outcome"] not in {"enter_long", "enter_short"}:
        return None
    instrument = assignment.instrument
    if (
        (
            instrument.venue_native_inst_id,
            instrument.canonical_instrument_id,
            instrument.quote_currency,
            instrument.settlement_currency,
        )
        != (market.native_id, market.canonical_id, "USDT", "USDT")
        or transport.venue_instrument_id != market.native_id
        or not cycle["decision_id"]
    ):
        raise ValueError("I17_SWAP_ENTRY_FX_SCOPE_MISMATCH")
    ref = dict(
        decision_id=cycle["decision_id"],
        decision_outcome=cycle["decision_outcome"],
        lane_id=assignment.lane_id,
        n5_selection_digest=assignment.selection.integrity_digest,
        instrument_id=market.canonical_id,
        venue_native_id=market.native_id,
        mark_sha256=market.source_hashes["mark"],
        market_event_unix=market.market_event_unix,
    )
    query = {"instId": USDT_USDC_SOURCE_IDENTITY}
    started = clock()
    response = transport.get_json(USDT_USDC_ENDPOINT, query)
    received = clock()
    raw = response.body
    digest = sha256(raw).hexdigest()
    durable_bytes_v1(market.receipt_path.parent / "entry-fx.json", raw)
    receipt = dict(
        ref,
        method="GET",
        url=response.url,
        http_status=response.status,
        received_at_unix=received,
        requested_at_unix=started,
        body_sha256=digest,
    )
    immutable_json_v1(market.receipt_path.parent / "entry-fx-receipt.json", receipt)
    try:
        url = urlsplit(response.url)
        if (
            response.status != 200
            or response.path != USDT_USDC_ENDPOINT
            or (url.scheme, url.netloc, url.path) != ("https", CANONICAL_HOST, USDT_USDC_ENDPOINT)
            or parse_qs(url.query, keep_blank_values=True)
            != {"instId": [USDT_USDC_SOURCE_IDENTITY]}
            or json.loads(raw) != response.payload
            or response.payload.get("code") != "0"
            or not market.mark_acquired_unix <= started <= received
        ):
            raise ValueError("I17_SWAP_ENTRY_FX_GET_MISMATCH")
        row = _one(response.payload, USDT_USDC_SOURCE_IDENTITY)
        _fresh(row, received, received, classify_live_mark_price_freshness_v1)
        mark_row = _one(market.source_observations["mark"].payload, market.native_id)
        _fresh(mark_row, market.mark_acquired_unix, received, classify_live_mark_price_freshness_v1)
        mark = _decimal(mark_row["markPx"], positive=True)
        epoch = datetime.fromtimestamp(received, timezone.utc).isoformat()
        edge = build_usdt_usdc_conversion_edge_from_index_tickers_v1(
            index_tickers_payload=response.payload,
            decision_epoch=epoch,
            observed_at=epoch,
            fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
            pair_base_currency="USDC",
            pair_quote_currency="USDT",
            provenance_ref=digest,
        )
        return dict(
            ref,
            status="OBSERVED",
            valuation_epoch=epoch,
            original_fx_sha256=digest,
            edge_digest=conversion_edge_digest_v1(edge),
            usdc_per_usdt=str(edge.normalized_rate),
            mark_usdt_per_base=str(mark),
            mark_usdc_per_base=str(mark * edge.normalized_rate),
        )
    except (MonetaryNormalizationError, KeyError, ValueError, TypeError, DecimalException) as exc:
        return dict(ref, status="UNAVAILABLE", original_fx_sha256=digest, reason=str(exc))
