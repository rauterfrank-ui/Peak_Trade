"""Fail-closed offline OS-native-store provider adapter V1.

Binds MACOS_KEYCHAIN behind FullCoreCheckoutIndependentCredentialProviderPortV1.
Consumes the canonical DZ identifier-only mapping and EB item-class/encoding
metadata. resolve_capability_v1 still does not access Keychain. Opaque
acquisition is a separate adapter method, requires an injected lookup backend,
and never emits material. No V5 join, GET, sign, or POST.

OWNER_GO=OWNER_GO_FULL_CORE_CHECKOUT_INDEPENDENT_FAIL_CLOSED_MACOS_KEYCHAIN_PROVIDER_ADAPTER_OFFLINE_CONTRACT_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import NoReturn

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    FullCoreCheckoutIndependentCredentialProviderPortV1,
    FullCoreCheckoutIndependentCredentialSourceRefV1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
    release_checkout_independent_credential_capability_v1,
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
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    FullCoreOsNativeStoreAcquisitionProofV1,
    OsNativeStoreLookupBackendV1,
    run_opaque_os_native_store_acquisition_v1,
    wipe_opaque_os_native_store_material_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
    KEYCHAIN_VALUE_ENCODING,
    prove_item_class_and_value_encoding_bound_v1,
    resolve_bound_keychain_item_class_and_value_encoding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    SOURCE_BACKEND_CLASS,
)

OWNER_GO = "OWNER_GO_FULL_CORE_CHECKOUT_INDEPENDENT_FAIL_CLOSED_MACOS_KEYCHAIN_PROVIDER_ADAPTER_OFFLINE_CONTRACT_V1"
THIS_SLICE = "11.2.1.EA.FULL_CORE_CHECKOUT_INDEPENDENT_FAIL_CLOSED_MACOS_KEYCHAIN_PROVIDER_ADAPTER"
CONTRACT_VERSION = "v1"
OFFLINE_ADAPTER_IMPLEMENTED = True
REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False
PRODUCTIVE_BACKEND_JOINED = False
CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE = False
V5_USES_NEW_PROVIDER = False
EPHEMERAL_MATERIAL_PATH_IMPLEMENTED = False
MATERIAL_LOADED_TRUE_REACHABLE = False
RESOLVE_DISPATCH_TO_ADAPTER_IMPLEMENTED = True

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

_FORBIDDEN_ADAPTER_AUTHORITY_ATTRS = (
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


class FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed OS-native-store adapter contract violation."""


class FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1:
    """Port implementation that never acquires Keychain material."""

    PRODUCTIVE_TARGET_BACKEND = "MACOS_KEYCHAIN"
    SOURCE_BACKEND_CLASS = "OS_NATIVE_SECRET_STORE"
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False
    REAL_KEYCHAIN_ACCESS_AUTHORIZED = False

    def __init__(self) -> None:
        self.resolve_dispatch_count = 0
        self.release_dispatch_count = 0
        self.last_source_ref_uri = ""

    def resolve_capability_v1(
        self,
        *,
        source_ref: FullCoreCheckoutIndependentCredentialSourceRefV1,
        credential_class: str,
        environment: str,
    ) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
        del credential_class, environment
        self.resolve_dispatch_count += 1
        uri = source_ref.as_uri() if hasattr(source_ref, "as_uri") else str(source_ref)
        self.last_source_ref_uri = uri
        identity = resolve_bound_keychain_item_identity_v1(uri)
        if identity.keychain_service_id != KEYCHAIN_SERVICE_ID:
            _error("KEYCHAIN_SERVICE_ID_MUST_REMAIN_OWNER_EXACT")
        if identity.keychain_account_id != KEYCHAIN_ACCOUNT_ID:
            _error("KEYCHAIN_ACCOUNT_ID_MUST_REMAIN_OWNER_EXACT")
        if identity.provider_ref_identifier != PROVIDER_REF_IDENTIFIER:
            _error("PROVIDER_REF_IDENTIFIER_MUST_REMAIN_OWNER_EXACT")
        if identity.source_ref_uri != SOURCE_REF_URI:
            _error("SOURCE_REF_URI_MUST_REMAIN_OWNER_COMPOSED")
        encoding = resolve_bound_keychain_item_class_and_value_encoding_v1(uri)
        if encoding.keychain_item_class != KEYCHAIN_ITEM_CLASS:
            _error("KEYCHAIN_ITEM_CLASS_DRIFT")
        if encoding.keychain_value_encoding != KEYCHAIN_VALUE_ENCODING:
            _error("KEYCHAIN_VALUE_ENCODING_DRIFT")
        if encoding.payload_schema_bound != FALSE_TOKEN:
            _error("PAYLOAD_SCHEMA_MUST_REMAIN_UNBOUND")
        if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
            _error("SOURCE_BACKEND_CLASS_DRIFT")
        if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
            _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")
        if self.PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
            _error("ADAPTER_BACKEND_MUST_REMAIN_MACOS_KEYCHAIN")
        if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
            _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
        if REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
            _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED")
        if PRODUCTIVE_PROVIDER_ACTIVE is True:
            _error("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
        for attr in _FORBIDDEN_ADAPTER_AUTHORITY_ATTRS:
            if hasattr(self, attr):
                _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")
        _error(REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE)

    def acquire_opaque_os_native_store_material_v1(
        self,
        *,
        source_ref: FullCoreCheckoutIndependentCredentialSourceRefV1 | str,
        backend: OsNativeStoreLookupBackendV1 | None,
    ) -> FullCoreOsNativeStoreAcquisitionProofV1:
        """Acquire opaque bytes inside this adapter. Never returns material."""

        return run_opaque_os_native_store_acquisition_v1(
            source_ref=source_ref,
            backend=backend,
            holder_id=id(self),
        )

    def release_capability_v1(
        self, capability: FullCoreCheckoutIndependentCredentialCapabilityV1
    ) -> None:
        self.release_dispatch_count += 1
        wipe_opaque_os_native_store_material_v1(id(self))
        if capability is None:
            _error("CAPABILITY_MISSING")
        if capability.material_loaded is True:
            _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        release_checkout_independent_credential_capability_v1(capability)


def _error(code: str) -> NoReturn:
    raise FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterError(code)


def bind_fail_closed_os_native_store_adapter_v1() -> (
    FullCoreCheckoutIndependentCredentialProviderPortV1
):
    return FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()


def prove_fail_closed_adapter_bound_v1() -> dict[str, str]:
    prove_concrete_keychain_item_identity_bound_v1()
    prove_item_class_and_value_encoding_bound_v1()
    if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
        _error("SOURCE_BACKEND_CLASS_DRIFT")
    if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
        _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")
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
    adapter = bind_fail_closed_os_native_store_adapter_v1()
    if not callable(getattr(adapter, "resolve_capability_v1", None)):
        _error("PROVIDER_PORT_RESOLVE_MISSING")
    if not callable(getattr(adapter, "release_capability_v1", None)):
        _error("PROVIDER_PORT_RELEASE_MISSING")
    return {
        "OFFLINE_ADAPTER_IMPLEMENTED": TRUE_TOKEN,
        "PROVIDER_PORT_IMPLEMENTED_BY_ADAPTER": TRUE_TOKEN,
        "CANONICAL_DZ_IDENTITY_CONSUMED": TRUE_TOKEN,
        "CANONICAL_EB_ITEM_CLASS_CONSUMED": TRUE_TOKEN,
        "KEYCHAIN_ITEM_CLASS": KEYCHAIN_ITEM_CLASS,
        "KEYCHAIN_VALUE_ENCODING": KEYCHAIN_VALUE_ENCODING,
        "RESOLVE_DISPATCH_TO_ADAPTER_IMPLEMENTED": TRUE_TOKEN,
        "SOURCE_BACKEND_CLASS": SOURCE_BACKEND_CLASS,
        "PRODUCTIVE_TARGET_BACKEND": PRODUCTIVE_TARGET_BACKEND,
        "KEYCHAIN_SERVICE_ID": KEYCHAIN_SERVICE_ID,
        "KEYCHAIN_ACCOUNT_ID": KEYCHAIN_ACCOUNT_ID,
        "PROVIDER_REF_IDENTIFIER": PROVIDER_REF_IDENTIFIER,
        "SOURCE_REF_URI": SOURCE_REF_URI,
        "REAL_KEYCHAIN_ACCESS_IMPLEMENTED": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
        "V5_USES_NEW_PROVIDER": FALSE_TOKEN,
        "EPHEMERAL_MATERIAL_PATH_IMPLEMENTED": FALSE_TOKEN,
        "MATERIAL_LOADED_TRUE_REACHABLE": FALSE_TOKEN,
        "REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE": REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    }


def prove_adapter_authority_non_interference_v1(
    adapter: FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
) -> dict[str, str]:
    for attr in _FORBIDDEN_ADAPTER_AUTHORITY_ATTRS:
        if hasattr(adapter, attr):
            _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")
    identity = resolve_bound_keychain_item_identity_v1(SOURCE_REF_URI)
    proof = prove_authority_non_interference_v1(identity)
    try:
        refuse_mint_external_effect_permit_from_credential_capability_v1()
    except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
        if "CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT" not in str(exc):
            raise
    else:
        _error("CREDENTIAL_CAPABILITY_MUST_NOT_MINT_PERMIT")
    return proof
