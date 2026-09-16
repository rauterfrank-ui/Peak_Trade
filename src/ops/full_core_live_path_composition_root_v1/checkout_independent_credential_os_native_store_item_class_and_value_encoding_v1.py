"""Offline Full-Core macOS Keychain item-class and value-encoding V1.

Owner-GO bind only, for the already-canonical DZ identifier tuple:

KEYCHAIN_SERVICE_ID=peak-trade.full-core.venue-credentials
KEYCHAIN_ACCOUNT_ID=okx-eea.productive
PROVIDER_REF_IDENTIFIER=okx-eea-productive

OS-semantic necessity given that tuple: generic-password is the Keychain
item class whose query attributes are service + account. Internet-password
requires unbound server/protocol attributes. Certificate/key/identity
classes are not secret-value items keyed by service + account.

OS-semantic necessity for stored value: Keychain kSecValueData is opaque
bytes, not a string object.

Minimal Owner decision authorized by this GO: when those bytes are later
interpreted as text, the encoding is utf-8. This is not a payload schema.
Canary/File-Vault JSON field names are not bound.

This slice does not access Keychain, load credential material, join V5,
activate a productive provider, or mint selection/trading/POST authority.

OWNER_GO=OWNER_GO_BIND_FULL_CORE_MACOS_KEYCHAIN_ITEM_CLASS_AND_VALUE_ENCODING_OFFLINE_CONTRACT_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, NoReturn

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    prove_capability_cannot_mutate_standing_gates_v1,
    prove_capability_does_not_upgrade_standing_gates_v1,
    prove_capability_grants_no_trading_or_post_authority_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    PROVIDER_REF_IDENTIFIER,
    SOURCE_REF_URI,
    prove_authority_non_interference_v1,
    prove_concrete_keychain_item_identity_bound_v1,
    resolve_bound_keychain_item_identity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    SOURCE_BACKEND_CLASS,
    acquire_offline_ephemeral_capability_v1,
)

OWNER_GO = (
    "OWNER_GO_BIND_FULL_CORE_MACOS_KEYCHAIN_ITEM_CLASS_AND_VALUE_ENCODING_OFFLINE_CONTRACT_V1"
)
THIS_SLICE = "11.2.1.EB.FULL_CORE_MACOS_KEYCHAIN_ITEM_CLASS_AND_VALUE_ENCODING"
CONTRACT_VERSION = "v1"
KEYCHAIN_ITEM_CLASS = "generic-password"
KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME = "kSecClassGenericPassword"
KEYCHAIN_VALUE_DATA_REPRESENTATION = "BYTES"
KEYCHAIN_VALUE_ENCODING = "utf-8"
KEYCHAIN_VALUE_TEXT_ENCODING = KEYCHAIN_VALUE_ENCODING
PAYLOAD_SCHEMA_BOUND = False
KEYCHAIN_ITEM_CLASS_BOUND = True
KEYCHAIN_VALUE_ENCODING_BOUND = True
REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False
V5_USES_NEW_PROVIDER = False
PRODUCTIVE_BACKEND_JOINED = False
CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE = False
EPHEMERAL_MATERIAL_PATH_IMPLEMENTED = False
MATERIAL_LOADED_TRUE_REACHABLE = False

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

FORBIDDEN_ITEM_CLASSES = frozenset(
    {
        "internet-password",
        "certificate",
        "key",
        "identity",
        "apple-share-password",
    }
)
FORBIDDEN_VALUE_ENCODINGS = frozenset(
    {
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "latin-1",
        "ascii",
        "utf-8-sig",
        "hex",
        "base64",
    }
)
FORBIDDEN_PAYLOAD_SCHEMA_FIELD_NAMES = frozenset(
    {
        "api_key",
        "api_secret",
        "passphrase",
        "ok-access-key",
        "ok-access-sign",
        "ok-access-passphrase",
    }
)
_FORBIDDEN_MAPPING_AUTHORITY_KEYS = (
    "selection_authority",
    "trading_decision_authority",
    "risk_authority",
    "admission_authority",
    "external_effect_authority",
    "post_authority",
    "send_authority",
    "side",
    "quantity",
    "submission_authority",
)


class FullCoreCheckoutIndependentCredentialMacosKeychainItemClassAndValueEncodingError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed item-class and value-encoding contract violation."""


