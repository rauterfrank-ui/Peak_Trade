"""Ephemeral Keychain provisioning scope (never flips standing write authorization)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.constants_v1 import (
    EPHEMERAL_PROVISIONING_CONSUMER,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)

_EPHEMERAL_PROVISIONING_CTX: ContextVar[bool] = ContextVar(
    "k1_ephemeral_keychain_provisioning_v1",
    default=False,
)


def ephemeral_keychain_provisioning_is_active_v1() -> bool:
    return _EPHEMERAL_PROVISIONING_CTX.get() is True


@contextmanager
def bounded_ephemeral_keychain_provisioning_v1(*, consumer_id: str) -> Iterator[None]:
    if str(consumer_id or "") != EPHEMERAL_PROVISIONING_CONSUMER:
        raise K1ProductiveMacosKeychainProvisioningError(
            "EPHEMERAL_PROVISIONING_CONSUMER_FORBIDDEN"
        )
    token: Token[bool] = _EPHEMERAL_PROVISIONING_CTX.set(True)
    try:
        yield
    finally:
        _EPHEMERAL_PROVISIONING_CTX.reset(token)
