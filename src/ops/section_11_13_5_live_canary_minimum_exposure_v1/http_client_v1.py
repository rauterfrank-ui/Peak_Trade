"""§11.13.5-scoped LIVE HTTP client. POST is permit-gated; not a general live transport."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    normalize_rest_host,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_CANCEL,
    ENDPOINT_SUBMIT,
    FORBIDDEN_DEMO_SIMULATION_HEADERS,
    FORBIDDEN_HOST_MARKERS,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PRIVATE,
    GET_ENDPOINTS_PUBLIC,
    POST_ENDPOINTS_GATED,
    REUSED_BINDING_REST_HOST,
    RETRY_BACKOFF_SECONDS,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)


class LiveCanaryHttpError(RuntimeError):
    """Fail-closed canary HTTP violation."""


@dataclass(frozen=True)
class LiveCanaryHttpRequestV1:
    method: str
    url: str
    host: str
    endpoint: str
    headers: Mapping[str, str]
    timeout_seconds: float
    body_text: str = ""


@dataclass(frozen=True)
class LiveCanaryHttpResponseV1:
    status_code: int
    body_bytes: bytes
    elapsed_seconds: float
    endpoint: str
    method: str
    send_attempted: bool = True


@dataclass(frozen=True)
class CanaryEntrySubmitPermitV1:
    owner_go: str
    clordid: str
    permit_id: str
    kind: str = "ENTRY_SUBMIT"


class LiveCanaryTransportV1(Protocol):
    transport_class: str
    venue_live_contact: bool

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        """Send exactly one HTTP request."""


@dataclass
class LiveCanaryRequestCountersV1:
    request_count: int = 0
    write_request_count: int = 0
    order_request_count: int = 0
    entry_submit_count: int = 0
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
            "ENTRY_SUBMIT_COUNT": self.entry_submit_count,
            "CANCEL_REQUEST_COUNT": self.cancel_request_count,
            "AMEND_REQUEST_COUNT": self.amend_request_count,
            "WITHDRAW_REQUEST_COUNT": self.withdraw_request_count,
            "TRANSFER_REQUEST_COUNT": self.transfer_request_count,
            "GET_REQUEST_COUNT": self.get_request_count,
            "methods_used": list(self.methods_used),
            "endpoints_used": list(self.endpoints_used),
            "http_result_classes": list(self.http_result_classes),
        }


def _endpoint_path_only(endpoint: str) -> str:
    return str(endpoint or "").strip().split("?", 1)[0]


def assert_no_demo_simulation_headers_v1(headers: Mapping[str, str] | None) -> None:
    if not headers:
        return
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l in FORBIDDEN_DEMO_SIMULATION_HEADERS:
            raise LiveCanaryHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")
        if str(value).strip() in {"1", "true", "yes"} and "simul" in key_l:
            raise LiveCanaryHttpError(f"DEMO_SIMULATION_HEADER_FORBIDDEN:{key_l}")


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


def _assert_host(host: str) -> str:
    normalized = normalize_rest_host(host)
    for marker in FORBIDDEN_HOST_MARKERS:
        if marker in normalized:
            raise LiveCanaryHttpError(f"FORBIDDEN_HOST_MARKER:{marker}")
    if normalized != REUSED_BINDING_REST_HOST:
        raise LiveCanaryHttpError(f"HOST_MISMATCH:{normalized}!={REUSED_BINDING_REST_HOST}")
    return normalized


@dataclass
class LiveCanaryHttpClientV1:
    """Canary-scoped client. GET for sizing/state; POST only with entry permit."""

    rest_base: str
    rest_host: str
    transport: LiveCanaryTransportV1
    max_request_count: int = 12
    max_retries: int = 2
    timeout_seconds: float = 10.0
    counters: LiveCanaryRequestCountersV1 = field(default_factory=LiveCanaryRequestCountersV1)
    _entry_submitted: bool = field(default=False, init=False, repr=False)
    _bound_clordid: str | None = field(default=None, init=False, repr=False)
    _entry_send_attempted: bool = field(default=False, init=False, repr=False)

    def _build_request(
        self,
        *,
        method: str,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
        body_text: str = "",
    ) -> LiveCanaryHttpRequestV1:
        m = str(method or "").strip().upper()
        ep = str(endpoint or "").strip()
        path = _endpoint_path_only(ep)
        if not path:
            raise LiveCanaryHttpError("ENDPOINT_REQUIRED")
        lowered = ep.lower()
        if m == "GET":
            if path not in GET_ENDPOINTS_PUBLIC and path not in GET_ENDPOINTS_PRIVATE:
                raise LiveCanaryHttpError(f"ENDPOINT_NOT_ALLOWLISTED:{ep}")
            if path in GET_ENDPOINTS_PRIVATE:
                for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
                    if marker in lowered and marker not in {
                        "/trade/order",
                        "/api/v5/trade/order",
                    }:
                        raise LiveCanaryHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
        elif m == "POST":
            if path not in POST_ENDPOINTS_GATED:
                raise LiveCanaryHttpError(f"POST_ENDPOINT_NOT_ALLOWLISTED:{ep}")
            for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
                if marker in lowered and path not in {ENDPOINT_SUBMIT, ENDPOINT_CANCEL}:
                    raise LiveCanaryHttpError(f"MUTATION_ENDPOINT_HARD_BLOCK:{ep}")
        else:
            raise LiveCanaryHttpError(f"HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:{m or '<empty>'}")
        hdrs = {str(k): str(v) for k, v in dict(headers or {}).items()}
        assert_no_demo_simulation_headers_v1(hdrs)
        url = f"{self.rest_base.rstrip('/')}{ep}"
        host = _assert_host(url)
        if host != self.rest_host:
            raise LiveCanaryHttpError(f"HOST_MISMATCH:{host}!={self.rest_host}")
        return LiveCanaryHttpRequestV1(
            method=m,
            url=url,
            host=host,
            endpoint=ep,
            headers=hdrs,
            timeout_seconds=self.timeout_seconds,
            body_text=body_text,
        )

    def get(
        self,
        *,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
    ) -> LiveCanaryHttpResponseV1:
        if self.counters.request_count >= self.max_request_count:
            raise LiveCanaryHttpError("MAX_REQUEST_COUNT_EXCEEDED")
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
                    raise LiveCanaryHttpError("TRANSPORT_RETURNED_NON_GET")
                self.counters.request_count += 1
                self.counters.get_request_count += 1
                self.counters.methods_used.append("GET")
                self.counters.endpoints_used.append(endpoint)
                self.counters.http_result_classes.append(
                    classify_http_result_v1(response.status_code)
                )
                return LiveCanaryHttpResponseV1(
                    status_code=response.status_code,
                    body_bytes=response.body_bytes,
                    elapsed_seconds=elapsed,
                    endpoint=endpoint,
                    method="GET",
                    send_attempted=True,
                )
            except LiveCanaryHttpError:
                raise
            except TimeoutError as exc:
                last_exc = exc
                if attempts > self.max_retries:
                    raise LiveCanaryHttpError("TIMEOUT") from exc
                time.sleep(RETRY_BACKOFF_SECONDS)
            except (URLError, OSError) as exc:
                last_exc = exc
                if attempts > self.max_retries:
                    raise LiveCanaryHttpError(f"NETWORK_ERROR:{exc}") from exc
                time.sleep(RETRY_BACKOFF_SECONDS)
        raise LiveCanaryHttpError(f"RETRY_EXHAUSTED:{last_exc}")

    def post_entry_order(
        self,
        *,
        permit: CanaryEntrySubmitPermitV1,
        body_text: str,
        headers: Mapping[str, str],
    ) -> LiveCanaryHttpResponseV1:
        if permit.kind != "ENTRY_SUBMIT":
            raise LiveCanaryHttpError("ENTRY_PERMIT_KIND_INVALID")
        if self._entry_submitted or self.counters.entry_submit_count >= 1:
            raise LiveCanaryHttpError("DUPLICATE_ENTRY_SUBMIT_FORBIDDEN")
        if self._entry_send_attempted:
            raise LiveCanaryHttpError("UNKNOWN_SUBMIT_NO_BLIND_RETRY")
        if self._bound_clordid and self._bound_clordid != permit.clordid:
            raise LiveCanaryHttpError("CLORDID_REBIND_FORBIDDEN")
        self._bound_clordid = permit.clordid
        request = self._build_request(
            method="POST",
            endpoint=ENDPOINT_SUBMIT,
            headers=headers,
            body_text=body_text,
        )
        self._entry_send_attempted = True
        try:
            started = time.monotonic()
            response = self.transport.send(request)
            elapsed = time.monotonic() - started
        except TimeoutError as exc:
            self.counters.write_request_count += 1
            self.counters.order_request_count += 1
            raise LiveCanaryHttpError("UNKNOWN_SUBMIT_TIMEOUT") from exc
        except (URLError, OSError) as exc:
            self.counters.write_request_count += 1
            self.counters.order_request_count += 1
            raise LiveCanaryHttpError("UNKNOWN_SUBMIT_NETWORK") from exc
        self.counters.request_count += 1
        self.counters.write_request_count += 1
        self.counters.order_request_count += 1
        self.counters.entry_submit_count += 1
        self.counters.methods_used.append("POST")
        self.counters.endpoints_used.append(ENDPOINT_SUBMIT)
        self.counters.http_result_classes.append(classify_http_result_v1(response.status_code))
        self._entry_submitted = True
        if response.method != "POST":
            raise LiveCanaryHttpError("TRANSPORT_RETURNED_NON_POST")
        return LiveCanaryHttpResponseV1(
            status_code=response.status_code,
            body_bytes=response.body_bytes,
            elapsed_seconds=elapsed,
            endpoint=ENDPOINT_SUBMIT,
            method="POST",
            send_attempted=True,
        )

    def post_cancel_order(
        self,
        *,
        clordid: str,
        body_text: str,
        headers: Mapping[str, str],
    ) -> LiveCanaryHttpResponseV1:
        if not self._entry_send_attempted:
            raise LiveCanaryHttpError("CANCEL_WITHOUT_ENTRY_SUBMIT_FORBIDDEN")
        if self._bound_clordid and self._bound_clordid != clordid:
            raise LiveCanaryHttpError("CANCEL_CLORDID_MISMATCH")
        request = self._build_request(
            method="POST",
            endpoint=ENDPOINT_CANCEL,
            headers=headers,
            body_text=body_text,
        )
        started = time.monotonic()
        response = self.transport.send(request)
        elapsed = time.monotonic() - started
        self.counters.request_count += 1
        self.counters.write_request_count += 1
        self.counters.cancel_request_count += 1
        self.counters.methods_used.append("POST")
        self.counters.endpoints_used.append(ENDPOINT_CANCEL)
        self.counters.http_result_classes.append(classify_http_result_v1(response.status_code))
        return LiveCanaryHttpResponseV1(
            status_code=response.status_code,
            body_bytes=response.body_bytes,
            elapsed_seconds=elapsed,
            endpoint=ENDPOINT_CANCEL,
            method="POST",
            send_attempted=True,
        )

    def post(self, *, endpoint: str, **_: Any) -> None:
        raise LiveCanaryHttpError(f"UNGATED_POST_FORBIDDEN:{endpoint}")


@dataclass
class RecordingFakeCanaryTransportV1:
    """Test transport: no real network."""

    status_code: int = 200
    body: bytes = b'{"code":"0","data":[]}'
    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = False
    calls: list[LiveCanaryHttpRequestV1] = field(default_factory=list)
    raise_timeout: bool = False
    raise_timeout_on_post: bool = False
    bodies_by_endpoint: dict[str, bytes] = field(default_factory=dict)
    post_body: bytes = b'{"code":"0","data":[{"sCode":"0","ordId":"fake-ord","clOrdId":"x"}]}'

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.calls.append(request)
        if self.raise_timeout:
            raise TimeoutError("fake-timeout")
        if request.method == "POST" and self.raise_timeout_on_post:
            raise TimeoutError("fake-post-timeout")
        path = _endpoint_path_only(request.endpoint)
        if request.method == "POST":
            body = self.post_body
        else:
            body = self.bodies_by_endpoint.get(
                path, self.bodies_by_endpoint.get(request.endpoint, self.body)
            )
        return LiveCanaryHttpResponseV1(
            status_code=self.status_code,
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method=request.method,
            send_attempted=True,
        )


@dataclass
class UrllibLiveCanaryTransportV1:
    """Real urllib transport. Constructed only under execute + productive wire flag."""

    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = True
    wire_send_enabled: bool = False

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        if not self.wire_send_enabled:
            raise LiveCanaryHttpError("PRODUCTIVE_WIRE_SEND_DISABLED")
        data = request.body_text.encode("utf-8") if request.body_text else None
        req = Request(request.url, data=data, method=request.method, headers=dict(request.headers))
        started = time.monotonic()
        try:
            with urlopen(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                body = resp.read()
                status = int(getattr(resp, "status", 200))
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = int(exc.code)
        elapsed = time.monotonic() - started
        return LiveCanaryHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=elapsed,
            endpoint=request.endpoint,
            method=request.method,
            send_attempted=True,
        )


def parse_json_object_v1(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveCanaryHttpError("MALFORMED_NON_JSON_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise LiveCanaryHttpError("RESPONSE_NOT_JSON_OBJECT")
    return payload
