"""Opaque handle for already-held read-only observation material.

The handle object does not expose credential fields. Material stays in a
private session map and is cleared on release. This module does not read a
vault, keychain, or file.
"""

from __future__ import annotations

from dataclasses import dataclass
from secrets import token_hex

from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)

_SESSION_FIELDS: dict[str, tuple[str, str, str]] = {}


@dataclass(frozen=True)
class ReadOnlyObservationGetHandleV1:
    """Distinct from the trade K1 handle. Cannot be passed to the trade signer."""

    handle_id: str
    bound: bool = True

    def __repr__(self) -> str:
        return "ReadOnlyObservationGetHandleV1(redacted)"


def bind_already_held_read_only_observation_session_v1(
    *,
    api_key: str,
    api_secret: str,
    passphrase: str,
) -> ReadOnlyObservationGetHandleV1:
    key = str(api_key or "").strip()
    secret = str(api_secret or "").strip()
    phrase = str(passphrase or "").strip()
    if not key or not secret or not phrase:
        raise ReadOnlyObservationGetError("CREDENTIAL_FIELDS_INCOMPLETE")
    handle_id = token_hex(16)
    _SESSION_FIELDS[handle_id] = (key, secret, phrase)
    return ReadOnlyObservationGetHandleV1(handle_id=handle_id, bound=True)


def borrow_read_only_observation_session_v1(
    handle: ReadOnlyObservationGetHandleV1,
) -> tuple[str, str, str]:
    if not isinstance(handle, ReadOnlyObservationGetHandleV1):
        raise ReadOnlyObservationGetError("HANDLE_TYPE_FORBIDDEN")
    if handle.bound is not True:
        raise ReadOnlyObservationGetError("HANDLE_NOT_BOUND")
    fields = _SESSION_FIELDS.get(handle.handle_id)
    if fields is None:
        raise ReadOnlyObservationGetError("EPHEMERAL_MATERIAL_GONE")
    return fields


def release_read_only_observation_session_v1(
    handle: ReadOnlyObservationGetHandleV1 | None,
) -> None:
    if handle is None:
        return
    if not isinstance(handle, ReadOnlyObservationGetHandleV1):
        raise ReadOnlyObservationGetError("HANDLE_TYPE_FORBIDDEN")
    _SESSION_FIELDS.pop(handle.handle_id, None)


__all__ = [
    "ReadOnlyObservationGetHandleV1",
    "bind_already_held_read_only_observation_session_v1",
    "borrow_read_only_observation_session_v1",
    "release_read_only_observation_session_v1",
]
