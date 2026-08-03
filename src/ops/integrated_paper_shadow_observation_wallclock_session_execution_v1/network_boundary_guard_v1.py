"""HTTPS hostname/path/method/header allowlist for EEA public MD observe."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional
from urllib.parse import parse_qs, urlparse

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    ALLOWED_HEADERS,
    ALLOWED_METHODS,
    ALLOWED_PATHS,
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
)

NETWORK_BOUNDARY_GUARD_ID = "ops.paper_shadow_wallclock_network_boundary_guard_v1"

_FORBIDDEN_PATH_FRAGMENTS = frozenset(
    {"order", "position", "balance", "account", "algo", "rfq", "trade", "users"}
)
_FORBIDDEN_HEADER_PREFIXES = ("authorization", "ok-access-")
_FORBIDDEN_ENV_MARKERS = (
    "OKX_API_KEY",
    "OKX_SECRET",
    "OKX_PASSPHRASE",
    "OKX_ACCESS_KEY",
    "OKX_API_SECRET",
    "OKX_API_PASSPHRASE",
)
_ALLOWED_QUERY_KEYS = frozenset({"instid", "insttype", "uly", "instfamily"})
_FORBIDDEN_SCHEMES = frozenset({"http", "file", "ftp", "unix", "data", "javascript"})


class NetworkBoundaryError(ValueError):
    """Fail-closed network boundary violation."""


@dataclass
class NetworkBoundaryAttestationV1:
    ok: bool
    host: str = CANONICAL_HOST
    scheme: str = "https"
    blockers: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=lambda: sorted(ALLOWED_PATHS))
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assert_proxy_policy_fail_closed_v1(*, environ: Optional[Mapping[str, str]] = None) -> list[str]:
    """Fail-closed proxy / NO_PROXY policy (O1 expanded key set).

    Delegates to the canonical O1 owner so wallclock and OHLCV paths share one policy.
    """
    from src.ops.canonical_runtime_environment_contract_v1.preflight_v1 import (
        assert_proxy_and_no_proxy_policy_fail_closed_v1,
    )

    return assert_proxy_and_no_proxy_policy_fail_closed_v1(environ=environ)


def assert_no_okx_credentials_in_env_v1(
    *, environ: Optional[Mapping[str, str]] = None
) -> list[str]:
    env = environ if environ is not None else os.environ
    blockers: list[str] = []
    for key in env:
        upper = str(key).upper()
        if upper in _FORBIDDEN_ENV_MARKERS:
            blockers.append(f"CREDENTIAL_ENV_PRESENT:{upper}")
            continue
        if upper.startswith("OKX_") and any(
            frag in upper for frag in ("SECRET", "PASSPHRASE", "API_KEY", "ACCESS_KEY", "TOKEN")
        ):
            blockers.append(f"CREDENTIAL_ENV_PRESENT:{upper}")
    return blockers


def assert_headers_allowed_v1(headers: Mapping[str, str]) -> list[str]:
    blockers: list[str] = []
    for key, value in headers.items():
        key_l = str(key).strip().lower()
        if key_l.startswith(_FORBIDDEN_HEADER_PREFIXES) or key_l == "authorization":
            blockers.append(f"AUTH_HEADER_DETECTED:{key}")
        if key_l == "x-simulated-trading":
            blockers.append("X_SIMULATED_TRADING_FORBIDDEN")
        if key_l not in ALLOWED_HEADERS:
            blockers.append(f"HEADER_NOT_ALLOWED:{key}")
        if any(frag in str(value).lower() for frag in ("bearer ", "ok-access-", "sign=")):
            blockers.append("SENSITIVE_HEADER_VALUE")
    return blockers


def assert_method_allowed_v1(method: str) -> list[str]:
    m = str(method or "").strip().upper()
    if m not in ALLOWED_METHODS:
        return [f"METHOD_FORBIDDEN:{m}"]
    return []


def assert_url_allowed_v1(url: str) -> list[str]:
    blockers: list[str] = []
    parsed = urlparse(str(url or ""))
    scheme = (parsed.scheme or "").lower()
    if scheme != "https":
        blockers.append(f"SCHEME_FORBIDDEN:{parsed.scheme}")
        if scheme in _FORBIDDEN_SCHEMES:
            blockers.append(f"SCHEME_CLASS_FORBIDDEN:{scheme}")
    host = (parsed.hostname or "").lower()
    if host != CANONICAL_HOST:
        blockers.append(f"HOST_FORBIDDEN:{host or parsed.netloc}")
    if host in {"localhost", "127.0.0.1", "::1", "www.okx.com", "okx.com"}:
        blockers.append(f"HOST_CLASS_FORBIDDEN:{host}")
    if parsed.port not in (None, 443):
        blockers.append(f"PORT_FORBIDDEN:{parsed.port}")
    path = parsed.path or ""
    if path not in ALLOWED_PATHS:
        blockers.append(f"PATH_NOT_ALLOWED:{path}")
    path_l = path.lower()
    for frag in _FORBIDDEN_PATH_FRAGMENTS:
        if f"/{frag}" in path_l or path_l.endswith(frag):
            # allowlist paths already checked; extra fragments in non-allowlisted paths
            if path not in ALLOWED_PATHS:
                blockers.append(f"PATH_FRAGMENT_FORBIDDEN:{frag}")
    if parsed.username or parsed.password:
        blockers.append("URL_USERINFO_FORBIDDEN")
    if parsed.fragment:
        blockers.append("URL_FRAGMENT_FORBIDDEN")
    # Query binding checks
    qs = parse_qs(parsed.query, keep_blank_values=True)
    for key, values in qs.items():
        kl = key.lower()
        if kl not in _ALLOWED_QUERY_KEYS:
            blockers.append(f"QUERY_KEY_NOT_ALLOWED:{key}")
        if kl in {"apikey", "secret", "passphrase", "password", "token", "authorization", "sign"}:
            blockers.append(f"SENSITIVE_QUERY_FORBIDDEN:{key}")
        if kl == "instid":
            for v in values:
                if v != CANONICAL_INSTRUMENT_ID:
                    blockers.append(f"INSTRUMENT_QUERY_FORBIDDEN:{v}")
        if kl == "insttype":
            for v in values:
                if str(v).upper() != "FUTURES":
                    blockers.append(f"INSTTYPE_QUERY_FORBIDDEN:{v}")
    return sorted(set(blockers))


def validate_request_boundary_v1(
    *,
    url: str,
    method: str = "GET",
    headers: Optional[Mapping[str, str]] = None,
    body: Optional[bytes] = None,
    environ: Optional[Mapping[str, str]] = None,
    allow_proxy: bool = False,
) -> NetworkBoundaryAttestationV1:
    blockers: list[str] = []
    blockers.extend(assert_method_allowed_v1(method))
    blockers.extend(assert_url_allowed_v1(url))
    blockers.extend(assert_headers_allowed_v1(headers or {}))
    blockers.extend(assert_no_okx_credentials_in_env_v1(environ=environ))
    if not allow_proxy:
        blockers.extend(assert_proxy_policy_fail_closed_v1(environ=environ))
    if body:
        blockers.append("REQUEST_BODY_FORBIDDEN")
        text = body.decode("utf-8", errors="replace").lower()
        if any(x in text for x in ("ordertype", "clordid", "side", "sz", "placeorder")):
            blockers.append("ORDER_PAYLOAD_FORBIDDEN")
    ok = not blockers
    return NetworkBoundaryAttestationV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=[
            f"GUARD_ID={NETWORK_BOUNDARY_GUARD_ID}",
            "TLS_VERIFY_REQUIRED",
            "MAX_REDIRECTS=0",
            "PROXY_FAIL_CLOSED",
        ],
    )
