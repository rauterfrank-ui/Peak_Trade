"""§11.13.5-scoped LIVE HTTP client. POST is permit-gated; not a general live transport."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

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
    USER_AGENT_CANARY,
)


class LiveCanaryHttpError(RuntimeError):
    """Fail-closed canary HTTP violation."""


class CanaryPostRedirectBlockedError(Exception):
    """Raised when a mutating canary POST receives an HTTP redirect. Do not follow."""

    def __init__(
        self,
        *,
        status_code: int,
        location: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> None:
        super().__init__(f"POST_REDIRECT_FAIL_CLOSED:{status_code}")
        self.status_code = int(status_code)
        self.location = str(location or "")
        self.body = body or b""
        self.headers = {str(k): str(v) for k, v in dict(headers).items()}


CANARY_SAFE_RESPONSE_HEADER_ALLOWLIST_V1 = frozenset(
    {
        "content-type",
        "content-length",
        "date",
        "server",
        "cf-ray",
        "cf-cache-status",
        "x-request-id",
        "ok-request-id",
        "x-okx-request-id",
        "location",
        "retry-after",
        "x-content-type-options",
    }
)
_FORBIDDEN_HEADER_NAME_MARKERS = (
    "authorization",
    "ok-access",
    "cookie",
    "set-cookie",
    "api-key",
    "passphrase",
    "secret",
    "sign",
)
_OKX_MSG_MAX_LEN = 200
_OKX_CODE_MAX_LEN = 64
_OKX_SMSG_MAX_LEN = 512
_OKX_ID_FIELD_MAX_LEN = 128
_VENUE_NATIVE_SCALAR_MAX_LEN = 128

CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1 = (
    "instId",
    "tdMode",
    "side",
    "ordType",
    "sz",
    "px",
    "posSide",
    "reduceOnly",
    "ccy",
    "tgtCcy",
    "banAmend",
    "stpMode",
    "tag",
    "clOrdId",
)
OKX_ORDER_DATA_ENTRY_FIELDS_V1 = ("sCode", "sMsg", "ordId", "clOrdId", "tag")
_CONTENT_TYPE_MAX_LEN = 128
_LOCATION_MAX_LEN = 512


def sanitize_redirect_location_v1(raw: str | None) -> str:
    """Keep scheme/host/path only. Drop userinfo, query, and fragment."""
    text = str(raw or "").strip()
    if not text:
        return ""
    if len(text) > _LOCATION_MAX_LEN:
        text = text[:_LOCATION_MAX_LEN]
    parts = urlsplit(text)
    host = parts.hostname or ""
    if not host and not parts.path:
        return ""
    netloc = host
    if parts.port:
        netloc = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def _headers_to_mapping(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if hasattr(headers, "items"):
        return {str(k): str(v) for k, v in headers.items()}
    return {}


def safe_response_headers_v1(headers: Mapping[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in dict(headers or {}).items():
        key_s = str(key)
        key_l = key_s.strip().lower()
        if key_l not in CANARY_SAFE_RESPONSE_HEADER_ALLOWLIST_V1:
            continue
        if any(marker in key_l for marker in _FORBIDDEN_HEADER_NAME_MARKERS):
            continue
        rendered = str(value)
        if key_l == "location":
            rendered = sanitize_redirect_location_v1(rendered)
        out[key_s] = rendered[:256]
    return out


def signed_wire_body_evidence_v1(
    *,
    signed_body_text: str,
    wire_body_bytes: bytes,
) -> dict[str, Any]:
    signed = str(signed_body_text or "").encode("utf-8")
    wire = wire_body_bytes or b""
    return {
        "SIGNED_BODY_EQUALS_WIRE_BODY": signed == wire,
        "signed_body_sha256_12": hashlib.sha256(signed).hexdigest()[:12],
        "wire_body_sha256_12": hashlib.sha256(wire).hexdigest()[:12],
        "signed_body_byte_len": len(signed),
        "wire_body_byte_len": len(wire),
        "SECRET_VALUES_INCLUDED": False,
    }


def _copy_allowlisted_scalar_fields_v1(
    source: Mapping[str, Any],
    allowlist: tuple[str, ...],
    *,
    max_len: int,
) -> dict[str, Any]:
    """Copy present allowlisted scalars only. Absent keys stay omitted."""
    out: dict[str, Any] = {}
    for key in allowlist:
        if key not in source:
            continue
        raw = source[key]
        if isinstance(raw, (dict, list)):
            continue
        if isinstance(raw, (bool, int, float)) or raw is None:
            out[key] = raw
            continue
        out[key] = str(raw)[:max_len]
    return out


def _extract_okx_order_data_entry_v1(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {"_entry_not_object": True}
    copied = _copy_allowlisted_scalar_fields_v1(
        item,
        OKX_ORDER_DATA_ENTRY_FIELDS_V1,
        max_len=_OKX_SMSG_MAX_LEN,
    )
    for key in ("sCode", "ordId", "clOrdId", "tag"):
        if key in copied and copied[key] is not None and not isinstance(copied[key], bool):
            copied[key] = str(copied[key])[:_OKX_ID_FIELD_MAX_LEN]
    if "sMsg" in copied and copied["sMsg"] is not None and not isinstance(copied["sMsg"], bool):
        copied["sMsg"] = str(copied["sMsg"])[:_OKX_SMSG_MAX_LEN]
    return copied


def extract_canary_venue_native_request_evidence_v1(*, body_text: str) -> dict[str, Any]:
    """Secret-safe venue-native POST body fields after final serialization."""
    parse_error: str | None = None
    payload: Any = None
    try:
        payload = json.loads(body_text)
    except (TypeError, json.JSONDecodeError, UnicodeDecodeError):
        parse_error = "REQUEST_BODY_NOT_JSON"
        payload = None
    if payload is not None and not isinstance(payload, dict):
        parse_error = "REQUEST_BODY_NOT_JSON_OBJECT"
        payload = None
    present_keys: list[str] = []
    absent_keys: list[str] = []
    fields: dict[str, Any] = {}
    if isinstance(payload, dict):
        fields = _copy_allowlisted_scalar_fields_v1(
            payload,
            CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1,
            max_len=_VENUE_NATIVE_SCALAR_MAX_LEN,
        )
        for key in CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1:
            if key in payload:
                present_keys.append(key)
            else:
                absent_keys.append(key)
    else:
        absent_keys = list(CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1)
    return {
        "fields": fields,
        "present_keys": present_keys,
        "absent_keys": absent_keys,
        "parse_error": parse_error,
        "SECRET_VALUES_INCLUDED": False,
    }


def build_canary_submit_adjudication_evidence_v1(
    *,
    http_evidence: Mapping[str, Any],
    venue_native_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Compact durable adjudication block. Survives result mapping without stdout."""
    request_fields = dict(venue_native_request.get("fields") or {})
    if not request_fields and "fields" not in venue_native_request:
        request_fields = {
            key: venue_native_request[key]
            for key in CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1
            if key in venue_native_request
        }
    return {
        "HTTP_STATUS": http_evidence.get("http_status"),
        "TOP_LEVEL_OKX_CODE": http_evidence.get("okx_code"),
        "TOP_LEVEL_OKX_MSG": http_evidence.get("okx_msg"),
        "OKX_DATA_COUNT": http_evidence.get("okx_data_count"),
        "okx_data": list(http_evidence.get("okx_data") or []),
        "venue_native_request": request_fields,
        "VENUE_NATIVE_PRESENT_KEYS": list(venue_native_request.get("present_keys") or []),
        "VENUE_NATIVE_ABSENT_KEYS": list(venue_native_request.get("absent_keys") or []),
        "SECRET_VALUES_INCLUDED": False,
    }


