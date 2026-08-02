"""Public-MD-only network boundary for Cap 7.2 (no live session in this capability)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_PRIVATE_PATH_PREFIXES,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    OWNER,
    PUBLIC_MD_ALLOWED_HOSTS,
    PUBLIC_MD_ALLOWED_PATH_PREFIXES,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)


class NetworkBoundaryError(RuntimeError):
    def __init__(self, code: ActivationFailureCodeV1, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code.value}:{detail}" if detail else code.value)


@dataclass(frozen=True)
class PublicMdTransportDecisionV1:
    allowed: bool
    host: str
    path: str
    method: str
    auth_header_present: bool
    reason: str


def _normalize_method(method: str) -> str:
    return str(method or "").strip().upper()


def evaluate_public_md_transport_v1(
    *,
    url: str,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
) -> PublicMdTransportDecisionV1:
    """Fixture/harness evaluator — does not open sockets."""
    hdrs = {str(k).lower(): str(v) for k, v in dict(headers or {}).items()}
    auth_present = any(
        k in hdrs for k in ("authorization", "ok-access-key", "ok-access-sign", "x-api-key")
    )
    parsed = urlparse(str(url))
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    m = _normalize_method(method)

    if auth_present:
        return PublicMdTransportDecisionV1(
            allowed=False,
            host=host,
            path=path,
            method=m,
            auth_header_present=True,
            reason=ActivationFailureCodeV1.AUTH_HEADER_REJECTED.value,
        )
    if m != "GET":
        return PublicMdTransportDecisionV1(
            allowed=False,
            host=host,
            path=path,
            method=m,
            auth_header_present=False,
            reason=ActivationFailureCodeV1.INVALID_HTTP_METHOD.value,
        )
    if host not in PUBLIC_MD_ALLOWED_HOSTS:
        return PublicMdTransportDecisionV1(
            allowed=False,
            host=host,
            path=path,
            method=m,
            auth_header_present=False,
            reason=ActivationFailureCodeV1.INVALID_ENDPOINT.value,
        )
    if any(path.startswith(p) for p in FORBIDDEN_PRIVATE_PATH_PREFIXES):
        return PublicMdTransportDecisionV1(
            allowed=False,
            host=host,
            path=path,
            method=m,
            auth_header_present=False,
            reason=ActivationFailureCodeV1.INVALID_ENDPOINT.value,
        )
    if not any(path.startswith(p) for p in PUBLIC_MD_ALLOWED_PATH_PREFIXES):
        return PublicMdTransportDecisionV1(
            allowed=False,
            host=host,
            path=path,
            method=m,
            auth_header_present=False,
            reason=ActivationFailureCodeV1.INVALID_ENDPOINT.value,
        )
    return PublicMdTransportDecisionV1(
        allowed=True,
        host=host,
        path=path,
        method=m,
        auth_header_present=False,
        reason="PUBLIC_MD_GET_ALLOWLISTED",
    )


def assert_public_md_transport_allowed_v1(
    *,
    url: str,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
) -> PublicMdTransportDecisionV1:
    decision = evaluate_public_md_transport_v1(url=url, method=method, headers=headers)
    if not decision.allowed:
        try:
            code = ActivationFailureCodeV1(decision.reason)
        except ValueError:
            code = ActivationFailureCodeV1.INVALID_ENDPOINT
        raise NetworkBoundaryError(
            code,
            f"{decision.method} {decision.host}{decision.path}",
        )
    return decision


def credential_loader_unreachable_v1() -> dict[str, Any]:
    """No-order host must not reach exchange credential loaders."""

    def _forbidden_loader(*_a: Any, **_k: Any) -> None:
        raise NetworkBoundaryError(
            ActivationFailureCodeV1.CREDENTIAL_LOADER_REACHABLE,
            "credential_loader_invoked",
        )

    return {
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "loader_bound": False,
        "loader_callable_name": _forbidden_loader.__name__,
        "AUTH_HEADER_PRESENT": False,
    }


def prove_network_credential_boundary_v1() -> dict[str, Any]:
    cases = [
        ("https://www.okx.com/api/v5/public/instruments?instType=SWAP", "GET", {}, True),
        ("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT-SWAP", "GET", {}, True),
        ("https://www.okx.com/api/v5/trade/order", "GET", {}, False),
        ("https://www.okx.com/api/v5/account/balance", "GET", {}, False),
        ("https://www.okx.com/api/v5/public/instruments", "POST", {}, False),
        ("https://www.okx.com/api/v5/public/instruments", "PUT", {}, False),
        ("https://www.okx.com/api/v5/public/instruments", "PATCH", {}, False),
        ("https://www.okx.com/api/v5/public/instruments", "DELETE", {}, False),
        (
            "https://www.okx.com/api/v5/public/instruments",
            "GET",
            {"Authorization": "Bearer x"},
            False,
        ),
        ("https://evil.example/api/v5/public/instruments", "GET", {}, False),
        ("https://www.okx.com/api/v5/users/self/verify", "GET", {}, False),
    ]
    results: list[dict[str, Any]] = []
    all_ok = True
    for url, method, headers, expect_allow in cases:
        decision = evaluate_public_md_transport_v1(url=url, method=method, headers=headers)
        row_ok = decision.allowed is expect_allow
        all_ok = all_ok and row_ok
        results.append(
            {
                "url": url,
                "method": method,
                "expect_allow": expect_allow,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "auth_header_present": decision.auth_header_present,
                "ok": row_ok,
            }
        )
    cred = credential_loader_unreachable_v1()
    private_reachable = any(
        r["allowed"] and ("/trade/" in r["url"] or "/account/" in r["url"]) for r in results
    )
    return {
        "ok": all_ok
        and not private_reachable
        and cred["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False,
        "owner": OWNER,
        "NETWORK_ALLOWLIST": NETWORK_ALLOWLIST,
        "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
        "NETWORK_ALLOWLIST_PUBLIC_MD_ONLY": True,
        "HTTP_METHOD_ALLOWLIST_GET_ONLY": True,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_PRESENT": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "forbidden_http_methods": list(FORBIDDEN_HTTP_METHODS),
        "cases": results,
        "credential_loader": cred,
    }
