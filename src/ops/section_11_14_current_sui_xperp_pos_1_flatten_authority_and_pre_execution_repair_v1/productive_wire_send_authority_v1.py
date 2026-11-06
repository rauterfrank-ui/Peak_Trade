"""Offline evaluator for OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1.

Never mints. Does not arm. Does not set network_session_authorized. Does not
POST. Does not call inner.send. Does not consume.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE,
    AUTHORITY_TYPE_OWNER_NETWORK_SESSION,
    FLATTEN_CONFIRM_TOKEN_EXPECTED,
    FORBIDDEN_AUTHORITY_SOURCES,
    NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    PRODUCTIVE_WIRE_SEND_ACTION,
    PRODUCTIVE_WIRE_SEND_AUTHORITY_ID_FIELDS,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_WIRE_SEND_INPUT_REQUIRED_FIELDS,
    PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
    PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

FLATTEN_SECTION_EXPECTED = "11.14"


class FlattenProductiveWireSendAuthorityError(RuntimeError):
    """Fail-closed Owner productive wire-send evaluator violation."""


def productive_wire_send_authority_id_v1(payload: Mapping[str, Any]) -> str:
    missing = [name for name in PRODUCTIVE_WIRE_SEND_AUTHORITY_ID_FIELDS if name not in payload]
    if missing:
        raise FlattenProductiveWireSendAuthorityError(
            "WIRE_SEND_AUTHORITY_ID_FIELDS_MISSING:" + ",".join(missing)
        )
    material = {name: payload[name] for name in PRODUCTIVE_WIRE_SEND_AUTHORITY_ID_FIELDS}
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _bind_reasons(explicit: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if str(explicit.get("schema_version") or "") != PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION:
        reasons.append("WIRE_SEND_SCHEMA_VERSION_MISMATCH")
    authority_type = str(explicit.get("authority_type") or "")
    if authority_type == AUTHORITY_TYPE_OWNER_FLATTEN_ISSUANCE:
        reasons.append("FLATTEN_GRANT_CANNOT_AUTHORIZE_WIRE_SEND")
    if authority_type == AUTHORITY_TYPE_OWNER_NETWORK_SESSION:
        reasons.append("NETWORK_SESSION_GRANT_CANNOT_AUTHORIZE_WIRE_SEND")
    if authority_type != AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND:
        reasons.append("WIRE_SEND_AUTHORITY_TYPE_MISMATCH")
    source = str(explicit.get("authority_source") or "").strip()
    if source != AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND:
        reasons.append("WIRE_SEND_AUTHORITY_SOURCE_NOT_CANONICAL")
    if source in FORBIDDEN_AUTHORITY_SOURCES:
        reasons.append("WIRE_SEND_AUTHORITY_SOURCE_FORBIDDEN")
    if not str(explicit.get("issued_at") or "").strip():
        reasons.append("WIRE_SEND_ISSUED_AT_REQUIRED")
    if str(explicit.get("section") or "") != FLATTEN_SECTION_EXPECTED:
        reasons.append("WIRE_SEND_SECTION_MISMATCH")
    if str(explicit.get("purpose") or "") != PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED:
        reasons.append("WIRE_SEND_PURPOSE_MISMATCH")
    if str(explicit.get("action") or "") != PRODUCTIVE_WIRE_SEND_ACTION:
        reasons.append("WIRE_SEND_ACTION_MISMATCH")
    confirm = str(explicit.get("confirm_token") or "")
    if confirm == FLATTEN_CONFIRM_TOKEN_EXPECTED:
        reasons.append("FLATTEN_CONFIRM_TOKEN_CANNOT_AUTHORIZE_WIRE_SEND")
    if confirm == NETWORK_SESSION_CONFIRM_TOKEN_EXPECTED:
        reasons.append("NETWORK_SESSION_CONFIRM_TOKEN_CANNOT_AUTHORIZE_WIRE_SEND")
    if confirm != PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED:
        reasons.append("WIRE_SEND_CONFIRM_TOKEN_MISMATCH")
    if explicit.get("single_use") is not True:
        reasons.append("WIRE_SEND_SINGLE_USE_REQUIRED")
    if explicit.get("consumed") is True:
        reasons.append("WIRE_SEND_CONSUMED_CANNOT_BE_REUSED")
    if explicit.get("consumed") is not False:
        reasons.append("WIRE_SEND_CONSUMED_MUST_BE_FALSE")
    if explicit.get("retry_allowed") is not False:
        reasons.append("WIRE_SEND_RETRY_MUST_BE_FALSE")
    if explicit.get("second_submit_allowed") is not False:
        reasons.append("WIRE_SEND_SECOND_SUBMIT_MUST_BE_FALSE")
    if explicit.get("network_session_grant_cannot_authorize_this") is not True:
        reasons.append("WIRE_SEND_NETWORK_SESSION_GRANT_SEPARATION_REQUIRED")
    if explicit.get("flatten_grant_cannot_authorize_this") is not True:
        reasons.append("WIRE_SEND_FLATTEN_GRANT_SEPARATION_REQUIRED")
    if explicit.get("live_flags_cannot_authorize_this") is not True:
        reasons.append("WIRE_SEND_LIVE_FLAGS_SEPARATION_REQUIRED")
    if explicit.get("session_arming_cannot_authorize_this") is not True:
        reasons.append("WIRE_SEND_SESSION_ARMING_SEPARATION_REQUIRED")
    return reasons


def verify_owner_productive_wire_send_authority_v1(
    *,
    issuance: Mapping[str, Any] | None,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
) -> dict[str, Any]:
    """Verify a wire-send artifact. Never mints. Does not POST. Does not consume."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveWireSendAuthorityError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    deny: dict[str, Any] = {
        "accepted": False,
        "issued": False,
        "consumed": False,
        "reasons": [],
        "authority_id": "",
        "EVALUATOR_IS_NOT_ISSUER": True,
        "INNER_SEND_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "SESSION_ARMING_EXECUTED": False,
        "NETWORK_SESSION_AUTHORIZED_CHANGED": False,
    }
    if issuance is None:
        return {**deny, "reasons": ["WIRE_SEND_OWNER_AUTHORITY_MISSING"]}
    reasons: list[str] = []
    missing = [
        name
        for name in (*PRODUCTIVE_WIRE_SEND_INPUT_REQUIRED_FIELDS, "issued", "authority_id")
        if name not in issuance
    ]
    if missing:
        reasons.append("WIRE_SEND_FIELDS_MISSING:" + ",".join(missing))
    reasons.extend(_bind_reasons(issuance))
    if issuance.get("issued") is not True:
        reasons.append("WIRE_SEND_ARTIFACT_NOT_ISSUED")
    bound_sha = str(issuance.get("origin_main_sha") or "").strip().lower()
    expected_sha = str(origin_main_sha or "").strip().lower()
    if bound_sha != expected_sha:
        reasons.append("WIRE_SEND_SHA_MISMATCH")
    if str(issuance.get("instrument_id") or "") != str(instrument_id or "").strip():
        reasons.append("WIRE_SEND_INSTRUMENT_MISMATCH")
    if str(issuance.get("exact_envelope_id") or "") != str(exact_envelope_id or "").strip():
        reasons.append("WIRE_SEND_ENVELOPE_MISMATCH")
    authority_id = ""
    try:
        authority_id = productive_wire_send_authority_id_v1(issuance)
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"WIRE_SEND_AUTHORITY_ID_UNCOMPUTABLE:{exc}")
    recorded_id = str(issuance.get("authority_id") or "")
    if authority_id and recorded_id and recorded_id != authority_id:
        reasons.append("WIRE_SEND_AUTHORITY_ID_MISMATCH")
    runtime_issued = (not reasons) and issuance.get("issued") is True
    consumed = issuance.get("consumed") is True
    accepted = (not reasons) and runtime_issued is True and consumed is False
    return {
        "accepted": accepted,
        "issued": runtime_issued,
        "consumed": consumed,
        "reasons": reasons,
        "authority_id": recorded_id or authority_id,
        "EVALUATOR_IS_NOT_ISSUER": True,
        "INNER_SEND_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "SESSION_ARMING_EXECUTED": False,
        "NETWORK_SESSION_AUTHORIZED_CHANGED": False,
    }
