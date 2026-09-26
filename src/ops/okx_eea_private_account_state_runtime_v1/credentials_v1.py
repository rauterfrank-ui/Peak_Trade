"""Governed observation credential join (SecretRef/K1 patterns; no secret material)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_CREDENTIAL_CLASSES,
    K2_ABSENT,
)


class ObservationCredentialError(ValueError):
    """Fail-closed observation credential violation."""


@dataclass(frozen=True)
class SecretRefIdentityV1:
    uri: Optional[str]
    bound: bool
    credential_class: str

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "uri_present": bool(self.uri),
            "bound": self.bound,
            "credential_class": self.credential_class,
        }


@dataclass(frozen=True)
class ObservationCredentialHandleV1:
    identity: SecretRefIdentityV1
    signing_capable: bool
    rest_post_authority: bool
    ws_order_send_authority: bool
    ws_amend_authority: bool
    ws_cancel_authority: bool
    k2_present: bool

    def release(self) -> None:
        return None


def validate_credential_class_v1(credential_class: str) -> None:
    if credential_class in FORBIDDEN_TRADE_CREDENTIAL_CLASSES:
        raise ObservationCredentialError("TRADE_CREDENTIAL_CLASS_FORBIDDEN")
    if credential_class != CREDENTIAL_CLASS:
        raise ObservationCredentialError("CREDENTIAL_CLASS_MISMATCH")


def join_observation_credential_v1(
    *,
    secretref_uri: Optional[str],
    secretref_bound: bool,
    credential_class: str,
) -> ObservationCredentialHandleV1:
    validate_credential_class_v1(credential_class)
    if not secretref_bound:
        raise ObservationCredentialError("SECRETREF_UNBOUND")
    if not secretref_uri:
        raise ObservationCredentialError("SECRETREF_URI_UNBOUND")
    if K2_ABSENT is not True:
        raise ObservationCredentialError("K2_MUST_BE_ABSENT")
    identity = SecretRefIdentityV1(
        uri=secretref_uri,
        bound=True,
        credential_class=credential_class,
    )
    return ObservationCredentialHandleV1(
        identity=identity,
        signing_capable=True,
        rest_post_authority=False,
        ws_order_send_authority=False,
        ws_amend_authority=False,
        ws_cancel_authority=False,
        k2_present=False,
    )


def redact_credential_payload_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_keys = (
        "api_key",
        "api_secret",
        "passphrase",
        "secret",
        "password",
        "token",
    )
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if any(part in key.lower() for part in forbidden_keys):
            out[key] = "<REDACTED>"
        elif isinstance(value, Mapping):
            out[key] = redact_credential_payload_v1(value)
        else:
            out[key] = value
    return out


def assert_no_trade_credential_fallback_v1(
    attempted_class: str,
    *,
    fallback_class: str,
) -> None:
    if attempted_class != CREDENTIAL_CLASS and fallback_class in FORBIDDEN_TRADE_CREDENTIAL_CLASSES:
        raise ObservationCredentialError("TRADE_CREDENTIAL_FALLBACK_FORBIDDEN")