@dataclass(frozen=True)
class FullCoreMacosKeychainItemClassAndValueEncodingV1:
    """Identifier-only item-class and encoding. Not possession or payload."""

    provider_ref_identifier: str
    source_ref_uri: str
    keychain_service_id: str
    keychain_account_id: str
    keychain_item_class: str
    keychain_item_class_os_constant_name: str
    keychain_value_data_representation: str
    keychain_value_encoding: str
    payload_schema_bound: str
    real_keychain_accessed: str
    credential_material_loaded: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider_ref_identifier": self.provider_ref_identifier,
            "source_ref_uri": self.source_ref_uri,
            "keychain_service_id": self.keychain_service_id,
            "keychain_account_id": self.keychain_account_id,
            "keychain_item_class": self.keychain_item_class,
            "keychain_item_class_os_constant_name": (self.keychain_item_class_os_constant_name),
            "keychain_value_data_representation": self.keychain_value_data_representation,
            "keychain_value_encoding": self.keychain_value_encoding,
            "payload_schema_bound": self.payload_schema_bound,
            "real_keychain_accessed": self.real_keychain_accessed,
            "credential_material_loaded": self.credential_material_loaded,
        }


def _error(code: str) -> NoReturn:
    raise FullCoreCheckoutIndependentCredentialMacosKeychainItemClassAndValueEncodingError(code)


def assert_keychain_item_class_v1(raw: str) -> str:
    value = str(raw or "")
    if value != value.strip() or value != value.lower():
        _error("KEYCHAIN_ITEM_CLASS_NORMALIZATION_FORBIDDEN")
    if value in FORBIDDEN_ITEM_CLASSES:
        _error("KEYCHAIN_ITEM_CLASS_FORBIDDEN")
    if value != KEYCHAIN_ITEM_CLASS:
        _error("KEYCHAIN_ITEM_CLASS_DRIFT")
    return value


def assert_keychain_value_encoding_v1(raw: str) -> str:
    value = str(raw or "")
    if value != value.strip() or value != value.lower():
        _error("KEYCHAIN_VALUE_ENCODING_NORMALIZATION_FORBIDDEN")
    if value in FORBIDDEN_VALUE_ENCODINGS:
        _error("KEYCHAIN_VALUE_ENCODING_FORBIDDEN")
    if value != KEYCHAIN_VALUE_ENCODING:
        _error("KEYCHAIN_VALUE_ENCODING_DRIFT")
    return value


def prove_payload_schema_unbound_v1(payload: Mapping[str, str]) -> dict[str, str]:
    if PAYLOAD_SCHEMA_BOUND is True:
        _error("PAYLOAD_SCHEMA_MUST_REMAIN_UNBOUND")
    for field in FORBIDDEN_PAYLOAD_SCHEMA_FIELD_NAMES:
        if field in payload:
            _error("PAYLOAD_SCHEMA_FIELD_MUST_NOT_BE_BOUND")
        if field in payload.values():
            _error("PAYLOAD_SCHEMA_FIELD_MUST_NOT_BE_BOUND")
    return {
        "PAYLOAD_SCHEMA_BOUND": FALSE_TOKEN,
        "CANARY_VAULT_FIELDS_BOUND_AS_KEYCHAIN_SSOT": FALSE_TOKEN,
    }