def extract_canary_http_response_evidence_v1(
    *,
    status_code: int,
    body_bytes: bytes,
    headers: Mapping[str, str] | None = None,
    redirect_followed: bool = False,
    redirect_status: int | None = None,
    redirect_location: str | None = None,
) -> dict[str, Any]:
    """Secret-safe HTTP error/response evidence. Never treats parse failure as success."""
    raw = body_bytes or b""
    headers_safe = safe_response_headers_v1(headers)
    content_type = ""
    for key, value in headers_safe.items():
        if str(key).lower() == "content-type":
            content_type = str(value)
            break
    json_parse_ok = False
    okx_code: str | None = None
    okx_msg: str | None = None
    parse_error: str | None = None
    okx_data: list[dict[str, Any]] = []
    okx_data_count: int | None = None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        parse_error = "MALFORMED_NON_JSON_RESPONSE"
        payload = None
    if payload is not None and not isinstance(payload, dict):
        parse_error = "RESPONSE_NOT_JSON_OBJECT"
        payload = None
    if isinstance(payload, dict):
        json_parse_ok = True
        if payload.get("code") is not None:
            okx_code = str(payload.get("code"))[:_OKX_CODE_MAX_LEN]
        if payload.get("msg") is not None:
            okx_msg = str(payload.get("msg"))[:_OKX_MSG_MAX_LEN]
        if "data" not in payload:
            okx_data_count = None
        elif not isinstance(payload.get("data"), list):
            parse_error = parse_error or "OKX_DATA_NOT_ARRAY"
            okx_data_count = None
        else:
            data_rows = payload.get("data")
            okx_data_count = len(data_rows)
            okx_data = [_extract_okx_order_data_entry_v1(item) for item in data_rows]
    location = sanitize_redirect_location_v1(
        redirect_location or headers_safe.get("Location") or headers_safe.get("location")
    )
    return {
        "http_status": int(status_code),
        "okx_code": okx_code,
        "okx_msg": okx_msg,
        "okx_data_count": okx_data_count,
        "okx_data": okx_data,
        "content_type": content_type[:_CONTENT_TYPE_MAX_LEN] if content_type else None,
        "response_headers_safe": headers_safe,
        "json_parse_ok": json_parse_ok,
        "parse_error": parse_error,
        "body_byte_len": len(raw),
        "body_sha256_12": hashlib.sha256(raw).hexdigest()[:12] if raw else "",
        "redirect_followed": bool(redirect_followed),
        "redirect_status": int(redirect_status) if redirect_status is not None else None,
        "redirect_location": location or None,
        "SECRET_VALUES_INCLUDED": False,
    }


