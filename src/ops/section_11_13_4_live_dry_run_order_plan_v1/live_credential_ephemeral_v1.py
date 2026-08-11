"""LIVE-scoped ephemeral SecretRef credential borrow/release for §11.13.4.

Reuses FileSecretRefVaultBackendV1. Does NOT call the Testnet-hardcoded
ephemeral loader. Plaintext never persists to disk or evidence.
Authoring/unlock does not borrow productive material; only the later
Owner-authorized execute path may resolve vault material.
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
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.secretref_v1 import (
    LiveDryRunOrderPlanSecretRefError,
    validate_live_dry_run_order_plan_secretref_uri_v1,
)


class LiveDryRunOrderPlanCredentialError(RuntimeError):
    """Fail-closed LIVE dry-run-order-plan credential borrow/release violation."""


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
        raise LiveDryRunOrderPlanCredentialError("VAULT_FILE_MISSING")
    return FileSecretRefVaultBackendV1(vault_file=path)


def parse_okx_live_ro_material_v1(material: str) -> dict[str, str]:
    try:
        payload = json.loads(material)
    except json.JSONDecodeError as exc:
        raise LiveDryRunOrderPlanCredentialError("CREDENTIAL_MATERIAL_NOT_JSON") from exc
    if not isinstance(payload, dict):
        raise LiveDryRunOrderPlanCredentialError("CREDENTIAL_MATERIAL_NOT_OBJECT")
    key = str(payload.get("api_key") or "").strip()
    secret = str(payload.get("api_secret") or "").strip()
    passphrase = str(payload.get("passphrase") or "").strip()
    if not key or not secret or not passphrase:
        raise LiveDryRunOrderPlanCredentialError("CREDENTIAL_FIELDS_INCOMPLETE")
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
        raise LiveDryRunOrderPlanCredentialError("SECRETREF_SCOPE_MUST_BE_LIVE")
    if str(credential_class or "").strip() != REQUIRED_CREDENTIAL_CLASS:
        raise LiveDryRunOrderPlanCredentialError(
            "LIVE_DRY_RUN_ORDER_PLAN_CREDENTIAL_CLASS_REQUIRED"
        )
    try:
        ref = validate_live_dry_run_order_plan_secretref_uri_v1(secret_reference)
    except LiveDryRunOrderPlanSecretRefError as exc:
        raise LiveDryRunOrderPlanCredentialError(str(exc)) from exc
    if vault_backend is None:
        raise LiveDryRunOrderPlanCredentialError("REAL_VAULT_BACKEND_REQUIRED")
    try:
        material = str(vault_backend.resolve_secretref_material_v1(secret_reference=ref))
    except Exception as exc:  # noqa: BLE001 — normalize vault backend errors
        raise LiveDryRunOrderPlanCredentialError(
            f"VAULT_RESOLVE_FAILED:{type(exc).__name__}"
        ) from exc
    if material.startswith("plaintext:") or "\nAuthorization:" in material:
        raise LiveDryRunOrderPlanCredentialError("VAULT_MATERIAL_SHAPE_FORBIDDEN")
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
        raise LiveDryRunOrderPlanCredentialError("EPHEMERAL_MATERIAL_GONE")
    return material


def release_live_ephemeral_material_v1(handle: LiveEphemeralCredentialHandleV1) -> None:
    _MATERIAL.pop(handle.handle_id, None)


def assert_no_plaintext_in_payload_v1(payload: Any) -> None:
    text = str(payload).lower()
    for needle in ("sk-", "plaintext:", "authorization: bearer"):
        if needle in text:
            raise LiveDryRunOrderPlanCredentialError(f"PLAINTEXT_LEAK_DETECTED:{needle}")
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            kl = str(key).lower()
            if kl in {"api_secret", "passphrase", "api_key", "secret", "ok-access-key"}:
                if isinstance(value, str) and value and value not in {"<REDACTED>", "<REF_ONLY>"}:
                    if not value.startswith("secretref-digest:") and not value.startswith("<"):
                        raise LiveDryRunOrderPlanCredentialError(f"PLAINTEXT_LEAK_DETECTED:{kl}")
