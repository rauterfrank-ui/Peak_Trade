"""Admit the existing productive Keychain item into the GET-only handle.

The item keeps its own credential class. Material is parsed in process memory
and stored only in the GET-only session map. This module does not sign, send,
or import a productive signer or POST transport.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    FORBIDDEN_TRADE_CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_SECRETREF_URI,
    K1_KEYCHAIN_ACCOUNT,
    K1_KEYCHAIN_SERVICE,
    K1_SOURCE_CREDENTIAL_CLASS,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    ReadOnlyObservationGetHandleV1,
    bind_already_held_read_only_observation_session_v1,
)

_FIELD_API_KEY = "apiKey"
_FIELD_SECRET_KEY = "secretKey"
_FIELD_PASSPHRASE = "passphrase"
_REQUIRED_FIELDS = frozenset({_FIELD_API_KEY, _FIELD_SECRET_KEY, _FIELD_PASSPHRASE})

OpaqueReader = Callable[[str, str], bytes | None]


def _reject_trade_source_v1(*, credential_class: str, keychain_account: str) -> None:
    kind = str(credential_class or "").strip()
    account = str(keychain_account or "").strip()
    if kind == FORBIDDEN_TRADE_CREDENTIAL_CLASS or account == FORBIDDEN_TRADE_SECRETREF_URI:
        raise ReadOnlyObservationGetError("TRADE_CREDENTIAL_FORBIDDEN")
    if FORBIDDEN_TRADE_SECRETREF_URI in kind or FORBIDDEN_TRADE_SECRETREF_URI in account:
        raise ReadOnlyObservationGetError("TRADE_CREDENTIAL_FORBIDDEN")


def _admit_identity_v1(
    *,
    keychain_service: str,
    keychain_account: str,
    credential_class: str,
) -> tuple[str, str, str]:
    service = str(keychain_service or "").strip()
    account = str(keychain_account or "").strip()
    kind = str(credential_class or "").strip()
    _reject_trade_source_v1(credential_class=kind, keychain_account=account)
    if service != K1_KEYCHAIN_SERVICE:
        raise ReadOnlyObservationGetError("KEYCHAIN_SERVICE_FORBIDDEN")
    if account != K1_KEYCHAIN_ACCOUNT:
        raise ReadOnlyObservationGetError("KEYCHAIN_ACCOUNT_FORBIDDEN")
    if kind != K1_SOURCE_CREDENTIAL_CLASS:
        raise ReadOnlyObservationGetError("CREDENTIAL_CLASS_FORBIDDEN")
    return service, account, kind


def _parse_opaque_utf8_json_v1(opaque: bytes) -> tuple[str, str, str]:
    if not isinstance(opaque, (bytes, bytearray)) or len(opaque) == 0:
        raise ReadOnlyObservationGetError("K1_OPAQUE_EMPTY")
    try:
        text = bytes(opaque).decode("utf-8")
    except UnicodeDecodeError:
        raise ReadOnlyObservationGetError("K1_OPAQUE_UTF8_DECODE_FAIL") from None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise ReadOnlyObservationGetError("K1_OPAQUE_JSON_MALFORMED") from None
    if not isinstance(payload, Mapping):
        raise ReadOnlyObservationGetError("K1_OPAQUE_JSON_NOT_OBJECT")
    if frozenset(str(key) for key in payload.keys()) != _REQUIRED_FIELDS:
        raise ReadOnlyObservationGetError("K1_OPAQUE_JSON_FIELD_SET_MISMATCH")
    api_key = str(payload.get(_FIELD_API_KEY) or "").strip()
    secret = str(payload.get(_FIELD_SECRET_KEY) or "").strip()
    phrase = str(payload.get(_FIELD_PASSPHRASE) or "").strip()
    if not api_key or not secret or not phrase:
        raise ReadOnlyObservationGetError("CREDENTIAL_FIELDS_INCOMPLETE")
    return api_key, secret, phrase


def read_named_k1_keychain_opaque_v1(service: str, account: str) -> bytes:
    """Read one named Keychain item. The bytes are not logged."""

    if service != K1_KEYCHAIN_SERVICE or account != K1_KEYCHAIN_ACCOUNT:
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_FORBIDDEN")
    completed = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-s",
            service,
            "-a",
            account,
            "-w",
        ],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_MISSING")
    raw = bytes(completed.stdout)
    if raw.endswith(b"\n"):
        raw = raw[:-1]
    if not raw:
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_MISSING")
    return raw


def admit_k1_keychain_get_source_v1(
    *,
    keychain_service: str,
    keychain_account: str,
    credential_class: str,
    opaque_reader: OpaqueReader,
) -> ReadOnlyObservationGetHandleV1:
    """Bind admitted material into the GET-only handle. The reader is not called on rejection."""

    service, account, _kind = _admit_identity_v1(
        keychain_service=keychain_service,
        keychain_account=keychain_account,
        credential_class=credential_class,
    )
    if not callable(opaque_reader):
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_MISSING")
    try:
        opaque = opaque_reader(service, account)
    except ReadOnlyObservationGetError:
        raise
    except Exception:
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_MISSING") from None
    if not isinstance(opaque, (bytes, bytearray)) or len(opaque) == 0:
        raise ReadOnlyObservationGetError("KEYCHAIN_SOURCE_MISSING")
    api_key, secret, phrase = _parse_opaque_utf8_json_v1(bytes(opaque))
    return bind_already_held_read_only_observation_session_v1(
        api_key=api_key,
        api_secret=secret,
        passphrase=phrase,
    )


def load_admitted_k1_get_handle_v1(
    *,
    keychain_service: str,
    keychain_account: str,
    credential_class: str,
) -> ReadOnlyObservationGetHandleV1:
    """Authorized entry for the named item only. Tests must pass their own reader."""

    return admit_k1_keychain_get_source_v1(
        keychain_service=keychain_service,
        keychain_account=keychain_account,
        credential_class=credential_class,
        opaque_reader=read_named_k1_keychain_opaque_v1,
    )


__all__ = [
    "admit_k1_keychain_get_source_v1",
    "load_admitted_k1_get_handle_v1",
    "read_named_k1_keychain_opaque_v1",
]
