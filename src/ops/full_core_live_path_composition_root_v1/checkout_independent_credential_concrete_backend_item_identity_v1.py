"""Offline Full-Core concrete macOS Keychain item identity V1.

Owner-supplied identifier-only bind:

KEYCHAIN_SERVICE_ID=peak-trade.full-core.venue-credentials
KEYCHAIN_ACCOUNT_ID=okx-eea.productive
PROVIDER_REF_IDENTIFIER=okx-eea-productive

This slice does not access Keychain, load credential material, join V5,
activate a productive provider, or mint selection/trading/POST authority.
Values are stored exactly as Owner-supplied. No normalization.

OWNER_GO=OWNER_GO_BIND_FULL_CORE_CONCRETE_MACOS_KEYCHAIN_ITEM_IDENTITY_VALUES_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, NoReturn

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    ALLOWED_SOURCE_KIND,
    FORBIDDEN_SECRET_TOKENS,
    FORBIDDEN_SOURCE_KINDS,
    SOURCE_REF_SCHEME,
    FullCoreCheckoutIndependentCredentialCapabilityError,
    FullCoreCheckoutIndependentCredentialCapabilityV1,
    assert_checkout_independent_source_ref_v1,
    prove_capability_cannot_mutate_standing_gates_v1,
    prove_capability_does_not_upgrade_standing_gates_v1,
    prove_capability_grants_no_trading_or_post_authority_v1,
    refuse_mint_external_effect_permit_from_credential_capability_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_source_backend_kind_v1 import (
    PRODUCTIVE_TARGET_BACKEND,
    SOURCE_BACKEND_CLASS,
    SOURCE_LOCATION_CLASS,
    SOURCE_REF_KIND,
    acquire_offline_ephemeral_capability_v1,
    prove_owner_backend_choice_bound_v1,
    prove_productive_backend_still_absent_v1,
)

OWNER_GO = "OWNER_GO_BIND_FULL_CORE_CONCRETE_MACOS_KEYCHAIN_ITEM_IDENTITY_VALUES_V1"
THIS_SLICE = "11.2.1.DZ.FULL_CORE_CONCRETE_MACOS_KEYCHAIN_ITEM_IDENTITY"
CONTRACT_VERSION = "v1"
KEYCHAIN_SERVICE_ID = "peak-trade.full-core.venue-credentials"
KEYCHAIN_ACCOUNT_ID = "okx-eea.productive"
PROVIDER_REF_IDENTIFIER = "okx-eea-productive"
SOURCE_REF_URI = f"{SOURCE_REF_SCHEME}://{ALLOWED_SOURCE_KIND}/{PROVIDER_REF_IDENTIFIER}"
CONCRETE_KEYCHAIN_SERVICE_BOUND = True
CONCRETE_KEYCHAIN_ACCOUNT_BOUND = True
CONCRETE_BACKEND_ITEM_IDENTITY_BOUND = True
PROVIDER_REF_IDENTIFIER_BOUND = True
PROVIDER_REF_TO_KEYCHAIN_IDENTITY_MAPPING_DEFINED = True
REAL_KEYCHAIN_ACCESS_AUTHORIZED = False
PRODUCTIVE_PROVIDER_ACTIVE = False
V5_JOINED = False
PRODUCTIVE_BACKEND_JOINED = False
CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE = False
KEYCHAIN_IDENTITY_IMPLIES_CREDENTIAL_POSSESSION = False
CREDENTIAL_POSSESSION_IMPLIES_SELECTION_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_TRADING_DECISION_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_RISK_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_ADMISSION_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_EXTERNAL_EFFECT_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_POST_AUTHORITY = False
CREDENTIAL_POSSESSION_IMPLIES_SEND_AUTHORITY = False
GET_AUTH_IMPLIES_SEND_AUTHORITY = False
SIGNING_IMPLIES_SEND_AUTHORITY = False

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"

# Identifier group reused from Phase-A SourceRef charset. Not a new alphabet.
_IDENTIFIER_ATTR_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_FORBIDDEN_IDENTITY_SUBSTRINGS = (
    "repo_root",
    "worktree",
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


class FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError(
    FullCoreCheckoutIndependentCredentialCapabilityError
):
    """Fail-closed concrete Keychain item-identity contract violation."""


@dataclass(frozen=True)
class FullCoreMacosKeychainItemIdentityV1:
    """Identifier-only Keychain item identity. Not possession or authority."""

    provider_ref_identifier: str
    source_ref_kind: str
    source_ref_uri: str
    keychain_service_id: str
    keychain_account_id: str
    source_backend_class: str
    productive_target_backend: str
    source_location_class: str
    source_ref_is_identifier_only: str
    source_ref_is_keychain_query: str
    keychain_identity_implies_credential_possession: str
    real_keychain_accessed: str
    credential_material_loaded: str

    def to_dict(self) -> dict[str, str]:
        return {
            "provider_ref_identifier": self.provider_ref_identifier,
            "source_ref_kind": self.source_ref_kind,
            "source_ref_uri": self.source_ref_uri,
            "keychain_service_id": self.keychain_service_id,
            "keychain_account_id": self.keychain_account_id,
            "source_backend_class": self.source_backend_class,
            "productive_target_backend": self.productive_target_backend,
            "source_location_class": self.source_location_class,
            "source_ref_is_identifier_only": self.source_ref_is_identifier_only,
            "source_ref_is_keychain_query": self.source_ref_is_keychain_query,
            "keychain_identity_implies_credential_possession": (
                self.keychain_identity_implies_credential_possession
            ),
            "real_keychain_accessed": self.real_keychain_accessed,
            "credential_material_loaded": self.credential_material_loaded,
        }


def _error(code: str) -> NoReturn:
    raise FullCoreCheckoutIndependentCredentialMacosKeychainItemIdentityError(code)


def _assert_identifier_only_attr_v1(raw: str, *, field: str) -> str:
    if raw != raw.strip() or raw != raw.lower():
        _error(f"{field}_NORMALIZATION_FORBIDDEN")
    if not raw or _IDENTIFIER_ATTR_RE.fullmatch(raw) is None:
        _error(f"{field}_CHARSET_VIOLATION")
    lowered = raw.lower()
    for token in FORBIDDEN_SECRET_TOKENS:
        if token in lowered:
            _error(f"{field}_SECRET_TOKEN_FORBIDDEN")
    if (
        raw.startswith("/")
        or raw.startswith("~")
        or ".." in raw
        or any(part in lowered for part in _FORBIDDEN_IDENTITY_SUBSTRINGS)
    ):
        _error("CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY")
    return raw


def prove_owner_identifier_values_exact_v1() -> dict[str, str]:
    service = _assert_identifier_only_attr_v1(KEYCHAIN_SERVICE_ID, field="KEYCHAIN_SERVICE_ID")
    account = _assert_identifier_only_attr_v1(KEYCHAIN_ACCOUNT_ID, field="KEYCHAIN_ACCOUNT_ID")
    identifier = _assert_identifier_only_attr_v1(
        PROVIDER_REF_IDENTIFIER, field="PROVIDER_REF_IDENTIFIER"
    )
    if service != "peak-trade.full-core.venue-credentials":
        _error("KEYCHAIN_SERVICE_ID_MUST_REMAIN_OWNER_EXACT")
    if account != "okx-eea.productive":
        _error("KEYCHAIN_ACCOUNT_ID_MUST_REMAIN_OWNER_EXACT")
    if identifier != "okx-eea-productive":
        _error("PROVIDER_REF_IDENTIFIER_MUST_REMAIN_OWNER_EXACT")
    parsed = assert_checkout_independent_source_ref_v1(SOURCE_REF_URI)
    if parsed.kind != SOURCE_REF_KIND or parsed.kind != ALLOWED_SOURCE_KIND:
        _error("SOURCE_REF_KIND_MUST_REMAIN_PROVIDER_REF")
    if parsed.kind in FORBIDDEN_SOURCE_KINDS or parsed.kind == "keychain":
        _error("SOURCE_REF_KIND_FORBIDDEN")
    if parsed.identifier != identifier:
        _error("PROVIDER_REF_IDENTIFIER_MUST_REMAIN_OWNER_EXACT")
    if parsed.as_uri() != SOURCE_REF_URI:
        _error("SOURCE_REF_URI_MUST_REMAIN_IDENTIFIER_ONLY")
    if SOURCE_REF_URI != "fullcore-cred://provider-ref/okx-eea-productive":
        _error("SOURCE_REF_URI_MUST_REMAIN_OWNER_COMPOSED")
    return {
        "OWNER_IDENTIFIER_VALUES_VALIDATED": TRUE_TOKEN,
        "KEYCHAIN_SERVICE_ID": service,
        "KEYCHAIN_ACCOUNT_ID": account,
        "PROVIDER_REF_IDENTIFIER": identifier,
        "SOURCE_REF_URI": SOURCE_REF_URI,
        "SOURCE_REF_KIND": parsed.kind,
        "VALUES_NORMALIZED": FALSE_TOKEN,
        "VALUES_INVENTED": FALSE_TOKEN,
    }


def prove_concrete_keychain_item_identity_bound_v1() -> dict[str, str]:
    prove_owner_backend_choice_bound_v1()
    values = prove_owner_identifier_values_exact_v1()
    if SOURCE_BACKEND_CLASS != "OS_NATIVE_SECRET_STORE":
        _error("SOURCE_BACKEND_CLASS_DRIFT")
    if PRODUCTIVE_TARGET_BACKEND != "MACOS_KEYCHAIN":
        _error("PRODUCTIVE_TARGET_BACKEND_DRIFT")
    if SOURCE_LOCATION_CLASS != "OS_NATIVE_SECRET_STORE_ITEM_IDENTIFIER":
        _error("SOURCE_LOCATION_CLASS_DRIFT")
    if REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    if PRODUCTIVE_PROVIDER_ACTIVE is True:
        _error("PRODUCTIVE_PROVIDER_MUST_REMAIN_INACTIVE")
    if KEYCHAIN_IDENTITY_IMPLIES_CREDENTIAL_POSSESSION is True:
        _error("KEYCHAIN_IDENTITY_MUST_NOT_IMPLY_POSSESSION")
    return {
        "CONCRETE_KEYCHAIN_SERVICE_BOUND": TRUE_TOKEN,
        "CONCRETE_KEYCHAIN_ACCOUNT_BOUND": TRUE_TOKEN,
        "CONCRETE_BACKEND_ITEM_IDENTITY_BOUND": TRUE_TOKEN,
        "PROVIDER_REF_IDENTIFIER_BOUND": TRUE_TOKEN,
        "PROVIDER_REF_TO_KEYCHAIN_IDENTITY_MAPPING_DEFINED": TRUE_TOKEN,
        "SOURCE_REF_KIND": SOURCE_REF_KIND,
        "SOURCE_REF_IS_IDENTIFIER_ONLY": TRUE_TOKEN,
        "SOURCE_REF_IS_KEYCHAIN_QUERY": FALSE_TOKEN,
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "PRODUCTIVE_PROVIDER_ACTIVE": FALSE_TOKEN,
        "V5_JOINED": FALSE_TOKEN,
        **values,
    }


def resolve_bound_keychain_item_identity_v1(
    raw: str | None,
) -> FullCoreMacosKeychainItemIdentityV1:
    """Map bound provider-ref identifier to Owner Keychain identity.

    Does not query Keychain. Unknown identifiers fail closed.
    """

    prove_concrete_keychain_item_identity_bound_v1()
    parsed = assert_checkout_independent_source_ref_v1(raw)
    if parsed.kind != SOURCE_REF_KIND:
        _error("SOURCE_REF_KIND_MUST_REMAIN_PROVIDER_REF")
    if parsed.kind == "keychain":
        _error("MALFORMED_PROVIDER_REFERENCE")
    if parsed.identifier != PROVIDER_REF_IDENTIFIER:
        _error("KEYCHAIN_IDENTITY_UNKNOWN_IDENTIFIER")
    if parsed.as_uri() != SOURCE_REF_URI:
        _error("SOURCE_REF_URI_MUST_REMAIN_OWNER_COMPOSED")
    identity = FullCoreMacosKeychainItemIdentityV1(
        provider_ref_identifier=PROVIDER_REF_IDENTIFIER,
        source_ref_kind=SOURCE_REF_KIND,
        source_ref_uri=SOURCE_REF_URI,
        keychain_service_id=KEYCHAIN_SERVICE_ID,
        keychain_account_id=KEYCHAIN_ACCOUNT_ID,
        source_backend_class=SOURCE_BACKEND_CLASS,
        productive_target_backend=PRODUCTIVE_TARGET_BACKEND,
        source_location_class=SOURCE_LOCATION_CLASS,
        source_ref_is_identifier_only=TRUE_TOKEN,
        source_ref_is_keychain_query=FALSE_TOKEN,
        keychain_identity_implies_credential_possession=FALSE_TOKEN,
        real_keychain_accessed=FALSE_TOKEN,
        credential_material_loaded=FALSE_TOKEN,
    )
    payload = identity.to_dict()
    for key in _FORBIDDEN_MAPPING_AUTHORITY_KEYS:
        if key in payload:
            _error("MAPPING_MUST_NOT_TRANSPORT_AUTHORITY")
    return identity


def prove_authority_non_interference_v1(
    identity: FullCoreMacosKeychainItemIdentityV1,
    *,
    standing_before: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if identity.provider_ref_identifier != PROVIDER_REF_IDENTIFIER:
        _error("PROVIDER_REF_IDENTIFIER_MUST_REMAIN_OWNER_EXACT")
    if identity.keychain_identity_implies_credential_possession != FALSE_TOKEN:
        _error("KEYCHAIN_IDENTITY_MUST_NOT_IMPLY_POSSESSION")
    if identity.credential_material_loaded != FALSE_TOKEN:
        _error("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    if identity.real_keychain_accessed != FALSE_TOKEN:
        _error("REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE")
    capability = acquire_offline_ephemeral_capability_v1(source_ref=identity.source_ref_uri)
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
        "KEYCHAIN_IDENTITY_IMPLIES_CREDENTIAL_POSSESSION": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_SELECTION_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_TRADING_DECISION_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_RISK_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_ADMISSION_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_EXTERNAL_EFFECT_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_POST_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_IMPLIES_SEND_AUTHORITY": FALSE_TOKEN,
        "GET_AUTH_IMPLIES_SEND_AUTHORITY": FALSE_TOKEN,
        "SIGNING_IMPLIES_SEND_AUTHORITY": FALSE_TOKEN,
        "CAP23_REMAINS_SELECTION_AUTHORITY": TRUE_TOKEN,
        "MASTER_V2_DOUBLE_PLAY_REMAINS_TRADING_DECISION_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_DECISION_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_SIDE_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_QUANTITY_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_RISK_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_ADMISSION_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_SUBMISSION_AUTHORITY": TRUE_TOKEN,
        "MAPPING_TRANSPORTS_NO_EXTERNAL_EFFECT_AUTHORITY": TRUE_TOKEN,
        "REAL_KEYCHAIN_ACCESSED": FALSE_TOKEN,
        "CREDENTIAL_MATERIAL_LOADED": FALSE_TOKEN,
        **authority,
    }


def refuse_mint_from_keychain_identity_bind_v1(
    identity: FullCoreMacosKeychainItemIdentityV1,
) -> None:
    del identity
    refuse_mint_external_effect_permit_from_credential_capability_v1()


def refuse_real_keychain_access_from_identity_bind_v1(*, attempted: bool = True) -> None:
    del attempted
    _error("REAL_KEYCHAIN_ACCESS_FORBIDDEN")


def prove_productive_backend_still_absent_from_identity_bind_v1() -> dict[str, str]:
    return prove_productive_backend_still_absent_v1(source_ref=SOURCE_REF_URI)
