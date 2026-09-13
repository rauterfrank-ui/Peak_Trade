"""Durable D4 BoundAccountIdentity runtime binding.

Persists an explicit typed BoundAccountIdentity as a digest-stable
runtime instance. Reuses the existing identity builder. Does not mint
identity from env, credential, GET, default, or history. Does not set
CONCRETE_UID_CORROBORATED. Not a venue GET. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_contract_v1 import (
    BoundAccountIdentityContractError,
    BoundAccountIdentityContractV1,
    FORBIDDEN_PROVENANCE_CLASSES,
    PROVENANCE_EXPLICIT_TYPED_BINDING,
    RATIFIED_IDENTITY_MEMBERS,
    build_bound_account_identity_contract_v1,
    compute_bound_account_identity_digest_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
    BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT,
    D4_CONCRETE_UID_CORROBORATED,
    D4_RUNTIME_BINDING_CONTRACT_PRESENT,
)

SCHEMA_CLASS = "BOUND_ACCOUNT_IDENTITY_RUNTIME_BINDING_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
CONTRACT_STATUS_PROVEN = "CONTRACT_PROVEN"
RUNTIME_INSTANCE_PRESENT_TOKEN = "true"
RUNTIME_INSTANCE_ABSENT_TOKEN = "false"
CONCRETE_UID_CORROBORATED_TOKEN = "false"
D4_RUNTIME_INSTANCE_FILENAME = "d4_bound_account_identity_runtime_instance_v1.json"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
REQUIRED_INPUT_FIELDS: Tuple[str, ...] = RATIFIED_IDENTITY_MEMBERS
FORBIDDEN_MINT_SOURCES: Tuple[str, ...] = (
    "ENVIRONMENT",
    "CREDENTIAL",
    "IMPLICIT_DEFAULT",
    "GET",
    "HISTORY",
    "ACCOUNT_CONFIG",
    "DEFAULT",
)
_FORBIDDEN_MINT_MARKERS: Tuple[str, ...] = (
    "os.environ",
    "getenv",
    "api_key",
    "secret",
    "credential",
    "implicit_default",
    "acct-uid-demo",
    "lookback",
    "history",
)


class BoundAccountIdentityRuntimeBindingError(ValueError):
    """Fail-closed D4 runtime-binding violation."""


@dataclass(frozen=True)
class BoundAccountIdentityRuntimeBindingV1:
    identity_id: str
    identity_kind: str
    authority_owner: str
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    settlement_currency: str
    identity_provenance_class: str
    identity_digest: str
    contract_status: str
    runtime_instance_present: str
    concrete_uid_corroborated: str
    observation_vs_authority_class: str
    authority_effect: str
    instance_digest: str
    provenance_digest: str


@dataclass(frozen=True)
class BoundAccountIdentityRuntimeBindingStatusV1:
    contract_status: str
    runtime_instance_present: str
    concrete_uid_corroborated: str
    canonical_runtime_instance_present: str
    artifact_present: str


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_d4_runtime_instance_digest_v1(canonical: Mapping[str, str]) -> str:
    return hashlib.sha256(_canonical_json(canonical).encode("utf-8")).hexdigest()


def _require_non_empty_str(*, field: str, raw: Any) -> str:
    if raw is None:
        raise BoundAccountIdentityRuntimeBindingError(f"D4_RUNTIME_FIELD_MISSING:{field}")
    if isinstance(raw, bool) or not isinstance(raw, str):
        raise BoundAccountIdentityRuntimeBindingError(f"D4_RUNTIME_FIELD_NOT_STRING:{field}")
    text = raw.strip()
    if text == "" or text != raw:
        raise BoundAccountIdentityRuntimeBindingError(f"D4_RUNTIME_FIELD_MISSING:{field}")
    return text


def _reject_mint_source(*, field: str, raw: str) -> None:
    if raw in FORBIDDEN_MINT_SOURCES or raw in FORBIDDEN_PROVENANCE_CLASSES:
        raise BoundAccountIdentityRuntimeBindingError(f"D4_RUNTIME_PROVENANCE_FORBIDDEN:{raw}")
    lowered = raw.lower()
    if any(marker in lowered for marker in _FORBIDDEN_MINT_MARKERS):
        raise BoundAccountIdentityRuntimeBindingError(
            f"D4_RUNTIME_IMPLICIT_OR_CREDENTIAL_TOKEN:{field}"
        )


def d4_runtime_instance_path_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / D4_RUNTIME_INSTANCE_FILENAME


def _assert_runtime_pins() -> None:
    if D4_RUNTIME_BINDING_CONTRACT_PRESENT is not True:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_BINDING_CONTRACT_NOT_PRESENT")
    if BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN is not True:
        raise BoundAccountIdentityRuntimeBindingError(
            "BOUND_ACCOUNT_IDENTITY_FROM_ENV_NOT_FORBIDDEN"
        )
    if BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN is not True:
        raise BoundAccountIdentityRuntimeBindingError(
            "BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_NOT_FORBIDDEN"
        )
    if BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN is not True:
        raise BoundAccountIdentityRuntimeBindingError(
            "BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_NOT_FORBIDDEN"
        )
    if D4_CONCRETE_UID_CORROBORATED is not False:
        raise BoundAccountIdentityRuntimeBindingError(
            "D4_CONCRETE_UID_CORROBORATED_MUST_REMAIN_FALSE"
        )
    if BOUND_ACCOUNT_CONCRETE_UID_OBSERVED is not False:
        raise BoundAccountIdentityRuntimeBindingError(
            "BOUND_ACCOUNT_CONCRETE_UID_OBSERVED_MUST_REMAIN_FALSE"
        )
    if ACCOUNT_EQUITY_AUTHORITY_OWNER != (
        "ops.governed_productive_account_equity_authority_producer_v1"
    ):
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_AUTHORITY_OWNER_MUTATED")


def _binding_from_identity(
    identity: BoundAccountIdentityContractV1,
) -> BoundAccountIdentityRuntimeBindingV1:
    payload = {
        "identity_id": identity.identity_id,
        "identity_kind": identity.identity_kind,
        "authority_owner": identity.authority_owner,
        "bound_account_identity": identity.bound_account_identity,
        "bound_venue_identity": identity.bound_venue_identity,
        "bound_td_mode": identity.bound_td_mode,
        "settlement_currency": identity.settlement_currency,
        "identity_provenance_class": identity.identity_provenance_class,
        "identity_digest": identity.identity_digest,
        "contract_status": CONTRACT_STATUS_PROVEN,
        "runtime_instance_present": RUNTIME_INSTANCE_PRESENT_TOKEN,
        "concrete_uid_corroborated": CONCRETE_UID_CORROBORATED_TOKEN,
        "observation_vs_authority_class": identity.observation_vs_authority_class,
        "authority_effect": AUTHORITY_EFFECT,
    }
    instance_digest = compute_d4_runtime_instance_digest_v1(payload)
    payload["instance_digest"] = instance_digest
    provenance_digest = compute_d4_runtime_instance_digest_v1(payload)
    return BoundAccountIdentityRuntimeBindingV1(
        **payload,
        provenance_digest=provenance_digest,
    )


def build_bound_account_identity_runtime_binding_v1(
    *,
    identity_id: str,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    settlement_currency: str,
    identity_provenance_class: str = PROVENANCE_EXPLICIT_TYPED_BINDING,
) -> BoundAccountIdentityRuntimeBindingV1:
    _assert_runtime_pins()
    provenance = _require_non_empty_str(
        field="identity_provenance_class", raw=identity_provenance_class
    )
    _reject_mint_source(field="identity_provenance_class", raw=provenance)
    if provenance != PROVENANCE_EXPLICIT_TYPED_BINDING:
        raise BoundAccountIdentityRuntimeBindingError(
            f"D4_RUNTIME_PROVENANCE_NOT_EXPLICIT_TYPED_BINDING:{provenance}"
        )
    try:
        identity = build_bound_account_identity_contract_v1(
            identity_id=identity_id,
            bound_account_identity=bound_account_identity,
            bound_venue_identity=bound_venue_identity,
            bound_td_mode=bound_td_mode,
            settlement_currency=settlement_currency,
            identity_provenance_class=provenance,
        )
    except BoundAccountIdentityContractError as exc:
        raise BoundAccountIdentityRuntimeBindingError(str(exc)) from exc
    binding = _binding_from_identity(identity)
    if binding.concrete_uid_corroborated != CONCRETE_UID_CORROBORATED_TOKEN:
        raise BoundAccountIdentityRuntimeBindingError(
            "D4_RUNTIME_CANNOT_SET_CONCRETE_UID_CORROBORATED"
        )
    if binding.contract_status != CONTRACT_STATUS_PROVEN:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_CONTRACT_STATUS_NOT_PROVEN")
    return binding


def persist_bound_account_identity_runtime_binding_v1(
    *,
    store_root: Path | str,
    identity_id: str,
    bound_account_identity: str,
    bound_venue_identity: str,
    bound_td_mode: str,
    settlement_currency: str,
    identity_provenance_class: str = PROVENANCE_EXPLICIT_TYPED_BINDING,
) -> BoundAccountIdentityRuntimeBindingV1:
    binding = build_bound_account_identity_runtime_binding_v1(
        identity_id=identity_id,
        bound_account_identity=bound_account_identity,
        bound_venue_identity=bound_venue_identity,
        bound_td_mode=bound_td_mode,
        settlement_currency=settlement_currency,
        identity_provenance_class=identity_provenance_class,
    )
    path = d4_runtime_instance_path_v1(store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "identity_id": binding.identity_id,
        "identity_kind": binding.identity_kind,
        "authority_owner": binding.authority_owner,
        "bound_account_identity": binding.bound_account_identity,
        "bound_venue_identity": binding.bound_venue_identity,
        "bound_td_mode": binding.bound_td_mode,
        "settlement_currency": binding.settlement_currency,
        "identity_provenance_class": binding.identity_provenance_class,
        "identity_digest": binding.identity_digest,
        "contract_status": binding.contract_status,
        "runtime_instance_present": binding.runtime_instance_present,
        "concrete_uid_corroborated": CONCRETE_UID_CORROBORATED_TOKEN,
        "observation_vs_authority_class": binding.observation_vs_authority_class,
        "authority_effect": binding.authority_effect,
        "instance_digest": binding.instance_digest,
        "provenance_digest": binding.provenance_digest,
    }
    encoded = _canonical_json(payload) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(encoded, encoding="utf-8")
    tmp.replace(path)
    return binding


def load_bound_account_identity_runtime_binding_v1(
    *,
    store_root: Path | str | None,
) -> BoundAccountIdentityRuntimeBindingV1:
    _assert_runtime_pins()
    if store_root is None:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_INSTANCE_ABSENT")
    path = d4_runtime_instance_path_v1(store_root=store_root)
    if not path.is_file():
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_INSTANCE_ABSENT")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_INSTANCE_MALFORMED")
    payload = {
        key: _require_non_empty_str(field=key, raw=raw.get(key))
        for key in (
            "identity_id",
            "identity_kind",
            "authority_owner",
            "bound_account_identity",
            "bound_venue_identity",
            "bound_td_mode",
            "settlement_currency",
            "identity_provenance_class",
            "identity_digest",
            "contract_status",
            "runtime_instance_present",
            "concrete_uid_corroborated",
            "observation_vs_authority_class",
            "authority_effect",
            "instance_digest",
            "provenance_digest",
        )
    }
    if payload["identity_provenance_class"] != PROVENANCE_EXPLICIT_TYPED_BINDING:
        raise BoundAccountIdentityRuntimeBindingError(
            "D4_RUNTIME_PROVENANCE_NOT_EXPLICIT_TYPED_BINDING:"
            f"{payload['identity_provenance_class']}"
        )
    if payload["concrete_uid_corroborated"] != CONCRETE_UID_CORROBORATED_TOKEN:
        raise BoundAccountIdentityRuntimeBindingError(
            "D4_RUNTIME_CANNOT_SET_CONCRETE_UID_CORROBORATED"
        )
    if payload["runtime_instance_present"] != RUNTIME_INSTANCE_PRESENT_TOKEN:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_INSTANCE_PRESENT_TOKEN_INVALID")
    if payload["contract_status"] != CONTRACT_STATUS_PROVEN:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_CONTRACT_STATUS_NOT_PROVEN")
    digest_payload = {
        key: payload[key] for key in payload if key not in {"instance_digest", "provenance_digest"}
    }
    expected_instance = compute_d4_runtime_instance_digest_v1(digest_payload)
    if payload["instance_digest"] != expected_instance:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_INSTANCE_DIGEST_MISMATCH")
    expected_provenance = compute_d4_runtime_instance_digest_v1(
        {**digest_payload, "instance_digest": payload["instance_digest"]}
    )
    if payload["provenance_digest"] != expected_provenance:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_PROVENANCE_DIGEST_MISMATCH")
    rebuilt = compute_bound_account_identity_digest_v1(
        {
            "identity_id": payload["identity_id"],
            "bound_account_identity": payload["bound_account_identity"],
            "bound_venue_identity": payload["bound_venue_identity"],
            "bound_td_mode": payload["bound_td_mode"],
            "settlement_currency": payload["settlement_currency"],
            "identity_provenance_class": payload["identity_provenance_class"],
        }
    )
    if rebuilt != payload["identity_digest"]:
        raise BoundAccountIdentityRuntimeBindingError("D4_RUNTIME_IDENTITY_DIGEST_MISMATCH")
    return BoundAccountIdentityRuntimeBindingV1(**payload)


def inspect_bound_account_identity_runtime_binding_status_v1(
    *,
    store_root: Path | str | None = None,
) -> BoundAccountIdentityRuntimeBindingStatusV1:
    _assert_runtime_pins()
    canonical_present = (
        TRUE_TOKEN if BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT is True else FALSE_TOKEN
    )
    if store_root is None:
        return BoundAccountIdentityRuntimeBindingStatusV1(
            contract_status=CONTRACT_STATUS_PROVEN,
            runtime_instance_present=RUNTIME_INSTANCE_ABSENT_TOKEN,
            concrete_uid_corroborated=CONCRETE_UID_CORROBORATED_TOKEN,
            canonical_runtime_instance_present=canonical_present,
            artifact_present=FALSE_TOKEN,
        )
    path = d4_runtime_instance_path_v1(store_root=store_root)
    if not path.is_file():
        return BoundAccountIdentityRuntimeBindingStatusV1(
            contract_status=CONTRACT_STATUS_PROVEN,
            runtime_instance_present=RUNTIME_INSTANCE_ABSENT_TOKEN,
            concrete_uid_corroborated=CONCRETE_UID_CORROBORATED_TOKEN,
            canonical_runtime_instance_present=canonical_present,
            artifact_present=FALSE_TOKEN,
        )
    loaded = load_bound_account_identity_runtime_binding_v1(store_root=store_root)
    return BoundAccountIdentityRuntimeBindingStatusV1(
        contract_status=loaded.contract_status,
        runtime_instance_present=loaded.runtime_instance_present,
        concrete_uid_corroborated=CONCRETE_UID_CORROBORATED_TOKEN,
        canonical_runtime_instance_present=canonical_present,
        artifact_present=TRUE_TOKEN,
    )
