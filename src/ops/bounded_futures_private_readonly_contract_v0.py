"""Kraken Futures Demo private-readonly reachability contract (v0).

Offline policy for private_readonly_reachability_only harness mode: GET allowlist,
order/host blocklist, response redaction rules. Does not authorize network, private
API execute, credentials read, or orders.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence
from urllib import error
from urllib.parse import urlparse

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
    FUTURES_TESTNET_ENDPOINT_ALLOWLIST,
    LIVE_FUTURES_HOST_PREFIXES,
    SPOT_KRAKEN_ENDPOINT_PREFIXES,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_INSTRUMENT,
    DEFAULT_MARGIN_MODE,
    DEFAULT_MARKET_TYPE,
    DEFAULT_ORDER_POLICY,
    DEFAULT_POSITION_MODE,
    EVIDENCE_SOURCE_FUTURES_HARNESS,
    FUTURES_SESSION_AUTHORIZED_NOW,
)
from src.ops.kraken_futures_demo_credential_presence_contract_v0 import (
    build_checker_boundary_v0,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_V0=true"
PRIVATE_READONLY_HTTP_WIRING_PRESENT = True
KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME = "KRAKEN_FUTURES_DEMO_API_KEY"
KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME = "KRAKEN_FUTURES_DEMO_API_SECRET"
PRIVATE_READONLY_MODE = "private_readonly_reachability_only"
DEFAULT_PRIVATE_READONLY_GET_TIMEOUT_SECONDS = 10.0
PRIVATE_READONLY_SESSION_CLASS = "bounded-futures-private-readonly-reachability-v0"
PRIVATE_READONLY_MAX_REQUEST_COUNT = 3
FETCH_FAILURE_CLASS_NETWORK = "network_timeout_or_fetch_exception"

DEMO_FUTURES_HOST = "demo-futures.kraken.com"
DEMO_FUTURES_REST_BASE_URL = f"{DEFAULT_FUTURES_TESTNET_NETWORK_HOST}/derivatives/api/v3"

FUTURES_PRIVATE_READONLY_GET_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/derivatives/api/v3/accounts",
        "/derivatives/api/v3/openpositions",
        "/derivatives/api/v3/openorders",
    }
)

PRIVATE_READONLY_ENDPOINT_ORDER: tuple[str, ...] = (
    "/derivatives/api/v3/accounts",
    "/derivatives/api/v3/openpositions",
    "/derivatives/api/v3/openorders",
)

FUTURES_PRIVATE_READONLY_FORBIDDEN_PATH_SUBSTRINGS: tuple[str, ...] = (
    "sendorder",
    "cancelorder",
    "cancelallorders",
    "cancelall",
    "validate-order",
    "validateorder",
    "batchorder",
    "withdraw",
    "transfer",
)

FUTURES_ORDER_MUTATION_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/derivatives/api/v3/sendorder",
        "/derivatives/api/v3/cancelorder",
        "/derivatives/api/v3/cancelallorders",
    }
)

ALLOWED_HTTP_METHODS_PRIVATE_READONLY: frozenset[str] = frozenset({"GET"})

CONFIRM_TOKEN_PRIVATE_READONLY_REACHABILITY = (
    "I_ACCEPT_ARCHIVE_FUTURES_PRIVATE_READONLY_REACHABILITY_MANUAL_EXECUTE"
)

FUTURES_PRIVATE_API_AUTHORIZED = False
PRIVATE_READONLY_EXECUTE_AUTHORIZED_NOW = False
PRIVATE_READONLY_NETWORK_AUTHORIZED_NOW = False

_REDACTED_NETWORK_CALL_KEYS = frozenset(
    {
        "endpoint",
        "http_method",
        "http_status",
        "http_status_class",
        "response_size_bytes",
        "response_sha256",
        "response_redacted",
        "parsed_summary",
        "auth_header_names",
        "credential_values_logged",
    }
)

_SENSITIVE_JSON_KEY_FRAGMENTS: tuple[str, ...] = (
    "balance",
    "available",
    "margin",
    "pnl",
    "position",
    "order",
    "account",
    "wallet",
    "key",
    "secret",
    "authent",
)


@dataclass(frozen=True)
class PrivateReadonlyHttpRequest:
    """Transport-ready GET request; header values must never appear in evidence."""

    method: str
    url: str
    endpoint_path: str
    headers: dict[str, str]
    auth_header_names: tuple[str, ...]


@dataclass(frozen=True)
class PrivateReadonlyReachabilityResult:
    endpoints_called: list[str]
    request_count: int
    network_calls: list[dict[str, Any]]
    private_readonly_reachability_proven: bool
    fetch_failure: bool = False
    failure_class: str | None = None
    failed_endpoint: str | None = None
    failed_method: str = "GET"
    failed_host: str = DEMO_FUTURES_HOST
    request_count_attempted: int = 0
    completed_request_count: int = 0
    exception_type: str | None = None
    partial_policy_accepted: bool = False


class PrivateReadonlyRestFetcher(Protocol):
    def fetch(
        self,
        http_request: PrivateReadonlyHttpRequest,
        *,
        timeout_seconds: float,
    ) -> tuple[int, bytes]:
        """Return HTTP status and body bytes (caller redacts before evidence)."""


def assert_private_readonly_authority_unchanged() -> None:
    """Defense-in-depth: module must not flip authorization flags."""
    if FUTURES_SESSION_AUTHORIZED_NOW:
        raise RuntimeError("FUTURES_SESSION_AUTHORIZED_NOW must remain false")
    if FUTURES_PRIVATE_API_AUTHORIZED:
        raise RuntimeError("FUTURES_PRIVATE_API_AUTHORIZED must remain false")
    if PRIVATE_READONLY_EXECUTE_AUTHORIZED_NOW:
        raise RuntimeError("PRIVATE_READONLY_EXECUTE_AUTHORIZED_NOW must remain false")
    if PRIVATE_READONLY_NETWORK_AUTHORIZED_NOW:
        raise RuntimeError("PRIVATE_READONLY_NETWORK_AUTHORIZED_NOW must remain false")


def path_contains_forbidden_substring(path: str) -> str | None:
    lowered = path.lower()
    for frag in FUTURES_PRIVATE_READONLY_FORBIDDEN_PATH_SUBSTRINGS:
        if frag in lowered:
            return frag
    return None


def validate_private_readonly_endpoint_path(path: str) -> list[str]:
    """Fail-closed path validation for private-readonly stage."""
    reasons: list[str] = []
    if not path.startswith("/derivatives/api/v3/"):
        reasons.append(f"path must be under /derivatives/api/v3/: {path!r}")
    forbidden = path_contains_forbidden_substring(path)
    if forbidden:
        reasons.append(f"forbidden path substring: {forbidden}")
    if path in FUTURES_ORDER_MUTATION_ENDPOINTS:
        reasons.append(f"order/mutation endpoint forbidden: {path}")
    if path in SPOT_KRAKEN_ENDPOINT_PREFIXES:
        reasons.append(f"spot endpoint forbidden: {path}")
    if path not in FUTURES_TESTNET_ENDPOINT_ALLOWLIST:
        reasons.append(f"path not on futures adapter allowlist: {path}")
    if path not in FUTURES_PRIVATE_READONLY_GET_ENDPOINTS:
        reasons.append(f"path not on private-readonly GET allowlist: {path}")
    return reasons


def validate_private_readonly_http_method(method: str) -> list[str]:
    normalized = method.strip().upper()
    if normalized not in ALLOWED_HTTP_METHODS_PRIVATE_READONLY:
        return [f"http method {method!r} forbidden; only GET allowed"]
    return []


def validate_private_readonly_rest_base_url(rest_base: str) -> list[str]:
    reasons: list[str] = []
    parsed = urlparse(rest_base)
    if parsed.scheme != "https":
        reasons.append("rest_base_url must use https")
    if parsed.netloc != DEMO_FUTURES_HOST:
        reasons.append(f"rest_base_url host must be {DEMO_FUTURES_HOST!r}")
    path = (parsed.path or "").rstrip("/")
    if path != "/derivatives/api/v3":
        reasons.append("rest_base_url path must be /derivatives/api/v3")
    for prefix in LIVE_FUTURES_HOST_PREFIXES:
        if rest_base.startswith(prefix):
            reasons.append(f"live host forbidden: {prefix}")
    if rest_base.startswith("https://api.kraken.com"):
        reasons.append("spot kraken.com host forbidden")
    return reasons


def compute_futures_private_authent(
    *,
    api_secret_b64: str,
    endpoint_path: str,
    post_data: str = "",
    nonce: str = "",
) -> str:
    """Kraken Futures v3 Authent (offline helper; secret must not be logged)."""
    sha = hashlib.sha256()
    sha.update(post_data.encode())
    sha.update(nonce.encode())
    sha.update(endpoint_path.encode())
    digest = sha.digest()
    secret = base64.b64decode(api_secret_b64)
    sig = hmac.new(secret, digest, hashlib.sha512).digest()
    return base64.b64encode(sig).decode().strip()


def _endpoint_path_suffix(full_path: str) -> str:
    if full_path.startswith("/derivatives/api/v3"):
        return full_path.split("/derivatives/api/v3", 1)[-1] or ""
    return full_path


def build_private_readonly_get_url(rest_base_url: str, endpoint_path: str) -> str:
    reasons = validate_private_readonly_endpoint_path(endpoint_path)
    if reasons:
        raise ValueError(f"private-readonly endpoint not allowed: {'; '.join(reasons)}")
    suffix = _endpoint_path_suffix(endpoint_path)
    return f"{rest_base_url.rstrip('/')}{suffix}"


def build_private_readonly_http_request(
    *,
    rest_base_url: str,
    endpoint_path: str,
    api_key: str,
    api_secret_b64: str,
    nonce: str | None = None,
) -> PrivateReadonlyHttpRequest:
    """Build a single authenticated GET request (fail-closed on blocklisted paths)."""
    method_reasons = validate_private_readonly_http_method("GET")
    if method_reasons:
        raise ValueError(method_reasons[0])
    url = build_private_readonly_get_url(rest_base_url, endpoint_path)
    url_reasons = validate_private_readonly_url(url, rest_base_url=rest_base_url)
    if url_reasons:
        raise ValueError(url_reasons[0])
    nonce_value = nonce if nonce is not None else str(int(time.time() * 1000))
    sign_path = _endpoint_path_suffix(endpoint_path)
    authent = compute_futures_private_authent(
        api_secret_b64=api_secret_b64,
        endpoint_path=sign_path,
        post_data="",
        nonce=nonce_value,
    )
    headers = {
        "APIKey": api_key,
        "Authent": authent,
        "Nonce": nonce_value,
    }
    return PrivateReadonlyHttpRequest(
        method="GET",
        url=url,
        endpoint_path=endpoint_path,
        headers=headers,
        auth_header_names=("APIKey", "Authent", "Nonce"),
    )


def build_private_readonly_get_request_plan(
    *,
    rest_base_url: str = DEMO_FUTURES_REST_BASE_URL,
) -> list[dict[str, str]]:
    """Unauthenticated plan rows (method/url/endpoint only) for offline tests."""
    plan: list[dict[str, str]] = []
    for endpoint_path in PRIVATE_READONLY_ENDPOINT_ORDER:
        plan.append(
            {
                "method": "GET",
                "endpoint_path": endpoint_path,
                "url": build_private_readonly_get_url(rest_base_url, endpoint_path),
            }
        )
    return plan


def _parsed_summary_without_sensitive_values(payload: Any) -> dict[str, Any]:
    """Schema/count metadata only — never copy balances, positions, orders, or secrets."""
    summary: dict[str, Any] = {
        "top_level_type": "unknown",
        "record_count": None,
        "sensitive_field_names_detected": [],
        "raw_values_emitted": False,
    }
    if isinstance(payload, dict):
        summary["top_level_type"] = "object"
        summary["top_level_keys"] = sorted(str(k) for k in payload.keys())
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(frag in key_l for frag in _SENSITIVE_JSON_KEY_FRAGMENTS):
                summary["sensitive_field_names_detected"].append(str(key))
            if isinstance(value, list):
                summary["record_count"] = len(value)
    elif isinstance(payload, list):
        summary["top_level_type"] = "array"
        summary["record_count"] = len(payload)
    else:
        summary["top_level_type"] = type(payload).__name__
    summary["sensitive_field_names_detected"] = sorted(
        set(summary.get("sensitive_field_names_detected", []))
    )
    return summary


def validate_private_readonly_url(url: str, *, rest_base_url: str) -> list[str]:
    reasons: list[str] = []
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != DEMO_FUTURES_HOST:
        reasons.append(f"network host not allowlisted: {url}")
    for prefix in LIVE_FUTURES_HOST_PREFIXES:
        if url.startswith(prefix):
            reasons.append(f"forbidden host prefix: {prefix}")
    if not url.startswith(rest_base_url.rstrip("/")):
        reasons.append("url must be under rest-base-url")
    path = parsed.path or ""
    reasons.extend(validate_private_readonly_endpoint_path(path))
    return reasons


def summarize_private_response_for_evidence(
    *,
    endpoint: str,
    http_status: int,
    body: bytes,
    http_method: str = "GET",
    auth_header_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Redacted network call metadata — no raw body, balances, positions, orders, or secrets."""
    parsed_summary: dict[str, Any] = {
        "top_level_type": "unparseable",
        "record_count": None,
        "sensitive_field_names_detected": [],
        "raw_values_emitted": False,
    }
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        else:
            parsed_summary = _parsed_summary_without_sensitive_values(payload)
    record = {
        "endpoint": endpoint,
        "http_method": http_method,
        "http_status": http_status,
        "http_status_class": _http_status_class(http_status),
        "response_size_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "response_redacted": True,
        "parsed_summary": parsed_summary,
        "auth_header_names": list(auth_header_names or ()),
        "credential_values_logged": False,
    }
    return record


