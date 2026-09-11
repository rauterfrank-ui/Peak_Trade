"""Public-MD raw-input source for Economic-MD MVR collection.

Reuses canonical OKX public GET paths for mark-price history and ticker.
Does not import Cap 5.2, CMC, canary, testnet, or selected-future MD clients.
Network I/O is optional and explicit; tests inject observations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence
from urllib import error, parse, request

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    ALLOWED_PUBLIC_GET_PATHS,
    FORBIDDEN_AUTH_HEADERS,
    FORBIDDEN_PATH_PREFIXES,
    HTTP_MAX_RESPONSE_BYTES,
    HTTP_MAX_RETRIES,
    HTTP_TIMEOUT_SECONDS,
    MARK_BAR,
    MARK_ENDPOINT_PATH,
    MARK_HISTORY_LIMIT,
    MARK_SOURCE_CLASS,
    PUBLIC_HTTP_BASE_URL,
    TICKER_ENDPOINT_PATH,
    TICKER_SOURCE_CLASS,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1


class EconomicMdPublicSourceError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class RawMarkCandleV1:
    venue_native_id: str
    ts_ms: str
    mark_px: str
    confirm: str
    receive_or_capture_timestamp: str
    source_class: str = MARK_SOURCE_CLASS
    source_endpoint: str = MARK_ENDPOINT_PATH


@dataclass(frozen=True)
class RawTickerQuoteV1:
    venue_native_id: str
    bid_px: Optional[str]
    ask_px: Optional[str]
    ticker_event_timestamp: Optional[str]
    capture_or_receive_timestamp: str
    source_class: str = TICKER_SOURCE_CLASS
    source_endpoint: str = TICKER_ENDPOINT_PATH


@dataclass(frozen=True)
class InstrumentPublicMdBundleV1:
    venue_native_id: str
    marks: tuple[RawMarkCandleV1, ...]
    ticker: Optional[RawTickerQuoteV1]
    failure_codes: tuple[str, ...] = ()


class EconomicMdPublicSourceV1(Protocol):
    def collect_instrument_raw_input_v1(
        self, *, venue_native_id: str
    ) -> InstrumentPublicMdBundleV1: ...


@dataclass(frozen=True)
class InjectedEconomicMdPublicSourceV1:
    """Offline/test source. No network. Observations must be supplied by the caller."""

    bundles: Mapping[str, InstrumentPublicMdBundleV1]

    def collect_instrument_raw_input_v1(
        self, *, venue_native_id: str
    ) -> InstrumentPublicMdBundleV1:
        bundle = self.bundles.get(venue_native_id)
        if bundle is None:
            return InstrumentPublicMdBundleV1(
                venue_native_id=venue_native_id,
                marks=(),
                ticker=None,
                failure_codes=(EconomicMdFailureCodeV1.PUBLIC_MD_SOURCE_UNAVAILABLE.value,),
            )
        return bundle


def assert_public_get_path_allowed_v1(path: str) -> str:
    normalized = str(path or "").split("?", 1)[0]
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    for prefix in FORBIDDEN_PATH_PREFIXES:
        if normalized.startswith(prefix):
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.FORBIDDEN_NETWORK_PATH.value, normalized
            )
    if normalized not in ALLOWED_PUBLIC_GET_PATHS:
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.FORBIDDEN_NETWORK_PATH.value, normalized
        )
    return normalized


PublicGetFetcher = Callable[[str, float, int], tuple[int, bytes, dict[str, str]]]


def _default_public_get(
    url: str, timeout_seconds: float, max_response_bytes: int
) -> tuple[int, bytes, dict[str, str]]:
    parsed = parse.urlparse(url)
    assert_public_get_path_allowed_v1(parsed.path)
    hdrs = {"User-Agent": "PeakTradeEconomicMdPublicGet/1", "Accept": "application/json"}
    req = request.Request(url, method="GET", headers=hdrs)
    try:
        with request.urlopen(req, timeout=min(timeout_seconds, HTTP_TIMEOUT_SECONDS)) as resp:
            body = resp.read(max_response_bytes + 1)
            if len(body) > max_response_bytes:
                raise EconomicMdPublicSourceError(
                    EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value,
                    "RESPONSE_TOO_LARGE",
                )
            return int(getattr(resp, "status", resp.getcode())), body, dict(resp.headers.items())
    except error.HTTPError as exc:
        body = exc.read(max_response_bytes)
        return int(exc.code), body, {k: v for k, v in exc.headers.items()}
    except (error.URLError, TimeoutError, OSError) as exc:
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.NETWORK_TIMEOUT.value, str(exc)
        ) from exc


def _build_url(path: str, params: Mapping[str, str]) -> str:
    assert_public_get_path_allowed_v1(path)
    query = parse.urlencode(dict(params))
    return f"{PUBLIC_HTTP_BASE_URL}{path}?{query}" if query else f"{PUBLIC_HTTP_BASE_URL}{path}"


def parse_okx_mark_candles_v1(
    payload: Mapping[str, Any],
    *,
    venue_native_id: str,
    receive_or_capture_timestamp: str,
) -> tuple[RawMarkCandleV1, ...]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "MARKS_NOT_LIST"
        )
    rows: list[RawMarkCandleV1] = []
    for item in data:
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)):
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "MARK_ROW"
            )
        if len(item) < 6:
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "MARK_ROW_SHORT"
            )
        confirm_idx = 5 if len(item) <= 6 else len(item) - 1
        rows.append(
            RawMarkCandleV1(
                venue_native_id=venue_native_id,
                ts_ms=str(item[0]),
                mark_px=str(item[4]),
                confirm=str(item[confirm_idx]),
                receive_or_capture_timestamp=receive_or_capture_timestamp,
            )
        )
    return tuple(rows)


def parse_okx_ticker_v1(
    payload: Mapping[str, Any],
    *,
    venue_native_id: str,
    capture_or_receive_timestamp: str,
) -> RawTickerQuoteV1:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "TICKER_EMPTY"
        )
    row = data[0]
    if not isinstance(row, Mapping):
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "TICKER_ROW"
        )
    bid = row.get("bidPx")
    ask = row.get("askPx")
    event_ts = row.get("ts")
    return RawTickerQuoteV1(
        venue_native_id=venue_native_id,
        bid_px=None if bid in (None, "") else str(bid),
        ask_px=None if ask in (None, "") else str(ask),
        ticker_event_timestamp=None if event_ts in (None, "") else str(event_ts),
        capture_or_receive_timestamp=capture_or_receive_timestamp,
    )


@dataclass
class OkxPublicEconomicMdReadAdapterV1:
    """Minimal public GET adapter owned by Economic-MD. Not a general MD framework."""

    capture_timestamp: str
    fetcher: PublicGetFetcher = _default_public_get
    timeout_seconds: float = HTTP_TIMEOUT_SECONDS
    max_response_bytes: int = HTTP_MAX_RESPONSE_BYTES

    def _get_json(self, path: str, params: Mapping[str, str]) -> Mapping[str, Any]:
        path = assert_public_get_path_allowed_v1(path)
        url = _build_url(path, params)
        last_error: Optional[Exception] = None
        attempts = HTTP_MAX_RETRIES + 1
        for _attempt in range(attempts):
            try:
                status, body, _headers = self.fetcher(
                    url, self.timeout_seconds, self.max_response_bytes
                )
            except EconomicMdPublicSourceError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
            if status != 200:
                last_error = EconomicMdPublicSourceError(
                    EconomicMdFailureCodeV1.PUBLIC_MD_SOURCE_UNAVAILABLE.value,
                    f"HTTP_{status}",
                )
                continue
            try:
                parsed = json_object(body)
            except EconomicMdPublicSourceError as exc:
                last_error = exc
                continue
            return parsed
        if last_error is not None:
            if isinstance(last_error, EconomicMdPublicSourceError):
                raise last_error
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.PUBLIC_MD_SOURCE_UNAVAILABLE.value, str(last_error)
            ) from last_error
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.PUBLIC_MD_SOURCE_UNAVAILABLE.value, "NO_RESPONSE"
        )

    def collect_instrument_raw_input_v1(
        self, *, venue_native_id: str
    ) -> InstrumentPublicMdBundleV1:
        try:
            marks_payload = self._get_json(
                MARK_ENDPOINT_PATH,
                {
                    "instId": venue_native_id,
                    "bar": MARK_BAR,
                    "limit": MARK_HISTORY_LIMIT,
                },
            )
            marks = parse_okx_mark_candles_v1(
                payload=marks_payload,
                venue_native_id=venue_native_id,
                receive_or_capture_timestamp=self.capture_timestamp,
            )
            ticker_payload = self._get_json(
                TICKER_ENDPOINT_PATH,
                {"instId": venue_native_id},
            )
            ticker = parse_okx_ticker_v1(
                payload=ticker_payload,
                venue_native_id=venue_native_id,
                capture_or_receive_timestamp=self.capture_timestamp,
            )
            return InstrumentPublicMdBundleV1(
                venue_native_id=venue_native_id,
                marks=marks,
                ticker=ticker,
            )
        except EconomicMdPublicSourceError as exc:
            return InstrumentPublicMdBundleV1(
                venue_native_id=venue_native_id,
                marks=(),
                ticker=None,
                failure_codes=(exc.failure_code,),
            )


def json_object(body: bytes) -> Mapping[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, str(exc)
        ) from exc
    if not isinstance(payload, Mapping):
        raise EconomicMdPublicSourceError(
            EconomicMdFailureCodeV1.MALFORMED_PUBLIC_MD_PAYLOAD.value, "NOT_OBJECT"
        )
    for key in FORBIDDEN_AUTH_HEADERS:
        if key in payload:
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.AUTH_HEADER_FORBIDDEN.value, key
            )
    return payload


def forbid_auth_headers_v1(headers: Mapping[str, Any] | None) -> None:
    if not headers:
        return
    for key in headers:
        if str(key).upper() in FORBIDDEN_AUTH_HEADERS:
            raise EconomicMdPublicSourceError(
                EconomicMdFailureCodeV1.AUTH_HEADER_FORBIDDEN.value, str(key)
            )