class CanaryPostRedirectFailClosedHandler(HTTPRedirectHandler):
    """Fail-closed: GET and POST must not follow 301/302/303/307/308."""

    def http_error_301(self, req: Request, fp: Any, code: int, msg: str, headers: Any) -> Any:
        return self._block_post_or_follow(req, fp, code, msg, headers)

    def http_error_302(self, req: Request, fp: Any, code: int, msg: str, headers: Any) -> Any:
        return self._block_post_or_follow(req, fp, code, msg, headers)

    def http_error_303(self, req: Request, fp: Any, code: int, msg: str, headers: Any) -> Any:
        return self._block_post_or_follow(req, fp, code, msg, headers)

    def http_error_307(self, req: Request, fp: Any, code: int, msg: str, headers: Any) -> Any:
        return self._block_post_or_follow(req, fp, code, msg, headers)

    def http_error_308(self, req: Request, fp: Any, code: int, msg: str, headers: Any) -> Any:
        return self._block_post_or_follow(req, fp, code, msg, headers)

    def _block_post_or_follow(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any
    ) -> Any:
        method = str(req.get_method() or "").upper()
        if method in {"GET", "POST"}:
            location = ""
            if headers is not None:
                location = str(headers.get("location") or headers.get("Location") or "")
            body = fp.read() if fp is not None and hasattr(fp, "read") else b""
            raise CanaryPostRedirectBlockedError(
                status_code=int(code),
                location=sanitize_redirect_location_v1(location),
                body=body if isinstance(body, (bytes, bytearray)) else b"",
                headers=_headers_to_mapping(headers),
            )
        return HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)


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
    wire_body_sha256: str = ""
    wire_body_byte_len: int = 0
    redirect_followed: bool = False
    redirect_status: int | None = None
    redirect_location: str | None = None
    response_headers_safe: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CanaryEntrySubmitPermitV1:
    owner_go: str
    clordid: str
    permit_id: str
    kind: str = "ENTRY_SUBMIT"


@dataclass(frozen=True)
class CanaryFlattenHttpPermitV1:
    """HTTP-layer flatten permit. Distinct from entry. Not live authorization."""

    owner_go: str
    clordid: str
    permit_id: str
    kind: str = "FLATTEN_SUBMIT"

    def __post_init__(self) -> None:
        if self.kind != "FLATTEN_SUBMIT":
            raise LiveCanaryHttpError("FLATTEN_HTTP_PERMIT_KIND_INVALID")


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
    flatten_submit_count: int = 0
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
            "FLATTEN_SUBMIT_COUNT": self.flatten_submit_count,
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