def _is_private_readonly_fetch_exception(exc: BaseException) -> bool:
    return isinstance(exc, (TimeoutError, error.URLError, socket.timeout))


def build_private_readonly_fetch_failure_network_record(
    *,
    endpoint: str,
    auth_header_names: Sequence[str],
) -> dict[str, Any]:
    """Redacted failure row when fetch raises before HTTP response (no secrets)."""
    record = {
        "endpoint": endpoint,
        "http_method": "GET",
        "http_status": 0,
        "http_status_class": "unknown",
        "response_size_bytes": 0,
        "response_sha256": hashlib.sha256(b"").hexdigest(),
        "response_redacted": True,
        "parsed_summary": {
            "top_level_type": "fetch_exception",
            "record_count": None,
            "sensitive_field_names_detected": [],
            "raw_values_emitted": False,
        },
        "auth_header_names": list(auth_header_names),
        "credential_values_logged": False,
    }
    redact_reasons = validate_redacted_network_call_record(record)
    if redact_reasons:
        raise RuntimeError(
            f"private-readonly failure evidence redaction failed: {'; '.join(redact_reasons)}"
        )
    return record


def run_private_readonly_reachability(
    *,
    rest_base_url: str,
    api_key: str,
    api_secret_b64: str,
    fetcher: PrivateReadonlyRestFetcher,
    duration_cap_seconds: int,
) -> PrivateReadonlyReachabilityResult:
    """Execute bounded private-readonly GET sequence via injectable fetcher."""
    assert_private_readonly_authority_unchanged()
    endpoints_called: list[str] = []
    network_calls: list[dict[str, Any]] = []
    deadline = time.monotonic() + float(duration_cap_seconds)
    timeout = min(
        DEFAULT_PRIVATE_READONLY_GET_TIMEOUT_SECONDS,
        float(duration_cap_seconds),
    )
    for endpoint_path in PRIVATE_READONLY_ENDPOINT_ORDER:
        if time.monotonic() > deadline:
            break
        http_request = build_private_readonly_http_request(
            rest_base_url=rest_base_url,
            endpoint_path=endpoint_path,
            api_key=api_key,
            api_secret_b64=api_secret_b64,
        )
        try:
            status, body = fetcher.fetch(http_request, timeout_seconds=timeout)
        except BaseException as exc:
            if not _is_private_readonly_fetch_exception(exc):
                raise
            attempted = len(endpoints_called) + 1
            failure_record = build_private_readonly_fetch_failure_network_record(
                endpoint=endpoint_path,
                auth_header_names=http_request.auth_header_names,
            )
            return PrivateReadonlyReachabilityResult(
                endpoints_called=list(endpoints_called),
                request_count=len(endpoints_called),
                network_calls=network_calls + [failure_record],
                private_readonly_reachability_proven=False,
                fetch_failure=True,
                failure_class=FETCH_FAILURE_CLASS_NETWORK,
                failed_endpoint=endpoint_path,
                failed_method=http_request.method,
                failed_host=DEMO_FUTURES_HOST,
                request_count_attempted=attempted,
                completed_request_count=len(endpoints_called),
                exception_type=type(exc).__name__,
                partial_policy_accepted=True,
            )
        record = summarize_private_response_for_evidence(
            endpoint=endpoint_path,
            http_status=status,
            body=body,
            http_method=http_request.method,
            auth_header_names=http_request.auth_header_names,
        )
        redact_reasons = validate_redacted_network_call_record(record)
        if redact_reasons:
            raise RuntimeError(
                f"private-readonly evidence redaction failed: {'; '.join(redact_reasons)}"
            )
        network_calls.append(record)
        endpoints_called.append(endpoint_path)
    proven = bool(endpoints_called) and all(
        200 <= int(call["http_status"]) < 300 for call in network_calls
    )
    completed = len(endpoints_called)
    return PrivateReadonlyReachabilityResult(
        endpoints_called=endpoints_called,
        request_count=completed,
        network_calls=network_calls,
        private_readonly_reachability_proven=proven,
        request_count_attempted=completed,
        completed_request_count=completed,
    )


