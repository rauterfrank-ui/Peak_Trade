"""Dedicated LIVE shadow with exchange reconciliation HTTP client (GET-only; no Testnet client reuse)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    LiveShadowReconVenueBindingV1,
    normalize_rest_host,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    ENDPOINT_ALLOWLIST,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    METHOD_ALLOWLIST,
    RETRY_BACKOFF_SECONDS,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)


class LiveShadowReconHttpError(RuntimeError):
    """Fail-closed Live shadow reconciliation HTTP violation."""


@dataclass(frozen=True)
class LiveShadowReconHttpRequestV1:
    method: str
    url: str
    host: str
    endpoint: str
    headers: Mapping[str, str]
    timeout_seconds: float


@dataclass(frozen=True)
class LiveShadowReconHttpResponseV1:
    status_code: int
    body_bytes: bytes
    elapsed_seconds: float
    endpoint: str
    method: str


class LiveShadowReconTransportV1(Protocol):
    transport_class: str
    venue_live_contact: bool

    def send(self, request: LiveShadowReconHttpRequestV1) -> LiveShadowReconHttpResponseV1:
        """Send exactly one HTTP request."""


@dataclass
class LiveShadowReconRequestCountersV1:
    request_count: int = 0
    write_request_count: int = 0
    order_request_count: int = 0
    cancel_request_count: int = 0
    amend_request_count: int = 0
    withdraw_request_count: int = 0
    transfer_request_count: int = 0
    get_request_count: int = 0
    methods_used: list[str] = field(default_factory=list)
    endpoints_used: list[str] = field(default_factory=list)
    http_result_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "REQUEST_COUNT": self.request_count,
            "WRITE_REQUEST_COUNT": self.write_request_count,
            "ORDER_REQUEST_COUNT": self.order_request_count,
            "CANCEL_REQUEST_COUNT": self.cancel_request_count,
            "AMEND_REQUEST_COUNT": self.amend_request_count,
            "WITHDRAW_REQUEST_COUNT": self.withdraw_request_count,
            "TRANSFER_REQUEST_COUNT": self.transfer_request_count,
            "GET_REQUEST_COUNT": self.get_request_count,
            "methods_used": list(self.methods_used),
            "endpoints_used": list(self.endpoints_used),
            "http_result_classes": list(self.http_result_classes),
        }


def assert_method_allowlisted_v1(method: str) -> str:
    m = str(method or "").strip().upper()
    if m in FORBIDDEN_HTTP_METHODS or m not in METHOD_ALLOWLIST:
        raise LiveShadowReconHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}")
    return m


def assert_endpoint_allowlisted_v1(endpoint: str) -> str:
    ep = str(endpoint or "").strip()
    if not ep:
        raise LiveShadowReconHttpError("ENDPOINT_REQUIRED")
    lowered = ep.lower()
    for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
        if marker not in lowered:
            continue
        # Do not false-positive GET /trade/orders-pending against /trade/order*.
        if marker.rstrip("?") in {"/trade/order", "/api/v5/trade/order"} and (
            "/trade/orders-" in lowered or lowered.endswith("/trade/orders-pending")
        ):
            continue
        raise LiveShadowReconHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
    if ep not in ENDPOINT_ALLOWLIST:
        raise LiveShadowReconHttpError(f"ENDPOINT_NOT_ALLOWLISTED:{ep}")
    return ep


def assert_no_demo_simulation_headers_v1(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise LiveShadowReconHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")
        if str(value).strip() in {"1", "true", "yes"} and "simul" in key_l:
            raise LiveShadowReconHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")


def assert_host_matches_binding_v1(
    *,
    binding: LiveShadowReconVenueBindingV1,
    request_host: str,
) -> None:
    host = normalize_rest_host(request_host)
    if host != binding.rest_host:
        raise LiveShadowReconHttpError(f"HOST_MISMATCH:{host}!={binding.rest_host}")


def classify_http_result_v1(status_code: int) -> str:
    if status_code == 200:
        return "HTTP_200_OK"
    if status_code == 401:
        return "HTTP_401_UNAUTHORIZED"
    if status_code == 403:
        return "HTTP_403_FORBIDDEN"
    if 400 <= status_code < 500:
        return f"HTTP_{status_code}_CLIENT_ERROR"
    if status_code >= 500:
        return f"HTTP_{status_code}_SERVER_ERROR"
    return f"HTTP_{status_code}"


@dataclass
class LiveShadowReconHttpClientV1:
    """GET-only Live shadow reconciliation client with hard mutation blocks before wire-send."""

    binding: LiveShadowReconVenueBindingV1
    transport: LiveShadowReconTransportV1
    endpoint_allowlist: tuple[str, ...] = ENDPOINT_ALLOWLIST
    max_request_count: int = 4
    max_retries: int = 2
    timeout_seconds: float = 10.0
    counters: LiveShadowReconRequestCountersV1 = field(
        default_factory=LiveShadowReconRequestCountersV1
    )

    def _build_request(
        self,
        *,
        method: str,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> LiveShadowReconHttpRequestV1:
        m = assert_method_allowlisted_v1(method)
        ep = assert_endpoint_allowlisted_v1(endpoint)
        if ep not in self.endpoint_allowlist:
            raise LiveShadowReconHttpError(f"ENDPOINT_NOT_IN_RUNTIME_ALLOWLIST:{ep}")
        hdrs = {str(k): str(v) for k, v in dict(headers or {}).items()}
        assert_no_demo_simulation_headers_v1(hdrs)
        url = f"{self.binding.rest_base.rstrip('/')}{ep}"
        host = normalize_rest_host(url)
        assert_host_matches_binding_v1(binding=self.binding, request_host=host)
        return LiveShadowReconHttpRequestV1(
            method=m,
            url=url,
            host=host,
            endpoint=ep,
            headers=hdrs,
            timeout_seconds=self.timeout_seconds,
        )

    def get(
        self,
        *,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> LiveShadowReconHttpResponseV1:
        if self.counters.request_count >= self.max_request_count:
            raise LiveShadowReconHttpError("MAX_REQUEST_COUNT_EXCEEDED")
        request = self._build_request(method="GET", endpoint=endpoint, headers=headers)
        attempts = 0
        last_exc: Exception | None = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                started = time.monotonic()
                response = self.transport.send(request)
                elapsed = time.monotonic() - started
                if response.method != "GET":
                    raise LiveShadowReconHttpError("TRANSPORT_RETURNED_NON_GET")
                self.counters.request_count += 1
                self.counters.get_request_count += 1
                self.counters.methods_used.append("GET")
                self.counters.endpoints_used.append(endpoint)
                self.counters.http_result_classes.append(
                    classify_http_result_v1(response.status_code)
                )
                return LiveShadowReconHttpResponseV1(
                    status_code=response.status_code,
                    body_bytes=response.body_bytes,
                    elapsed_seconds=elapsed,
                    endpoint=endpoint,
                    method="GET",
                )
            except LiveShadowReconHttpError:
                raise
            except TimeoutError as exc:
                last_exc = exc
                if attempts > self.max_retries:
                    raise LiveShadowReconHttpError("TIMEOUT") from exc
                time.sleep(RETRY_BACKOFF_SECONDS)
            except (URLError, OSError) as exc:
                last_exc = exc
                if attempts > self.max_retries:
                    raise LiveShadowReconHttpError(f"NETWORK_ERROR:{exc}") from exc
                time.sleep(RETRY_BACKOFF_SECONDS)
        raise LiveShadowReconHttpError(f"RETRY_EXHAUSTED:{last_exc}")

    def post(self, *, endpoint: str, **_: Any) -> None:
        self.counters.write_request_count += 1
        assert_method_allowlisted_v1("POST")

    def request(self, *, method: str, endpoint: str, **_: Any) -> LiveShadowReconHttpResponseV1:
        m = str(method or "").strip().upper()
        if m != "GET":
            if "ORDER" in endpoint.upper() or "order" in endpoint:
                self.counters.order_request_count += 1
            if "cancel" in endpoint.lower():
                self.counters.cancel_request_count += 1
            if "amend" in endpoint.lower() or "batch" in endpoint.lower():
                self.counters.amend_request_count += 1
            if "withdraw" in endpoint.lower():
                self.counters.withdraw_request_count += 1
            if "transfer" in endpoint.lower():
                self.counters.transfer_request_count += 1
            self.counters.write_request_count += 1
            assert_method_allowlisted_v1(m)
        return self.get(endpoint=endpoint)


@dataclass
class RecordingFakeTransportV1:
    """Test transport: no real network."""

    status_code: int = 200
    body: bytes = b'{"code":"0","data":[{"uid":"acct-live-redacted"}]}'
    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = True
    calls: list[LiveShadowReconHttpRequestV1] = field(default_factory=list)
    raise_timeout: bool = False
    raise_malformed_once: bool = False

    def send(self, request: LiveShadowReconHttpRequestV1) -> LiveShadowReconHttpResponseV1:
        self.calls.append(request)
        if self.raise_timeout:
            raise TimeoutError("fake-timeout")
        if request.method != "GET":
            raise LiveShadowReconHttpError("FAKE_TRANSPORT_GET_ONLY")
        return LiveShadowReconHttpResponseV1(
            status_code=self.status_code,
            body_bytes=self.body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method=request.method,
        )


@dataclass
class UrllibLiveTransportV1:
    """Real urllib transport. Must only be used under separate Execute-GO."""

    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = True

    def send(self, request: LiveShadowReconHttpRequestV1) -> LiveShadowReconHttpResponseV1:
        if request.method != "GET":
            raise LiveShadowReconHttpError("URLLIB_TRANSPORT_GET_ONLY")
        req = Request(request.url, method="GET", headers=dict(request.headers))
        started = time.monotonic()
        try:
            with urlopen(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                body = resp.read()
                status = int(getattr(resp, "status", 200))
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = int(exc.code)
        elapsed = time.monotonic() - started
        return LiveShadowReconHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=elapsed,
            endpoint=request.endpoint,
            method="GET",
        )


def parse_json_object_v1(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveShadowReconHttpError("MALFORMED_NON_JSON_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise LiveShadowReconHttpError("RESPONSE_NOT_JSON_OBJECT")
    return payload