def _parse_json_object_or_error(body_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(body_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise LiveCanaryHttpError("POST_BODY_NOT_JSON_OBJECT") from exc
    if not isinstance(payload, dict):
        raise LiveCanaryHttpError("POST_BODY_NOT_JSON_OBJECT")
    return payload


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
    if 300 <= status_code < 400:
        return f"HTTP_{status_code}_REDIRECT"
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
    _flatten_submitted: bool = field(default=False, init=False, repr=False)
    _bound_clordid: str | None = field(default=None, init=False, repr=False)
    _bound_flatten_clordid: str | None = field(default=None, init=False, repr=False)
    _entry_send_attempted: bool = field(default=False, init=False, repr=False)
    _flatten_send_attempted: bool = field(default=False, init=False, repr=False)

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
        if not any(str(k).strip().lower() == "user-agent" for k in hdrs):
            hdrs["User-Agent"] = USER_AGENT_CANARY
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
                return replace(
                    response,
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
        flatten_kind = str(getattr(permit, "kind", "") or "")
        if isinstance(permit, CanaryFlattenHttpPermitV1) or flatten_kind == "FLATTEN_SUBMIT":
            raise LiveCanaryHttpError("FLATTEN_PERMIT_CANNOT_USE_ENTRY_TRANSPORT")
        if permit.kind != "ENTRY_SUBMIT":
            raise LiveCanaryHttpError("ENTRY_PERMIT_KIND_INVALID")
        parsed_body = _parse_json_object_or_error(body_text)
        if parsed_body.get("reduceOnly") is True:
            raise LiveCanaryHttpError("ENTRY_REDUCE_ONLY_FORBIDDEN")
        entry_ord_type = str(parsed_body.get("ordType") or "").strip().lower()
        if entry_ord_type and entry_ord_type != "limit":
            raise LiveCanaryHttpError("ENTRY_MARKET_FORBIDDEN")
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
        if response.redirect_followed:
            raise LiveCanaryHttpError("POST_REDIRECT_FOLLOWED_FORBIDDEN")
        return replace(
            response,
            elapsed_seconds=elapsed,
            endpoint=ENDPOINT_SUBMIT,
            method="POST",
            send_attempted=True,
        )

    def post_flatten_order(
        self,
        *,
        permit: CanaryFlattenHttpPermitV1,
        body_text: str,
        headers: Mapping[str, str],
    ) -> LiveCanaryHttpResponseV1:
        if not isinstance(permit, CanaryFlattenHttpPermitV1) or permit.kind != "FLATTEN_SUBMIT":
            raise LiveCanaryHttpError("FLATTEN_HTTP_PERMIT_KIND_INVALID")
        if isinstance(permit, CanaryEntrySubmitPermitV1) and permit.kind == "ENTRY_SUBMIT":
            raise LiveCanaryHttpError("ENTRY_PERMIT_CANNOT_USE_FLATTEN_TRANSPORT")
        parsed_body = _parse_json_object_or_error(body_text)
        if parsed_body.get("reduceOnly") is not True:
            raise LiveCanaryHttpError("FLATTEN_REDUCE_ONLY_REQUIRED")
        if str(parsed_body.get("ordType") or "").lower() != "limit":
            raise LiveCanaryHttpError("FLATTEN_MARKET_FORBIDDEN")
        if not str(parsed_body.get("px") or "").strip():
            raise LiveCanaryHttpError("FLATTEN_LIMIT_PX_REQUIRED")
        if self._flatten_submitted or self.counters.flatten_submit_count >= 1:
            raise LiveCanaryHttpError("DUPLICATE_FLATTEN_SUBMIT_FORBIDDEN")
        if self._flatten_send_attempted:
            raise LiveCanaryHttpError("UNKNOWN_FLATTEN_SUBMIT_NO_BLIND_RETRY")
        if self._bound_flatten_clordid and self._bound_flatten_clordid != permit.clordid:
            raise LiveCanaryHttpError("FLATTEN_CLORDID_REBIND_FORBIDDEN")
        self._bound_flatten_clordid = permit.clordid
        request = self._build_request(
            method="POST",
            endpoint=ENDPOINT_SUBMIT,
            headers=headers,
            body_text=body_text,
        )
        if "/trade/close-position" in str(request.endpoint).lower():
            raise LiveCanaryHttpError("CLOSE_POSITION_ENDPOINT_FORBIDDEN")
        self._flatten_send_attempted = True
        try:
            started = time.monotonic()
            response = self.transport.send(request)
            elapsed = time.monotonic() - started
        except TimeoutError as exc:
            self.counters.write_request_count += 1
            self.counters.order_request_count += 1
            raise LiveCanaryHttpError("UNKNOWN_FLATTEN_SUBMIT_TIMEOUT") from exc
        except (URLError, OSError) as exc:
            self.counters.write_request_count += 1
            self.counters.order_request_count += 1
            raise LiveCanaryHttpError("UNKNOWN_FLATTEN_SUBMIT_NETWORK") from exc
        self.counters.request_count += 1
        self.counters.write_request_count += 1
        self.counters.order_request_count += 1
        self.counters.flatten_submit_count += 1
        self.counters.methods_used.append("POST")
        self.counters.endpoints_used.append(ENDPOINT_SUBMIT)
        self.counters.http_result_classes.append(classify_http_result_v1(response.status_code))
        self._flatten_submitted = True
        if response.method != "POST":
            raise LiveCanaryHttpError("TRANSPORT_RETURNED_NON_POST")
        if response.redirect_followed:
            raise LiveCanaryHttpError("POST_REDIRECT_FOLLOWED_FORBIDDEN")
        return replace(
            response,
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
        if response.redirect_followed:
            raise LiveCanaryHttpError("POST_REDIRECT_FOLLOWED_FORBIDDEN")
        return replace(
            response,
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
    post_status_code: int | None = None
    post_headers: dict[str, str] = field(default_factory=dict)
    post_redirect_status: int | None = None
    post_redirect_location: str | None = None

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.calls.append(request)
        if self.raise_timeout:
            raise TimeoutError("fake-timeout")
        if request.method == "POST" and self.raise_timeout_on_post:
            raise TimeoutError("fake-post-timeout")
        path = _endpoint_path_only(request.endpoint)
        wire = request.body_text.encode("utf-8") if request.body_text else b""
        if request.method == "POST":
            body = self.post_body
            status = int(self.post_status_code or self.status_code)
            headers = dict(self.post_headers)
            redirect_status = self.post_redirect_status
            redirect_location = self.post_redirect_location
            if 300 <= status < 400 and redirect_status is None:
                redirect_status = status
        else:
            body = self.bodies_by_endpoint.get(
                path, self.bodies_by_endpoint.get(request.endpoint, self.body)
            )
            status = self.status_code
            headers = {}
            redirect_status = None
            redirect_location = None
        return LiveCanaryHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method=request.method,
            send_attempted=True,
            wire_body_sha256=hashlib.sha256(wire).hexdigest(),
            wire_body_byte_len=len(wire),
            redirect_followed=False,
            redirect_status=redirect_status,
            redirect_location=sanitize_redirect_location_v1(redirect_location),
            response_headers_safe=safe_response_headers_v1(headers),
        )


@dataclass
class UrllibLiveCanaryTransportV1:
    """Real urllib transport. Constructed only under execute + productive wire flag."""

    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = True
    wire_send_enabled: bool = False
    http_exchange_count: int = 0

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        if not self.wire_send_enabled:
            raise LiveCanaryHttpError("PRODUCTIVE_WIRE_SEND_DISABLED")
        wire_bytes = request.body_text.encode("utf-8") if request.body_text else b""
        data = wire_bytes if wire_bytes else None
        req = Request(request.url, data=data, method=request.method, headers=dict(request.headers))
        started = time.monotonic()
        redirect_followed = False
        redirect_status: int | None = None
        redirect_location: str | None = None
        header_src: Any = None
        try:
            self.http_exchange_count += 1
            opener = build_opener(ProxyHandler({}), CanaryPostRedirectFailClosedHandler())
            try:
                with opener.open(req, timeout=request.timeout_seconds) as resp:  # noqa: S310
                    body = resp.read()
                    status = int(getattr(resp, "status", 200))
                    header_src = getattr(resp, "headers", None)
            except CanaryPostRedirectBlockedError as blocked:
                body = blocked.body
                status = int(blocked.status_code)
                header_src = blocked.headers
                redirect_followed = False
                redirect_status = status
                redirect_location = blocked.location
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = int(exc.code)
            header_src = getattr(exc, "headers", None)
        elapsed = time.monotonic() - started
        headers_safe = safe_response_headers_v1(_headers_to_mapping(header_src))
        return LiveCanaryHttpResponseV1(
            status_code=status,
            body_bytes=body,
            elapsed_seconds=elapsed,
            endpoint=request.endpoint,
            method=request.method,
            send_attempted=True,
            wire_body_sha256=hashlib.sha256(wire_bytes).hexdigest(),
            wire_body_byte_len=len(wire_bytes),
            redirect_followed=redirect_followed,
            redirect_status=redirect_status,
            redirect_location=sanitize_redirect_location_v1(redirect_location),
            response_headers_safe=headers_safe,
        )


def parse_json_object_v1(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveCanaryHttpError("MALFORMED_NON_JSON_RESPONSE") from exc
    if not isinstance(payload, dict):
        raise LiveCanaryHttpError("RESPONSE_NOT_JSON_OBJECT")
    return payload
