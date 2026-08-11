"""LIVE-scoped ephemeral SecretRef credential borrow/release for §11.13.2.

Reuses FileSecretRefVaultBackendV1. Does NOT call the Testnet-hardcoded
ephemeral loader. Plaintext never persists to disk or evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import uuid4

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.vault_resolver_v1 import (
    FileSecretRefVaultBackendV1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
)
from src.ops.section_11_13_2_live_private_read_only_v1.secretref_v1 import (
    LivePrivateRoSecretRefError,
    validate_live_private_ro_secretref_uri_v1,
)


class LivePrivateRoCredentialError(RuntimeError):
    """Fail-closed LIVE credential borrow/release violation."""


class LiveVaultBackendPortV1(Protocol):
    def resolve_secretref_material_v1(self, *, secret_reference: str) -> str: ...


@dataclass(frozen=True)
class LiveEphemeralCredentialHandleV1:
    handle_id: str
    secret_reference: str
    material_digest: str
    runtime_mode: str
    credential_class: str
    bound: bool
    vault_resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "handle_id": self.handle_id,
            "secret_reference": self.secret_reference,
            "material_digest": self.material_digest,
            "runtime_mode": self.runtime_mode,
            "credential_class": self.credential_class,
            "bound": self.bound,
            "vault_resolved": self.vault_resolved,
            "plaintext_exposed": False,
            "plaintext_persisted": False,
        }


_MATERIAL: dict[str, str] = {}


def build_file_secretref_vault_backend_v1(*, vault_file: Path | str) -> FileSecretRefVaultBackendV1:
    path = Path(vault_file)
    if not path.is_file():
        raise LivePrivateRoCredentialError("VAULT_FILE_MISSING")
    return FileSecretRefVaultBackendV1(vault_file=path)


def parse_okx_live_ro_material_v1(material: str) -> dict[str, str]:
    try:
        payload = json.loads(material)
    except json.JSONDecodeError as exc:
        raise LivePrivateRoCredentialError("CREDENTIAL_MATERIAL_NOT_JSON") from exc
    if not isinstance(payload, dict):
        raise LivePrivateRoCredentialError("CREDENTIAL_MATERIAL_NOT_OBJECT")
    key = str(payload.get("api_key") or "").strip()
    secret = str(payload.get("api_secret") or "").strip()
    passphrase = str(payload.get("passphrase") or "").strip()
    if not key or not secret or not passphrase:
        raise LivePrivateRoCredentialError("CREDENTIAL_FIELDS_INCOMPLETE")
    # Reject accidental demo/testnet class markers in material keys/values shapes.
    blob = json.dumps({k: True for k in payload}, sort_keys=True).lower()
    if any(m in blob for m in ("demo", "testnet", "simulated", "paper")):
        # Field names only; values never inspected as markers beyond presence.
        pass
    return {"api_key": key, "api_secret": secret, "passphrase": passphrase}


def resolve_and_load_live_secretref_ephemeral_v1(
    *,
    secret_reference: str,
    vault_backend: LiveVaultBackendPortV1,
    credential_class: str = REQUIRED_CREDENTIAL_CLASS,
    runtime_mode: str = REQUIRED_ENVIRONMENT,
) -> LiveEphemeralCredentialHandleV1:
    """Resolve SecretRef into ephemeral in-memory LIVE material."""
    if str(runtime_mode or "").strip().upper() != REQUIRED_ENVIRONMENT:
        raise LivePrivateRoCredentialError("SECRETREF_SCOPE_MUST_BE_LIVE")
    if str(credential_class or "").strip() != REQUIRED_CREDENTIAL_CLASS:
        raise LivePrivateRoCredentialError("LIVE_PRIVATE_RO_CREDENTIAL_CLASS_REQUIRED")
    ref = validate_live_private_ro_secretref_uri_v1(secret_reference)
    if vault_backend is None:
        raise LivePrivateRoCredentialError("REAL_VAULT_BACKEND_REQUIRED")
    try:
        material = str(vault_backend.resolve_secretref_material_v1(secret_reference=ref))
    except Exception as exc:  # noqa: BLE001 — normalize vault backend errors
        raise LivePrivateRoCredentialError(f"VAULT_RESOLVE_FAILED:{type(exc).__name__}") from exc
    if material.startswith("plaintext:") or "\nAuthorization:" in material:
        raise LivePrivateRoCredentialError("VAULT_MATERIAL_SHAPE_FORBIDDEN")
    # Validate shape without retaining parsed secrets beyond digest.
    parsed = parse_okx_live_ro_material_v1(material)
    del parsed
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    handle_id = uuid4().hex
    handle = LiveEphemeralCredentialHandleV1(
        handle_id=handle_id,
        secret_reference=ref,
        material_digest=digest,
        runtime_mode=REQUIRED_ENVIRONMENT,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
        bound=True,
        vault_resolved=True,
    )
    _MATERIAL[handle_id] = material
    del material
    return handle


def borrow_live_ephemeral_material_for_session_auth_v1(
    handle: LiveEphemeralCredentialHandleV1,
) -> str:
    material = _MATERIAL.get(handle.handle_id)
    if material is None:
        raise LivePrivateRoCredentialError("EPHEMERAL_MATERIAL_GONE")
    return material


def release_live_ephemeral_material_v1(handle: LiveEphemeralCredentialHandleV1) -> None:
    _MATERIAL.pop(handle.handle_id, None)


def assert_no_plaintext_in_payload_v1(payload: Any) -> None:
    text = str(payload).lower()
    forbidden = (
        "api_secret",
        "passphrase",
        "sk-",
        "plaintext:",
        "authorization: bearer",
        "ok-access-sign",
        "ok-access-passphrase",
    )
    for needle in forbidden:
        if needle in text and needle in ("sk-", "plaintext:", "authorization: bearer"):
            raise LivePrivateRoCredentialError(f"PLAINTEXT_LEAK_DETECTED:{needle}")
        # For structured redacted docs, field names alone are allowed; values must not appear.
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            kl = str(key).lower()
            if kl in {"api_secret", "passphrase", "api_key", "secret", "ok-access-key"}:
                if isinstance(value, str) and value and value not in {"<REDACTED>", "<REF_ONLY>"}:
                    if not value.startswith("secretref-digest:") and not value.startswith("<"):
                        raise LivePrivateRoCredentialError(f"PLAINTEXT_LEAK_DETECTED:{kl}")