def resolve_private_readonly_credentials_from_environ(
    environ: Mapping[str, str],
) -> tuple[str, str] | None:
    """Read demo key names from environ only (never log values; no env-file I/O)."""
    api_key = (environ.get(KRAKEN_FUTURES_DEMO_API_KEY_ENV_NAME) or "").strip()
    api_secret = (environ.get(KRAKEN_FUTURES_DEMO_API_SECRET_ENV_NAME) or "").strip()
    if api_key and api_secret:
        return api_key, api_secret
    return None


def _http_status_class(status: int) -> str:
    if 200 <= status < 300:
        return "2xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def validate_redacted_network_call_record(record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    extra = set(record.keys()) - _REDACTED_NETWORK_CALL_KEYS
    if extra:
        reasons.append(f"unexpected network call keys: {sorted(extra)}")
    if not record.get("response_redacted"):
        reasons.append("response_redacted must be true")
    if "response_body" in record or "raw_response" in record:
        reasons.append("raw response body forbidden in evidence")
    summary = record.get("parsed_summary")
    if isinstance(summary, dict) and summary.get("raw_values_emitted"):
        reasons.append("raw_values_emitted must be false")
    if isinstance(summary, dict) and summary.get("order_id_fields_present"):
        reasons.append("order id fields must not be copied into evidence summary")
    return reasons


