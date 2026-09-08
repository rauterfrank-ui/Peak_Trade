"""Owner Network-Session authority producer. Distinct from Flatten issuance.

Does not evaluate Flatten GO. Does not POST. Does not set
network_session_authorized. Never fills missing fields, never reads env,
never parses chat, and never treats CLI flags or standing Live flags as
authority. Flatten issuance artifacts cannot mint this contract.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE,
    AUTHORITY_SOURCE_CANONICAL_OWNER_NETWORK_SESSION,
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FLATTEN_GRANT_CANNOT_AUTHORIZE_NETWORK_SESSION,
    FLATTEN_SECTION,
    FORBIDDEN_AUTHORITY_SOURCES,
    INSTRUMENT_ID,
    NETWORK_SESSION_ACTION,
    NETWORK_SESSION_AUTHORITY_ID_FIELDS,
    NETWORK_SESSION_CANNOT_AUTHORIZE_FLATTEN,
    NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR,
    NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
    NETWORK_SESSION_PURPOSE_EXPECTED,
    NETWORK_SESSION_SCHEMA_VERSION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

NETWORK_SESSION_INPUT_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "authority_type",
    "authority_source",
    "issued_at",
    "section",
    "purpose",
    "action",
    "origin_main_sha",
    "exact_envelope_id",
    "instrument_id",
    "confirm_token",
    "single_use",
    "consumed",
    "retry_allowed",
    "second_submit_allowed",
    "flatten_grant_cannot_authorize_this",
    "live_flags_cannot_authorize_this",
)


class FlattenNetworkSessionAuthorityError(RuntimeError):
    """Fail-closed Owner network-session producer violation."""


def network_session_authority_id_v1(payload: Mapping[str, Any]) -> str:
    missing = [name for name in NETWORK_SESSION_AUTHORITY_ID_FIELDS if name not in payload]
    if missing:
        raise FlattenNetworkSessionAuthorityError(
            "NETWORK_SESSION_AUTHORITY_ID_FIELDS_MISSING:" + ",".join(missing)
        )
    material = {name: payload[name] for name in NETWORK_SESSION_AUTHORITY_ID_FIELDS}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _bind_reasons(explicit: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if str(explicit.get("schema_version") or "") != NETWORK_SESSION_SCHEMA_VERSION:
        reasons.append("NETWORK_SESSION_SCHEMA_VERSION_MISMATCH")
    authority_type = str(explicit.get("authority_type") or "")
    if authority_type == AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE:
        reasons.append("FLATTEN_GRANT_CANNOT_AUTHORIZE_NETWORK_SESSION")
    if authority_type != AUTHORITY_TYPE_OWNER_NETWORK_SESSION:
        reasons.append("NETWORK_SESSION_AUTHORITY_TYPE_MISMATCH")
    source = str(explicit.get("authority_source") or "").strip()
    if source == AUTHORITY_SOURCE_CANONICAL_OWNER_ISSUANCE:
        reasons.append("FLATTEN_GRANT_SOURCE_CANNOT_AUTHORIZE_NETWORK_SESSION")
    if source != AUTHORITY_SOURCE_CANONICAL_OWNER_NETWORK_SESSION:
        reasons.append("NETWORK_SESSION_AUTHORITY_SOURCE_NOT_CANONICAL")
    if source in FORBIDDEN_AUTHORITY_SOURCES:
        reasons.append("NETWORK_SESSION_AUTHORITY_SOURCE_FORBIDDEN")
    if not str(explicit.get("issued_at") or "").strip():
        reasons.append("NETWORK_SESSION_ISSUED_AT_REQUIRED")
    if str(explicit.get("section") or "") != FLATTEN_SECTION:
        reasons.append("NETWORK_SESSION_SECTION_MISMATCH")
    if str(explicit.get("purpose") or "") != NETWORK_SESSION_PURPOSE_EXPECTED:
        reasons.append("NETWORK_SESSION_PURPOSE_MISMATCH")
    if str(explicit.get("action") or "") != NETWORK_SESSION_ACTION:
        reasons.append("NETWORK_SESSION_ACTION_MISMATCH")
    if str(explicit.get("origin_main_sha") or "").strip().lower() != BOUND_ORIGIN_MAIN_SHA:
        reasons.append("NETWORK_SESSION_SHA_MISMATCH")
    if str(explicit.get("exact_envelope_id") or "") != BOUND_FROZEN_ENVELOPE_ID:
        reasons.append("NETWORK_SESSION_ENVELOPE_MISMATCH")
    if str(explicit.get("instrument_id") or "") != INSTRUMENT_ID:
        reasons.append("NETWORK_SESSION_INSTRUMENT_MISMATCH")
    confirm = str(explicit.get("confirm_token") or "")
    if confirm == FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("FLATTEN_CONFIRM_TOKEN_CANNOT_AUTHORIZE_NETWORK_SESSION")
    if confirm != NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED:
        reasons.append("NETWORK_SESSION_CONFIRM_TOKEN_MISMATCH")
    if explicit.get("single_use") is not True:
        reasons.append("NETWORK_SESSION_SINGLE_USE_REQUIRED")
    if explicit.get("consumed") is not False:
        reasons.append("NETWORK_SESSION_CONSUMED_MUST_BE_FALSE")
    if explicit.get("retry_allowed") is not False:
        reasons.append("NETWORK_SESSION_RETRY_MUST_BE_FALSE")
    if explicit.get("second_submit_allowed") is not False:
        reasons.append("NETWORK_SESSION_SECOND_SUBMIT_MUST_BE_FALSE")
    if explicit.get("flatten_grant_cannot_authorize_this") is not True:
        reasons.append("NETWORK_SESSION_FLATTEN_GRANT_SEPARATION_REQUIRED")
    if explicit.get("live_flags_cannot_authorize_this") is not True:
        reasons.append("NETWORK_SESSION_LIVE_FLAGS_SEPARATION_REQUIRED")
    if FLATTEN_GRANT_CANNOT_AUTHORIZE_NETWORK_SESSION is not True:
        reasons.append("NETWORK_SESSION_STANDING_FLATTEN_SEPARATION_DRIFT")
    if NETWORK_SESSION_CANNOT_AUTHORIZE_FLATTEN is not True:
        reasons.append("NETWORK_SESSION_STANDING_FLATTEN_INVERSE_DRIFT")
    if NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR is not True:
        reasons.append("NETWORK_SESSION_STANDING_NO_SEND_DRIFT")
    return reasons


def issue_owner_network_session_authority_v1(
    *, explicit: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Mint issued=true only from a fully explicit canonical Owner input."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenNetworkSessionAuthorityError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    deny = {
        "issued": False,
        "artifact": None,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "FLATTEN_GRANT_IS_NOT_SESSION_AUTHORITY": True,
        "LIVE_FLAGS_ARE_NOT_SESSION_AUTHORITY": True,
    }
    if explicit is None:
        return {**deny, "reasons": ["NETWORK_SESSION_EXPLICIT_INPUT_MISSING"]}
    if "issued" in explicit:
        return {**deny, "reasons": ["NETWORK_SESSION_INPUT_MUST_NOT_SELF_ATTEST_ISSUED"]}
    reasons: list[str] = []
    missing = [name for name in NETWORK_SESSION_INPUT_REQUIRED_FIELDS if name not in explicit]
    if missing:
        reasons.append("NETWORK_SESSION_FIELDS_MISSING:" + ",".join(missing))
    reasons.extend(_bind_reasons(explicit))
    if reasons:
        return {**deny, "reasons": reasons}
    artifact: dict[str, Any] = {
        "schema_version": str(explicit["schema_version"]),
        "authority_type": str(explicit["authority_type"]),
        "authority_source": str(explicit["authority_source"]),
        "issued": True,
        "issued_at": str(explicit["issued_at"]),
        "section": str(explicit["section"]),
        "purpose": str(explicit["purpose"]),
        "action": str(explicit["action"]),
        "origin_main_sha": str(explicit["origin_main_sha"]).strip().lower(),
        "exact_envelope_id": str(explicit["exact_envelope_id"]),
        "instrument_id": str(explicit["instrument_id"]),
        "confirm_token": str(explicit["confirm_token"]),
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "flatten_grant_cannot_authorize_this": True,
        "live_flags_cannot_authorize_this": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "AUTHORITY_IS_SINGLE_USE": True,
        "WIRE_SEND_NOT_AUTHORIZED_BY_THIS_REPAIR": True,
    }
    artifact["authority_id"] = network_session_authority_id_v1(artifact)
    return {
        "issued": True,
        "reasons": [],
        "artifact": artifact,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
        "FLATTEN_GRANT_IS_NOT_SESSION_AUTHORITY": True,
        "LIVE_FLAGS_ARE_NOT_SESSION_AUTHORITY": True,
    }


def current_section_11_14_network_session_explicit_v1(*, issued_at: str) -> dict[str, Any]:
    """Fully explicit current-bind input. Not itself an issued artifact."""
    return {
        "schema_version": NETWORK_SESSION_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_NETWORK_SESSION,
        "issued_at": str(issued_at),
        "section": FLATTEN_SECTION,
        "purpose": NETWORK_SESSION_PURPOSE_EXPECTED,
        "action": NETWORK_SESSION_ACTION,
        "origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "exact_envelope_id": BOUND_FROZEN_ENVELOPE_ID,
        "instrument_id": INSTRUMENT_ID,
        "confirm_token": NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "flatten_grant_cannot_authorize_this": True,
        "live_flags_cannot_authorize_this": True,
    }


def verify_owner_network_session_authority_v1(
    *,
    issuance: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> dict[str, Any]:
    """Verify a network-session artifact. Never mints issued=true. Does not POST."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenNetworkSessionAuthorityError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if issuance is None:
        return {
            "accepted": False,
            "issued": False,
            "reasons": ["NETWORK_SESSION_OWNER_AUTHORITY_MISSING"],
            "authority_id": "",
            "EVALUATOR_IS_NOT_ISSUER": True,
        }
    reasons: list[str] = []
    missing = [
        name
        for name in (*NETWORK_SESSION_INPUT_REQUIRED_FIELDS, "issued", "authority_id")
        if name not in issuance
    ]
    if missing:
        reasons.append("NETWORK_SESSION_FIELDS_MISSING:" + ",".join(missing))
    reasons.extend(_bind_reasons(issuance))
    if issuance.get("issued") is not True:
        reasons.append("NETWORK_SESSION_ARTIFACT_NOT_ISSUED")
    bound_sha = str(issuance.get("origin_main_sha") or "").strip().lower()
    expected_sha = str(origin_main_sha or "").strip().lower()
    if bound_sha != expected_sha:
        reasons.append("NETWORK_SESSION_SHA_MISMATCH")
    if str(issuance.get("instrument_id") or "") != str(instrument_id or "").strip():
        reasons.append("NETWORK_SESSION_INSTRUMENT_MISMATCH")
    if str(issuance.get("exact_envelope_id") or "") != str(exact_envelope_id or "").strip():
        reasons.append("NETWORK_SESSION_ENVELOPE_MISMATCH")
    authority_id = ""
    try:
        authority_id = network_session_authority_id_v1(issuance)
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"NETWORK_SESSION_AUTHORITY_ID_UNCOMPUTABLE:{exc}")
    recorded_id = str(issuance.get("authority_id") or "")
    if authority_id and recorded_id and recorded_id != authority_id:
        reasons.append("NETWORK_SESSION_AUTHORITY_ID_MISMATCH")
    runtime_issued = (not reasons) and issuance.get("issued") is True
    return {
        "accepted": not reasons,
        "issued": runtime_issued,
        "reasons": reasons,
        "authority_id": recorded_id or authority_id,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "WIRE_SEND_NOT_AUTHORIZED_BY_THIS_REPAIR": True,
    }


