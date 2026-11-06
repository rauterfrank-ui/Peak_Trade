"""Fail-closed K1 credential capability bind for governed-cycle occupancy.

Occupancy-adjacent consumer only. Reuses the existing EA provider port and
DX capability. Resolve remains fail-closed while Keychain access is
unauthorized. Does not load material, GET, sign, POST, or join V5.

OWNER_GO=OWNER_GO_K1_GOVERNED_CYCLE_CREDENTIAL_BIND_JOIN_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NoReturn

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_ENVIRONMENT,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialProviderPortV1,
    prove_capability_cannot_mutate_standing_gates_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
    resolve_checkout_independent_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
    bind_fail_closed_os_native_store_adapter_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as K1_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)

OWNER_GO = "OWNER_GO_K1_GOVERNED_CYCLE_CREDENTIAL_BIND_JOIN_V1"
THIS_SLICE = "K1_GOVERNED_CYCLE_CREDENTIAL_BIND_JOIN_V1"
CONTRACT_VERSION = "v1"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_GOVERNED_CYCLE_K1_CREDENTIAL_BIND_SEAM_V1"
CONSUMER_ROLE = "GOVERNED_CYCLE_OCCUPANCY_ADJACENT_K1_CAPABILITY_BIND"
SEAM_LOCATION = "GOVERNED_CYCLE_AFTER_EG_BEFORE_OCCUPANCY_CLASSIFY"
JOIN_SEMANTICS = "FAIL_CLOSED_AUTHORITY_NEUTRAL_K1_CAPABILITY_BIND"
PRODUCTIVE_CONSUMER_JOINED = True
PRODUCTIVE_PROVIDER_ACTIVE = False
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
REAL_KEYCHAIN_ACCESS_IMPLEMENTED = False
V5_JOINED = False
V5_USES_NEW_PROVIDER = False
SEND_HANDLE_JOINED = False
MATERIAL_LOADED_TRUE_REACHABLE = False
EPHEMERAL_MATERIAL_PATH_IMPLEMENTED = False
MAY_PERFORM_GET = False
MAY_EXECUTE_NETWORK = False
MAY_MINT_PERMIT = False
MAY_POST = False
JOIN_TRADING_AUTHORITY = False
JOIN_RANKING_AUTHORITY = False
JOIN_SELECTION_AUTHORITY = False
JOIN_EXECUTION_AUTHORITY = False

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
EXPECTED_RESOLVE_FAIL_CLOSED_CODE = REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE

_FORBIDDEN_CONSUMER_AUTHORITY_ATTRS = (
    "selection_authority",
    "trading_decision_authority",
    "risk_authority",
    "admission_authority",
    "external_effect_authority",
    "post_authority",
    "send_authority",
)


class FullCoreGovernedCycleK1CredentialBindError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed governed-cycle K1 capability-bind violation."""


@dataclass(frozen=True)
class FullCoreGovernedCycleK1CredentialBindProofV1:
    """Non-material occupancy-adjacent bind proof. Never carries secrets."""

    disposition: str
    provider_port_reused: str
    source_ref_uri: str
    credential_class: str
    resolve_fail_closed: str
    resolve_fail_closed_code: str
    material_loaded: str
    real_keychain_access_authorized: str
    real_keychain_access_implemented: str
    productive_provider_active: str
    v5_joined: str
    send_handle_joined: str
    permit_created: str
    post_count: str
    perform_get: str
    execute_network: str

    def to_dict(self) -> dict[str, str]:
        return {
            "disposition": self.disposition,
            "provider_port_reused": self.provider_port_reused,
            "source_ref_uri": self.source_ref_uri,
            "credential_class": self.credential_class,
            "resolve_fail_closed": self.resolve_fail_closed,
            "resolve_fail_closed_code": self.resolve_fail_closed_code,
            "material_loaded": self.material_loaded,
            "real_keychain_access_authorized": self.real_keychain_access_authorized,
            "real_keychain_access_implemented": self.real_keychain_access_implemented,
            "productive_provider_active": self.productive_provider_active,
            "v5_joined": self.v5_joined,
            "send_handle_joined": self.send_handle_joined,
            "permit_created": self.permit_created,
            "post_count": self.post_count,
            "perform_get": self.perform_get,
            "execute_network": self.execute_network,
        }

    def __repr__(self) -> str:
        return "FullCoreGovernedCycleK1CredentialBindProofV1(redacted)"

    def __str__(self) -> str:
        return "FullCoreGovernedCycleK1CredentialBindProofV1(redacted)"


def _error(code: str) -> NoReturn:
    raise FullCoreGovernedCycleK1CredentialBindError(code)


