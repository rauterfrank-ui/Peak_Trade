"""Bounded read-only OKX public REST client for market-data pipeline.

Public endpoints only. No API keys. TLS verified. Explicit timeouts and size limits.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urlparse

from src.ops.okx_captured_at_freshness_policy_v1 import (
    build_okx_capture_clocks_v1,
    provider_ms_to_utc_iso,
    utc_now_iso,
)

PACKAGE_MARKER = "OKX_PUBLIC_MARKET_DATA_CLIENT_V1=true"
ALLOWED_HOST = "www.okx.com"
ALLOWED_PATHS = frozenset(
    {
        "/api/v5/public/instruments",
        "/api/v5/public/mark-price",
        "/api/v5/market/tickers",
        "/api/v5/market/history-candles",
        "/api/v5/market/candles",
    }
)
USER_AGENT = "PeakTradeOkxPublicMarketData/1.0 (+read-only; no-credentials; no-orders)"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_RESPONSE_BYTES = 8_000_000
FORBIDDEN_QUERY_TOKENS = frozenset(
    {"apikey", "secret", "passphrase", "password", "token", "authorization", "sign"}
)


class OkxPublicMarketDataClientError(RuntimeError):
    """Public OKX fetch failure."""


@dataclass(frozen=True)
class OkxPublicCaptureEnvelopeV1:
    request_url: str
    request_path: str
    query_parameters: dict[str, str]
    http_status: int
    provider_code: str
    provider_message: str
    capture_started_at: str
    response_received_at: str
    captured_at: str
    effective_at: str | None
    provider_timestamp: str | None
    raw_payload_digest: str
    byte_size: int
    raw_body_utf8: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


HttpFetcher = Callable[[str, float], tuple[int, bytes]]


def _assert_public_url(url: str) -> tuple[str, dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST:
        raise OkxPublicMarketDataClientError(f"URL_NOT_ALLOWED:{url}")
    if parsed.path not in ALLOWED_PATHS:
        raise OkxPublicMarketDataClientError(f"PATH_NOT_ALLOWED:{parsed.path}")
    query: dict[str, str] = {}
    if parsed.query:
        for part in parsed.query.split("&"):
            if not part:
                continue
            if "=" in part:
                k, v = part.split("=", 1)
            else:
                k, v = part, ""
            if k.lower() in FORBIDDEN_QUERY_TOKENS:
                raise OkxPublicMarketDataClientError("SENSITIVE_QUERY_REFUSED")
            query[k] = v
    return parsed.path, query


def default_public_get(url: str, timeout_seconds: float) -> tuple[int, bytes]:
    _assert_public_url(url)
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            status = int(getattr(resp, "status", 200))
            body = resp.read(DEFAULT_MAX_RESPONSE_BYTES + 1)
            return status, body
    except urllib.error.HTTPError as exc:
        body = exc.read(DEFAULT_MAX_RESPONSE_BYTES + 1) if exc.fp else b""
        return int(exc.code), body


class OkxPublicMarketDataClientV1:
    def __init__(
        self,
        *,
        fetcher: HttpFetcher | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.fetcher = fetcher or default_public_get
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.sleep = sleep

    def get_json(self, path: str, params: Mapping[str, str]) -> OkxPublicCaptureEnvelopeV1:
        if path not in ALLOWED_PATHS:
            raise OkxPublicMarketDataClientError(f"PATH_NOT_ALLOWED:{path}")
        query = {str(k): str(v) for k, v in params.items()}
        url = f"https://{ALLOWED_HOST}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        _assert_public_url(url)

        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            capture_started = utc_now_iso()
            try:
                status, body = self.fetcher(url, self.timeout_seconds)
                response_received = utc_now_iso()
                if len(body) > DEFAULT_MAX_RESPONSE_BYTES:
                    raise OkxPublicMarketDataClientError(
                        f"RESPONSE_TOO_LARGE:bytes={len(body)}:max={DEFAULT_MAX_RESPONSE_BYTES}"
                    )
                if status in {401, 403}:
                    raise OkxPublicMarketDataClientError(f"AUTH_REQUIRED:HTTP_{status}")
                if status == 429:
                    raise OkxPublicMarketDataClientError("RATE_LIMIT_HTTP_429")
                if status >= 400:
                    raise OkxPublicMarketDataClientError(f"HTTP_{status}")
                text = body.decode("utf-8")
                payload = json.loads(text)
                if not isinstance(payload, dict):
                    raise OkxPublicMarketDataClientError("PAYLOAD_NOT_OBJECT")
                provider_code = str(payload.get("code") if payload.get("code") is not None else "")
                provider_message = str(payload.get("msg") if payload.get("msg") is not None else "")
                if provider_code != "0":
                    raise OkxPublicMarketDataClientError(
                        f"PROVIDER_CODE_{provider_code}:{provider_message}"
                    )
                provider_ts = None
                data = payload.get("data")
                if isinstance(data, list) and data:
                    first = data[0]
                    if isinstance(first, dict) and "ts" in first:
                        provider_ts = provider_ms_to_utc_iso(first.get("ts"))
                clocks = build_okx_capture_clocks_v1(
                    capture_started_at=capture_started,
                    response_received_at=response_received,
                    provider_timestamp=provider_ts,
                )
                digest = hashlib.sha256(body).hexdigest()
                return OkxPublicCaptureEnvelopeV1(
                    request_url=url,
                    request_path=path,
                    query_parameters=query,
                    http_status=status,
                    provider_code=provider_code,
                    provider_message=provider_message,
                    capture_started_at=clocks.capture_started_at,
                    response_received_at=clocks.response_received_at,
                    captured_at=clocks.captured_at,
                    effective_at=clocks.effective_at,
                    provider_timestamp=clocks.provider_timestamp,
                    raw_payload_digest=digest,
                    byte_size=len(body),
                    raw_body_utf8=text,
                )
            except OkxPublicMarketDataClientError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt >= self.max_retries:
                    break
                self.sleep(0.5 * (2**attempt))
        assert last_err is not None
        raise OkxPublicMarketDataClientError(f"FETCH_FAILED:{last_err}") from last_err
