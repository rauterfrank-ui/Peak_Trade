"""Bounded K1 macOS Keychain provisioning authority (Owner-GO gated upsert only)."""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PROVIDER_REF_IDENTIFIER,
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.constants_v1 import (
    EPHEMERAL_PROVISIONING_CONSUMER,
    EXTERNAL_EFFECT_AUTHORIZED,
    K2_REINTRODUCED,
    NETWORK_EXECUTION_AUTHORIZED,
    OWNER_GO,
    REAL_KEYCHAIN_WRITE_AUTHORIZED,
    WRITE_AUTHORIZATION_DEFAULT,
    WP_ID,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.errors_v1 import (
    K1ProductiveMacosKeychainProvisioningError,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.material_policy_v1 import (
    assert_provisioning_material_policy_v1,
    public_material_shape_proof_v1,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.provisioning_backend_v1 import (
    MacosSecurityFrameworkProvisioningBackendV1,
    OsNativeStoreProvisioningBackendV1,
)
from src.ops.k1_productive_macos_credential_store_provisioning_authority_v1.provisioning_context_v1 import (
    bounded_ephemeral_keychain_provisioning_v1,
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


@dataclass(frozen=True)
class K1ProductiveMacosKeychainProvisioningProofV1:
    disposition: str
    wp_id: str
    owner_go_accepted: str
    source_ref_uri: str
    keychain_service_id: str
    keychain_account_id: str
    provider_ref_identifier: str
    write_performed: str
    material_shape: dict[str, str]

    def to_dict(self) -> dict[str, str]:
        out = {
            "disposition": self.disposition,
            "wp_id": self.wp_id,
            "owner_go_accepted": self.owner_go_accepted,
            "source_ref_uri": self.source_ref_uri,
            "keychain_service_id": self.keychain_service_id,
            "keychain_account_id": self.keychain_account_id,
            "provider_ref_identifier": self.provider_ref_identifier,
            "write_performed": self.write_performed,
        }
        for key, value in self.material_shape.items():
            out[f"shape_{key}"] = value
        return out

    def __repr__(self) -> str:
        return "K1ProductiveMacosKeychainProvisioningProofV1(redacted)"


def prove_provisioning_standing_gates_v1() -> dict[str, str]:
    _assert_standing_pins_v1()
    return {
        "WRITE_AUTHORIZATION_DEFAULT": str(WRITE_AUTHORIZATION_DEFAULT).lower(),
        "REAL_KEYCHAIN_WRITE_AUTHORIZED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "NETWORK_EXECUTION_AUTHORIZED": FALSE_TOKEN,
        "K2_REINTRODUCED": str(K2_REINTRODUCED).lower(),
    }


def provision_bound_k1_productive_macos_keychain_material_v1(
    *,
    owner_go: str,
    source_ref_uri: str,
    api_key: str,
    api_secret: str,
    passphrase: str,
    backend: OsNativeStoreProvisioningBackendV1 | None = None,
) -> K1ProductiveMacosKeychainProvisioningProofV1:
    """Upsert opaque UTF-8 JSON at the DZ-bound Keychain tuple. Requires Owner-GO + ephemeral scope."""

    _assert_standing_pins_v1()
    if str(owner_go or "").strip() != OWNER_GO:
        raise K1ProductiveMacosKeychainProvisioningError("OWNER_GO_MISMATCH")
    if WRITE_AUTHORIZATION_DEFAULT is True:
        raise K1ProductiveMacosKeychainProvisioningError(
            "WRITE_AUTHORIZATION_DEFAULT_MUST_REMAIN_FALSE"
        )
    if str(source_ref_uri or "").strip() != SOURCE_REF_URI:
        raise K1ProductiveMacosKeychainProvisioningError("ALTERNATE_BACKEND_SOURCE_REF_FORBIDDEN")

    key = str(api_key or "")
    secret = str(api_secret or "")
    phrase = str(passphrase or "")
    needles = (key, secret, phrase)
    opaque: bytes = b""
    shape: dict[str, str] = {}
    try:
        opaque = assert_provisioning_material_policy_v1(
            api_key=key,
            api_secret=secret,
            passphrase=phrase,
        )
        write_backend = (
            backend if backend is not None else MacosSecurityFrameworkProvisioningBackendV1()
        )
        with bounded_ephemeral_keychain_provisioning_v1(
            consumer_id=EPHEMERAL_PROVISIONING_CONSUMER
        ):
            write_backend.upsert_bound_generic_password_opaque_v1(
                service=KEYCHAIN_SERVICE_ID,
                account=KEYCHAIN_ACCOUNT_ID,
                item_class=KEYCHAIN_ITEM_CLASS,
                opaque=opaque,
            )
        shape = public_material_shape_proof_v1(opaque=opaque)
    finally:
        key = ""
        secret = ""
        phrase = ""
        opaque = b""

    proof = K1ProductiveMacosKeychainProvisioningProofV1(
        disposition="PROVISIONING_UPSERT_PASS",
        wp_id=WP_ID,
        owner_go_accepted=TRUE_TOKEN,
        source_ref_uri=SOURCE_REF_URI,
        keychain_service_id=KEYCHAIN_SERVICE_ID,
        keychain_account_id=KEYCHAIN_ACCOUNT_ID,
        provider_ref_identifier=PROVIDER_REF_IDENTIFIER,
        write_performed=TRUE_TOKEN,
        material_shape=shape,
    )
    _assert_proof_has_no_plaintext_secrets_v1(proof=proof, needles=needles)
    return proof


def _assert_standing_pins_v1() -> None:
    if REAL_KEYCHAIN_WRITE_AUTHORIZED is True:
        raise K1ProductiveMacosKeychainProvisioningError(
            "REAL_KEYCHAIN_WRITE_MUST_REMAIN_UNAUTHORIZED"
        )
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise K1ProductiveMacosKeychainProvisioningError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if NETWORK_EXECUTION_AUTHORIZED is True:
        raise K1ProductiveMacosKeychainProvisioningError("NETWORK_MUST_REMAIN_UNAUTHORIZED")
    if K2_REINTRODUCED is True:
        raise K1ProductiveMacosKeychainProvisioningError("K2_REINTRODUCED_FORBIDDEN")


def _assert_proof_has_no_plaintext_secrets_v1(
    *,
    proof: K1ProductiveMacosKeychainProvisioningProofV1,
    needles: tuple[str, ...],
) -> None:
    blob = repr(proof) + str(proof.to_dict())
    for needle in needles:
        if needle and len(needle) >= 4 and needle in blob:
            raise K1ProductiveMacosKeychainProvisioningError("SECRET_LEAK_IN_PUBLIC_SURFACE")
