"""Fail-closed OKX Global Demo venue/host/account/instrument binding contract.

Offline evaluation only. Never loads credentials, never opens network
sessions, never posts orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_okx_global_demo_venue_host_account_instrument_binding_v1.constants_v1 import (
    ACCOUNT_IDENTITY_PLACEHOLDER,
    CREDENTIAL_CLASS,
    DEMO_MARKER_HEADER_NAME,
    DEMO_MARKER_HEADER_VALUE,
    EEA_CREDENTIAL_CLASS_MARKERS,
    ENVIRONMENT,
    FORBIDDEN_HOST_FALLBACKS,
    FORBIDDEN_INSTRUMENT_SUBSTITUTIONS,
    FORBIDDEN_VENUE_FALLBACKS,
    INSTRUMENT_SCOPE_EXACT,
    INSTRUMENT_TYPE,
    LIVE_CREDENTIAL_CLASS_MARKERS,
    ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED,
    ORDER_POST_AUTHORIZED,
    PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER,
    REST_BASE,
    REST_HOST,
    RUNTIME_MODE,
    SECRET_REFERENCE,
    VENUE,
)


class OkxGlobalDemoBindingError(RuntimeError):
    """Fail-closed binding violation."""


@dataclass(frozen=True)
class OkxGlobalDemoBindingV1:
    venue: str
    environment: str
    runtime_mode: str
    rest_host: str
    rest_base: str
    demo_marker_header_name: str
    demo_marker_header_value: str
    instrument_scope_exact: str
    instrument_type: str
    credential_class: str
    secret_reference: str
    account_identity: str
    order_post_authorized: bool
    network_session_authorized: bool
    venue_activated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "environment": self.environment,
            "runtime_mode": self.runtime_mode,
            "rest_host": self.rest_host,
            "rest_base": self.rest_base,
            "demo_marker_header_name": self.demo_marker_header_name,
            "demo_marker_header_value": self.demo_marker_header_value,
            "instrument_scope_exact": self.instrument_scope_exact,
            "instrument_type": self.instrument_type,
            "credential_class": self.credential_class,
            "secret_reference": self.secret_reference,
            "account_identity": self.account_identity,
            "order_post_authorized": self.order_post_authorized,
            "network_session_authorized": self.network_session_authorized,
            "venue_activated": self.venue_activated,
            "plaintext_exposed": False,
        }


def _normalize_host(rest_base_or_host: str) -> str:
    raw = str(rest_base_or_host or "").strip().lower()
    if not raw:
        raise OkxGlobalDemoBindingError("REST_HOST_REQUIRED")
    if "://" in raw:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
    else:
        host = raw.split("/")[0]
    if not host:
        raise OkxGlobalDemoBindingError("REST_HOST_UNPARSEABLE")
    return host


def _assert_secretref_only(secret_reference: str) -> None:
    ref = str(secret_reference or "").strip()
    if not ref.startswith("secretref://"):
        raise OkxGlobalDemoBindingError("SECRETREF_ONLY_REQUIRED")
    if ref.startswith("plaintext:") or ref.startswith("sk-"):
        raise OkxGlobalDemoBindingError("PLAINTEXT_SECRET_FORBIDDEN")


def _assert_demo_header(
    *,
    header_name: str | None,
    header_value: str | None,
    headers: Mapping[str, str] | None,
) -> None:
    name = (header_name or DEMO_MARKER_HEADER_NAME).strip().lower()
    value = str(header_value if header_value is not None else "").strip()
    if headers is not None:
        # Prefer explicit headers map when provided (empty map = missing header).
        matched = None
        for key, val in headers.items():
            if str(key).strip().lower() == DEMO_MARKER_HEADER_NAME:
                matched = str(val).strip()
                break
        if matched is None:
            raise OkxGlobalDemoBindingError("DEMO_MARKER_HEADER_MISSING")
        value = matched
        name = DEMO_MARKER_HEADER_NAME
    if name != DEMO_MARKER_HEADER_NAME:
        raise OkxGlobalDemoBindingError("DEMO_MARKER_HEADER_NAME_MISMATCH")
    if value != DEMO_MARKER_HEADER_VALUE:
        raise OkxGlobalDemoBindingError("DEMO_MARKER_HEADER_VALUE_MISMATCH")


def _assert_credential_class(credential_class: str) -> None:
    klass = str(credential_class or "").strip()
    if not klass:
        raise OkxGlobalDemoBindingError("CREDENTIAL_CLASS_REQUIRED")
    upper = klass.upper()
    for marker in LIVE_CREDENTIAL_CLASS_MARKERS:
        if marker.upper() in upper or upper == marker.upper():
            raise OkxGlobalDemoBindingError("LIVE_CREDENTIAL_CLASS_HARD_BLOCK")
    for marker in EEA_CREDENTIAL_CLASS_MARKERS:
        if marker.upper() in upper or upper == marker.upper():
            raise OkxGlobalDemoBindingError("EEA_CREDENTIAL_CLASS_HARD_BLOCK")
    if klass != CREDENTIAL_CLASS:
        raise OkxGlobalDemoBindingError("DEMO_CREDENTIAL_CLASS_REQUIRED")


def _assert_instrument(*, instrument: str, instrument_type: str) -> None:
    inst = str(instrument or "").strip()
    itype = str(instrument_type or "").strip()
    if not inst:
        raise OkxGlobalDemoBindingError("INSTRUMENT_REQUIRED")
    if inst in FORBIDDEN_INSTRUMENT_SUBSTITUTIONS:
        raise OkxGlobalDemoBindingError("GENERIC_OR_ALTERNATE_SYMBOL_SUBSTITUTION_FORBIDDEN")
    if inst != INSTRUMENT_SCOPE_EXACT:
        raise OkxGlobalDemoBindingError("EXACT_INSTRUMENT_SCOPE_REQUIRED")
    if itype != INSTRUMENT_TYPE:
        raise OkxGlobalDemoBindingError("INSTRUMENT_TYPE_MISMATCH")


def _assert_venue_environment_mode(*, venue: str, environment: str, runtime_mode: str) -> None:
    if str(venue or "").strip() != VENUE:
        if str(venue or "").strip() in FORBIDDEN_VENUE_FALLBACKS:
            raise OkxGlobalDemoBindingError("SILENT_VENUE_FALLBACK_FORBIDDEN")
        raise OkxGlobalDemoBindingError("VENUE_MISMATCH")
    if str(environment or "").strip() != ENVIRONMENT:
        raise OkxGlobalDemoBindingError("ENVIRONMENT_MISMATCH_FAIL_CLOSED")
    if str(runtime_mode or "").strip() != RUNTIME_MODE:
        raise OkxGlobalDemoBindingError("RUNTIME_MODE_MISMATCH_FAIL_CLOSED")


def _assert_host(rest_base_or_host: str) -> str:
    host = _normalize_host(rest_base_or_host)
    if host in FORBIDDEN_HOST_FALLBACKS:
        raise OkxGlobalDemoBindingError(f"SILENT_HOST_FALLBACK_FORBIDDEN:{host}")
    if any(marker in host for marker in ("live", "prod", "production", "mainnet")):
        raise OkxGlobalDemoBindingError(f"LIVE_HOST_HARD_BLOCK:{host}")
    if host != REST_HOST:
        raise OkxGlobalDemoBindingError(f"HOST_NOT_OKX_GLOBAL_DEMO_ALLOWLIST:{host}")
    return host


def assert_order_send_forbidden_v1(
    *, endpoint: str | None = None, order_post: bool = False
) -> None:
    if order_post or ORDER_POST_AUTHORIZED:
        raise OkxGlobalDemoBindingError("ORDER_POST_HARD_BLOCK_IN_BINDING_PACKAGE")
    if endpoint is None:
        return
    path = str(endpoint).strip()
    if path in ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED:
        raise OkxGlobalDemoBindingError(f"ORDER_MUTATION_ENDPOINT_HARD_BLOCK:{path}")
    if path and path not in PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER:
        # Unknown private endpoints also fail closed in this package.
        raise OkxGlobalDemoBindingError(f"ENDPOINT_NOT_IN_NO_ORDER_ALLOWLIST:{path}")


def evaluate_okx_global_demo_binding_v1(
    *,
    venue: str = VENUE,
    environment: str = ENVIRONMENT,
    runtime_mode: str = RUNTIME_MODE,
    rest_base: str = REST_BASE,
    demo_marker_header_name: str = DEMO_MARKER_HEADER_NAME,
    demo_marker_header_value: str = DEMO_MARKER_HEADER_VALUE,
    headers: Mapping[str, str] | None = None,
    instrument_scope_exact: str = INSTRUMENT_SCOPE_EXACT,
    instrument_type: str = INSTRUMENT_TYPE,
    credential_class: str = CREDENTIAL_CLASS,
    secret_reference: str = SECRET_REFERENCE,
    account_identity: str = ACCOUNT_IDENTITY_PLACEHOLDER,
    order_post_authorized: bool = False,
    network_session_authorized: bool = False,
    venue_activated: bool = False,
    live_mode: bool = False,
    live_account: bool = False,
) -> OkxGlobalDemoBindingV1:
    """Evaluate and return a fail-closed binding. Raises on any ambiguity."""
    if live_mode or live_account:
        raise OkxGlobalDemoBindingError("LIVE_MODE_OR_ACCOUNT_HARD_BLOCK")
    if order_post_authorized:
        raise OkxGlobalDemoBindingError("ORDER_POST_HARD_BLOCK_IN_BINDING_PACKAGE")
    if network_session_authorized:
        raise OkxGlobalDemoBindingError("NETWORK_SESSION_NOT_AUTHORIZED_IN_BINDING_PACKAGE")
    if venue_activated:
        raise OkxGlobalDemoBindingError("VENUE_ACTIVATION_FORBIDDEN_IN_BINDING_PACKAGE")

    _assert_venue_environment_mode(venue=venue, environment=environment, runtime_mode=runtime_mode)
    host = _assert_host(rest_base)
    _assert_demo_header(
        header_name=demo_marker_header_name,
        header_value=demo_marker_header_value,
        headers=headers,
    )
    _assert_credential_class(credential_class)
    _assert_instrument(instrument=instrument_scope_exact, instrument_type=instrument_type)
    _assert_secretref_only(secret_reference)
    identity = str(account_identity or "").strip()
    if not identity:
        raise OkxGlobalDemoBindingError("ACCOUNT_IDENTITY_REQUIRED")

    return OkxGlobalDemoBindingV1(
        venue=VENUE,
        environment=ENVIRONMENT,
        runtime_mode=RUNTIME_MODE,
        rest_host=host,
        rest_base=REST_BASE,
        demo_marker_header_name=DEMO_MARKER_HEADER_NAME,
        demo_marker_header_value=DEMO_MARKER_HEADER_VALUE,
        instrument_scope_exact=INSTRUMENT_SCOPE_EXACT,
        instrument_type=INSTRUMENT_TYPE,
        credential_class=CREDENTIAL_CLASS,
        secret_reference=secret_reference,
        account_identity=identity,
        order_post_authorized=False,
        network_session_authorized=False,
        venue_activated=False,
    )


def canonical_binding_headers_v1() -> dict[str, str]:
    """Return the mandatory Demo marker header map (no auth secrets)."""
    return {DEMO_MARKER_HEADER_NAME: DEMO_MARKER_HEADER_VALUE}


def default_canonical_binding_v1() -> OkxGlobalDemoBindingV1:
    return evaluate_okx_global_demo_binding_v1(headers=canonical_binding_headers_v1())
