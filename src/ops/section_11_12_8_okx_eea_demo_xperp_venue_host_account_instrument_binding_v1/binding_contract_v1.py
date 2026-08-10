"""Fail-closed OKX EEA Demo XPerp venue/host/account/instrument binding contract.

Offline evaluation only. Never loads credentials, never opens network
sessions, never posts orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.constants_v1 import (
    ACCOUNT_IDENTITY_PLACEHOLDER,
    CREDENTIAL_CLASS,
    DEMO_MARKER_HEADER_NAME,
    DEMO_MARKER_HEADER_VALUE,
    ENVIRONMENT,
    FORBIDDEN_HOST_FALLBACKS,
    FORBIDDEN_INSTRUMENT_SUBSTITUTIONS,
    FORBIDDEN_VENUE_FALLBACKS,
    GLOBAL_CREDENTIAL_CLASS_MARKERS,
    INSTRUMENT_SCOPE_EXACT,
    INSTRUMENT_TYPE,
    LIVE_CREDENTIAL_CLASS_MARKERS,
    ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED,
    ORDER_POST_AUTHORIZED,
    PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER,
    REST_BASE,
    REST_HOST,
    RULE_TYPE,
    RUNTIME_MODE,
    SECRET_REFERENCE,
    VENUE,
)


class OkxEeaDemoXperpBindingError(RuntimeError):
    """Fail-closed binding violation."""


@dataclass(frozen=True)
class OkxEeaDemoXperpBindingV1:
    venue: str
    environment: str
    runtime_mode: str
    rest_host: str
    rest_base: str
    demo_marker_header_name: str
    demo_marker_header_value: str
    instrument_scope_exact: str
    instrument_type: str
    rule_type: str
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
            "rule_type": self.rule_type,
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
        raise OkxEeaDemoXperpBindingError("REST_HOST_REQUIRED")
    if "://" in raw:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
    else:
        host = raw.split("/")[0]
    if not host:
        raise OkxEeaDemoXperpBindingError("REST_HOST_UNPARSEABLE")
    return host


def _assert_secretref_only(secret_reference: str) -> None:
    ref = str(secret_reference or "").strip()
    if not ref.startswith("secretref://"):
        raise OkxEeaDemoXperpBindingError("SECRETREF_ONLY_REQUIRED")
    if ref.startswith("plaintext:") or ref.startswith("sk-"):
        raise OkxEeaDemoXperpBindingError("PLAINTEXT_SECRET_FORBIDDEN")


def _assert_demo_header(
    *,
    header_name: str | None,
    header_value: str | None,
    headers: Mapping[str, str] | None,
) -> None:
    name = (header_name or DEMO_MARKER_HEADER_NAME).strip().lower()
    value = str(header_value if header_value is not None else "").strip()
    if headers is not None:
        matched = None
        for key, val in headers.items():
            if str(key).strip().lower() == DEMO_MARKER_HEADER_NAME:
                matched = str(val).strip()
                break
        if matched is None:
            raise OkxEeaDemoXperpBindingError("DEMO_MARKER_HEADER_MISSING")
        value = matched
        name = DEMO_MARKER_HEADER_NAME
    if name != DEMO_MARKER_HEADER_NAME:
        raise OkxEeaDemoXperpBindingError("DEMO_MARKER_HEADER_NAME_MISMATCH")
    if value != DEMO_MARKER_HEADER_VALUE:
        raise OkxEeaDemoXperpBindingError("DEMO_MARKER_HEADER_VALUE_MISMATCH")


def _assert_credential_class(credential_class: str) -> None:
    klass = str(credential_class or "").strip()
    if not klass:
        raise OkxEeaDemoXperpBindingError("CREDENTIAL_CLASS_REQUIRED")
    upper = klass.upper()
    for marker in LIVE_CREDENTIAL_CLASS_MARKERS:
        if marker.upper() in upper or upper == marker.upper():
            raise OkxEeaDemoXperpBindingError("LIVE_CREDENTIAL_CLASS_HARD_BLOCK")
    for marker in GLOBAL_CREDENTIAL_CLASS_MARKERS:
        if marker.upper() in upper or upper == marker.upper():
            raise OkxEeaDemoXperpBindingError("GLOBAL_CREDENTIAL_CLASS_HARD_BLOCK")
    if klass != CREDENTIAL_CLASS:
        raise OkxEeaDemoXperpBindingError("EEA_DEMO_CREDENTIAL_CLASS_REQUIRED")


def _assert_instrument(*, instrument: str, instrument_type: str, rule_type: str) -> None:
    inst = str(instrument or "").strip()
    itype = str(instrument_type or "").strip()
    rtype = str(rule_type or "").strip()
    if not inst:
        raise OkxEeaDemoXperpBindingError("INSTRUMENT_REQUIRED")
    if inst in FORBIDDEN_INSTRUMENT_SUBSTITUTIONS:
        if inst == "BTC-USDT-SWAP":
            raise OkxEeaDemoXperpBindingError("LEGACY_BTC_USDT_SWAP_ACTIVE_BINDING_FORBIDDEN")
        raise OkxEeaDemoXperpBindingError("GENERIC_OR_ALTERNATE_SYMBOL_SUBSTITUTION_FORBIDDEN")
    if inst != INSTRUMENT_SCOPE_EXACT:
        raise OkxEeaDemoXperpBindingError("EXACT_INSTRUMENT_SCOPE_REQUIRED")
    if itype != INSTRUMENT_TYPE:
        raise OkxEeaDemoXperpBindingError("INSTRUMENT_TYPE_MISMATCH")
    if rtype != RULE_TYPE:
        raise OkxEeaDemoXperpBindingError("RULE_TYPE_MISMATCH")


def _assert_venue_environment_mode(*, venue: str, environment: str, runtime_mode: str) -> None:
    if str(venue or "").strip() != VENUE:
        if str(venue or "").strip() in FORBIDDEN_VENUE_FALLBACKS:
            raise OkxEeaDemoXperpBindingError("SILENT_VENUE_FALLBACK_FORBIDDEN")
        raise OkxEeaDemoXperpBindingError("VENUE_MISMATCH")
    if str(environment or "").strip() != ENVIRONMENT:
        raise OkxEeaDemoXperpBindingError("ENVIRONMENT_MISMATCH_FAIL_CLOSED")
    if str(runtime_mode or "").strip() != RUNTIME_MODE:
        raise OkxEeaDemoXperpBindingError("RUNTIME_MODE_MISMATCH_FAIL_CLOSED")


def _assert_host(rest_base_or_host: str) -> str:
    host = _normalize_host(rest_base_or_host)
    if host in FORBIDDEN_HOST_FALLBACKS:
        raise OkxEeaDemoXperpBindingError(f"SILENT_HOST_FALLBACK_FORBIDDEN:{host}")
    if any(marker in host for marker in ("live", "prod", "production", "mainnet")):
        raise OkxEeaDemoXperpBindingError(f"LIVE_HOST_HARD_BLOCK:{host}")
    if host != REST_HOST:
        raise OkxEeaDemoXperpBindingError(f"HOST_NOT_OKX_EEA_DEMO_ALLOWLIST:{host}")
    return host


def assert_order_send_forbidden_v1(
    *, endpoint: str | None = None, order_post: bool = False
) -> None:
    if order_post or ORDER_POST_AUTHORIZED:
        raise OkxEeaDemoXperpBindingError("ORDER_POST_HARD_BLOCK_IN_BINDING_PACKAGE")
    if endpoint is None:
        return
    path = str(endpoint).strip()
    if path in ORDER_MUTATION_ENDPOINTS_HARD_BLOCKED:
        raise OkxEeaDemoXperpBindingError(f"ORDER_MUTATION_ENDPOINT_HARD_BLOCK:{path}")
    if path and path not in PRIVATE_ENDPOINT_ALLOWLIST_NO_ORDER:
        raise OkxEeaDemoXperpBindingError(f"ENDPOINT_NOT_IN_NO_ORDER_ALLOWLIST:{path}")


def evaluate_okx_eea_demo_xperp_binding_v1(
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
    rule_type: str = RULE_TYPE,
    credential_class: str = CREDENTIAL_CLASS,
    secret_reference: str = SECRET_REFERENCE,
    account_identity: str = ACCOUNT_IDENTITY_PLACEHOLDER,
    order_post_authorized: bool = False,
    network_session_authorized: bool = False,
    venue_activated: bool = False,
    live_mode: bool = False,
    live_account: bool = False,
) -> OkxEeaDemoXperpBindingV1:
    """Evaluate and return a fail-closed binding. Raises on any ambiguity."""
    if live_mode or live_account:
        raise OkxEeaDemoXperpBindingError("LIVE_MODE_OR_ACCOUNT_HARD_BLOCK")
    if order_post_authorized:
        raise OkxEeaDemoXperpBindingError("ORDER_POST_HARD_BLOCK_IN_BINDING_PACKAGE")
    if network_session_authorized:
        raise OkxEeaDemoXperpBindingError("NETWORK_SESSION_NOT_AUTHORIZED_IN_BINDING_PACKAGE")
    if venue_activated:
        raise OkxEeaDemoXperpBindingError("VENUE_ACTIVATION_FORBIDDEN_IN_BINDING_PACKAGE")

    _assert_venue_environment_mode(venue=venue, environment=environment, runtime_mode=runtime_mode)
    host = _assert_host(rest_base)
    _assert_demo_header(
        header_name=demo_marker_header_name,
        header_value=demo_marker_header_value,
        headers=headers,
    )
    _assert_credential_class(credential_class)
    _assert_instrument(
        instrument=instrument_scope_exact,
        instrument_type=instrument_type,
        rule_type=rule_type,
    )
    _assert_secretref_only(secret_reference)
    identity = str(account_identity or "").strip()
    if not identity:
        raise OkxEeaDemoXperpBindingError("ACCOUNT_IDENTITY_REQUIRED")

    return OkxEeaDemoXperpBindingV1(
        venue=VENUE,
        environment=ENVIRONMENT,
        runtime_mode=RUNTIME_MODE,
        rest_host=host,
        rest_base=REST_BASE,
        demo_marker_header_name=DEMO_MARKER_HEADER_NAME,
        demo_marker_header_value=DEMO_MARKER_HEADER_VALUE,
        instrument_scope_exact=INSTRUMENT_SCOPE_EXACT,
        instrument_type=INSTRUMENT_TYPE,
        rule_type=RULE_TYPE,
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


def default_canonical_binding_v1() -> OkxEeaDemoXperpBindingV1:
    return evaluate_okx_eea_demo_xperp_binding_v1(headers=canonical_binding_headers_v1())
