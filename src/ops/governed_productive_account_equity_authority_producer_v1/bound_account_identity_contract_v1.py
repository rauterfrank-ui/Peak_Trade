"""Bound account-identity contract for OPTION_D reconstruction domain.

Typed identity binding so checkpoint, classified events, and fresh-eq
targets can be assigned to one governed account domain. Identity is
explicit and deterministic. Environment, credential, and implicit
default provenance fail closed. Instrument identity is not a D4
member. Not a venue GET. Not equity source authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN,
    SOURCE_SELECTED,
)

SCHEMA_CLASS = "BOUND_ACCOUNT_IDENTITY_CONTRACT_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
IDENTITY_KIND = "GOVERNED_ACCOUNT_DOMAIN_IDENTITY"
OBSERVATION_VS_AUTHORITY_CLASS = "NON_AUTHORITATIVE_IDENTITY_BINDING"
PROVENANCE_EXPLICIT_TYPED_BINDING = "EXPLICIT_TYPED_BINDING"
PROVENANCE_GENESIS_FRESH_TYPED_BINDING = "GENESIS_FRESH_TYPED_BINDING"
RATIFIED_PROVENANCE_CLASSES: Tuple[str, ...] = (
    PROVENANCE_EXPLICIT_TYPED_BINDING,
    PROVENANCE_GENESIS_FRESH_TYPED_BINDING,
)
FORBIDDEN_PROVENANCE_CLASSES: Tuple[str, ...] = (
    "ENVIRONMENT",
    "CREDENTIAL",
    "IMPLICIT_DEFAULT",
    "UNKNOWN",
    "UNCLASSIFIED",
)
RATIFIED_IDENTITY_MEMBERS: Tuple[str, ...] = (
    "bound_account_identity",
    "bound_venue_identity",
    "bound_td_mode",
    "settlement_currency",
)
NOT_D4_IDENTITY_MEMBERS: Tuple[str, ...] = (
    "expected_instrument_id",
    "instId",
    "rest_host",
    "account_mode",
)
REQUIRED_FIELDS: Tuple[str, ...] = (
    "identity_id",
    "identity_kind",
    "authority_owner",
    "bound_account_identity",
    "bound_venue_identity",
    "bound_td_mode",
    "settlement_currency",
    "identity_provenance_class",
    "identity_digest",
)
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_IMPLICIT_MARKERS: Tuple[str, ...] = (
    "os.environ",
    "getenv",
    "api_key",
    "secret",
    "credential",
    "implicit_default",
    "acct-uid-demo",
)
_UNKNOWN_TOKENS: Tuple[str, ...] = ("UNKNOWN", "UNCLASSIFIED", "UNPROVEN", "MISSING", "DEFAULT")


class BoundAccountIdentityContractError(ValueError):
    """Fail-closed bound-account-identity contract violation."""


@dataclass(frozen=True)
class BoundAccountIdentityContractV1:
    identity_id: str
    identity_kind: str
    authority_owner: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    settlement_currency: str
    identity_provenance_class: str
    identity_digest: str
    observation_vs_authority_class: str
    authority_effect: str
    provenance_digest: str


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise BoundAccountIdentityContractError(f"BOUND_ACCOUNT_IDENTITY_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise BoundAccountIdentityContractError(f"BOUND_ACCOUNT_IDENTITY_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise BoundAccountIdentityContractError(f"BOUND_ACCOUNT_IDENTITY_FIELD_MISSING:{field}")
    return text


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_bound_account_identity_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _reject_implicit_or_unknown_token(*, field: str, raw: str) -> None:
    if raw in _UNKNOWN_TOKENS:
        raise BoundAccountIdentityContractError(
            f"BOUND_ACCOUNT_IDENTITY_UNKNOWN_OR_MISSING:{field}"
        )
    lowered = raw.lower()
    if any(marker in lowered for marker in _FORBIDDEN_IMPLICIT_MARKERS):
        raise BoundAccountIdentityContractError(
            f"BOUND_ACCOUNT_IDENTITY_IMPLICIT_OR_CREDENTIAL_TOKEN:{field}"
        )


def require_bound_account_identity_ref_v1(
    *,
    bound_account_identity_ref: Any,
    bound_account_identity_digest: Any,
) -> tuple[str, str]:
    identity_ref = _require_non_empty_str(
        field="bound_account_identity_ref", raw=bound_account_identity_ref
    )
    identity_digest = _require_non_empty_str(
        field="bound_account_identity_digest", raw=bound_account_identity_digest
    )
    if identity_ref in _UNKNOWN_TOKENS:
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_REF_UNKNOWN")
    if not _SHA256_HEX.match(identity_digest):
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_DIGEST_NOT_SHA256")
    return identity_ref, identity_digest


def assert_same_bound_account_identity_v1(
    *,
    left_ref: str,
    left_digest: str,
    right_ref: str,
    right_digest: str,
) -> None:
    left = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=left_ref,
        bound_account_identity_digest=left_digest,
    )
    right = require_bound_account_identity_ref_v1(
        bound_account_identity_ref=right_ref,
        bound_account_identity_digest=right_digest,
    )
    if left != right:
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_MISMATCH_CROSS_ACCOUNT")


def build_bound_account_identity_contract_v1(
    *,
    identity_id: str,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    settlement_currency: str,
    identity_provenance_class: str = PROVENANCE_EXPLICIT_TYPED_BINDING,
) -> BoundAccountIdentityContractV1:
    if SOURCE_SELECTED is True:
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_CANNOT_SELECT_SOURCE")
    if BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN is not True:
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_FROM_ENV_NOT_FORBIDDEN")
    if BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN is not True:
        raise BoundAccountIdentityContractError(
            "BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_NOT_FORBIDDEN"
        )
    if BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN is not True:
        raise BoundAccountIdentityContractError(
            "BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_NOT_FORBIDDEN"
        )
    provenance = _require_non_empty_str(
        field="identity_provenance_class", raw=identity_provenance_class
    )
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        raise BoundAccountIdentityContractError(
            f"BOUND_ACCOUNT_IDENTITY_PROVENANCE_FORBIDDEN:{provenance}"
        )
    if provenance not in RATIFIED_PROVENANCE_CLASSES:
        raise BoundAccountIdentityContractError(
            f"BOUND_ACCOUNT_IDENTITY_PROVENANCE_NOT_RATIFIED:{provenance}"
        )
    payload = {
        "identity_id": _require_non_empty_str(field="identity_id", raw=identity_id),
        "identity_kind": IDENTITY_KIND,
        "authority_owner": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "bound_account_identity": _require_non_empty_str(
            field="bound_account_identity", raw=bound_account_identity
        ),
        "bound_venue_identity": _require_non_empty_str(
            field="bound_venue_identity", raw=bound_venue_identity
        ),
        "bound_td_mode": _require_non_empty_str(field="bound_td_mode", raw=bound_td_mode),
        "settlement_currency": _require_non_empty_str(
            field="settlement_currency", raw=settlement_currency
        ),
        "identity_provenance_class": provenance,
    }
    if payload["authority_owner"] != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise BoundAccountIdentityContractError("BOUND_ACCOUNT_IDENTITY_OWNER_MUTATED")
    for field in RATIFIED_IDENTITY_MEMBERS:
        _reject_implicit_or_unknown_token(field=field, raw=payload[field])
    _reject_implicit_or_unknown_token(field="identity_id", raw=payload["identity_id"])
    member_digest_payload = {key: payload[key] for key in RATIFIED_IDENTITY_MEMBERS}
    member_digest_payload["identity_id"] = payload["identity_id"]
    member_digest_payload["identity_provenance_class"] = payload["identity_provenance_class"]
    identity_digest = compute_bound_account_identity_digest_v1(member_digest_payload)
    payload["identity_digest"] = identity_digest
    digest_payload = dict(payload)
    digest_payload["observation_vs_authority_class"] = OBSERVATION_VS_AUTHORITY_CLASS
    digest_payload["authority_effect"] = AUTHORITY_EFFECT
    provenance_digest = compute_bound_account_identity_digest_v1(digest_payload)
    return BoundAccountIdentityContractV1(
        **payload,
        observation_vs_authority_class=OBSERVATION_VS_AUTHORITY_CLASS,
        authority_effect=AUTHORITY_EFFECT,
        provenance_digest=provenance_digest,
    )
