"""SecretRef-only credential path and productive Testnet account binding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    CANONICAL_ACCOUNT_IDENTITY,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_SECRET_REFERENCE,
    CANONICAL_VENUE,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.campaign_authorization_gate_v1 import (
    Section11128TerminalGateError,
    bind_credential_load_path_without_loading_v1,
)


class Section11128SecretRefAccountError(RuntimeError):
    """Fail-closed SecretRef / account binding violation."""


@dataclass(frozen=True)
class SecretRefResolutionV1:
    secret_reference: str
    resolved_structurally: bool
    plaintext_exposed: bool
    plaintext_persisted: bool
    credential_load_performed: bool
    runtime_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_reference": self.secret_reference,
            "resolved_structurally": self.resolved_structurally,
            "plaintext_exposed": self.plaintext_exposed,
            "plaintext_persisted": self.plaintext_persisted,
            "credential_load_performed": self.credential_load_performed,
            "runtime_mode": self.runtime_mode,
        }


@dataclass(frozen=True)
class ProductiveTestnetAccountBindingV1:
    account_identity: str
    venue: str
    runtime_mode: str
    bound: bool
    secret_reference_bound: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_identity": self.account_identity,
            "venue": self.venue,
            "runtime_mode": self.runtime_mode,
            "bound": self.bound,
            "secret_reference_bound": self.secret_reference_bound,
        }


def resolve_secretref_structurally_v1(
    *,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    plaintext_secret: str | None = None,
) -> SecretRefResolutionV1:
    """Resolve SecretRef structurally without loading or exposing plaintext."""
    if plaintext_secret is not None:
        raise Section11128SecretRefAccountError("PLAINTEXT_SECRET_FORBIDDEN")
    if runtime_mode != "TESTNET":
        raise Section11128SecretRefAccountError("SECRETREF_SCOPE_MUST_BE_TESTNET")
    try:
        bound = bind_credential_load_path_without_loading_v1(
            secret_reference=secret_reference,
            runtime_mode=runtime_mode,
        )
    except Section11128TerminalGateError as exc:
        message = str(exc)
        if "SECRET_REFERENCE_ONLY_REQUIRED" in message:
            raise Section11128SecretRefAccountError("SECRET_REFERENCE_ONLY_REQUIRED") from exc
        raise Section11128SecretRefAccountError(message) from exc
    if bound.get("credential_plaintext_loaded") is not False:
        raise Section11128SecretRefAccountError("PLAINTEXT_LEAK_DETECTED")
    # Never return or log secret material beyond the opaque reference string.
    return SecretRefResolutionV1(
        secret_reference=str(bound["secret_reference"]),
        resolved_structurally=True,
        plaintext_exposed=False,
        plaintext_persisted=False,
        credential_load_performed=False,
        runtime_mode=runtime_mode,
    )


def bind_productive_testnet_account_v1(
    *,
    account_identity: str = CANONICAL_ACCOUNT_IDENTITY,
    venue: str = CANONICAL_VENUE,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
) -> ProductiveTestnetAccountBindingV1:
    if runtime_mode != "TESTNET":
        raise Section11128SecretRefAccountError("ACCOUNT_BINDING_REQUIRES_TESTNET")
    if venue != CANONICAL_VENUE:
        raise Section11128SecretRefAccountError("ACCOUNT_BINDING_VENUE_MISMATCH")
    identity = str(account_identity or "").strip()
    if not identity:
        raise Section11128SecretRefAccountError("ACCOUNT_IDENTITY_REQUIRED")
    secret = resolve_secretref_structurally_v1(
        secret_reference=secret_reference,
        runtime_mode=runtime_mode,
    )
    return ProductiveTestnetAccountBindingV1(
        account_identity=identity,
        venue=venue,
        runtime_mode=runtime_mode,
        bound=True,
        secret_reference_bound=secret.resolved_structurally,
    )
