"""SecretRef credential path — ephemeral material, no plaintext leakage."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_RUNTIME_MODE,
    CANONICAL_SECRET_REFERENCE,
)


class ActualStartSecretRefError(RuntimeError):
    """Fail-closed SecretRef violation."""


class VaultBackendPortV1(Protocol):
    """Real SecretRef vault backend — returns ephemeral material, never persists it."""

    def resolve_secretref_material_v1(self, *, secret_reference: str) -> str: ...


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if secret_reference.startswith("secretref:"):
        return True
    return "://" in secret_reference


@dataclass(frozen=True)
class EphemeralCredentialHandleV1:
    """Opaque handle. Plaintext lives only in a private id-keyed store."""

    handle_id: str
    secret_reference: str
    material_digest: str
    runtime_mode: str
    bound: bool
    vault_resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        # Never include plaintext.
        return {
            "handle_id": self.handle_id,
            "secret_reference": self.secret_reference,
            "material_digest": self.material_digest,
            "runtime_mode": self.runtime_mode,
            "bound": self.bound,
            "vault_resolved": self.vault_resolved,
            "plaintext_exposed": False,
            "plaintext_persisted": False,
        }


_MATERIAL: dict[str, str] = {}


def resolve_and_load_secretref_ephemeral_v1(
    *,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    stub_material: str | None = None,
    allow_real_vault: bool = False,
    vault_backend: VaultBackendPortV1 | None = None,
) -> EphemeralCredentialHandleV1:
    """Resolve SecretRef into ephemeral in-memory material.

    Stubbed acceptance may supply ``stub_material``. Real productive path requires
    ``allow_real_vault=True`` and a bound ``vault_backend`` that resolves the
    SecretRef without persisting plaintext.
    """
    if runtime_mode != "TESTNET":
        raise ActualStartSecretRefError("SECRETREF_SCOPE_MUST_BE_TESTNET")
    if not _is_secret_reference_only(secret_reference):
        raise ActualStartSecretRefError("SECRET_REFERENCE_ONLY_REQUIRED")

    vault_resolved = False
    if allow_real_vault:
        if vault_backend is None:
            raise ActualStartSecretRefError("REAL_VAULT_BACKEND_REQUIRED")
        material = str(
            vault_backend.resolve_secretref_material_v1(secret_reference=secret_reference)
        )
        vault_resolved = True
    else:
        if stub_material is None:
            raise ActualStartSecretRefError("STUB_MATERIAL_REQUIRED_FOR_NON_VAULT_PATH")
        material = str(stub_material)

    if material.startswith("plaintext:") or "\nAuthorization:" in material:
        raise ActualStartSecretRefError("STUB_MATERIAL_SHAPE_FORBIDDEN")
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    handle_id = uuid4().hex
    handle = EphemeralCredentialHandleV1(
        handle_id=handle_id,
        secret_reference=secret_reference,
        material_digest=digest,
        runtime_mode=runtime_mode,
        bound=True,
        vault_resolved=vault_resolved,
    )
    _MATERIAL[handle_id] = material
    # Drop local name; only private store retains material.
    del material
    return handle


def borrow_ephemeral_material_for_session_auth_v1(
    handle: EphemeralCredentialHandleV1,
) -> str:
    """Borrow material for session auth only; caller must not persist/log."""
    material = _MATERIAL.get(handle.handle_id)
    if material is None:
        raise ActualStartSecretRefError("EPHEMERAL_MATERIAL_GONE")
    return material


def release_ephemeral_material_v1(handle: EphemeralCredentialHandleV1) -> None:
    _MATERIAL.pop(handle.handle_id, None)


def assert_no_plaintext_in_payload_v1(payload: Any) -> None:
    text = str(payload).lower()
    forbidden = ("api_secret", "passphrase", "sk-", "plaintext:", "authorization: bearer")
    for needle in forbidden:
        if needle in text:
            raise ActualStartSecretRefError(f"PLAINTEXT_LEAK_DETECTED:{needle}")
