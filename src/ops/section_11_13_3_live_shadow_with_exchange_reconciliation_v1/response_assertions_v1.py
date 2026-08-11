"""Response assertions and redaction for §11.13.3."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    REQUIRED_PERMISSION_ATTESTATION,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
    LiveShadowReconHttpError,
    LiveShadowReconHttpResponseV1,
    parse_json_object_v1,
)


class LiveShadowReconAssertionError(RuntimeError):
    """Fail-closed response assertion violation."""


_SENSITIVE_RE = re.compile(
    r"(api[_-]?key|secret|passphrase|token|authorization|signature|plaintext|sk-)",
    re.IGNORECASE,
)
_DEMO_MARKER_KEYS = frozenset(
    {
        "demo",
        "testnet",
        "simulated",
        "simulated-trading",
        "paper",
        "x-simulated-trading",
    }
)


@dataclass(frozen=True)
class AuthenticatedPrivateReadSuccessV1:
    authenticated_read_success: bool
    http_status: int
    response_type: str
    account_identity_redacted: str
    account_identity_hash: str
    response_digest: str
    transport_class: str
    venue_live_contact: bool
    fixture_or_demo_or_testnet: bool
    okx_code: str = "0"
    account_scope_match: bool = True
    sanitized_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "authenticated_read_success": self.authenticated_read_success,
            "http_status": self.http_status,
            "response_type": self.response_type,
            "account_identity_redacted": self.account_identity_redacted,
            "account_identity_hash": self.account_identity_hash,
            "response_digest": self.response_digest,
            "transport_class": self.transport_class,
            "venue_live_contact": self.venue_live_contact,
            "fixture_or_demo_or_testnet": self.fixture_or_demo_or_testnet,
            "okx_code": self.okx_code,
            "account_scope_match": self.account_scope_match,
        }


def redact_account_identity_v1(raw: str) -> tuple[str, str]:
    value = str(raw or "").strip()
    if not value:
        return ("<ABSENT>", hashlib.sha256(b"").hexdigest())
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    if len(value) <= 4:
        redacted = "***"
    else:
        redacted = f"{value[:2]}***{value[-2:]}"
    return redacted, digest


def redact_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if _SENSITIVE_RE.search(str(key)):
            out[str(key)] = "<REDACTED>"
            continue
        if isinstance(value, Mapping):
            out[str(key)] = redact_mapping_v1(value)
        elif isinstance(value, list):
            out[str(key)] = [redact_mapping_v1(v) if isinstance(v, Mapping) else v for v in value]
        elif isinstance(value, str) and _SENSITIVE_RE.search(value):
            out[str(key)] = "<REDACTED>"
        else:
            out[str(key)] = value
    return out


def assert_okx_business_code_success_v1(payload: Mapping[str, Any]) -> str:
    raw = payload.get("code", None)
    if raw is None:
        raise LiveShadowReconAssertionError("OKX_CODE_MISSING")
    code = str(raw).strip()
    if code != "0":
        raise LiveShadowReconAssertionError(f"OKX_CODE_NOT_SUCCESS:{code}")
    return code


def _payload_has_demo_testnet_marker(payload: Mapping[str, Any]) -> bool:
    def walk(node: Any) -> bool:
        if isinstance(node, Mapping):
            for key, value in node.items():
                key_l = str(key).strip().lower()
                if key_l in _DEMO_MARKER_KEYS or any(m in key_l for m in _DEMO_MARKER_KEYS):
                    return True
                if isinstance(value, str):
                    val_l = value.strip().lower()
                    if val_l in _DEMO_MARKER_KEYS:
                        return True
                    if val_l in {"1", "true", "yes"} and "simul" in key_l:
                        return True
                if walk(value):
                    return True
        elif isinstance(node, list):
            return any(walk(item) for item in node)
        return False

    return walk(payload)


def assert_authenticated_private_read_success_v1(
    *,
    response: LiveShadowReconHttpResponseV1,
    transport_class: str,
    venue_live_contact: bool,
    expected_environment: str = "LIVE",
    expected_account_scope: str | None = None,
    require_account_identity: bool = False,
) -> AuthenticatedPrivateReadSuccessV1:
    status = int(response.status_code)
    if status in {401, 403}:
        raise LiveShadowReconAssertionError(f"AUTH_FAIL_NOT_PROVEN:HTTP_{status}")
    if status != 200:
        raise LiveShadowReconAssertionError(f"HTTP_STATUS_NOT_SUCCESS:{status}")

    try:
        payload = parse_json_object_v1(response.body_bytes)
    except LiveShadowReconHttpError as exc:
        raise LiveShadowReconAssertionError(str(exc)) from exc

    okx_code = assert_okx_business_code_success_v1(payload)

    if _payload_has_demo_testnet_marker(payload):
        raise LiveShadowReconAssertionError("DEMO_TESTNET_MARKER_IN_RESPONSE")

    if expected_environment != "LIVE":
        raise LiveShadowReconAssertionError("ENVIRONMENT_NOT_LIVE")

    fixture_like = (
        transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE or venue_live_contact is False
    )

    account_raw = extract_account_identity_v1(payload)
    if require_account_identity and not account_raw:
        raise LiveShadowReconAssertionError("ACCOUNT_IDENTITY_REQUIRED")

    account_scope_match = True
    if expected_account_scope is not None and str(expected_account_scope).strip():
        expected = str(expected_account_scope).strip()
        if not account_raw:
            raise LiveShadowReconAssertionError("ACCOUNT_SCOPE_CROSSCHECK_IDENTITY_MISSING")
        if account_raw != expected:
            raise LiveShadowReconAssertionError("ACCOUNT_SCOPE_MISMATCH")
        account_scope_match = True

    redacted, hashed = redact_account_identity_v1(account_raw)
    digest = hashlib.sha256(response.body_bytes).hexdigest()
    return AuthenticatedPrivateReadSuccessV1(
        authenticated_read_success=True,
        http_status=status,
        response_type="application/json",
        account_identity_redacted=redacted,
        account_identity_hash=hashed,
        response_digest=digest,
        transport_class=transport_class,
        venue_live_contact=bool(venue_live_contact),
        fixture_or_demo_or_testnet=fixture_like,
        okx_code=okx_code,
        account_scope_match=account_scope_match,
        sanitized_payload=redact_mapping_v1(payload),
    )


def extract_account_identity_v1(payload: Mapping[str, Any]) -> str:
    for key in ("uid", "account_identity", "acctId", "accountId"):
        if key in payload and str(payload[key]).strip():
            return str(payload[key]).strip()
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, Mapping):
            for key in ("uid", "acctId", "accountId"):
                if key in first and str(first[key]).strip():
                    return str(first[key]).strip()
    return ""


def json_safe_lower(payload: Mapping[str, Any]) -> str:
    return str(payload).lower()


def productive_proven_allowed_v1(
    *,
    transport_class: str,
    venue_live_contact: bool,
    fixture_or_demo_or_testnet: bool,
    authenticated_read_success: bool,
) -> bool:
    return (
        transport_class == TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
        and venue_live_contact is True
        and fixture_or_demo_or_testnet is False
        and authenticated_read_success is True
    )


def validate_permission_attestation_v1(attestation: Mapping[str, Any] | None) -> dict[str, bool]:
    if not isinstance(attestation, Mapping):
        raise LiveShadowReconAssertionError("PERMISSION_ATTESTATION_REQUIRED")
    read = attestation.get("READ")
    trade = attestation.get("TRADE")
    withdraw = attestation.get("WITHDRAW")
    if read is not True:
        raise LiveShadowReconAssertionError("PERMISSION_ATTESTATION_READ_MUST_BE_TRUE")
    if trade is not False:
        raise LiveShadowReconAssertionError("PERMISSION_ATTESTATION_TRADE_MUST_BE_FALSE")
    if withdraw is not False:
        raise LiveShadowReconAssertionError("PERMISSION_ATTESTATION_WITHDRAW_MUST_BE_FALSE")
    expected = dict(REQUIRED_PERMISSION_ATTESTATION)
    return {"READ": expected["READ"], "TRADE": expected["TRADE"], "WITHDRAW": expected["WITHDRAW"]}
