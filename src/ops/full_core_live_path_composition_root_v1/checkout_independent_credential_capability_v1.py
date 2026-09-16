"""Offline Full-Core checkout-independent credential capability contract V1.

Phase A: OFFLINE_CONTRACT_ONLY. No productive backend. No V5 join. No secrets.
No network. Credential capability is technical venue-auth capability only.

OWNER_GO=OWNER_GO_FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_CAPABILITY_OFFLINE_CONTRACT_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol
from uuid import uuid4

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = "OWNER_GO_FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_CAPABILITY_OFFLINE_CONTRACT_V1"
THIS_SLICE = "11.2.1.DX.FULL_CORE_CHECKOUT_INDEPENDENT_CREDENTIAL_CAPABILITY_OFFLINE_CONTRACT"
CONTRACT_VERSION = "v1"
SOURCE_REF_SCHEME = "fullcore-cred"
ALLOWED_SOURCE_KIND = "provider-ref"
REQUIRED_ENVIRONMENT = "LIVE"
REQUIRED_CREDENTIAL_CLASS = "FULL_CORE_VENUE_AUTH_CLASS"
PRODUCTIVE_BACKEND_JOINED = False
V5_JOINED = False
CHECKOUT_INDEPENDENT_PRODUCTIVE_PROVIDER_ACTIVE = False
AUTONOMOUS_EXECUTOR_ACTIVATED = False
REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE = "REAL_BACKEND_ACCESS_NOT_IMPLEMENTED_AND_NOT_AUTHORIZED"
HISTORICAL_PHASE_A_PRODUCTIVE_BACKEND_ABSENT_CODE = "PRODUCTIVE_BACKEND_ABSENT"

CREDENTIAL_CAPABILITY_IS_TECHNICAL_CAPABILITY_NOT_TRADING_AUTHORITY = True
CREDENTIAL_POSSESSION_GRANTS_NO_TRADING_AUTHORITY = True
CREDENTIAL_POSSESSION_ALONE_GRANTS_NO_POST_AUTHORITY = True
EXECUTION_AUTONOMY_TRADING_DECISION_AUTHORITY = False
GET_AUTH_CAPABILITY_IMPLIES_POST_AUTHORITY = False
SIGNING_CAPABILITY_IMPLIES_SEND_AUTHORITY = False

FORBIDDEN_SOURCE_KINDS = frozenset(
    {
        "file",
        "path",
        "worktree",
        "repo-root",
        "keychain",
        "aws",
        "hashicorp",
        "env",
        "socket",
        "daemon",
        "ipc",
        "symlink",
        "vault-file",
        "json-file",
    }
)
FORBIDDEN_SECRET_TOKENS = (
    "api_key",
    "apikey",
    "api_secret",
    "passphrase",
    "private_key",
    "secret",
    "sk-",
    "plaintext",
    "authorization",
)
FORBIDDEN_AUTHORITY_FIELDS = (
    "selection_authority",
    "trading_decision_authority",
    "risk_authority",
    "admission_authority",
    "external_effect_authority",
    "post_authority",
)
AUTONOMOUS_EXECUTOR_FORBIDDEN_ACTIONS = (
    "RANKING_MUTATE",
    "RANKING_MINT",
    "TOP5_RESELECT",
    "CAP23_OVERRIDE",
    "INSTRUMENT_SWITCH",
    "MASTER_V2_DECISION_MINT",
    "DOUBLE_PLAY_DECISION_MINT",
    "SIDE_MUTATE",
    "QUANTITY_INCREASE",
    "STEP_29P_OVERRIDE",
    "SAFETY_VETO_OVERRIDE",
    "ADMISSION_UPGRADE",
    "PLAN_ONLY_TO_SUBMIT",
    "POST_FROM_CREDENTIAL_AVAILABILITY",
)
_SOURCE_REF_RE = re.compile(
    r"^fullcore-cred://([a-z][a-z0-9_-]{0,31})/([a-z0-9][a-z0-9._-]{0,127})$"
)
_RELEASED_IDS: set[str] = set()

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_PLAINTEXT_FIELD_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "api_secret",
        "passphrase",
        "private_key",
        "secret",
        "ok-access-key",
        "ok-access-sign",
        "ok-access-passphrase",
    }
)


def _assert_payload_has_no_plaintext_fields_v1(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        kl = str(key).lower()
        if kl in _PLAINTEXT_FIELD_KEYS:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(
                f"PLAINTEXT_CREDENTIAL_FIELD_FORBIDDEN:{kl}"
            )
        if isinstance(value, Mapping):
            _assert_payload_has_no_plaintext_fields_v1(value)


class FullCoreCheckoutIndependentCredentialCapabilityError(RuntimeError):
    """Fail-closed checkout-independent credential contract violation."""


@dataclass(frozen=True)
class FullCoreCheckoutIndependentCredentialSourceRefV1:
    """Backend-neutral, non-secret-bearing provider reference."""

    kind: str
    identifier: str

    def as_uri(self) -> str:
        return f"{SOURCE_REF_SCHEME}://{self.kind}/{self.identifier}"

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "identifier": self.identifier,
            "uri": self.as_uri(),
            "scheme": SOURCE_REF_SCHEME,
        }


@dataclass(frozen=True)
class FullCoreCheckoutIndependentCredentialCapabilityV1:
    """Ephemeral Full-Core credential capability. No plaintext credential fields."""

    capability_id: str
    source_ref: FullCoreCheckoutIndependentCredentialSourceRefV1
    credential_class: str
    environment: str
    bound: bool
    released: bool
    material_loaded: bool
    can_authenticate_private_get: bool
    can_sign: bool
    selection_authority: bool = False
    trading_decision_authority: bool = False
    risk_authority: bool = False
    admission_authority: bool = False
    external_effect_authority: bool = False
    post_authority: bool = False
    send_authority: bool = False
    checkout_identity: str = ""
    repo_root: str = ""

    def __post_init__(self) -> None:
        if self.material_loaded is True:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(
                "CREDENTIAL_MATERIAL_LOADED_FORBIDDEN"
            )
        if self.checkout_identity or self.repo_root:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(
                "CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY"
            )
        _assert_payload_has_no_plaintext_fields_v1(self.to_dict())
        _assert_payload_has_no_plaintext_fields_v1(self.to_claims())
        _assert_payload_has_no_plaintext_fields_v1(self.to_log_safe())
        for field in FORBIDDEN_AUTHORITY_FIELDS:
            if getattr(self, field) is True:
                raise FullCoreCheckoutIndependentCredentialCapabilityError(
                    f"CREDENTIAL_CAPABILITY_MUST_NOT_GRANT_{field.upper()}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "source_ref": self.source_ref.to_dict(),
            "credential_class": self.credential_class,
            "environment": self.environment,
            "bound": TRUE_TOKEN if self.bound else FALSE_TOKEN,
            "released": TRUE_TOKEN if self.released else FALSE_TOKEN,
            "material_loaded": FALSE_TOKEN,
            "can_authenticate_private_get": (
                TRUE_TOKEN if self.can_authenticate_private_get else FALSE_TOKEN
            ),
            "can_sign": TRUE_TOKEN if self.can_sign else FALSE_TOKEN,
            "selection_authority": FALSE_TOKEN,
            "trading_decision_authority": FALSE_TOKEN,
            "risk_authority": FALSE_TOKEN,
            "admission_authority": FALSE_TOKEN,
            "external_effect_authority": FALSE_TOKEN,
            "post_authority": FALSE_TOKEN,
            "send_authority": FALSE_TOKEN,
            "get_auth_implies_post_authority": FALSE_TOKEN,
            "signing_implies_send_authority": FALSE_TOKEN,
            "plaintext_present": FALSE_TOKEN,
        }

    def to_claims(self) -> dict[str, str]:
        payload = self.to_dict()
        claims: dict[str, str] = {}
        for key, value in payload.items():
            if key == "source_ref":
                claims["SOURCE_REF_URI"] = str(self.source_ref.as_uri())
                claims["SOURCE_REF_KIND"] = self.source_ref.kind
                continue
            claims[str(key).upper()] = str(value)
        return claims

    def to_log_safe(self) -> dict[str, str]:
        return {
            "capability_id": self.capability_id,
            "source_kind": self.source_ref.kind,
            "credential_class": self.credential_class,
            "bound": TRUE_TOKEN if self.bound else FALSE_TOKEN,
            "released": TRUE_TOKEN if self.released else FALSE_TOKEN,
            "material_loaded": FALSE_TOKEN,
        }


class FullCoreCheckoutIndependentCredentialProviderPortV1(Protocol):
    """Fail-closed provider port. Real Keychain acquisition is not implemented."""

    def resolve_capability_v1(
        self,
        *,
        source_ref: FullCoreCheckoutIndependentCredentialSourceRefV1,
        credential_class: str,
        environment: str,
    ) -> FullCoreCheckoutIndependentCredentialCapabilityV1: ...

    def release_capability_v1(
        self, capability: FullCoreCheckoutIndependentCredentialCapabilityV1
    ) -> None: ...


def assert_checkout_independent_source_ref_v1(
    raw: str | FullCoreCheckoutIndependentCredentialSourceRefV1 | None,
) -> FullCoreCheckoutIndependentCredentialSourceRefV1:
    if raw is None:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("PROVIDER_REFERENCE_MISSING")
    if isinstance(raw, FullCoreCheckoutIndependentCredentialSourceRefV1):
        uri = raw.as_uri()
    else:
        uri = str(raw or "").strip()
    lowered = uri.lower()
    for token in FORBIDDEN_SECRET_TOKENS:
        if token in lowered:
            raise FullCoreCheckoutIndependentCredentialCapabilityError(
                "MALFORMED_PROVIDER_REFERENCE"
            )
    matched = _SOURCE_REF_RE.fullmatch(uri)
    if matched is None:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("MALFORMED_PROVIDER_REFERENCE")
    kind, identifier = matched.group(1), matched.group(2)
    if kind in FORBIDDEN_SOURCE_KINDS or kind != ALLOWED_SOURCE_KIND:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("MALFORMED_PROVIDER_REFERENCE")
    if "repo_root" in identifier or "worktree" in identifier:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY"
        )
    return FullCoreCheckoutIndependentCredentialSourceRefV1(kind=kind, identifier=identifier)


def _assert_environment_v1(environment: str) -> str:
    env = str(environment or "").strip()
    if env != REQUIRED_ENVIRONMENT:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("ENVIRONMENT_MISMATCH")
    return env


def _assert_credential_class_v1(credential_class: str) -> str:
    klass = str(credential_class or "").strip()
    if klass != REQUIRED_CREDENTIAL_CLASS:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("CREDENTIAL_CLASS_MISMATCH")
    return klass


def bind_offline_contract_capability_v1(
    *,
    source_ref: str | FullCoreCheckoutIndependentCredentialSourceRefV1,
    credential_class: str = REQUIRED_CREDENTIAL_CLASS,
    environment: str = REQUIRED_ENVIRONMENT,
    can_authenticate_private_get: bool = True,
    can_sign: bool = True,
) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
    """Offline contract object only. Does not load secrets or join a backend."""

    parsed = assert_checkout_independent_source_ref_v1(source_ref)
    env = _assert_environment_v1(environment)
    klass = _assert_credential_class_v1(credential_class)
    capability = FullCoreCheckoutIndependentCredentialCapabilityV1(
        capability_id=f"fc-cicc-{uuid4().hex}",
        source_ref=parsed,
        credential_class=klass,
        environment=env,
        bound=True,
        released=False,
        material_loaded=False,
        can_authenticate_private_get=can_authenticate_private_get is True,
        can_sign=can_sign is True,
    )
    prove_capability_serialization_has_no_plaintext_v1(capability)
    return capability


def resolve_checkout_independent_credential_capability_v1(
    *,
    source_ref: str | FullCoreCheckoutIndependentCredentialSourceRefV1 | None,
    credential_class: str = REQUIRED_CREDENTIAL_CLASS,
    environment: str = REQUIRED_ENVIRONMENT,
    provider: Optional[FullCoreCheckoutIndependentCredentialProviderPortV1] = None,
    repo_root: str | None = None,
    checkout_identity: str | None = None,
) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
    """Dispatch to an explicit provider, then remain fail-closed before acquisition."""

    if repo_root or checkout_identity:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY"
        )
    parsed = assert_checkout_independent_source_ref_v1(source_ref)
    env = _assert_environment_v1(environment)
    klass = _assert_credential_class_v1(credential_class)
    if provider is None:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("PROVIDER_UNAVAILABLE")
    resolve_fn = getattr(provider, "resolve_capability_v1", None)
    if not callable(resolve_fn):
        raise FullCoreCheckoutIndependentCredentialCapabilityError("PROVIDER_UNAVAILABLE")
    returned = resolve_fn(
        source_ref=parsed,
        credential_class=klass,
        environment=env,
    )
    if getattr(returned, "material_loaded", False) is True:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CREDENTIAL_MATERIAL_LOADED_FORBIDDEN"
        )
    raise FullCoreCheckoutIndependentCredentialCapabilityError(REAL_BACKEND_ACCESS_FAIL_CLOSED_CODE)


def release_checkout_independent_credential_capability_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> FullCoreCheckoutIndependentCredentialCapabilityV1:
    if capability is None or not isinstance(
        capability, FullCoreCheckoutIndependentCredentialCapabilityV1
    ):
        raise FullCoreCheckoutIndependentCredentialCapabilityError("CAPABILITY_MISSING")
    if capability.capability_id in _RELEASED_IDS or capability.released is True:
        raise FullCoreCheckoutIndependentCredentialCapabilityError("CAPABILITY_ALREADY_RELEASED")
    _RELEASED_IDS.add(capability.capability_id)
    return FullCoreCheckoutIndependentCredentialCapabilityV1(
        capability_id=capability.capability_id,
        source_ref=capability.source_ref,
        credential_class=capability.credential_class,
        environment=capability.environment,
        bound=False,
        released=True,
        material_loaded=False,
        can_authenticate_private_get=False,
        can_sign=False,
    )


def prove_capability_serialization_has_no_plaintext_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> dict[str, str]:
    _assert_payload_has_no_plaintext_fields_v1(capability.to_dict())
    _assert_payload_has_no_plaintext_fields_v1(capability.to_claims())
    _assert_payload_has_no_plaintext_fields_v1(capability.to_log_safe())
    return {"PLAINTEXT_PRESENT": FALSE_TOKEN, "MATERIAL_LOADED": FALSE_TOKEN}


def prove_capability_grants_no_trading_or_post_authority_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
) -> dict[str, str]:
    if capability.can_authenticate_private_get is True and capability.post_authority is True:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "GET_AUTH_MUST_NOT_IMPLY_POST_AUTHORITY"
        )
    if capability.can_sign is True and capability.send_authority is True:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "SIGNING_MUST_NOT_IMPLY_SEND_AUTHORITY"
        )
    return {
        "SELECTION_AUTHORITY": FALSE_TOKEN,
        "TRADING_DECISION_AUTHORITY": FALSE_TOKEN,
        "RISK_AUTHORITY": FALSE_TOKEN,
        "ADMISSION_AUTHORITY": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORITY": FALSE_TOKEN,
        "POST_AUTHORITY": FALSE_TOKEN,
        "SEND_AUTHORITY": FALSE_TOKEN,
        "GET_AUTH_IMPLIES_POST_AUTHORITY": FALSE_TOKEN,
        "SIGNING_IMPLIES_SEND_AUTHORITY": FALSE_TOKEN,
        "CREDENTIAL_POSSESSION_GRANTS_NO_TRADING_AUTHORITY": TRUE_TOKEN,
        "CREDENTIAL_POSSESSION_ALONE_GRANTS_NO_POST_AUTHORITY": TRUE_TOKEN,
    }


def refuse_mint_external_effect_permit_from_credential_capability_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1 | None = None,
) -> None:
    del capability
    raise FullCoreCheckoutIndependentCredentialCapabilityError(
        "CREDENTIAL_CAPABILITY_CANNOT_MINT_PERMIT"
    )


def prove_capability_cannot_mutate_standing_gates_v1() -> dict[str, str]:
    snapshot = {
        "LIVE_ENABLED": TRUE_TOKEN if LIVE_ENABLED is True else FALSE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN if LIVE_ARMED is True else FALSE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN if WIRE_SEND_PERMITTED is True else FALSE_TOKEN,
        "SUBMISSION_AUTHORIZED": TRUE_TOKEN if SUBMISSION_AUTHORIZED is True else FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": (
            TRUE_TOKEN if EXTERNAL_EFFECT_AUTHORIZED is True else FALSE_TOKEN
        ),
        "REAL_VENUE_POST_ALLOWED": TRUE_TOKEN if REAL_VENUE_POST_ALLOWED is True else FALSE_TOKEN,
        "POST_ALLOWED": TRUE_TOKEN if POST_ALLOWED is True else FALSE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": str(int(MAX_POSITIONS_EFFECTIVE)),
    }
    if snapshot["EXTERNAL_EFFECT_AUTHORIZED"] != FALSE_TOKEN:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE"
        )
    if snapshot["REAL_VENUE_POST_ALLOWED"] != FALSE_TOKEN:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "STANDING_REAL_VENUE_POST_MUST_REMAIN_FALSE"
        )
    if snapshot["POST_ALLOWED"] != FALSE_TOKEN:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "STANDING_POST_MUST_REMAIN_FALSE"
        )
    if snapshot["MAX_POSITIONS_EFFECTIVE"] != "1":
        raise FullCoreCheckoutIndependentCredentialCapabilityError("MAX_POSITIONS_EFFECTIVE_DRIFT")
    return snapshot


def prove_repo_root_not_provider_authority_v1(*, repo_root: str | None) -> dict[str, str]:
    if repo_root:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY"
        )
    return {"REPO_ROOT_IS_CREDENTIAL_AUTHORITY": FALSE_TOKEN}


def prove_worktree_identity_not_required_v1(*, checkout_identity: str | None) -> dict[str, str]:
    if checkout_identity:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CHECKOUT_IDENTITY_MUST_NOT_BE_CREDENTIAL_AUTHORITY"
        )
    return {
        "WORKTREE_IDENTITY_REQUIRED": FALSE_TOKEN,
        "GIT_WORKTREE_CREATION_IMPLIES_CREDENTIAL_DUPLICATION": FALSE_TOKEN,
    }


def prove_autonomous_executor_boundary_v1() -> dict[str, str]:
    return {
        "EXECUTION_AUTONOMY_TRADING_DECISION_AUTHORITY": FALSE_TOKEN,
        "FORBIDDEN_ACTIONS": ",".join(AUTONOMOUS_EXECUTOR_FORBIDDEN_ACTIONS),
        "CREDENTIAL_AVAILABILITY_MAY_NOT_UPGRADE_STANDING_GATES": TRUE_TOKEN,
    }


def prove_capability_does_not_upgrade_standing_gates_v1(
    capability: FullCoreCheckoutIndependentCredentialCapabilityV1,
    *,
    before: Mapping[str, str],
) -> dict[str, str]:
    del capability
    after = prove_capability_cannot_mutate_standing_gates_v1()
    if dict(before) != after:
        raise FullCoreCheckoutIndependentCredentialCapabilityError(
            "CREDENTIAL_CAPABILITY_MUST_NOT_MUTATE_STANDING_GATES"
        )
    return after
