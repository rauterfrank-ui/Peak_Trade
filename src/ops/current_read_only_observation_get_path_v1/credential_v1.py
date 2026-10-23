"""Read-only observation credential class gate.

Accepts only READ_ONLY_OBSERVATION_API_KEY and its own SecretRef URI.
Trade credential class and the live-canary SecretRef are rejected.
Vault files are refused and never opened.
"""

from __future__ import annotations

from src.ops.current_read_only_observation_get_path_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_CREDENTIAL_CLASS,
    FORBIDDEN_TRADE_SECRETREF_URI,
    SECRETREF_URI,
)
from src.ops.current_read_only_observation_get_path_v1.errors_v1 import (
    ReadOnlyObservationGetError,
)
from src.ops.current_read_only_observation_get_path_v1.handle_v1 import (
    ReadOnlyObservationGetHandleV1,
    bind_already_held_read_only_observation_session_v1,
)


def refuse_vault_file_v1(_vault_file: object) -> None:
    """Vault I/O is outside this path. The argument is ignored and refused."""

    raise ReadOnlyObservationGetError("VAULT_READ_FORBIDDEN")


def assert_read_only_observation_credential_v1(
    *,
    credential_class: str,
    secret_reference: str,
) -> None:
    kind = str(credential_class or "").strip()
    reference = str(secret_reference or "").strip()
    if kind == FORBIDDEN_TRADE_CREDENTIAL_CLASS or reference == FORBIDDEN_TRADE_SECRETREF_URI:
        raise ReadOnlyObservationGetError("TRADE_CREDENTIAL_FORBIDDEN")
    if kind != CREDENTIAL_CLASS:
        raise ReadOnlyObservationGetError("CREDENTIAL_CLASS_FORBIDDEN")
    if reference != SECRETREF_URI:
        raise ReadOnlyObservationGetError("SECRETREF_URI_FORBIDDEN")


def bind_read_only_observation_credential_v1(
    *,
    credential_class: str,
    secret_reference: str,
    api_key: str,
    api_secret: str,
    passphrase: str,
) -> ReadOnlyObservationGetHandleV1:
    assert_read_only_observation_credential_v1(
        credential_class=credential_class,
        secret_reference=secret_reference,
    )
    return bind_already_held_read_only_observation_session_v1(
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
    )


__all__ = [
    "assert_read_only_observation_credential_v1",
    "bind_read_only_observation_credential_v1",
    "refuse_vault_file_v1",
]