def prove_item_class_and_value_encoding_bound_v1() -> dict[str, str]:
    prove_concrete_keychain_item_identity_bound_v1()
    item_class = assert_keychain_item_class_v1(KEYCHAIN_ITEM_CLASS)
    encoding = assert_keychain_value_encoding_v1(KEYCHAIN_VALUE_ENCODING)
    if KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME != "kSecClassGenericPassword":
        _error("KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME_DRIFT")
    if KEYCHAIN_VALUE_DATA_REPRESENTATION != "BYTES":
        _error("KEYCHAIN_VALUE_DATA_REPRESENTATION_DRIFT")
    if KEYCHAIN_VALUE_TEXT_ENCODING != encoding:
        _error("KEYCHAIN_VALUE_TEXT_ENCODING_DRIFT")
    if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
        _error("SOURCE_BACKEND_CLASS_DRIFT")
    if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
        _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")
    if KEYCHAIN_SERVICE_ID != "peak-trade.full-core.venue-credentials":
        _error("KEYCHAIN_SERVICE_ID_MUST_REMAIN_OWNER_EXACT")
    if KEYCHAIN_ACCOUNT_ID != "okx-eea.productive":
        _error("KEYCHAIN_ACCOUNT_ID_MUST_REMAIN_OWNER_EXACT")
    if PROVIDER_REF_IDENTIFIER != "okx-eea-productive":
        _error("PROVIDER_REF_IDENTIFIER_MUST_REMAIN_OWNER_EXACT")
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED")
    if PRODUCTIVE_PROVIDER_ACTIVE is True:
        _error("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
    if V5_USES_NEW_PROVIDER is True:
        _error("V5_MUST_NOT_USE_NEW_PROVIDER")
    if EPHEMERAL_MATERIAL_PATH_IMPLEMENTED is True:
        _error("EPHEMERAL_MATERIAL_PATH_MUST_REMAIN_UNIMPLEMENTED")
    if MATERIAL_LOADED_TRUE_REACHABLE is True:
        _error("MATERIAL_LOADED_TRUE_MUST_REMAIN_UNREACHABLE")
    proof = {
        "KEYCHAIN_ITEM_CLASS_BOUND": TRUE_TOKEN,
        "KEYCHAIN_VALUE_ENCODING_BOUND": TRUE_TOKEN,
        "KEYCHAIN_ITEM_CLASS": item_class,
        "KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME": KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME,
        "KEYCHAIN_VALUE_DATA_REPRESENTATION": KEYCHAIN_VALUE_DATA_REPRESENTATION,
        "KEYCHAIN_VALUE_ENCODING": encoding,
        "KEYCHAIN_VALUE_TEXT_ENCODING": KEYCHAIN_VALUE_TEXT_ENCODING,
        "KEYCHAIN_SERVICE_ID": KEYCHAIN_SERVICE_ID,
        "KEYCHAIN_ACCOUNT_ID": KEYCHAIN_ACCOUNT_ID,
        "PROVIDER_REF_IDENTIFIER": PROVIDER_REF_IDENTIFIER,
        "SOURCE_REF_URI": SOURCE_REF_URI,
        "PAYLOAD_SCHEMA_BOUND": FALSE_TOKEN,
        "CANARY_VAULT_FIELDS_BOUND_AS_KEYCHAIN_SSOT": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_IMPLEMENTED": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
        "V5_USES_NEW_PROVIDER": FALSE_TOKEN,
        "EPHEMERAL_MATERIAL_PATH_IMPLEMENTED": FALSE_TOKEN,
        "MATERIAL_LOADED_TRUE_REACHABLE": FALSE_TOKEN,
        "QUERY_ATTRIBUTE_TUPLE": "service+account",
        "ITEM_CLASS_QUERY_SEMANTICS": "generic-password-service-account",
    }
    prove_payload_schema_unbound_v1(proof)
    return proof


def resolve_bound_keychain_item_class_and_value_encoding_v1(
    raw: str | None,
) -> FullCoreMacosKeychainItemClassAndValueEncodingV1:
    """Bind class/encoding onto the canonical DZ identity. Does not query Keychain."""

    prove_item_class_and_value_encoding_bound_v1()
    identity = resolve_bound_keychain_item_identity_v1(raw)
    bound = FullCoreMacosKeychainItemClassAndValueEncodingV1(
        provider_ref_identifier=identity.provider_ref_identifier,
        source_ref_uri=identity.source_ref_uri,
        keychain_service_id=identity.keychain_service_id,
        keychain_account_id=identity.keychain_account_id,
        keychain_item_class=KEYCHAIN_ITEM_CLASS,
        keychain_item_class_os_constant_name=KEYCHAIN_ITEM_CLASS_OS_CONSTANT_NAME,
        keychain_value_data_representation=KEYCHAIN_VALUE_DATA_REPRESENTATION,
        keychain_value_encoding=KEYCHAIN_VALUE_ENCODING,
        payload_schema_bound=FALSE_TOKEN,
        real_keychain_accessed=FALSE_TOKEN,
        credential_material_loaded=FALSE_TOKEN,
    )
    payload = bound.to_dict()
    for key in _FORBIDDEN_MAPPING_AUTHORITY_KEYS:
        if key in payload:
            _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")
    prove_payload_schema_unbound_v1(payload)
    return bound


def prove_item_class_encoding_authority_non_interference_v1(
    bound: FullCoreMacosKeychainItemClassAndValueEncodingV1,
    *,
    standing_before: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if bound.keychain_item_class != KEYCHAIN_ITEM_CLASS:
        _error("KEYCHAIN_ITEM_CLASS_DRIFT")
    if bound.keychain_value_encoding != KEYCHAIN_VALUE_ENCODING:
        _error("KEYCHAIN_VALUE_ENCODING_DRIFT")
    if bound.payload_schema_bound != FALSE_TOKEN:
        _error("PAYLOAD_SCHEMA_MUST_REMAIN_UNBOUND")
    if bound.credential_material_loaded != FALSE_TOKEN:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    if bound.real_keychain_accessed != FALSE_TOKEN:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE")
    identity = resolve_bound_keychain_item_identity_v1(bound.source_ref_uri)
    proof = prove_authority_non_interference_v1(identity, standing_before=standing_before)
    capability = acquire_offline_ephemeral_capability_v1(source_ref=bound.source_ref_uri)
    if not isinstance(capability, FullCoreCheckoutIndependentCredentialCapabilityV1):
        _error("CAPABILITY_MISSING")
    if capability.material_loaded is True:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    authority = prove_capability_grants_no_trading_or_post_authority_v1(capability)
    before = standing_before or prove_capability_cannot_mutate_standing_gates_v1()
    after = prove_capability_does_not_upgrade_standing_gates_v1(capability, before=before)
    if dict(before) != after:
        _error("CREDENTIAL_CAPABILITY_MUST_NOT_MUTATE_STANDING_GATES")
    return {
        "AUTHORITY_NON_INTERFERENCE_PROVEN": TRUE_TOKEN,
        "KEYCHAIN_ITEM_CLASS": bound.keychain_item_class,
        "KEYCHAIN_VALUE_ENCODING": bound.keychain_value_encoding,
        "PAYLOAD_SCHEMA_BOUND": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESSED": FALSE_TOKEN,
        "CREDENTIAL_MATERIAL_LOADED": FALSE_TOKEN,
        **authority,
        **{k: v for k, v in proof.items() if k not in authority},
    }


def refuse_mint_from_item_class_bind_v1(
    bound: FullCoreMacosKeychainItemClassAndValueEncodingV1,
) -> None:
    del bound
    refuse_mint_external_effect_permit_from_credential_capability_v1()


def refuse_real_keychain_access_from_item_class_bind_v1(*, attempted: bool = True) -> None:
    del attempted
    _error("REAL_KEYCHAIN_ACCESS_FORBIDDEN")