def build_private_readonly_checker_boundary() -> dict[str, Any]:
    boundary = build_checker_boundary_v0()
    boundary["private_readonly_harness_mode"] = PRIVATE_READONLY_MODE
    boundary["credential_presence_implies_execute"] = False
    return boundary


def build_private_readonly_plan_evidence_skeleton(
    *,
    run_id: str,
    rest_base_url: str = DEMO_FUTURES_REST_BASE_URL,
) -> dict[str, Any]:
    """Plan-only evidence template (no network, no credentials)."""
    assert_private_readonly_authority_unchanged()
    return {
        "session_class": PRIVATE_READONLY_SESSION_CLASS,
        "order_policy": DEFAULT_ORDER_POLICY,
        "instrument": DEFAULT_INSTRUMENT,
        "market_type": DEFAULT_MARKET_TYPE,
        "margin_mode": DEFAULT_MARGIN_MODE,
        "max_leverage": 5.0,
        "leverage_within_cap": True,
        "position_mode": DEFAULT_POSITION_MODE,
        "order_side_semantics": "long",
        "reduce_only_supported": True,
        "order_attempt_count": 0,
        "real_orders_created_count": 0,
        "cancel_or_close_attempt_count": 0,
        "order_notional_eur": 0.0,
        "order_notional_within_cap": True,
        "position_flattened_by_end": True,
        "cancel_or_close_evidence_valid": True,
        "futures_endpoint_isolation_pass": True,
        "spot_endpoint_isolation_pass": True,
        "funding_risk_acknowledged": True,
        "liquidation_risk_acknowledged": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "master_v2_double_play_authority_used": False,
        "endpoints_called": [],
        "network_host": DEFAULT_FUTURES_TESTNET_NETWORK_HOST,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
        "futures_session_authorized_now": False,
        "futures_private_api_authorized": False,
        "order_attempted": False,
        "order_created": False,
        "fills": 0,
        "positions_changed": False,
        "credential_values_logged": False,
        "credential_values_read": False,
        "evidence_source": EVIDENCE_SOURCE_FUTURES_HARNESS,
        "harness_mode": PRIVATE_READONLY_MODE,
        "run_id": run_id,
        "request_count": 0,
        "private_readonly_reachability_proven": False,
        "network_private_readonly_proven": False,
        "network_target_allowlist": sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS),
        "network_calls": [],
        "manifest_verification_expected": True,
        "checker_boundary_v0": build_private_readonly_checker_boundary(),
        "private_readonly_http_wiring_present": PRIVATE_READONLY_HTTP_WIRING_PRESENT,
        "private_readonly_execute_wired": True,
    }


