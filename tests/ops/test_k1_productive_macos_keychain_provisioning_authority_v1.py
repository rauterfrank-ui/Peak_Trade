"""Bounded K1 macOS Keychain provisioning authority tests (injected backend only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.k1_productive_macos_keychain_provisioning_authority_v1.constants_v1 import (
    K2_REINTRODUCED,
    OWNER_GO,
    REAL_KEYCHAIN_WRITE_AUTHORIZED,
    WRITE_AUTHORIZATION_DEFAULT,
)
from src.ops.k1_productive_macos_keychain_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)
from src.ops.k1_productive_macos_keychain_provisioning_authority_v1.provisioning_authority_v1 import (
    prove_provisioning_standing_gates_v1,
    provision_bound_k1_productive_macos_keychain_material_v1,
)
from src.ops.k1_productive_macos_keychain_provisioning_authority_v1.provisioning_backend_v1 import (
    MacosSecurityFrameworkProvisioningBackendV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = REPO_ROOT / "src/ops/k1_productive_macos_keychain_provisioning_authority_v1"

VALID_KEY = "11111111-2222-3333-4444-555555555555"
VALID_SECRET = "VALID_SECRET_KEY_MATERIAL_32CHARS__"
VALID_PASS = "VALID_PASSPHRASE_MATERIAL__"
SENTINEL_SECRET = "SENTINEL-SECRET-MUST-NOT-LEAK-XY99"


@dataclass
class _FakeProvisioningBackend:
    calls: list[tuple[str, str, bytes]] = field(default_factory=list)

    def upsert_bound_generic_password_opaque_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
        opaque: bytes,
    ) -> None:
        del item_class
        self.calls.append((service, account, opaque))


def test_default_write_denied_without_owner_go() -> None:
    with pytest.raises(K1ProductiveMacosKeychainProvisioningError, match="OWNER_GO_MISMATCH"):
        provision_bound_k1_productive_macos_keychain_material_v1(
            owner_go="",
            source_ref_uri=SOURCE_REF_URI,
            api_key=VALID_KEY,
            api_secret=VALID_SECRET,
            passphrase=VALID_PASS,
            backend=_FakeProvisioningBackend(),
        )


def test_wrong_owner_go_denied() -> None:
    with pytest.raises(K1ProductiveMacosKeychainProvisioningError, match="OWNER_GO_MISMATCH"):
        provision_bound_k1_productive_macos_keychain_material_v1(
            owner_go="OWNER_GO_WRONG",
            source_ref_uri=SOURCE_REF_URI,
            api_key=VALID_KEY,
            api_secret=VALID_SECRET,
            passphrase=VALID_PASS,
            backend=_FakeProvisioningBackend(),
        )


def test_wrong_service_denied() -> None:
    backend = MacosSecurityFrameworkProvisioningBackendV1()
    with pytest.raises(
        K1ProductiveMacosKeychainProvisioningError, match="KEYCHAIN_IDENTITY_MISMATCH"
    ):
        backend.upsert_bound_generic_password_opaque_v1(
            service="other.service",
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
            opaque=b"{}",
        )


def test_wrong_account_denied() -> None:
    backend = MacosSecurityFrameworkProvisioningBackendV1()
    with pytest.raises(
        K1ProductiveMacosKeychainProvisioningError, match="KEYCHAIN_IDENTITY_MISMATCH"
    ):
        backend.upsert_bound_generic_password_opaque_v1(
            service=KEYCHAIN_SERVICE_ID,
            account="other.account",
            item_class=KEYCHAIN_ITEM_CLASS,
            opaque=b"{}",
        )


def test_malformed_schema_denied() -> None:
    with pytest.raises(K1ProductiveMacosKeychainProvisioningError, match="MALFORMED_SCHEMA"):
        provision_bound_k1_productive_macos_keychain_material_v1(
            owner_go=OWNER_GO,
            source_ref_uri=SOURCE_REF_URI,
            api_key="",
            api_secret=VALID_SECRET,
            passphrase=VALID_PASS,
            backend=_FakeProvisioningBackend(),
        )


def test_placeholder_class_denied() -> None:
    with pytest.raises(K1ProductiveMacosKeychainProvisioningError, match="PLACEHOLDER"):
        provision_bound_k1_productive_macos_keychain_material_v1(
            owner_go=OWNER_GO,
            source_ref_uri=SOURCE_REF_URI,
            api_key="x",
            api_secret="x",
            passphrase="x",
            backend=_FakeProvisioningBackend(),
        )


def test_secret_output_denied_in_proof() -> None:
    fake = _FakeProvisioningBackend()
    proof = provision_bound_k1_productive_macos_keychain_material_v1(
        owner_go=OWNER_GO,
        source_ref_uri=SOURCE_REF_URI,
        api_key=VALID_KEY,
        api_secret=SENTINEL_SECRET,
        passphrase=VALID_PASS,
        backend=fake,
    )
    blob = repr(proof) + str(proof.to_dict())
    assert SENTINEL_SECRET not in blob
    assert VALID_SECRET not in blob


def test_alternative_backend_denied() -> None:
    with pytest.raises(
        K1ProductiveMacosKeychainProvisioningError,
        match="ALTERNATE_BACKEND_SOURCE_REF_FORBIDDEN",
    ):
        provision_bound_k1_productive_macos_keychain_material_v1(
            owner_go=OWNER_GO,
            source_ref_uri="fullcore-cred://provider-ref/other",
            api_key=VALID_KEY,
            api_secret=VALID_SECRET,
            passphrase=VALID_PASS,
            backend=_FakeProvisioningBackend(),
        )


def test_valid_bounded_provisioning_contract_pass() -> None:
    fake = _FakeProvisioningBackend()
    proof = provision_bound_k1_productive_macos_keychain_material_v1(
        owner_go=OWNER_GO,
        source_ref_uri=SOURCE_REF_URI,
        api_key=VALID_KEY,
        api_secret=VALID_SECRET,
        passphrase=VALID_PASS,
        backend=fake,
    )
    assert proof.disposition == "PROVISIONING_UPSERT_PASS"
    assert len(fake.calls) == 1
    service, account, opaque = fake.calls[0]
    assert service == KEYCHAIN_SERVICE_ID
    assert account == KEYCHAIN_ACCOUNT_ID
    assert b"apiKey" in opaque and b"secretKey" in opaque


def test_standing_gates_and_authority_flags() -> None:
    gates = prove_provisioning_standing_gates_v1()
    assert gates["WRITE_AUTHORIZATION_DEFAULT"] == "false"
    assert gates["REAL_KEYCHAIN_WRITE_AUTHORIZED"] == "false"
    assert WRITE_AUTHORIZATION_DEFAULT is False
    assert REAL_KEYCHAIN_WRITE_AUTHORIZED is False
    assert K2_REINTRODUCED is False


def test_k2_legacy_not_used_and_no_network_imports() -> None:
    text = "\n".join(p.read_text(encoding="utf-8") for p in MODULE_DIR.glob("*.py"))
    for forbidden in (
        "secretref",
        "SecretRef",
        "file_vault",
        "import urllib",
        "from urllib",
        "import requests",
        "import socket",
    ):
        assert forbidden not in text
    assert "K2_REINTRODUCED = False" in text


def test_real_macos_backend_requires_ephemeral_scope() -> None:
    backend = MacosSecurityFrameworkProvisioningBackendV1()
    with pytest.raises(
        K1ProductiveMacosKeychainProvisioningError,
        match="EPHEMERAL_PROVISIONING_SCOPE_REQUIRED",
    ):
        backend.upsert_bound_generic_password_opaque_v1(
            service=KEYCHAIN_SERVICE_ID,
            account=KEYCHAIN_ACCOUNT_ID,
            item_class=KEYCHAIN_ITEM_CLASS,
            opaque=b'{"apiKey":"a","secretKey":"b","passphrase":"c"}',
        )
