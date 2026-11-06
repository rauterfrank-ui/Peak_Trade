"""Offline Full-Core checkout-independent credential source-backend-kind V1.

Owner Option-4 bind only:

SOURCE_BACKEND_CLASS=OS_NATIVE_SECRET_STORE
PRODUCTIVE_TARGET_BACKEND=MACOS_KEYCHAIN
SOURCE_REF_KIND=provider-ref
CHECKOUT_INDEPENDENT_REQUIRED=true

This slice does not access Keychain, load credential material, join V5,
activate a productive provider, or mint selection/trading/POST authority.

OWNER_GO=OWNER_GO_BIND_FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_SOURCE_BACKEND_KIND_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, NoReturn

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    ALLOWED_SOURCE_KIND,
    FORBIDDEN_SOURCE_KINDS,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    assert_checkout_independent_source_ref_v1,
    bind_offline_contract_capability_v1,
    prove_capability_grants_no_trading_or_post_authority_v1,
    prove_capability_serialization_has_no_plaintext_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
    release_checkout_independent_credential_capability_v1,
    resolve_checkout_independent_credential_capability_v1,
)

OWNER_GO = "OWNER_GO_BIND_FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_SOURCE_BACKEND_KIND_V1"
THIS_SLICE = "11.2.1.DY.FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_SOURCE_BACKEND_KIND"
CONTRACT_VERSION = "v1"
SOURCE_BACKEND_CLASS = "OS_NATIVE_SECRET_STORE"
PRODUCTIVE_TARGET_BACKEND = "MACOS_KEYCHAIN"
SOURCE_REF_KIND = "provider-ref"
CHECKOUT_INDEPENDENT_REQUIRED = True
SOURCE_LOCATION_BOUND = True
SOURCE_LOCATION_CLASS = "OS_NATIVE_SECRET_STORE_ITEM_IDENTIFIER"
SOURCE_LOCATION_IS_FILESYSTEM_PATH = False
SOURCE_LOCATION_DERIVED_FROM_REPO_ROOT = False
CONCRETE_KEYCHAIN_SERVICE_BOUND = False
CONCRETE_KEYCHAIN_ACCOUNT_BOUND = False
CONCRETE_BACKEND_ITEM_IDENTITY_BOUND = False
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False
PRODUCTIVE_BACKEND_JOINED = False
CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE = False

LIFETIME_STATE_ACQUIRED = "ACQUIRED"
LIFETIME_STATE_IN_USE = "IN_USE"
LIFETIME_STATE_RELEASED = "RELEASED"
LIFETIME_STATE_FAILED = "FAILED"
ALLOWED_LIFETIME_STATES = frozenset(
    {
        LIFETIME_STATE_ACQUIRED,
        LIFETIME_STATE_IN_USE,
        LIFETIME_STATE_RELEASED,
        LIFETIME_STATE_FAILED,
    }
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

_LIFETIME_STATE: dict[str, str] = {}
_LIFETIME_BACKEND_DELETED: dict[str, bool] = {}


class FullCoreCheckoutIndependentCredentialSourceBackendKindError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed Option-4 source-backend-kind contract violation."""


@dataclass(frozen=True)
class FullCoreCheckoutIndependentCredentialLifetimeRecordV1:
    """Process-local lifetime record. Not a Keychain mutation proof."""

    capability_id: str
    source_ref_uri: str
    source_ref_kind: str
    state: str
    material_loaded: str
    handle_released: str
    backend_item_deleted: str
    real_keychain_accessed: str
    handle_release_equals_backend_deletion: str

    def to_dict(self) -> dict[str, str]:
        return {
            "capability_id": self.capability_id,
            "source_ref_uri": self.source_ref_uri,
            "source_ref_kind": self.source_ref_kind,
            "state": self.state,
            "material_loaded": self.material_loaded,
            "handle_released": self.handle_released,
            "backend_item_deleted": self.backend_item_deleted,
            "real_keychain_accessed": self.real_keychain_accessed,
            "handle_release_equals_backend_deletion": (self.handle_release_equals_backend_deletion),
        }


def _error(code: str) -> NoReturn:
    raise FullCoreCheckoutIndependentCredentialSourceBackendKindError(code)