def build_private_readonly_evidence_from_network(
    *,
    timing: Any,
    run_id: str,
    result: PrivateReadonlyReachabilityResult,
    pe8_pass: bool,
    harness_version: str,
) -> dict[str, Any]:
    evidence = build_private_readonly_plan_evidence_skeleton(run_id=run_id)
    policy_accepted = (
        result.private_readonly_reachability_proven and not result.fetch_failure
    )
    updates: dict[str, Any] = {
        "harness_version": harness_version,
        "monotonic_elapsed_seconds": timing.monotonic_elapsed_seconds,
        "wall_clock_elapsed_seconds": timing.wall_clock_elapsed_seconds,
        "wall_clock_start_utc": timing.wall_clock_start_utc,
        "wall_clock_end_utc": timing.wall_clock_end_utc,
        "bounded_futures_testnet_pass": pe8_pass,
        "endpoints_called": list(result.endpoints_called),
        "request_count": result.request_count,
        "network_calls": list(result.network_calls),
        "private_readonly_reachability_proven": result.private_readonly_reachability_proven,
        "network_private_readonly_proven": result.private_readonly_reachability_proven,
        "private_readonly_policy_accepted": policy_accepted,
        "request_count_attempted": result.request_count_attempted,
        "completed_request_count": result.completed_request_count,
        "order_attempted": False,
        "order_created": False,
        "position_mutation_attempted": False,
        "balance_mutation_attempted": False,
    }
    if result.fetch_failure:
        updates.update(
            {
                "fetch_failure": True,
                "failure_class": result.failure_class,
                "failed_endpoint": result.failed_endpoint,
                "failed_method": result.failed_method,
                "failed_host": result.failed_host,
                "exception_type": result.exception_type,
                "partial_policy_accepted": result.partial_policy_accepted,
                "private_readonly_policy_accepted": False,
                "http_status_unknown": True,
            }
        )
    evidence.update(updates)
    return evidence


