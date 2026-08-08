"""Productive SecretRef vault resolver — ephemeral load, no plaintext persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_SECRET_REFERENCE,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    VAULT_BACKEND_KIND,
)


class UnlockVaultResolverError(RuntimeError):
    """Fail-closed vault resolver violation."""


@dataclass(frozen=True)
class InMemorySecretRefVaultBackendV1:
    """Real vault backend bound to an in-process SecretRef map (ephemeral only)."""

    mapping: Mapping[str, str]
    backend_kind: str = VAULT_BACKEND_KIND

    def resolve_secretref_material_v1(self, *, secret_reference: str) -> str:
        ref = str(secret_reference or "").strip()
        if not ref.startswith("secretref:"):
            raise UnlockVaultResolverError("SECRET_REFERENCE_ONLY_REQUIRED")
        if ref not in self.mapping:
            raise UnlockVaultResolverError(f"SECRETREF_NOT_FOUND:{ref}")
        material = str(self.mapping[ref])
        if material.startswith("plaintext:") or "\nAuthorization:" in material:
            raise UnlockVaultResolverError("VAULT_MATERIAL_SHAPE_FORBIDDEN")
        return material


@dataclass(frozen=True)
class FileSecretRefVaultBackendV1:
    """File-backed SecretRef vault (JSON map). Material never written by resolver."""

    vault_file: Path
    backend_kind: str = VAULT_BACKEND_KIND

    def resolve_secretref_material_v1(self, *, secret_reference: str) -> str:
        ref = str(secret_reference or "").strip()
        if not ref.startswith("secretref:"):
            raise UnlockVaultResolverError("SECRET_REFERENCE_ONLY_REQUIRED")
        if not self.vault_file.is_file():
            raise UnlockVaultResolverError("VAULT_FILE_MISSING")
        payload = json.loads(self.vault_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise UnlockVaultResolverError("VAULT_FILE_NOT_OBJECT")
        if ref not in payload:
            raise UnlockVaultResolverError(f"SECRETREF_NOT_FOUND:{ref}")
        material = str(payload[ref])
        if material.startswith("plaintext:") or "\nAuthorization:" in material:
            raise UnlockVaultResolverError("VAULT_MATERIAL_SHAPE_FORBIDDEN")
        return material


def build_acceptance_fixture_vault_backend_v1(
    *,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
    material: str | None = None,
) -> InMemorySecretRefVaultBackendV1:
    """Synthetic non-secret fixture vault for pre-merge path certification."""
    fixture = material or json.dumps(
        {
            "api_key": "fixture-okx-testnet-key",
            "api_secret": "fixture-okx-testnet-secret-not-real",
            "passphrase": "fixture-passphrase-not-real",
        },
        separators=(",", ":"),
    )
    return InMemorySecretRefVaultBackendV1(mapping={secret_reference: fixture})


def vault_backend_to_dict_v1(backend: Any) -> dict[str, Any]:
    return {
        "backend_kind": getattr(backend, "backend_kind", VAULT_BACKEND_KIND),
        "plaintext_exposed": False,
        "plaintext_persisted": False,
    }
