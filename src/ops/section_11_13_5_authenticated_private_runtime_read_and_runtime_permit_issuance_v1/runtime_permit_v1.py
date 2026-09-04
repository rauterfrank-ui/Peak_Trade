"""Runtime BoundedActivationPermit issuance with size and observation binding.

Extends the proven P16 schema without rewriting it. Runtime issuance requires
fresh observation identity and size binding. Price remains the separate
FlattenPricePermitV1 at pre-send (N08); public GET is not on this path.
Does not POST. Does not flatten. Implementation Owner-GOs cannot be permit.owner_go.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    AUTHORIZED_ACCOUNT_UID,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESHNESS_POLICY_MAX_AGE_MS,
    OWNER_GO,
    PERMIT_OWNER_GO_CANONICAL,
    TARGET_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    BOUNDED_ACTIVATION_AUTHORITY_KIND,
    BOUNDED_ACTIVATION_PERMIT_KIND,
    BOUNDED_ACTIVATION_PURPOSE_CANONICAL,
    BoundedActivationPermitV1,
    FORBIDDEN_BOUNDED_ACTIVATION_OWNER_GOS,
    evaluate_bounded_activation_permit_v1,
)

PRICE_BINDING_ROLE = "NOT_BOUND_PUBLIC_GET_NOT_ON_PERMIT_PATH_FLATTEN_PRICE_PERMIT_IS_N08"
RUNTIME_PERMIT_SCHEMA_VERSION = "runtime_bounded_activation_permit.v1"

REASON_OBSERVATION_MISSING = "RUNTIME_PERMIT_OBSERVATION_MISSING"
REASON_OBSERVATION_NOT_FRESH = "RUNTIME_PERMIT_OBSERVATION_NOT_FRESH"
REASON_EMPTY_DATA = "RUNTIME_PERMIT_EMPTY_DATA_IS_NOT_ZERO"
REASON_NOT_OBSERVED = "RUNTIME_PERMIT_TARGET_INSTRUMENT_NOT_OBSERVED"
REASON_ZERO_POSITION = "RUNTIME_PERMIT_ZERO_POSITION_IS_NOT_FLATTENABLE"
REASON_AMBIGUOUS = "RUNTIME_PERMIT_AMBIGUOUS_OR_CONTRADICTORY"
REASON_MALFORMED = "RUNTIME_PERMIT_MALFORMED_OBSERVATION"
REASON_AUTH_FAILURE = "RUNTIME_PERMIT_AUTHENTICATION_FAILURE"
REASON_TRANSPORT_FAILURE = "RUNTIME_PERMIT_TRANSPORT_FAILURE"
REASON_HTTP_OR_OKX = "RUNTIME_PERMIT_HTTP_OR_OKX_ERROR"
REASON_SIZE_MISSING = "RUNTIME_PERMIT_SIZE_BINDING_MISSING"
REASON_OBSERVATION_IDENTITY_MISSING = "RUNTIME_PERMIT_OBSERVATION_IDENTITY_MISSING"
REASON_BODY_SHA_MISSING = "RUNTIME_PERMIT_OBSERVATION_BODY_SHA256_MISSING"
REASON_INSTRUMENT_MISMATCH = "RUNTIME_PERMIT_INSTRUMENT_MISMATCH"
REASON_SHA_MISMATCH = "RUNTIME_PERMIT_BOUND_SHA_MISMATCH"
REASON_IMPLEMENTATION_GO_AS_PERMIT = "RUNTIME_PERMIT_IMPLEMENTATION_GO_FORBIDDEN_AS_PERMIT_OWNER_GO"
REASON_LIVE_AUTHORIZED = "RUNTIME_PERMIT_GLOBAL_LIVE_AUTHORIZED_CANNOT_SUBSTITUTE"
REASON_POST = "RUNTIME_PERMIT_POST_FORBIDDEN"
REASON_FLATTEN = "RUNTIME_PERMIT_FLATTEN_EXECUTE_FORBIDDEN"
REASON_UNSIGNED_TRANSPORT = "RUNTIME_PERMIT_UNSIGNED_FLATTEN_TRANSPORT_FORBIDDEN"
REASON_HISTORICAL = "RUNTIME_PERMIT_HISTORICAL_OBSERVATION_FORBIDDEN"
REASON_P16_SCHEMA = "RUNTIME_PERMIT_P16_SCHEMA_DENIED"
REASON_PRICE_CLAIMED = "RUNTIME_PERMIT_PRICE_BINDING_CLAIM_WITHOUT_PROVEN_PRODUCER"


class RuntimePermitIssuanceError(RuntimeError):
    """Fail-closed runtime permit issuance violation."""


@dataclass(frozen=True)
class RuntimeIssuedPermitV1:
    """Runtime permit artifact. Not flatten-execute. Not a wire receipt."""

    kind: str
    purpose: str
    owner_go: str
    bound_origin_main_sha: str
    instrument_id: str
    account_uid_binding: str
    observation_identity: str
    observation_body_sha256: str
    size_binding: str
    price_binding_role: str
    issuance_monotonic_ms: int
    not_after_monotonic_ms: int
    freshness_max_age_ms: int
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "purpose": self.purpose,
            "owner_go": self.owner_go,
            "bound_origin_main_sha": self.bound_origin_main_sha,
            "instrument_id": self.instrument_id,
            "account_uid_binding": self.account_uid_binding,
            "observation_identity": self.observation_identity,
            "observation_body_sha256": self.observation_body_sha256,
            "size_binding": self.size_binding,
            "price_binding_role": self.price_binding_role,
            "issuance_monotonic_ms": int(self.issuance_monotonic_ms),
            "not_after_monotonic_ms": int(self.not_after_monotonic_ms),
            "freshness_max_age_ms": int(self.freshness_max_age_ms),
            "schema_version": self.schema_version,
            "flatten_execute_not_implied": True,
            "network_session_not_implied": True,
            "post_not_implied": True,
            "live_authorized_not_implied": True,
        }

    def canonical_identity_material_v1(self) -> str:
        payload = {
            "account_uid_binding": self.account_uid_binding,
            "bound_origin_main_sha": self.bound_origin_main_sha,
            "freshness_max_age_ms": int(self.freshness_max_age_ms),
            "instrument_id": self.instrument_id,
            "issuance_monotonic_ms": int(self.issuance_monotonic_ms),
            "kind": self.kind,
            "not_after_monotonic_ms": int(self.not_after_monotonic_ms),
            "observation_body_sha256": self.observation_body_sha256,
            "observation_identity": self.observation_identity,
            "owner_go": self.owner_go,
            "price_binding_role": self.price_binding_role,
            "purpose": self.purpose,
            "schema_version": self.schema_version,
            "size_binding": self.size_binding,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def identity_sha256_v1(self) -> str:
        return hashlib.sha256(self.canonical_identity_material_v1().encode("utf-8")).hexdigest()

    def p16_permit_v1(self) -> BoundedActivationPermitV1:
        return BoundedActivationPermitV1(
            kind=self.kind,
            purpose=self.purpose,
            owner_go=self.owner_go,
            bound_origin_main_sha=self.bound_origin_main_sha,
            instrument_id=self.instrument_id,
            not_after_monotonic_ms=self.not_after_monotonic_ms,
        )


def runtime_permit_identity_sha256_v1(permit: Mapping[str, Any] | RuntimeIssuedPermitV1) -> str:
    if isinstance(permit, RuntimeIssuedPermitV1):
        return permit.identity_sha256_v1()
    material = json.dumps(
        {
            "account_uid_binding": str(permit.get("account_uid_binding") or ""),
            "bound_origin_main_sha": str(permit.get("bound_origin_main_sha") or ""),
            "freshness_max_age_ms": int(permit.get("freshness_max_age_ms") or 0),
            "instrument_id": str(permit.get("instrument_id") or ""),
            "issuance_monotonic_ms": int(permit.get("issuance_monotonic_ms") or 0),
            "kind": str(permit.get("kind") or ""),
            "not_after_monotonic_ms": int(permit.get("not_after_monotonic_ms") or 0),
            "observation_body_sha256": str(permit.get("observation_body_sha256") or ""),
            "observation_identity": str(permit.get("observation_identity") or ""),
            "owner_go": str(permit.get("owner_go") or ""),
            "price_binding_role": str(permit.get("price_binding_role") or ""),
            "purpose": str(permit.get("purpose") or ""),
            "schema_version": str(permit.get("schema_version") or ""),
            "size_binding": str(permit.get("size_binding") or ""),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def evaluate_runtime_permit_issuance_v1(
    *,
    origin_main_sha: str,
    instrument_id: str,
    observation_class: str | None,
    observation_identity: str | None,
    observation_body_sha256: str | None,
    size_binding: str | None,
    freshness_allowed: bool,
    freshness_reject_reason: str | None,
    issuance_monotonic_ms: int,
    response_received_monotonic_ms: int | None,
    result_class: str | None,
    authentication_failure: str | None = None,
    transport_error: str | None = None,
    unsigned_flatten_transport_used: bool = False,
    live_authorized_claim: bool = False,
    post_performed_claim: bool = False,
    flatten_execute_authorized_claim: bool = False,
    historical_reuse_claim: bool = False,
    price_binding_claimed: str | None = None,
    permit_owner_go: str | None = PERMIT_OWNER_GO_CANONICAL,
    implementation_owner_go: str = OWNER_GO,
) -> tuple[RuntimeIssuedPermitV1 | None, tuple[str, ...]]:
    """Issue only when every required runtime-read gate is fresh PASS."""
    reasons: list[str] = []
    bound_sha = str(origin_main_sha or "").strip().lower()
    expected = str(EXPECTED_ORIGIN_MAIN_SHA or "").strip().lower()
    if bound_sha != expected:
        reasons.append(REASON_SHA_MISMATCH)
    target = str(instrument_id or "").strip()
    if target != TARGET_INSTRUMENT_ID:
        reasons.append(REASON_INSTRUMENT_MISMATCH)
    if live_authorized_claim is True:
        reasons.append(REASON_LIVE_AUTHORIZED)
    if post_performed_claim is True:
        reasons.append(REASON_POST)
    if flatten_execute_authorized_claim is True:
        reasons.append(REASON_FLATTEN)
    if unsigned_flatten_transport_used is True:
        reasons.append(REASON_UNSIGNED_TRANSPORT)
    if historical_reuse_claim is True:
        reasons.append(REASON_HISTORICAL)
    if str(authentication_failure or "").strip():
        reasons.append(REASON_AUTH_FAILURE)
    if str(transport_error or "").strip():
        reasons.append(REASON_TRANSPORT_FAILURE)
    if (
        str(price_binding_claimed or "").strip()
        and str(price_binding_claimed) != PRICE_BINDING_ROLE
    ):
        reasons.append(REASON_PRICE_CLAIMED)

    go = str(permit_owner_go or "").strip()
    if not go:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_PERMIT)
    elif go == implementation_owner_go or go in FORBIDDEN_BOUNDED_ACTIVATION_OWNER_GOS:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_PERMIT)
    elif go != PERMIT_OWNER_GO_CANONICAL:
        reasons.append(REASON_IMPLEMENTATION_GO_AS_PERMIT)

    klass = str(observation_class or "").strip()
    if str(result_class or "").strip() and str(result_class) != "HTTP_200_OKX_0":
        if str(result_class) in {"TRANSPORT_OR_CLIENT_FAIL"}:
            if REASON_TRANSPORT_FAILURE not in reasons:
                reasons.append(REASON_TRANSPORT_FAILURE)
        elif str(result_class) in {"HTTP_401_OKX_50110"}:
            if REASON_AUTH_FAILURE not in reasons:
                reasons.append(REASON_AUTH_FAILURE)
        else:
            reasons.append(REASON_HTTP_OR_OKX)
    if not klass:
        reasons.append(REASON_OBSERVATION_MISSING)
    elif klass == "CASE_C_EMPTY_DATA_NOT_ZERO":
        reasons.append(REASON_EMPTY_DATA)
    elif klass == "CASE_D_TARGET_NOT_OBSERVED":
        reasons.append(REASON_NOT_OBSERVED)
    elif klass == "CASE_B_TARGET_ZERO":
        reasons.append(REASON_ZERO_POSITION)
    elif klass == "CASE_F_AMBIGUOUS":
        reasons.append(REASON_AMBIGUOUS)
    elif klass == "CASE_E_HTTP_OR_OKX_ERROR":
        reasons.append(REASON_HTTP_OR_OKX)
    elif klass != "CASE_A_TARGET_NONZERO":
        reasons.append(REASON_MALFORMED)

    if freshness_allowed is not True:
        reasons.append(REASON_OBSERVATION_NOT_FRESH)
        if freshness_reject_reason:
            reasons.append(str(freshness_reject_reason))
    if response_received_monotonic_ms is None:
        reasons.append(REASON_OBSERVATION_NOT_FRESH)

    ident = str(observation_identity or "").strip()
    if not ident:
        reasons.append(REASON_OBSERVATION_IDENTITY_MISSING)
    body_sha = str(observation_body_sha256 or "").strip().lower()
    if not body_sha or len(body_sha) != 64:
        reasons.append(REASON_BODY_SHA_MISSING)
    size = str(size_binding or "").strip()
    if not size or size in {"0", "+0", "-0", "UNRESOLVED", "NONE"}:
        reasons.append(REASON_SIZE_MISSING)

    if reasons:
        return (None, tuple(reasons))

    received = int(response_received_monotonic_ms or 0)
    issuance_ms = int(issuance_monotonic_ms)
    not_after = received + int(FRESHNESS_POLICY_MAX_AGE_MS)
    if issuance_ms > not_after:
        return (None, (REASON_OBSERVATION_NOT_FRESH,))

    permit = RuntimeIssuedPermitV1(
        kind=BOUNDED_ACTIVATION_PERMIT_KIND,
        purpose=BOUNDED_ACTIVATION_PURPOSE_CANONICAL,
        owner_go=PERMIT_OWNER_GO_CANONICAL,
        bound_origin_main_sha=bound_sha,
        instrument_id=target,
        account_uid_binding=AUTHORIZED_ACCOUNT_UID,
        observation_identity=ident,
        observation_body_sha256=body_sha,
        size_binding=size,
        price_binding_role=PRICE_BINDING_ROLE,
        issuance_monotonic_ms=issuance_ms,
        not_after_monotonic_ms=not_after,
        freshness_max_age_ms=int(FRESHNESS_POLICY_MAX_AGE_MS),
        schema_version=RUNTIME_PERMIT_SCHEMA_VERSION,
    )
    p16_ok, p16_reasons = evaluate_bounded_activation_permit_v1(
        permit=permit.p16_permit_v1(),
        origin_main_sha=bound_sha,
        instrument_id=target,
        evaluation_monotonic_ms=issuance_ms,
    )
    if not p16_ok:
        return (None, (REASON_P16_SCHEMA, *p16_reasons))
    return (permit, ())


def runtime_permit_audit_v1(
    *,
    permit: RuntimeIssuedPermitV1 | None,
    deny_reasons: tuple[str, ...],
) -> dict[str, Any]:
    issued = permit is not None and not deny_reasons
    payload = permit.to_dict() if permit is not None else {}
    identity = permit.identity_sha256_v1() if permit is not None else None
    return {
        "kind": BOUNDED_ACTIVATION_AUTHORITY_KIND,
        "schema_version": RUNTIME_PERMIT_SCHEMA_VERSION,
        "accepted": issued,
        "issued": issued,
        "reasons": list(deny_reasons),
        "permit_identity_sha256": identity,
        "permit": payload,
        "implementation_go_is_not_permit": True,
        "global_live_authorized_cannot_substitute": True,
        "network_session_not_implied": True,
        "flatten_execute_not_implied": True,
        "post_not_implied": True,
        "price_binding_role": PRICE_BINDING_ROLE,
    }