def evaluate_private_readonly_policy(
    *,
    endpoints_called: list[str] | None = None,
    http_methods: list[str] | None = None,
    rest_base_url: str = DEMO_FUTURES_REST_BASE_URL,
) -> dict[str, Any]:
    """Offline policy evaluation for allowlist/blocklist."""
    result: dict[str, Any] = {
        "private_readonly_policy_pass": False,
        "allowlist_exact_match": False,
        "post_blocked": True,
        "order_endpoints_blocked": True,
        "live_host_blocked": True,
        "demo_host_only": True,
        "fail_reasons": [],
    }
    result["fail_reasons"].extend(validate_private_readonly_rest_base_url(rest_base_url))

    methods = http_methods or ["GET"]
    for method in methods:
        result["fail_reasons"].extend(validate_private_readonly_http_method(method))
    result["post_blocked"] = all(m.strip().upper() == "GET" for m in methods)

    eps = endpoints_called or []
    if eps:
        if set(eps) - FUTURES_PRIVATE_READONLY_GET_ENDPOINTS:
            result["fail_reasons"].append("endpoints_called outside private-readonly allowlist")
        for ep in eps:
            result["fail_reasons"].extend(validate_private_readonly_endpoint_path(ep))
    else:
        result["allowlist_exact_match"] = True

    for order_ep in FUTURES_ORDER_MUTATION_ENDPOINTS:
        if order_ep in eps:
            result["fail_reasons"].append(f"order endpoint must remain blocked: {order_ep}")
            result["order_endpoints_blocked"] = False

    result["allowlist_exact_match"] = (
        bool(eps) and set(eps) <= FUTURES_PRIVATE_READONLY_GET_ENDPOINTS
    ) or not eps
    result["demo_host_only"] = not any(
        r for r in result["fail_reasons"] if "host" in r and "demo-futures" not in r
    )
    result["private_readonly_policy_pass"] = not result["fail_reasons"]
    return result
