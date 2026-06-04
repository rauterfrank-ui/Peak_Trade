"""Kraken Futures Demo private-readonly reachability contract (v0).

Offline policy for private_readonly_reachability_only harness mode: GET allowlist,
order/host blocklist, response redaction rules. Does not authorize network, private
API execute, credentials read, or orders.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
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
PRIVATE_READONLY_MODE = "private_readonly_reachability_only"
PRIVATE_READONLY_SESSION_CLASS = "bounded-futures-private-readonly-reachability-v0"
PRIVATE_READONLY_MAX_REQUEST_COUNT = 3

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
        "http_status",
        "http_status_class",
        "response_size_bytes",
        "response_sha256",
        "response_redacted",
        "parsed_summary",
    }
)


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
) -> dict[str, Any]:
    """Redacted network call metadata — no raw body, balances, or order ids."""
    parsed_summary: dict[str, Any] = {
        "top_level_type": "unknown",
        "record_count": None,
        "order_id_fields_present": False,
    }
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed_summary["top_level_type"] = "unparseable"
        else:
            if isinstance(payload, dict):
                parsed_summary["top_level_type"] = "object"
                parsed_summary["top_level_keys"] = sorted(str(k) for k in payload.keys())
                for key in ("accounts", "openPositions", "openOrders", "positions", "orders"):
                    if key in payload and isinstance(payload[key], list):
                        parsed_summary["record_count"] = len(payload[key])
                dump = json.dumps(payload)
                if re.search(r'"order[_-]?id"', dump, re.IGNORECASE):
                    parsed_summary["order_id_fields_present"] = True
            elif isinstance(payload, list):
                parsed_summary["top_level_type"] = "array"
                parsed_summary["record_count"] = len(payload)
    return {
        "endpoint": endpoint,
        "http_status": http_status,
        "http_status_class": _http_status_class(http_status),
        "response_size_bytes": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "response_redacted": True,
        "parsed_summary": parsed_summary,
    }


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
    }


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
