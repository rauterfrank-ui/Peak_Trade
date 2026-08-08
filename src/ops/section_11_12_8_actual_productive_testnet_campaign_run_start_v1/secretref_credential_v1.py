"""SecretRef credential path — ephemeral material, no plaintext leakage."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_RUNTIME_MODE,
    CANONICAL_SECRET_REFERENCE,
)


class ActualStartSecretRefError(RuntimeError):
    """Fail-closed SecretRef violation."""


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

    def to_dict(self) -> dict[str, Any]:
        # Never include plaintext.
        return {
            "handle_id": self.handle_id,
            "secret_reference": self.secret_reference,
            "material_digest": self.material_digest,
            "runtime_mode": self.runtime_mode,
            "bound": self.bound,
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
) -> EphemeralCredentialHandleV1:
    """Resolve SecretRef into ephemeral in-memory material.

    During stubbed acceptance, ``stub_material`` supplies synthetic bytes that
    never leave this function except as a digest-bound handle.
    Real vault resolution requires ``allow_real_vault=True`` (not used in this
    implementation OWNER_GO).
    """
    if runtime_mode != "TESTNET":
        raise ActualStartSecretRefError("SECRETREF_SCOPE_MUST_BE_TESTNET")
    if not _is_secret_reference_only(secret_reference):
        raise ActualStartSecretRefError("SECRET_REFERENCE_ONLY_REQUIRED")
    if allow_real_vault:
        raise ActualStartSecretRefError("REAL_VAULT_NOT_INVOKED_IN_IMPLEMENTATION_GO")
    if stub_material is None:
        raise ActualStartSecretRefError("STUB_MATERIAL_REQUIRED_FOR_NON_VAULT_PATH")
    if stub_material.startswith("plaintext:") or "\nAuthorization:" in stub_material:
        raise ActualStartSecretRefError("STUB_MATERIAL_SHAPE_FORBIDDEN")
    material = str(stub_material)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    handle_id = uuid4().hex
    handle = EphemeralCredentialHandleV1(
        handle_id=handle_id,
        secret_reference=secret_reference,
        material_digest=digest,
        runtime_mode=runtime_mode,
        bound=True,
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
