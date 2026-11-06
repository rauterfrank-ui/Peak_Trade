"""Productive READ credential loader for execute_network (#6806 join slot).

Uses the existing §11.13.5 SecretRef vault contract and K1 venue-auth session
bind (same authority as authenticated private runtime read / 29P fresh GET).
Does not authorize POST, permit mint, or external effect.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    AuthenticatedPrivateRuntimeReadError,
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
)

CREDENTIAL_AUTHORITY = "SECTION_11_13_5_SECRETREF_VAULT_AND_K1_VENUE_AUTH_SESSION_V1"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_EXECUTE_NETWORK_READ_CREDENTIAL_LOADER_V1"
CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS = "CREDENTIAL_HANDLE_FAIL_CLOSED"


@dataclass(frozen=True)
class ProductiveReadCredentialVaultBackendV1:
    """Opaque vault backend token. Never carries credential material."""

    vault_path: str

    def __repr__(self) -> str:
        return "ProductiveReadCredentialVaultBackendV1(redacted)"


class ProductiveExecuteNetworkReadCredentialLoaderError(RuntimeError):
    """Fail-closed productive READ credential loader violation."""


def _fail_closed() -> None:
    raise RuntimeError(CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS)


def _assert_read_only_standing_pins_v1() -> None:
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise ProductiveExecuteNetworkReadCredentialLoaderError("POST_STANDING_MUST_REMAIN_FALSE")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise ProductiveExecuteNetworkReadCredentialLoaderError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")


def _parse_vault_material_ephemeral_v1(*, vault_file: Path) -> tuple[str, str, str]:
    try:
        secretref_identity_without_values_v1(vault_file=vault_file)
        payload = json.loads(vault_file.read_text(encoding="utf-8"))
    except AuthenticatedPrivateRuntimeReadError as exc:
        raise ProductiveExecuteNetworkReadCredentialLoaderError(str(exc)) from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ProductiveExecuteNetworkReadCredentialLoaderError(
            f"VAULT_FAIL_CLOSED:{type(exc).__name__}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise ProductiveExecuteNetworkReadCredentialLoaderError("VAULT_NOT_OBJECT")
    if REQUIRED_SECRETREF_URI not in payload:
        raise ProductiveExecuteNetworkReadCredentialLoaderError("SECRETREF_URI_UNBOUND")
    raw = payload[REQUIRED_SECRETREF_URI]
    if isinstance(raw, str):
        material = json.loads(raw)
    elif isinstance(raw, Mapping):
        material = raw
    else:
        raise ProductiveExecuteNetworkReadCredentialLoaderError("SECRETREF_MATERIAL_TYPE")
    if not isinstance(material, Mapping):
        raise ProductiveExecuteNetworkReadCredentialLoaderError("SECRETREF_MATERIAL_NOT_OBJECT")
    key = str(material.get("api_key") or "").strip()
    secret = str(material.get("api_secret") or "").strip()
    phrase = str(material.get("passphrase") or "").strip()
    if not key or not secret or not phrase:
        raise ProductiveExecuteNetworkReadCredentialLoaderError("CREDENTIAL_FIELDS_INCOMPLETE")
    return key, secret, phrase


def resolve_productive_read_credential_vault_backend_v1(
    *, vault_file: Path | str
) -> ProductiveReadCredentialVaultBackendV1:
    _assert_read_only_standing_pins_v1()
    path = Path(vault_file)
    secretref_identity_without_values_v1(vault_file=path)
    return ProductiveReadCredentialVaultBackendV1(vault_path=str(path.resolve()))


def acquire_productive_read_opaque_k1_handle_v1(
    *,
    secret_reference: str,
    vault_backend: ProductiveReadCredentialVaultBackendV1 | Path | str,
    credential_class: str,
) -> FullCoreK1BoundVenueAuthHandleV1:
    _assert_read_only_standing_pins_v1()
    if str(secret_reference or "").strip() != REQUIRED_SECRETREF_URI:
        _fail_closed()
    if str(credential_class or "").strip() != REQUIRED_CREDENTIAL_CLASS:
        _fail_closed()
    if isinstance(vault_backend, ProductiveReadCredentialVaultBackendV1):
        vault_path = Path(vault_backend.vault_path)
    else:
        vault_path = Path(vault_backend)
    key = secret = phrase = ""
    try:
        key, secret, phrase = _parse_vault_material_ephemeral_v1(vault_file=vault_path)
        handle = bind_already_held_k1_venue_auth_session_v1(
            api_key=key,
            api_secret=secret,
            passphrase=phrase,
        )
        return handle
    except ProductiveExecuteNetworkReadCredentialLoaderError:
        _fail_closed()
    except RuntimeError:
        raise
    except Exception as exc:
        raise ProductiveExecuteNetworkReadCredentialLoaderError(
            f"K1_BIND_FAIL_CLOSED:{type(exc).__name__}"
        ) from exc
    finally:
        key = ""
        secret = ""
        phrase = ""
    _fail_closed()


def release_productive_read_opaque_k1_handle_v1(handle: Any) -> None:
    if handle is None:
        return
    if not isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        _fail_closed()
    release_k1_venue_auth_session_v1(handle)


def productive_execute_network_read_credential_loader_v1(*_a: Any, **kwargs: Any) -> Any:
    """Multi-mode loader slot consumed by #6806 credential join (fail-closed default)."""

    if kwargs.get("handle") is not None:
        release_productive_read_opaque_k1_handle_v1(kwargs["handle"])
        return None
    if "repo_root" in kwargs:
        _fail_closed()
    if "vault_file" in kwargs and "secret_reference" not in kwargs:
        try:
            return resolve_productive_read_credential_vault_backend_v1(
                vault_file=kwargs["vault_file"]
            )
        except (
            ProductiveExecuteNetworkReadCredentialLoaderError,
            AuthenticatedPrivateRuntimeReadError,
        ):
            _fail_closed()
    if "secret_reference" in kwargs:
        try:
            backend = kwargs.get("vault_backend")
            if backend is None:
                _fail_closed()
            return acquire_productive_read_opaque_k1_handle_v1(
                secret_reference=str(kwargs.get("secret_reference") or ""),
                vault_backend=backend,
                credential_class=str(kwargs.get("credential_class") or ""),
            )
        except ProductiveExecuteNetworkReadCredentialLoaderError:
            _fail_closed()
    _fail_closed()