def _assert_standing_access_pins_v1() -> None:
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED")
    if K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("K1_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if K1_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        _error("K1_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED")
    if EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("EA_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        _error("EA_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED")
    if PRODUCTIVE_PROVIDER_ACTIVE is True:
        _error("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
    if V5_JOINED is True or V5_USES_NEW_PROVIDER is True:
        _error("V5_MUST_NOT_JOIN_K1_BIND")
    if SEND_HANDLE_JOINED is True:
        _error("SEND_HANDLE_MUST_NOT_JOIN_K1_BIND")
    if MATERIAL_LOADED_TRUE_REACHABLE is True:
        _error("MATERIAL_LOADED_TRUE_MUST_REMAIN_UNREACHABLE")
    if MAY_PERFORM_GET is True or MAY_EXECUTE_NETWORK is True:
        _error("GET_AND_NETWORK_MUST_REMAIN_UNAUTHORIZED")
    if MAY_MINT_PERMIT is True or MAY_POST is True:
        _error("PERMIT_AND_POST_MUST_REMAIN_UNAUTHORIZED")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        _error("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        _error("STANDING_POST_MUST_REMAIN_FALSE")
    if JOIN_TRADING_AUTHORITY or JOIN_RANKING_AUTHORITY or JOIN_SELECTION_AUTHORITY:
        _error("BIND_MUST_NOT_GRANT_TRADING_AUTHORITY")
    if JOIN_EXECUTION_AUTHORITY:
        _error("BIND_MUST_NOT_GRANT_EXECUTION_AUTHORITY")


def _proof(*, resolve_fail_closed_code: str) -> FullCoreGovernedCycleK1CredentialBindProofV1:
    return FullCoreGovernedCycleK1CredentialBindProofV1(
        disposition="FAIL_CLOSED_BOUND",
        provider_port_reused=TRUE_TOKEN,
        source_ref_uri=SOURCE_REF_URI,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
        resolve_fail_closed=TRUE_TOKEN,
        resolve_fail_closed_code=resolve_fail_closed_code,
        material_loaded=FALSE_TOKEN,
        real_keychain_access_authorized=FALSE_TOKEN,
        real_keychain_access_implemented=FALSE_TOKEN,
        productive_provider_active=FALSE_TOKEN,
        v5_joined=FALSE_TOKEN,
        send_handle_joined=FALSE_TOKEN,
        permit_created=FALSE_TOKEN,
        post_count="0",
        perform_get=FALSE_TOKEN,
        execute_network=FALSE_TOKEN,
    )


def bind_k1_credential_capability_for_governed_cycle_occupancy_v1(
    *,
    provider: FullCoreCheckoutIndependentCredentialProviderPortV1 | None = None,
) -> FullCoreGovernedCycleK1CredentialBindProofV1:
    """Bind the existing K1/EA provider into the cycle. Do not block on fail-closed resolve."""

    _assert_standing_access_pins_v1()
    before = prove_capability_cannot_mutate_standing_gates_v1()
    bound_provider = provider
    if bound_provider is None:
        bound_provider = bind_fail_closed_os_native_store_adapter_v1()
    if not callable(getattr(bound_provider, "resolve_capability_v1", None)):
        _error("PROVIDER_PORT_RESOLVE_MISSING")
    if not callable(getattr(bound_provider, "release_capability_v1", None)):
        _error("PROVIDER_PORT_RELEASE_MISSING")
    for attr in _FORBIDDEN_CONSUMER_AUTHORITY_ATTRS:
        if hasattr(bound_provider, attr) and getattr(bound_provider, attr) is True:
            _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")
    if isinstance(bound_provider, FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1):
        for attr in _FORBIDDEN_CONSUMER_AUTHORITY_ATTRS:
            if hasattr(bound_provider, attr):
                _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")

    try:
        resolve_checkout_independent_credential_capability_v1(
            source_ref=SOURCE_REF_URI,
            credential_class=REQUIRED_CREDENTIAL_CLASS,
            environment=REQUIRED_ENVIRONMENT,
            provider=bound_provider,
        )
    except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
        code = str(exc)
        if EXPECTED_RESOLVE_FAIL_CLOSED_CODE not in code:
            raise
        if "CREDENTIAL_MATERIAL_LOADED_FORBIDDEN" in code:
            _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    else:
        _error("RESOLVE_MUST_REMAIN_FAIL_CLOSED")

    try:
        refuse_mint_external_effect_permit_from_credential_capability_v1()
    except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
        if "CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT" not in str(exc):
            raise
    else:
        _error("CREDENTIAL_CAPABILITY_MUST_NOT_MINT_PERMIT")

    after = prove_capability_cannot_mutate_standing_gates_v1()
    if before != after:
        _error("STANDING_GATES_MUST_REMAIN_UNCHANGED")
    proof = _proof(resolve_fail_closed_code=EXPECTED_RESOLVE_FAIL_CLOSED_CODE)
    if proof.material_loaded != FALSE_TOKEN:
        _error("MATERIAL_LOADED_MUST_REMAIN_FALSE")
    return proof
