"""Response assertions and redaction for §11.13.2."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_2_live_private_read_only_v1.http_client_v1 import (
    LivePrivateRoHttpError,
    LivePrivateRoHttpResponseV1,
    parse_json_object_v1,
)


class LivePrivateRoAssertionError(RuntimeError):
    """Fail-closed response assertion violation."""


_SENSITIVE_RE = re.compile(
    r"(api[_-]?key|secret|passphrase|token|authorization|signature|plaintext|sk-)",
    re.IGNORECASE,
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


def assert_authenticated_private_read_success_v1(
    *,
    response: LivePrivateRoHttpResponseV1,
    transport_class: str,
    venue_live_contact: bool,
    expected_environment: str = "LIVE",
) -> AuthenticatedPrivateReadSuccessV1:
    status = int(response.status_code)
    if status in {401, 403}:
        raise LivePrivateRoAssertionError(f"AUTH_FAIL_NOT_PROVEN:HTTP_{status}")
    if status != 200:
        raise LivePrivateRoAssertionError(f"HTTP_STATUS_NOT_SUCCESS:{status}")

    try:
        payload = parse_json_object_v1(response.body_bytes)
    except LivePrivateRoHttpError as exc:
        raise LivePrivateRoAssertionError(str(exc)) from exc

    # Reject obvious demo/testnet markers in payload.
    blob = json_safe_lower(payload)
    if any(m in blob for m in ("demo", "testnet", "simulated-trading", "paper")):
        raise LivePrivateRoAssertionError("DEMO_TESTNET_MARKER_IN_RESPONSE")

    if expected_environment != "LIVE":
        raise LivePrivateRoAssertionError("ENVIRONMENT_NOT_LIVE")

    fixture_like = (
        transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE or venue_live_contact is False
    )
    if fixture_like:
        # Fixture may validate schema locally but never counts as Live proven success
        # for the productive claim path.
        pass

    account_raw = extract_account_identity_v1(payload)
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