def prove_owner_backend_choice_bound_v1() -> dict[str, str]:
    if SOURCE_REF_KIND != ALLOWED_SOURCE_KIND:
        _error("SOURCE_REF_KIND_MUST_REMAIN_PROVIDER_REF")
    if SOURCE_REF_KIND in FORBIDDEN_SOURCE_KINDS:
        _error("SOURCE_REF_KIND_FORBIDDEN")
    if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
        _error("SOURCE_BACKEND_CLASS_DRIFT")
    if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
        _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")
    if CHECKOUT_INDEPENDENT_REQUIRED is not True:
        _error("CHECKOUT_INDEPENDENT_REQUIRED_DRIFT")
    if SOURCE_LOCATION_IS_FILESYSTEM_PATH is True:
        _error("SOURCE_LOCATION_MUST_NOT_BE_FILESYSTEM_PATH")
    if SOURCE_LOCATION_DERIVED_FROM_REPO_ROOT is True:
        _error("SOURCE_LOCATION_MUST_NOT_DERIVE_FROM_REPO_ROOT")
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if PRODUCTIVE_PROVIDER_ACTIVE is True:
        _error("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
    return {
        "OWNER_BACKEND_CHOICE_BOUND": TRUE_TOKEN,
        "SOURCE_BACKEND_CLASS": SOURCE_BACKEND_CLASS,
        "PRODUCTIVE_TARGET_BACKEND": PRODUCTIVE_TARGET_BACKEND,
        "SOURCE_REF_KIND": SOURCE_REF_KIND,
        "CHECKOUT_INDEPENDENT_REQUIRED": TRUE_TOKEN,
        "SOURCE_LOCATION_BOUND": TRUE_TOKEN if SOURCE_LOCATION_BOUND else FALSE_TOKEN,
        "SOURCE_LOCATION_CLASS": SOURCE_LOCATION_CLASS,
        "SOURCE_LOCATION_IS_FILESYSTEM_PATH": FALSE_TOKEN,
        "SOURCE_LOCATION_DERIVED_FROM_REPO_ROOT": FALSE_TOKEN,
        "CONCRETE_KEYCHAIN_SERVICE_BOUND": FALSE_TOKEN,
        "CONCRETE_KEYCHAIN_ACCOUNT_BOUND": FALSE_TOKEN,
        "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
    }


def prove_source_ref_identifier_only_semantics_v1(
    raw: str | None,
) -> dict[str, str]:
    parsed = assert_checkout_independent_source_ref_v1(raw)
    if parsed.kind != SOURCE_REF_KIND:
        _error("SOURCE_REF_KIND_MUST_REMAIN_PROVIDER_REF")
    if parsed.kind == "keychain":
        _error("MALFORMED_PROVIDER_REFERENCE")
    identifier = parsed.identifier
    if (
        identifier.startswith("/")
        or identifier.startswith("~")
        or ".." in identifier
        or "repo_root" in identifier
        or "worktree" in identifier
    ):
        _error("CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY")
    return {
        "SOURCE_REF_KIND": parsed.kind,
        "SOURCE_REF_IDENTIFIER": identifier,
        "SOURCE_REF_URI": parsed.as_uri(),
        "SOURCE_REF_IS_IDENTIFIER_ONLY": TRUE_TOKEN,
        "SOURCE_REF_IS_FILESYSTEM_PATH": FALSE_TOKEN,
        "SOURCE_REF_IS_KEYCHAIN_QUERY": FALSE_TOKEN,
        "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND": FALSE_TOKEN,
    }


def refuse_real_keychain_access_v1(*, attempted: bool = True) -> None:
    del attempted
    _error("REAL_KEYCHAIN_ACCESS_FORBIDDEN")


def _record_for(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> FullCoreCheckoutIndependentCredentialLifetimeRecordV1:
    state = _LIFETIME_STATE.get(capability.capability_id)
    if state is None:
        _error("LIFETIME_RECORD_MISSING")
    backend_deleted = _LIFETIME_BACKEND_DELETED.get(capability.capability_id, False)
    released = state == LIFETIME_STATE_RELEASED
    return FullCoreCheckoutIndependentCredentialLifetimeRecordV1(
        capability_id=capability.capability_id,
        source_ref_uri=capability.source_ref.as_uri(),
        source_ref_kind=capability.source_ref.kind,
        state=state,
        material_loaded=FALSE_TOKEN,
        handle_released=TRUE_TOKEN if released else FALSE_TOKEN,
        backend_item_deleted=TRUE_TOKEN if backend_deleted else FALSE_TOKEN,
        real_keychain_accessed=FALSE_TOKEN,
        handle_release_equals_backend_deletion=FALSE_TOKEN,
    )


def acquire_offline_ephemeral_capability_v1(
    *,
    source_ref: str,
) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
    """Bind a process-local capability. Does not query Keychain or load material."""

    prove_owner_backend_choice_bound_v1()
    prove_source_ref_identifier_only_semantics_v1(source_ref)
    capability = bind_offline_contract_capability_v1(source_ref=source_ref)
    if capability.material_loaded is True:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    _LIFETIME_STATE[capability.capability_id] = LIFETIME_STATE_ACQUIRED
    _LIFETIME_BACKEND_DELETED[capability.capability_id] = False
    prove_capability_serialization_has_no_plaintext_v1(capability)
    return capability


def use_offline_ephemeral_capability_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> dict[str, str]:
    """Mark IN_USE. Does not load material, sign, GET, or POST."""

    if capability is None or not isinstance(
        capability, FullCoreCheckoutIndependentCredentialCapabilityV1
    ):
        _error("CAPABILITY_MISSING")
    state = _LIFETIME_STATE.get(capability.capability_id)
    if state is None:
        _error("LIFETIME_RECORD_MISSING")
    if state == LIFETIME_STATE_RELEASED:
        _error("CAPABILITY_ALREADY_RELEASED")
    if state == LIFETIME_STATE_FAILED:
        _error("CAPABILITY_LIFETIME_FAILED")
    if state not in {LIFETIME_STATE_ACQUIRED, LIFETIME_STATE_IN_USE}:
        _error("CAPABILITY_LIFETIME_STATE_FORBIDDEN")
    if capability.material_loaded is True:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    _LIFETIME_STATE[capability.capability_id] = LIFETIME_STATE_IN_USE
    authority = prove_capability_grants_no_trading_or_post_authority_v1(capability)
    return {
        "state": LIFETIME_STATE_IN_USE,
        "material_loaded": FALSE_TOKEN,
        "real_keychain_accessed": FALSE_TOKEN,
        "can_authenticate_private_get": (
            TRUE_TOKEN if capability.can_authenticate_private_get else FALSE_TOKEN
        ),
        "can_sign": TRUE_TOKEN if capability.can_sign else FALSE_TOKEN,
        "use_loads_material": FALSE_TOKEN,
        "use_performs_network": FALSE_TOKEN,
        "use_mints_post_authority": FALSE_TOKEN,
        **authority,
    }


def release_offline_ephemeral_capability_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> FullCoreCheckoutIndependentCredentialLifetimeRecordV1:
    """Invalidate the process-local handle. Does not delete a Keychain item."""

    if capability is None or not isinstance(
        capability, FullCoreCheckoutIndependentCredentialCapabilityV1
    ):
        _error("CAPABILITY_MISSING")
    state = _LIFETIME_STATE.get(capability.capability_id)
    if state is None:
        _error("LIFETIME_RECORD_MISSING")
    if state == LIFETIME_STATE_RELEASED:
        _error("CAPABILITY_ALREADY_RELEASED")
    if state == LIFETIME_STATE_FAILED:
        _error("CAPABILITY_LIFETIME_FAILED")
    released = release_checkout_independent_credential_capability_v1(capability)
    _LIFETIME_STATE[capability.capability_id] = LIFETIME_STATE_RELEASED
    _LIFETIME_BACKEND_DELETED[capability.capability_id] = False
    record = _record_for(released)
    if record.backend_item_deleted != FALSE_TOKEN:
        _error("BACKEND_DELETION_MUST_NOT_BE_CLAIMED")
    if record.handle_release_equals_backend_deletion != FALSE_TOKEN:
        _error("HANDLE_RELEASE_MUST_NOT_EQUAL_BACKEND_DELETION")
    return record


def fail_offline_ephemeral_capability_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1 | None = None,
    *,
    reason: str,
) -> NoReturn:
    """Record failure without loading material or touching Keychain."""

    code = str(reason or "").strip() or "CAPABILITY_LIFETIME_FAILED"
    if capability is None:
        _error(code)
    state = _LIFETIME_STATE.get(capability.capability_id)
    if state is None:
        _error("LIFETIME_RECORD_MISSING")
    if state == LIFETIME_STATE_RELEASED:
        _error("CAPABILITY_ALREADY_RELEASED")
    _LIFETIME_STATE[capability.capability_id] = LIFETIME_STATE_FAILED
    _LIFETIME_BACKEND_DELETED[capability.capability_id] = False
    _error(code)


def prove_handle_release_is_not_backend_deletion_v1(
    record: FullCoreCheckoutIndependentCredentialLifetimeRecordV1,
) -> dict[str, str]:
    if record.handle_released != TRUE_TOKEN:
        _error("HANDLE_NOT_RELEASED")
    if record.backend_item_deleted != FALSE_TOKEN:
        _error("BACKEND_DELETION_MUST_NOT_BE_CLAIMED")
    if record.handle_release_equals_backend_deletion != FALSE_TOKEN:
        _error("HANDLE_RELEASE_MUST_NOT_EQUAL_BACKEND_DELETION")
    if record.real_keychain_accessed != FALSE_TOKEN:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE")
    return {
        "HANDLE_RELEASED": TRUE_TOKEN,
        "BACKEND_ITEM_DELETED": FALSE_TOKEN,
        "HANDLE_RELEASE_EQUALS_BACKEND_DELETION": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESSED": FALSE_TOKEN,
        "KEYCHAIN_ITEM_CREATE_PERFORMED": FALSE_TOKEN,
        "KEYCHAIN_ITEM_READ_PERFORMED": FALSE_TOKEN,
        "KEYCHAIN_ITEM_WRITE_PERFORMED": FALSE_TOKEN,
        "KEYCHAIN_ITEM_DELETE_PERFORMED": FALSE_TOKEN,
    }


def prove_zero_retention_semantics_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> dict[str, str]:
    """Zero-retention only as far as this unloaded process-local handle proves.

    Secret values were never loaded. Process-memory wipe is not proven.
    Backend/Keychain deletion is not performed and not claimed.
    """

    if capability.material_loaded is True:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    state = _LIFETIME_STATE.get(capability.capability_id, "")
    return {
        "ZERO_RETENTION_SEMANTICS_DEFINED": TRUE_TOKEN,
        "PLAINTEXT_WAS_LOADED": FALSE_TOKEN,
        "ZERO_RETENTION_OF_PLAINTEXT_IN_THIS_PROCESS": TRUE_TOKEN,
        "PROCESS_MEMORY_WIPE_PROVEN": FALSE_TOKEN,
        "BACKEND_ITEM_DELETED": FALSE_TOKEN,
        "HANDLE_RELEASE_EQUALS_BACKEND_DELETION": FALSE_TOKEN,
        "ZERO_RETENTION_CLAIM_SCOPE": (
            "PROCESS_LOCAL_UNLOADED_HANDLE_ONLY_NOT_BACKEND_DELETION_NOT_MEMORY_WIPE"
        ),
        "LIFETIME_STATE": state,
        "MATERIAL_LOADED": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESSED": FALSE_TOKEN,
    }


def prove_productive_backend_still_absent_v1(*, source_ref: str) -> dict[str, str]:
    try:
        resolve_checkout_independent_credential_capability_v1(source_ref=source_ref)
    except FullCoreCheckoutIndependentCredentialCapabilityError as exc:
        if "PROVIDER_UNAVAILABLE" not in str(exc) and "PRODUCTIVE_BACKEND_ABSENT" not in str(exc):
            raise
    else:
        _error("PRODUCTIVE_BACKEND_MUST_REMAIN_ABSENT")
    return {
        "PRODUCTIVE_BACKEND_JOINED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESSED": FALSE_TOKEN,
        "CREDENTIAL_MATERIAL_LOADED": FALSE_TOKEN,
    }


def refuse_mint_from_source_backend_bind_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> None:
    refuse_mint_external_effect_permit_from_credential_capability_v1(capability)


def prove_lifetime_contract_defined_v1() -> dict[str, str]:
    return {
        "EPHEMERAL_LIFETIME_CONTRACT_DEFINED": TRUE_TOKEN,
        "LIFETIME_STATES": ",".join(
            (
                LIFETIME_STATE_ACQUIRED,
                LIFETIME_STATE_IN_USE,
                LIFETIME_STATE_RELEASED,
                LIFETIME_STATE_FAILED,
            )
        ),
        "ACQUIRE_LOADS_MATERIAL": FALSE_TOKEN,
        "USE_LOADS_MATERIAL": FALSE_TOKEN,
        "RELEASE_DELETES_BACKEND_ITEM": FALSE_TOKEN,
        "FAILURE_ACCESSES_KEYCHAIN": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
    }


def current_lifetime_state_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> str:
    state = _LIFETIME_STATE.get(capability.capability_id)
    if state is None:
        _error("LIFETIME_RECORD_MISSING")
    if state not in ALLOWED_LIFETIME_STATES:
        _error("CAPABILITY_LIFETIME_STATE_FORBIDDEN")
    return state


def prove_source_backend_bind_does_not_grant_authority_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
    *,
    standing_before: Mapping[str, str],
) -> dict[str, str]:
    del standing_before
    return prove_capability_grants_no_trading_or_post_authority_v1(capability)
