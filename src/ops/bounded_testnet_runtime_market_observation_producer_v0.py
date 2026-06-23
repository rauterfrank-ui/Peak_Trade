"""Bounded testnet runtime market observation producer v0.

Canonical repo-owner for one-shot public read-only PF_ETHUSD testnet ticker fetch.
Fail-closed host/endpoint boundary, typed parsing, no retry, no credentials.
Does not authorize testnet execute, orders, or live trading.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol
from urllib import error, request
from urllib.parse import urlparse

from src.ops.bounded_testnet_market_input_admission_wiring_v0 import (
    REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
    BoundedTestnetFuturesMarketObservationV0,
    BoundedTestnetFuturesMarketPriceTickObservationV0,
    CANONICAL_TESTNET_OBSERVATION_LANE,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesMarketType,
)

BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_LAYER_VERSION = "v0"
BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_OWNER = (
    "ops.bounded_testnet_runtime_market_observation_producer_v0"
)
PACKAGE_MARKER = "BOUNDED_TESTNET_RUNTIME_MARKET_OBSERVATION_PRODUCER_V0=true"

CANONICAL_TESTNET_BASE_URL = "https://demo-futures.kraken.com"
CANONICAL_TICKER_ENDPOINT = "/derivatives/api/v3/tickers"
CANONICAL_PUBLIC_TESTNET_READ_ONLY_CLASS = "PUBLIC_TESTNET_READ_ONLY"
DEFAULT_EXCHANGE = "kraken_futures_demo"
DEFAULT_DATASET_ID = "bounded_testnet_runtime_public_ticker_v0"
DEFAULT_PRICE_SOURCE = "demo_futures_public_ticker"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 262_144
DEFAULT_MAX_STALENESS_SECONDS = 120.0

FORBIDDEN_TESTNET_HOST_PREFIXES: frozenset[str] = frozenset(
    {
        "https://futures.kraken.com",
        "https://api.kraken.com",
        "http://",
    }
)
_FORBIDDEN_VENUE_SYMBOL_RE = re.compile(r"(?i)(pf_xbtusd|pf_btcusd|xbt|btc|/usd|/eur|spot)")
_ALLOWED_HTTP_STATUS_SUCCESS = range(200, 300)


class BoundedTestnetRuntimeClock(Protocol):
    def utc_now(self) -> datetime:
        """Return current UTC time."""

    def utc_now_iso_z(self) -> str:
        """Return current UTC timestamp as ISO-8601 Z string."""


class PublicTestnetTickerFetcher(Protocol):
    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        """Perform exactly one bounded GET; no retry."""


PublicTestnetTickerFetcherCallable = Callable[[str, float], tuple[int, bytes]]


class RuntimeMarketObservationFailureClass:
    TESTNET_HOST_NOT_ALLOWED = "TESTNET_HOST_NOT_ALLOWED"
    ENDPOINT_NOT_ALLOWED = "ENDPOINT_NOT_ALLOWED"
    HTTP_503_SERVICE_UNAVAILABLE = "HTTP_503_SERVICE_UNAVAILABLE"
    HTTP_STATUS_NOT_ALLOWED = "HTTP_STATUS_NOT_ALLOWED"
    RESPONSE_NOT_JSON = "RESPONSE_NOT_JSON"
    RESPONSE_SCHEMA_INVALID = "RESPONSE_SCHEMA_INVALID"
    VENUE_SYMBOL_NOT_FOUND = "VENUE_SYMBOL_NOT_FOUND"
    PRICE_FIELD_MISSING = "PRICE_FIELD_MISSING"
    PRICE_FIELD_NOT_FINITE = "PRICE_FIELD_NOT_FINITE"
    TIMESTAMP_INVALID = "TIMESTAMP_INVALID"
    OBSERVATION_STALE = "OBSERVATION_STALE"
    INSTRUMENT_MAPPING_MISMATCH = "INSTRUMENT_MAPPING_MISMATCH"
    NETWORK_EXCEPTION_REDACTED = "NETWORK_EXCEPTION_REDACTED"


@dataclass(frozen=True)
class BoundedTestnetRuntimeTickerFetchResultV0:
    """Single bounded public ticker fetch outcome (one HTTP round-trip, no retry)."""

    success: bool
    failure_class: str | None
    failure_detail: str | None
    http_status: int | None
    tick: BoundedTestnetFuturesMarketPriceTickObservationV0 | None
    mark_price_available: bool
    last_price_available: bool
    index_price_available: bool
    price_timestamp_utc: str | None
    observed_at_utc: str | None
    fetch_count: int = 1


@dataclass(frozen=True)
class BoundedTestnetRuntimeClockV0:
    """Injectable UTC clock for deterministic offline tests."""

    _now: datetime | None = None

    def utc_now(self) -> datetime:
        if self._now is not None:
            return self._now
        return datetime.now(timezone.utc)

    def utc_now_iso_z(self) -> str:
        return self.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


class UrllibPublicTestnetTickerFetcher:
    """Default one-shot urllib GET fetcher; redirects disabled fail-closed."""

    def fetch(self, url: str, *, timeout_seconds: float) -> tuple[int, bytes]:
        req = request.Request(url, method="GET")
        opener = request.build_opener(_NoRedirectHandler())
        with opener.open(req, timeout=timeout_seconds) as resp:
            status = int(getattr(resp, "status", resp.getcode()))
            body = resp.read(DEFAULT_MAX_RESPONSE_BYTES + 1)
            if len(body) > DEFAULT_MAX_RESPONSE_BYTES:
                body = body[:DEFAULT_MAX_RESPONSE_BYTES]
            return status, body


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def _normalize_base_url(url: str) -> str:
    return url.strip().rstrip("/")


def validate_testnet_public_ticker_request_url(
    testnet_base_url: str,
    *,
    endpoint_path: str = CANONICAL_TICKER_ENDPOINT,
) -> str | None:
    """Return failure class when URL is not the canonical bounded public testnet ticker GET."""
    base = _normalize_base_url(testnet_base_url)
    for prefix in FORBIDDEN_TESTNET_HOST_PREFIXES:
        if base.startswith(prefix) or testnet_base_url.startswith(prefix):
            return RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    if base != CANONICAL_TESTNET_BASE_URL:
        return RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    if endpoint_path != CANONICAL_TICKER_ENDPOINT:
        return RuntimeMarketObservationFailureClass.ENDPOINT_NOT_ALLOWED
    parsed = urlparse(f"{base}{endpoint_path}")
    if parsed.scheme != "https" or parsed.netloc != "demo-futures.kraken.com":
        return RuntimeMarketObservationFailureClass.TESTNET_HOST_NOT_ALLOWED
    if parsed.path != CANONICAL_TICKER_ENDPOINT:
        return RuntimeMarketObservationFailureClass.ENDPOINT_NOT_ALLOWED
    return None


def build_canonical_testnet_public_ticker_url(testnet_base_url: str) -> str:
    return f"{_normalize_base_url(testnet_base_url)}{CANONICAL_TICKER_ENDPOINT}"


def _failure(
    failure_class: str,
    detail: str,
    *,
    http_status: int | None = None,
) -> BoundedTestnetRuntimeTickerFetchResultV0:
    return BoundedTestnetRuntimeTickerFetchResultV0(
        success=False,
        failure_class=failure_class,
        failure_detail=detail,
        http_status=http_status,
        tick=None,
        mark_price_available=False,
        last_price_available=False,
        index_price_available=False,
        price_timestamp_utc=None,
        observed_at_utc=None,
        fetch_count=1,
    )


def _parse_price_field(entry: Mapping[str, object], field: str) -> tuple[float | None, str | None]:
    if field not in entry:
        return None, RuntimeMarketObservationFailureClass.PRICE_FIELD_MISSING
    raw = entry[field]
    if raw is None:
        return None, RuntimeMarketObservationFailureClass.PRICE_FIELD_MISSING
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None, RuntimeMarketObservationFailureClass.PRICE_FIELD_NOT_FINITE
    if not math.isfinite(value) or value <= 0.0:
        return None, RuntimeMarketObservationFailureClass.PRICE_FIELD_NOT_FINITE
    return value, None


def _parse_ticker_timestamp_ms(entry: Mapping[str, object]) -> tuple[int | None, str | None]:
    for key in ("lastTime", "timestamp", "time"):
        if key not in entry:
            continue
        raw = entry[key]
        if isinstance(raw, (int, float)) and math.isfinite(float(raw)):
            ts = float(raw)
            if ts > 1_000_000_000_000:
                return int(ts), None
            if ts > 1_000_000_000:
                return int(ts * 1000), None
        if isinstance(raw, str) and raw.strip():
            text = raw.strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError:
                return None, RuntimeMarketObservationFailureClass.TIMESTAMP_INVALID
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return int(parsed.timestamp() * 1000), None
    return None, RuntimeMarketObservationFailureClass.TIMESTAMP_INVALID


def _find_pf_ethusd_ticker(payload: object) -> Mapping[str, object] | None:
    if not isinstance(payload, dict):
        return None
    tickers = payload.get("tickers")
    if not isinstance(tickers, list):
        return None
    for item in tickers:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).strip()
        if (
            _FORBIDDEN_VENUE_SYMBOL_RE.search(symbol)
            and symbol != REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL
        ):
            continue
        if symbol == REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL:
            return item
    return None


def parse_pf_ethusd_ticker_entry(
    entry: Mapping[str, object],
    *,
    tick_index: int,
    sequence: int,
    clock: BoundedTestnetRuntimeClock,
    max_staleness_seconds: float,
) -> BoundedTestnetRuntimeTickerFetchResultV0:
    symbol = str(entry.get("symbol", "")).strip()
    if symbol != REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL:
        return _failure(
            RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH,
            "venue_symbol_mismatch",
        )
    if _FORBIDDEN_VENUE_SYMBOL_RE.search(symbol) and symbol != REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL:
        return _failure(
            RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH,
            "forbidden_venue_symbol",
        )

    mark_price, mark_reason = _parse_price_field(entry, "markPrice")
    if mark_reason is not None:
        return _failure(mark_reason, "markPrice_invalid")
    assert mark_price is not None

    last_price, last_reason = _parse_price_field(entry, "last")
    last_available = last_reason is None and last_price is not None
    index_price, index_reason = _parse_price_field(entry, "indexPrice")
    index_available = index_reason is None and index_price is not None
    if not last_available and "bid" in entry:
        bid_price, bid_reason = _parse_price_field(entry, "bid")
        last_available = bid_reason is None and bid_price is not None
    if not index_available and "ask" in entry:
        ask_price, ask_reason = _parse_price_field(entry, "ask")
        index_available = ask_reason is None and ask_price is not None

    timestamp_ms, ts_reason = _parse_ticker_timestamp_ms(entry)
    if ts_reason is not None or timestamp_ms is None:
        return _failure(
            ts_reason or RuntimeMarketObservationFailureClass.TIMESTAMP_INVALID, "timestamp_invalid"
        )

    observed_at = clock.utc_now()
    age_seconds = (observed_at.timestamp() * 1000 - timestamp_ms) / 1000.0
    if age_seconds > max_staleness_seconds:
        return _failure(RuntimeMarketObservationFailureClass.OBSERVATION_STALE, "observation_stale")

    price_timestamp_utc = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    tick = BoundedTestnetFuturesMarketPriceTickObservationV0(
        tick_index=tick_index,
        timestamp_ms=timestamp_ms,
        mark_price=mark_price,
        sequence=sequence,
    )
    return BoundedTestnetRuntimeTickerFetchResultV0(
        success=True,
        failure_class=None,
        failure_detail=None,
        http_status=200,
        tick=tick,
        mark_price_available=True,
        last_price_available=last_available,
        index_price_available=index_available,
        price_timestamp_utc=price_timestamp_utc,
        observed_at_utc=clock.utc_now_iso_z(),
        fetch_count=1,
    )


def fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
    *,
    testnet_base_url: str = CANONICAL_TESTNET_BASE_URL,
    instrument: str = REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    venue_symbol: str = REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
    source_run_id: str,
    tick_index: int,
    sequence: int,
    fetcher: PublicTestnetTickerFetcher | PublicTestnetTickerFetcherCallable,
    clock: BoundedTestnetRuntimeClock | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    max_staleness_seconds: float = DEFAULT_MAX_STALENESS_SECONDS,
) -> BoundedTestnetRuntimeTickerFetchResultV0:
    """Perform exactly one bounded public testnet ticker fetch for PF_ETHUSD."""
    if instrument != REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID:
        return _failure(
            RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH,
            "instrument_not_eth_perp",
        )
    if venue_symbol != REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL:
        return _failure(
            RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH,
            "venue_symbol_not_pf_ethusd",
        )
    if _FORBIDDEN_VENUE_SYMBOL_RE.search(instrument) or _FORBIDDEN_VENUE_SYMBOL_RE.search(
        venue_symbol
    ):
        return _failure(
            RuntimeMarketObservationFailureClass.INSTRUMENT_MAPPING_MISMATCH,
            "btc_or_spot_symbol_rejected",
        )

    url_failure = validate_testnet_public_ticker_request_url(testnet_base_url)
    if url_failure is not None:
        return _failure(url_failure, "request_url_not_allowed")

    url = build_canonical_testnet_public_ticker_url(testnet_base_url)
    runtime_clock = clock or BoundedTestnetRuntimeClockV0()

    try:
        if hasattr(fetcher, "fetch"):
            status, body = fetcher.fetch(url, timeout_seconds=timeout_seconds)
        else:
            status, body = fetcher(url, timeout_seconds)
    except error.HTTPError as exc:
        status = int(exc.code)
        body = exc.read(max_response_bytes + 1) if hasattr(exc, "read") else b""
    except Exception:
        return _failure(
            RuntimeMarketObservationFailureClass.NETWORK_EXCEPTION_REDACTED,
            "network_exception_redacted",
        )

    if status == 503:
        return _failure(
            RuntimeMarketObservationFailureClass.HTTP_503_SERVICE_UNAVAILABLE,
            "http_503_service_unavailable",
            http_status=status,
        )
    if status not in _ALLOWED_HTTP_STATUS_SUCCESS:
        return _failure(
            RuntimeMarketObservationFailureClass.HTTP_STATUS_NOT_ALLOWED,
            f"http_status_{status}",
            http_status=status,
        )

    if len(body) > max_response_bytes:
        return _failure(
            RuntimeMarketObservationFailureClass.RESPONSE_SCHEMA_INVALID, "response_too_large"
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _failure(RuntimeMarketObservationFailureClass.RESPONSE_NOT_JSON, "response_not_json")

    if not isinstance(payload, dict) or payload.get("result") not in ("success", None):
        return _failure(
            RuntimeMarketObservationFailureClass.RESPONSE_SCHEMA_INVALID, "result_not_success"
        )

    entry = _find_pf_ethusd_ticker(payload)
    if entry is None:
        return _failure(
            RuntimeMarketObservationFailureClass.VENUE_SYMBOL_NOT_FOUND, "pf_ethusd_not_found"
        )

    return parse_pf_ethusd_ticker_entry(
        entry,
        tick_index=tick_index,
        sequence=sequence,
        clock=runtime_clock,
        max_staleness_seconds=max_staleness_seconds,
    )


def assemble_bounded_testnet_runtime_market_observation_v0(
    *,
    tick_results: tuple[BoundedTestnetRuntimeTickerFetchResultV0, ...],
    source_run_id: str,
    instrument: str = REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    venue_symbol: str = REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
) -> tuple[BoundedTestnetFuturesMarketObservationV0 | None, str | None, str | None]:
    """Assemble a canonical observation envelope from successful single-fetch ticks."""
    if not tick_results:
        return None, "no_ticks", "no_tick_results"
    for result in tick_results:
        if not result.success or result.tick is None:
            return None, result.failure_class, result.failure_detail
    ticks = tuple(result.tick for result in tick_results if result.tick is not None)
    last = tick_results[-1]
    return (
        BoundedTestnetFuturesMarketObservationV0(
            selected_future_id=instrument,
            venue_symbol=venue_symbol,
            exchange=DEFAULT_EXCHANGE,
            market_type=FuturesMarketType.PERPETUAL,
            source_run_id=source_run_id,
            dataset_id=DEFAULT_DATASET_ID,
            price_source=DEFAULT_PRICE_SOURCE,
            freshness_state=FuturesFreshnessState.FRESH,
            observed_at_utc=last.observed_at_utc or "",
            price_timestamp_utc=last.price_timestamp_utc or "",
            mark_price_available=all(r.mark_price_available for r in tick_results),
            last_price_available=all(r.last_price_available for r in tick_results),
            index_price_available=all(r.index_price_available for r in tick_results),
            price_ticks=ticks,
            source_lane=CANONICAL_TESTNET_OBSERVATION_LANE,
            synthetic_offline_fixture=False,
        ),
        None,
        None,
    )


def collect_bounded_testnet_runtime_market_observation_v0(
    *,
    testnet_base_url: str,
    source_run_id: str,
    max_steps: int,
    fetcher: PublicTestnetTickerFetcher | PublicTestnetTickerFetcherCallable,
    clock: BoundedTestnetRuntimeClock | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_staleness_seconds: float = DEFAULT_MAX_STALENESS_SECONDS,
    step_sleep: Callable[[float], None] | None = None,
    step_interval_seconds: float = 0.0,
) -> tuple[BoundedTestnetFuturesMarketObservationV0 | None, str | None, str | None]:
    """Collect up to max_steps single-fetch ticks; fail-closed on first fetch failure (no retry)."""
    if max_steps <= 0:
        return None, "max_steps_invalid", "max_steps_must_be_positive"

    tick_results: list[BoundedTestnetRuntimeTickerFetchResultV0] = []
    for step in range(max_steps):
        if step > 0 and step_interval_seconds > 0.0 and step_sleep is not None:
            step_sleep(step_interval_seconds)
        result = fetch_bounded_testnet_pf_ethusd_ticker_tick_v0(
            testnet_base_url=testnet_base_url,
            source_run_id=source_run_id,
            tick_index=step,
            sequence=step + 1,
            fetcher=fetcher,
            clock=clock,
            timeout_seconds=timeout_seconds,
            max_staleness_seconds=max_staleness_seconds,
        )
        if not result.success:
            return None, result.failure_class, result.failure_detail
        tick_results.append(result)
    return assemble_bounded_testnet_runtime_market_observation_v0(
        tick_results=tuple(tick_results),
        source_run_id=source_run_id,
    )


def default_public_testnet_ticker_fetcher() -> UrllibPublicTestnetTickerFetcher:
    return UrllibPublicTestnetTickerFetcher()
