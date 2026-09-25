"""FC-01 productive READ credential loader for execute_network join."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    prove_k1_signing_does_not_authorize_network_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_credential_join_v1 import (
    CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    bind_productive_read_only_get_transport_for_execute_network_v1,
    release_productive_credential_handle_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_read_credential_loader_v1 import (
    CREDENTIAL_AUTHORITY,
    acquire_productive_read_opaque_k1_handle_v1,
    productive_execute_network_read_credential_loader_v1,
    resolve_productive_read_credential_vault_backend_v1,
)

_REPO = Path(__file__).resolve().parents[2]
_FAKE_KEY = "unit-test-api-key-not-real"
_FAKE_SECRET = "unit-test-api-secret-not-real"
_FAKE_PASS = "unit-test-passphrase-not-real"


def _write_vault(path: Path, *, credential_class: str | None = None) -> None:
    material = {
        "api_key": _FAKE_KEY,
        "api_secret": _FAKE_SECRET,
        "passphrase": _FAKE_PASS,
    }
    if credential_class is not None:
        material["credential_class"] = credential_class
    path.write_text(
        json.dumps({REQUIRED_SECRETREF_URI: material}),
        encoding="utf-8",
    )


def test_missing_credential_fail_closed_no_network() -> None:
    transport, status, handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=True,
        fresh_get_transport=None,
        vault_file=None,
        repo_root=_REPO,
    )
    assert transport is None
    assert handle is None
    assert status == CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS


def test_authorized_vault_binds_opaque_k1_handle_and_transport(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    _write_vault(vault)
    backend = resolve_productive_read_credential_vault_backend_v1(vault_file=vault)
    handle = acquire_productive_read_opaque_k1_handle_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
    )
    assert isinstance(handle, FullCoreK1BoundVenueAuthHandleV1)
    assert handle.bound is True
    assert handle.material_loaded is False
    assert _FAKE_KEY not in repr(handle)
    assert _FAKE_KEY not in str(handle.to_dict())
    transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle)
    assert transport.request_count == 0
    release_productive_credential_handle_v1(handle)


def test_join_end_to_end_with_vault_no_network_until_get(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    _write_vault(vault)
    transport, status, handle = bind_productive_read_only_get_transport_for_execute_network_v1(
        execute_network=True,
        fresh_get_transport=None,
        vault_file=vault,
        repo_root=_REPO,
    )
    assert status == ""
    assert transport is not None
    assert handle is not None
    assert transport.request_count == 0
    release_productive_credential_handle_v1(handle)


def test_invalid_credential_class_fail_closed(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    _write_vault(vault)
    with pytest.raises(RuntimeError, match=CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS):
        acquire_productive_read_opaque_k1_handle_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=resolve_productive_read_credential_vault_backend_v1(vault_file=vault),
            credential_class="WRONG_CLASS",
        )


def test_secrets_not_in_loader_exceptions(tmp_path: Path) -> None:
    vault = tmp_path / "bad.json"
    vault.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match=CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS) as exc_info:
        productive_execute_network_read_credential_loader_v1(vault_file=vault)
    assert _FAKE_SECRET not in str(exc_info.value)
    assert _FAKE_KEY not in str(exc_info.value)


def test_read_authorization_does_not_imply_post() -> None:
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    proof = prove_k1_signing_does_not_authorize_network_v1()
    assert proof["MAY_POST"] == "false"
    assert proof["EXTERNAL_EFFECT_AUTHORIZED"] == "false"
    assert CREDENTIAL_AUTHORITY.startswith("SECTION_11_13_5")
