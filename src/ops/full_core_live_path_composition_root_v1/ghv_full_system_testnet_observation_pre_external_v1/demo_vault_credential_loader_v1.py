"""Fail-closed SecretRef vault loader for GHV Demo GET-only credential bind.

Resolves secretref://vault/peak-trade/testnet-demo from operator-local vault JSON
(outside repo by convention). Does not authorize POST, GHV observation, or external effect.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    DEFAULT_VAULT_RELATIVE,
    DEMO_SECRET_REFERENCE,
    VAULT_FILE_ENV_VAR,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_okx_venue_auth_headers_v1 import (
    FullCoreDemoBoundVenueAuthHandleV1,
    bind_already_held_demo_venue_auth_session_v1,
    release_demo_venue_auth_session_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS as LIVE_K1_REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI as LIVE_K1_SECRETREF_URI,
)

JOIN_SEAM_ID = "GHV_FULL_SYSTEM_TESTNET_OBSERVATION_DEMO_SECRETREF_VAULT_LOADER_V1"
CREDENTIAL_AUTHORITY = "GHV_DEMO_SECRETREF_VAULT_AND_DEMO_VENUE_AUTH_SESSION_V1"


class GhvTestnetDemoSecretrefVaultLoaderError(RuntimeError):
    """Fail-closed Demo SecretRef vault loader violation."""


@dataclass(frozen=True)
class GhvTestnetDemoCredentialVaultBackendV1:
    """Opaque vault backend token. Never carries credential material."""

    vault_path: str

    def __repr__(self) -> str:
        return "GhvTestnetDemoCredentialVaultBackendV1(redacted)"


def _assert_read_only_standing_pins_v1() -> None:
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise GhvTestnetDemoSecretrefVaultLoaderError("POST_STANDING_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise GhvTestnetDemoSecretrefVaultLoaderError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")


def resolve_ghv_testnet_demo_vault_file_v1(*, vault_file: Path | str | None = None) -> Path:
    """Resolve operator-local vault path. Never searches repo tracked paths for secrets."""

    _assert_read_only_standing_pins_v1()
    if vault_file is not None and str(vault_file).strip():
        path = Path(vault_file).expanduser()
    else:
        env_path = str(os.environ.get(VAULT_FILE_ENV_VAR) or "").strip()
        if env_path:
            path = Path(env_path).expanduser()
        else:
            path = Path.cwd() / DEFAULT_VAULT_RELATIVE
    resolved = path.resolve()
    if not resolved.is_file():
        raise GhvTestnetDemoSecretrefVaultLoaderError("VAULT_FILE_MISSING")
    return resolved


def demo_secretref_identity_without_values_v1(*, vault_file: Path | str) -> dict[str, Any]:
    """Prove SecretRef binding by URI and field lengths only. Never returns values."""

    _assert_read_only_standing_pins_v1()
    path = Path(vault_file)
    if not path.is_file():
        raise GhvTestnetDemoSecretrefVaultLoaderError("VAULT_FILE_MISSING")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GhvTestnetDemoSecretrefVaultLoaderError("VAULT_FILE_NOT_JSON") from exc
    if not isinstance(payload, Mapping):
        raise GhvTestnetDemoSecretrefVaultLoaderError("VAULT_FILE_NOT_OBJECT")
    if DEMO_SECRET_REFERENCE not in payload:
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_URI_UNBOUND")
    raw = payload[DEMO_SECRET_REFERENCE]
    if isinstance(raw, str):
        try:
            material = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_MATERIAL_NOT_JSON") from exc
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_MATERIAL_TYPE_FORBIDDEN")
    if not isinstance(material, Mapping):
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_MATERIAL_NOT_OBJECT")
    declared_class = str(material.get("credential_class") or "").strip()
    if declared_class and declared_class != CREDENTIAL_CLASS:
        raise GhvTestnetDemoSecretrefVaultLoaderError("DEMO_CREDENTIAL_CLASS_REJECTED")
    if declared_class == LIVE_K1_REQUIRED_CREDENTIAL_CLASS:
        raise GhvTestnetDemoSecretrefVaultLoaderError("LIVE_CREDENTIAL_IN_DEMO_BIND_REJECTED")
    key_len = len(str(material.get("api_key") or "").strip())
    secret_len = len(str(material.get("api_secret") or "").strip())
    passphrase_len = len(str(material.get("passphrase") or "").strip())
    if key_len <= 0 or secret_len <= 0 or passphrase_len <= 0:
        raise GhvTestnetDemoSecretrefVaultLoaderError("CREDENTIAL_FIELDS_INCOMPLETE")
    return {
        "VAULT_FILE_PRESENT": True,
        "SECRETREF_URI_BOUND": True,
        "SECRETREF_URI": DEMO_SECRET_REFERENCE,
        "CREDENTIAL_CLASS": CREDENTIAL_CLASS,
        "API_KEY_LEN": key_len,
        "API_SECRET_LEN": secret_len,
        "PASSPHRASE_LEN": passphrase_len,
        "VALUES_INCLUDED": False,
    }


def _parse_demo_vault_material_ephemeral_v1(*, vault_file: Path) -> tuple[str, str, str]:
    demo_secretref_identity_without_values_v1(vault_file=vault_file)
    payload = json.loads(vault_file.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise GhvTestnetDemoSecretrefVaultLoaderError("VAULT_FILE_NOT_OBJECT")
    raw = payload[DEMO_SECRET_REFERENCE]
    if isinstance(raw, str):
        material = json.loads(raw)
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_MATERIAL_TYPE_FORBIDDEN")
    if not isinstance(material, Mapping):
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_MATERIAL_NOT_OBJECT")
    key = str(material.get("api_key") or "").strip()
    secret = str(material.get("api_secret") or "").strip()
    phrase = str(material.get("passphrase") or "").strip()
    if not key or not secret or not phrase:
        raise GhvTestnetDemoSecretrefVaultLoaderError("CREDENTIAL_FIELDS_INCOMPLETE")
    return key, secret, phrase


def resolve_ghv_testnet_demo_credential_vault_backend_v1(
    *, vault_file: Path | str | None = None
) -> GhvTestnetDemoCredentialVaultBackendV1:
    path = resolve_ghv_testnet_demo_vault_file_v1(vault_file=vault_file)
    demo_secretref_identity_without_values_v1(vault_file=path)
    return GhvTestnetDemoCredentialVaultBackendV1(vault_path=str(path))


def acquire_ghv_testnet_demo_opaque_handle_v1(
    *,
    secret_reference: str,
    vault_backend: GhvTestnetDemoCredentialVaultBackendV1 | Path | str,
    credential_class: str = CREDENTIAL_CLASS,
) -> FullCoreDemoBoundVenueAuthHandleV1:
    _assert_read_only_standing_pins_v1()
    if str(secret_reference or "").strip() != DEMO_SECRET_REFERENCE:
        raise GhvTestnetDemoSecretrefVaultLoaderError("SECRETREF_URI_MISMATCH")
    if str(credential_class or "").strip() != CREDENTIAL_CLASS:
        raise GhvTestnetDemoSecretrefVaultLoaderError("DEMO_CREDENTIAL_CLASS_REJECTED")
    if str(credential_class or "").strip() == LIVE_K1_REQUIRED_CREDENTIAL_CLASS:
        raise GhvTestnetDemoSecretrefVaultLoaderError("LIVE_CREDENTIAL_IN_DEMO_BIND_REJECTED")
    if isinstance(vault_backend, GhvTestnetDemoCredentialVaultBackendV1):
        vault_path = Path(vault_backend.vault_path)
    else:
        vault_path = Path(vault_backend)
    key = secret = phrase = ""
    try:
        key, secret, phrase = _parse_demo_vault_material_ephemeral_v1(vault_file=vault_path)
        return bind_already_held_demo_venue_auth_session_v1(
            api_key=key,
            api_secret=secret,
            passphrase=phrase,
            credential_class=CREDENTIAL_CLASS,
        )
    finally:
        key = ""
        secret = ""
        phrase = ""


def release_ghv_testnet_demo_opaque_handle_v1(handle: FullCoreDemoBoundVenueAuthHandleV1) -> None:
    release_demo_venue_auth_session_v1(handle)


def prove_demo_credential_presence_gate_v1(
    *, vault_file: Path | str | None = None
) -> dict[str, bool]:
    """Boolean-only gate for preflight. Does not return reconstructable material."""

    out = {
        "DEMO_SECRETREF_RESOLVABLE": False,
        "DEMO_API_KEY_PRESENT": False,
        "DEMO_SECRET_PRESENT": False,
        "DEMO_PASSPHRASE_PRESENT": False,
        "DEMO_CREDENTIAL_SET_COMPLETE": False,
        "DEMO_CREDENTIAL_CLASS_VALID": False,
        "DEMO_CREDENTIAL_DISTINCT_FROM_K1": True,
        "K1_FALLBACK_POSSIBLE": False,
    }
    try:
        path = resolve_ghv_testnet_demo_vault_file_v1(vault_file=vault_file)
        identity = demo_secretref_identity_without_values_v1(vault_file=path)
    except GhvTestnetDemoSecretrefVaultLoaderError:
        return out
    out["DEMO_SECRETREF_RESOLVABLE"] = True
    out["DEMO_API_KEY_PRESENT"] = int(identity.get("API_KEY_LEN") or 0) > 0
    out["DEMO_SECRET_PRESENT"] = int(identity.get("API_SECRET_LEN") or 0) > 0
    out["DEMO_PASSPHRASE_PRESENT"] = int(identity.get("PASSPHRASE_LEN") or 0) > 0
    out["DEMO_CREDENTIAL_CLASS_VALID"] = (
        str(identity.get("CREDENTIAL_CLASS") or "") == CREDENTIAL_CLASS
    )
    out["DEMO_CREDENTIAL_SET_COMPLETE"] = (
        out["DEMO_API_KEY_PRESENT"]
        and out["DEMO_SECRET_PRESENT"]
        and out["DEMO_PASSPHRASE_PRESENT"]
        and out["DEMO_CREDENTIAL_CLASS_VALID"]
    )
    return out


def load_ghv_testnet_demo_credential_handle_v1(
    *,
    vault_file: Path | str | None = None,
) -> FullCoreDemoBoundVenueAuthHandleV1:
    """Default credential_loader for GHV Demo transport bind (GET-only)."""

    backend = resolve_ghv_testnet_demo_credential_vault_backend_v1(vault_file=vault_file)
    handle = acquire_ghv_testnet_demo_opaque_handle_v1(
        secret_reference=DEMO_SECRET_REFERENCE,
        vault_backend=backend,
        credential_class=CREDENTIAL_CLASS,
    )
    if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        raise GhvTestnetDemoSecretrefVaultLoaderError("LIVE_K1_HANDLE_IN_DEMO_BIND_REJECTED")
    return handle


def load_ghv_testnet_demo_credential_handle_for_bind_v1() -> FullCoreDemoBoundVenueAuthHandleV1:
    """Zero-arg loader slot consumed by open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1."""

    return load_ghv_testnet_demo_credential_handle_v1()