def network_session_owner_contract_schema_v1() -> dict[str, Any]:
    """Unbound schema. Mechanism expected-values are not issued authority."""
    return {
        "kind": AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
        "ISSUED": False,
        "PRESENT": False,
        "schema_version": NETWORK_SESSION_SCHEMA_VERSION,
        "action": NETWORK_SESSION_ACTION,
        "purpose_expected": NETWORK_SESSION_PURPOSE_EXPECTED,
        "confirm_token_expected": NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
        "flatten_grant_cannot_authorize_network_session": True,
        "network_session_cannot_authorize_flatten": True,
        "wire_send_not_authorized_by_this_repair": True,
        "standing_live_enabled": bool(LIVE_ENABLED),
        "standing_live_armed": bool(LIVE_ARMED),
        "standing_canary_authorized": bool(CANARY_AUTHORIZED),
        "standing_post_allowed": bool(POST_ALLOWED),
        "required_fields": list(NETWORK_SESSION_INPUT_REQUIRED_FIELDS),
        "MECHANISM_EXPECTED_VALUES_ARE_NOT_ISSUED_AUTHORITY": True,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "CHAT_IS_NOT_AUTHORITY": True,
        "ENV_IS_NOT_AUTHORITY": True,
        "CLI_FLAG_IS_NOT_AUTHORITY": True,
    }
